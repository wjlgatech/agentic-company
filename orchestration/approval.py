"""
Approval gate system for human-in-the-loop workflows.

Supports automatic, manual, and hybrid approval strategies.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"


@dataclass
class ApprovalRequest:
    """A request for approval."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    step_name: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    reason: str = ""

    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    def is_expired(self) -> bool:
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return self.status == ApprovalStatus.EXPIRED

    def approve(self, by: str = "system", reason: str = "") -> None:
        self.status = ApprovalStatus.APPROVED
        self.decided_at = datetime.now()
        self.decided_by = by
        self.reason = reason

    def reject(self, by: str = "system", reason: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self.decided_at = datetime.now()
        self.decided_by = by
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step_name": self.step_name,
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
            "reason": self.reason,
        }


class ApprovalGate(ABC):
    """Abstract base class for approval gates."""

    name: str = "base"

    @abstractmethod
    async def request_approval(self, request: ApprovalRequest) -> ApprovalRequest:
        """Request approval and return the result."""
        pass

    @abstractmethod
    async def check_status(self, request_id: str) -> Optional[ApprovalRequest]:
        """Check the status of an approval request."""
        pass

    @abstractmethod
    async def list_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests."""
        pass


class AutoApprovalGate(ApprovalGate):
    """Automatic approval based on rules."""

    name = "auto"

    def __init__(
        self,
        rules: Optional[list[Callable[[ApprovalRequest], bool]]] = None,
        default_approve: bool = True,
    ):
        self.rules = rules or []
        self.default_approve = default_approve
        self.requests: dict[str, ApprovalRequest] = {}

    async def request_approval(self, request: ApprovalRequest) -> ApprovalRequest:
        """Evaluate rules and auto-approve/reject."""
        # Check all rules
        for rule in self.rules:
            if not rule(request):
                request.status = ApprovalStatus.AUTO_REJECTED
                request.decided_at = datetime.now()
                request.decided_by = "auto_rule"
                self.requests[request.id] = request
                return request

        # All rules passed or no rules defined
        if self.default_approve:
            request.status = ApprovalStatus.AUTO_APPROVED
        else:
            request.status = ApprovalStatus.AUTO_REJECTED

        request.decided_at = datetime.now()
        request.decided_by = "auto"
        self.requests[request.id] = request
        return request

    async def check_status(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    async def list_pending(self) -> list[ApprovalRequest]:
        return [r for r in self.requests.values() if r.is_pending()]


class HumanApprovalGate(ApprovalGate):
    """Human-in-the-loop approval gate."""

    name = "human"

    def __init__(
        self,
        timeout_seconds: int = 3600,
        notification_callback: Optional[Callable[[ApprovalRequest], None]] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.notification_callback = notification_callback
        self.requests: dict[str, ApprovalRequest] = {}

    async def request_approval(self, request: ApprovalRequest) -> ApprovalRequest:
        """Submit request for human approval."""
        request.expires_at = datetime.now() + timedelta(seconds=self.timeout_seconds)
        self.requests[request.id] = request

        # Send notification if callback provided
        if self.notification_callback:
            self.notification_callback(request)

        return request

    async def check_status(self, request_id: str) -> Optional[ApprovalRequest]:
        """Check status of request."""
        request = self.requests.get(request_id)
        if request and request.is_pending() and request.is_expired():
            request.status = ApprovalStatus.EXPIRED
        return request

    async def list_pending(self) -> list[ApprovalRequest]:
        """List all pending requests."""
        pending = []
        for request in self.requests.values():
            if request.is_pending():
                if request.is_expired():
                    request.status = ApprovalStatus.EXPIRED
                else:
                    pending.append(request)
        return pending

    async def approve(self, request_id: str, by: str, reason: str = "") -> Optional[ApprovalRequest]:
        """Approve a pending request."""
        request = self.requests.get(request_id)
        if request and request.is_pending():
            request.approve(by, reason)
            return request
        return None

    async def reject(self, request_id: str, by: str, reason: str = "") -> Optional[ApprovalRequest]:
        """Reject a pending request."""
        request = self.requests.get(request_id)
        if request and request.is_pending():
            request.reject(by, reason)
            return request
        return None

    async def wait_for_decision(
        self,
        request_id: str,
        poll_interval: float = 1.0,
    ) -> ApprovalRequest:
        """Wait for a decision on the request."""
        while True:
            request = await self.check_status(request_id)
            if request is None:
                raise ValueError(f"Request {request_id} not found")

            if not request.is_pending():
                return request

            await asyncio.sleep(poll_interval)


class HybridApprovalGate(ApprovalGate):
    """Hybrid gate that uses auto-approval for low-risk, human for high-risk."""

    name = "hybrid"

    def __init__(
        self,
        risk_scorer: Callable[[ApprovalRequest], float],
        risk_threshold: float = 0.5,
        auto_gate: Optional[AutoApprovalGate] = None,
        human_gate: Optional[HumanApprovalGate] = None,
    ):
        self.risk_scorer = risk_scorer
        self.risk_threshold = risk_threshold
        self.auto_gate = auto_gate or AutoApprovalGate()
        self.human_gate = human_gate or HumanApprovalGate()

    async def request_approval(self, request: ApprovalRequest) -> ApprovalRequest:
        """Route to auto or human gate based on risk score."""
        risk_score = self.risk_scorer(request)
        request.metadata["risk_score"] = risk_score

        if risk_score < self.risk_threshold:
            return await self.auto_gate.request_approval(request)
        else:
            return await self.human_gate.request_approval(request)

    async def check_status(self, request_id: str) -> Optional[ApprovalRequest]:
        """Check status in both gates."""
        result = await self.auto_gate.check_status(request_id)
        if result:
            return result
        return await self.human_gate.check_status(request_id)

    async def list_pending(self) -> list[ApprovalRequest]:
        """List pending from both gates."""
        auto_pending = await self.auto_gate.list_pending()
        human_pending = await self.human_gate.list_pending()
        return auto_pending + human_pending


class ApprovalQueue:
    """Queue for managing multiple approval requests."""

    def __init__(self, gate: ApprovalGate):
        self.gate = gate
        self.history: list[ApprovalRequest] = []

    async def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        """Submit a request to the queue."""
        result = await self.gate.request_approval(request)
        self.history.append(result)
        return result

    async def get_pending(self) -> list[ApprovalRequest]:
        """Get all pending requests."""
        return await self.gate.list_pending()

    def get_history(
        self,
        status: Optional[ApprovalStatus] = None,
        limit: int = 100,
    ) -> list[ApprovalRequest]:
        """Get request history, optionally filtered by status."""
        history = self.history
        if status:
            history = [r for r in history if r.status == status]
        return sorted(history, key=lambda r: r.created_at, reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about approvals."""
        stats = {
            "total": len(self.history),
            "by_status": {},
        }
        for request in self.history:
            status = request.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        return stats


# Helper functions
def create_approval_gate(
    gate_type: str = "auto",
    **kwargs,
) -> ApprovalGate:
    """Factory function to create approval gates."""
    if gate_type == "auto":
        return AutoApprovalGate(**kwargs)
    elif gate_type == "human":
        return HumanApprovalGate(**kwargs)
    elif gate_type == "hybrid":
        return HybridApprovalGate(**kwargs)
    else:
        raise ValueError(f"Unknown gate type: {gate_type}")


def simple_risk_scorer(request: ApprovalRequest) -> float:
    """Simple risk scorer based on content length and keywords."""
    risk = 0.0

    # Longer content = higher risk
    content_length = len(request.content)
    if content_length > 1000:
        risk += 0.2
    if content_length > 5000:
        risk += 0.2

    # Check for high-risk keywords
    high_risk_keywords = ["delete", "remove", "publish", "send", "payment", "transfer"]
    content_lower = request.content.lower()
    for keyword in high_risk_keywords:
        if keyword in content_lower:
            risk += 0.1

    return min(risk, 1.0)
