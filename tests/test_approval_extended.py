"""
Tests for orchestration/approval.py — ApprovalRequest, AutoApprovalGate,
HumanApprovalGate, HybridApprovalGate, ApprovalQueue, simple_risk_scorer,
create_approval_gate.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from orchestration.approval import (
    ApprovalQueue,
    ApprovalRequest,
    ApprovalStatus,
    AutoApprovalGate,
    HumanApprovalGate,
    HybridApprovalGate,
    create_approval_gate,
    simple_risk_scorer,
)

# ---------------------------------------------------------------------------
# ApprovalRequest
# ---------------------------------------------------------------------------


class TestApprovalRequest:
    def test_is_expired_false_when_no_expires_at(self):
        req = ApprovalRequest()
        assert req.is_expired() is False

    def test_is_expired_false_when_future(self):
        req = ApprovalRequest(expires_at=datetime.now() + timedelta(hours=1))
        assert req.is_expired() is False

    def test_is_expired_true_when_past(self):
        req = ApprovalRequest(expires_at=datetime.now() - timedelta(seconds=1))
        assert req.is_expired() is True

    def test_is_expired_true_when_status_expired(self):
        req = ApprovalRequest(status=ApprovalStatus.EXPIRED)
        assert req.is_expired() is True

    def test_approve_sets_status(self):
        req = ApprovalRequest()
        req.approve(by="admin", reason="looks good")
        assert req.status == ApprovalStatus.APPROVED
        assert req.decided_by == "admin"
        assert req.reason == "looks good"
        assert req.decided_at is not None

    def test_reject_sets_status(self):
        req = ApprovalRequest()
        req.reject(by="admin", reason="too risky")
        assert req.status == ApprovalStatus.REJECTED
        assert req.decided_by == "admin"

    def test_to_dict_has_required_keys(self):
        req = ApprovalRequest(workflow_id="wf1", step_name="step1", content="do thing")
        d = req.to_dict()
        for key in (
            "id",
            "workflow_id",
            "step_name",
            "content",
            "status",
            "created_at",
        ):
            assert key in d

    def test_to_dict_status_is_string(self):
        req = ApprovalRequest()
        d = req.to_dict()
        assert isinstance(d["status"], str)


# ---------------------------------------------------------------------------
# AutoApprovalGate
# ---------------------------------------------------------------------------


class TestAutoApprovalGate:
    async def test_no_rules_default_true_auto_approved(self):
        gate = AutoApprovalGate(rules=[], default_approve=True)
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status == ApprovalStatus.AUTO_APPROVED

    async def test_no_rules_default_false_auto_rejected(self):
        gate = AutoApprovalGate(rules=[], default_approve=False)
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status == ApprovalStatus.AUTO_REJECTED

    async def test_rule_blocks_auto_rejected(self):
        def block_all(r):
            return False

        gate = AutoApprovalGate(rules=[block_all], default_approve=True)
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status == ApprovalStatus.AUTO_REJECTED

    async def test_rule_passes_default_true_auto_approved(self):
        def allow_all(r):
            return True

        gate = AutoApprovalGate(rules=[allow_all], default_approve=True)
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status == ApprovalStatus.AUTO_APPROVED

    async def test_check_status_returns_request(self):
        gate = AutoApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        found = await gate.check_status(req.id)
        assert found is not None
        assert found.id == req.id

    async def test_list_pending_empty_when_none_pending(self):
        gate = AutoApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        pending = await gate.list_pending()
        assert pending == []


# ---------------------------------------------------------------------------
# HumanApprovalGate
# ---------------------------------------------------------------------------


class TestHumanApprovalGate:
    async def test_notification_callback_called(self):
        callback = MagicMock()
        gate = HumanApprovalGate(notification_callback=callback)
        req = ApprovalRequest()
        await gate.request_approval(req)
        callback.assert_called_once_with(req)

    async def test_approve_happy_path(self):
        gate = HumanApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        result = await gate.approve(req.id, by="human")
        assert result is not None
        assert result.status == ApprovalStatus.APPROVED

    async def test_reject_happy_path(self):
        gate = HumanApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        result = await gate.reject(req.id, by="human", reason="no")
        assert result is not None
        assert result.status == ApprovalStatus.REJECTED

    async def test_reject_already_approved_returns_none(self):
        gate = HumanApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        await gate.approve(req.id, by="admin")
        result = await gate.reject(req.id, by="admin")
        assert result is None

    async def test_list_pending_marks_expired(self):
        gate = HumanApprovalGate(timeout_seconds=1)
        req = ApprovalRequest()
        await gate.request_approval(req)
        # Manually expire it
        gate.requests[req.id].expires_at = datetime.now() - timedelta(seconds=1)
        pending = await gate.list_pending()
        assert req.id not in [r.id for r in pending]
        assert gate.requests[req.id].status == ApprovalStatus.EXPIRED

    async def test_wait_for_decision_pre_approved(self):
        gate = HumanApprovalGate()
        req = ApprovalRequest()
        await gate.request_approval(req)
        await gate.approve(req.id, by="admin")
        result = await gate.wait_for_decision(req.id, poll_interval=0.01)
        assert result.status == ApprovalStatus.APPROVED

    async def test_wait_for_decision_bad_id_raises(self):
        gate = HumanApprovalGate()
        with pytest.raises(ValueError):
            await gate.wait_for_decision("nonexistent", poll_interval=0.01)


# ---------------------------------------------------------------------------
# HybridApprovalGate
# ---------------------------------------------------------------------------


class TestHybridApprovalGate:
    def _low_risk_scorer(self, r):
        return 0.1

    def _high_risk_scorer(self, r):
        return 0.9

    async def test_low_risk_goes_to_auto_gate(self):
        gate = HybridApprovalGate(risk_scorer=self._low_risk_scorer, risk_threshold=0.5)
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status in (
            ApprovalStatus.AUTO_APPROVED,
            ApprovalStatus.AUTO_REJECTED,
        )

    async def test_high_risk_goes_to_human_gate(self):
        gate = HybridApprovalGate(
            risk_scorer=self._high_risk_scorer, risk_threshold=0.5
        )
        req = ApprovalRequest()
        result = await gate.request_approval(req)
        assert result.status == ApprovalStatus.PENDING

    async def test_check_status_searches_both(self):
        gate = HybridApprovalGate(risk_scorer=self._low_risk_scorer, risk_threshold=0.5)
        req = ApprovalRequest()
        await gate.request_approval(req)
        found = await gate.check_status(req.id)
        assert found is not None

    async def test_list_pending_combines(self):
        gate = HybridApprovalGate(
            risk_scorer=self._high_risk_scorer, risk_threshold=0.5
        )
        req = ApprovalRequest()
        await gate.request_approval(req)
        pending = await gate.list_pending()
        assert len(pending) >= 1


# ---------------------------------------------------------------------------
# ApprovalQueue
# ---------------------------------------------------------------------------


class TestApprovalQueue:
    async def test_submit_returns_result(self):
        gate = AutoApprovalGate()
        queue = ApprovalQueue(gate)
        req = ApprovalRequest(content="do something")
        result = await queue.submit(req)
        assert result is not None

    async def test_get_pending_delegates_to_gate(self):
        gate = HumanApprovalGate()
        queue = ApprovalQueue(gate)
        req = ApprovalRequest()
        await queue.submit(req)
        pending = await queue.get_pending()
        assert len(pending) == 1

    async def test_get_history_all(self):
        gate = AutoApprovalGate()
        queue = ApprovalQueue(gate)
        await queue.submit(ApprovalRequest())
        await queue.submit(ApprovalRequest())
        history = queue.get_history()
        assert len(history) == 2

    async def test_get_history_filtered_by_status(self):
        gate = AutoApprovalGate(default_approve=True)
        queue = ApprovalQueue(gate)
        await queue.submit(ApprovalRequest())
        history = queue.get_history(status=ApprovalStatus.AUTO_APPROVED)
        assert all(r.status == ApprovalStatus.AUTO_APPROVED for r in history)

    async def test_get_stats(self):
        gate = AutoApprovalGate()
        queue = ApprovalQueue(gate)
        await queue.submit(ApprovalRequest())
        stats = queue.get_stats()
        assert stats["total"] == 1
        assert "by_status" in stats


# ---------------------------------------------------------------------------
# simple_risk_scorer
# ---------------------------------------------------------------------------


class TestSimpleRiskScorer:
    def test_short_content_low_risk(self):
        req = ApprovalRequest(content="short task")
        score = simple_risk_scorer(req)
        assert score < 0.5

    def test_long_content_higher_risk(self):
        req = ApprovalRequest(content="x" * 2000)
        score = simple_risk_scorer(req)
        assert score > 0.1

    def test_keyword_increases_risk(self):
        req_normal = ApprovalRequest(content="do a thing")
        req_risky = ApprovalRequest(content="delete all records from database")
        score_normal = simple_risk_scorer(req_normal)
        score_risky = simple_risk_scorer(req_risky)
        assert score_risky > score_normal

    def test_capped_at_one(self):
        long_risky = "delete transfer send payment remove publish " * 100
        req = ApprovalRequest(content=long_risky)
        score = simple_risk_scorer(req)
        assert score <= 1.0


# ---------------------------------------------------------------------------
# create_approval_gate factory
# ---------------------------------------------------------------------------


class TestCreateApprovalGate:
    def test_create_auto(self):
        gate = create_approval_gate("auto")
        assert isinstance(gate, AutoApprovalGate)

    def test_create_human(self):
        gate = create_approval_gate("human")
        assert isinstance(gate, HumanApprovalGate)

    def test_create_hybrid(self):
        gate = create_approval_gate("hybrid", risk_scorer=lambda r: 0.5)
        assert isinstance(gate, HybridApprovalGate)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError):
            create_approval_gate("unknown_gate_type")
