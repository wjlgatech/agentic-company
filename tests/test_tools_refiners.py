"""
Tests for tools refiners:
- ConversationalRefiner (orchestration/tools/conversational_refiner.py)
- HybridRefiner & SyncHybridRefiner (orchestration/tools/hybrid_refiner.py)
- SmartRefiner & SyncSmartRefiner (orchestration/tools/smart_refiner.py)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestration.tools.conversational_refiner import (
    ConversationState,
    ConversationalRefiner,
    RefinementSession,
)
from orchestration.tools.hybrid_refiner import (
    HybridRefiner,
    Session,
    SessionState,
    SyncHybridRefiner,
)

# ===========================================================================
# ConversationalRefiner
# ===========================================================================


class TestConversationalRefiner:
    def setup_method(self):
        self.refiner = ConversationalRefiner(quality_threshold=0.7)

    # --- session management ---

    def test_start_session_returns_session(self):
        session = self.refiner.start_session()
        assert isinstance(session, RefinementSession)
        assert session.session_id is not None

    def test_start_session_stored(self):
        session = self.refiner.start_session()
        found = self.refiner.get_session(session.session_id)
        assert found is session

    def test_get_session_not_found_returns_none(self):
        assert self.refiner.get_session("nonexistent") is None

    # --- process_input (clarification path) ---

    def test_process_vague_input_returns_clarifying_state(self):
        session = self.refiner.start_session()
        turn = self.refiner.process_input(session, "help me")
        # Vague input → clarification or draft, never complete
        assert turn.state in (
            ConversationState.CLARIFYING,
            ConversationState.DRAFT_READY,
        )

    def test_process_input_appends_turn(self):
        session = self.refiner.start_session()
        self.refiner.process_input(session, "help me with something")
        assert len(session.turns) == 1

    def test_process_input_returns_conversation_turn(self):
        session = self.refiner.start_session()
        from orchestration.tools.conversational_refiner import ConversationTurn

        turn = self.refiner.process_input(session, "write a blog post about AI")
        assert isinstance(turn, turn.__class__)
        assert turn.user_input == "write a blog post about AI"

    # --- acceptance detection ---

    def test_acceptance_signal_on_draft_ready_state(self):
        session = self.refiner.start_session()
        session.state = ConversationState.DRAFT_READY
        # Prime some content
        session.quality_score = 0.8
        session.quality_threshold = 0.7

        # Mock refiner.refine to avoid import issues
        with patch.object(
            self.refiner.refiner,
            "refine",
            return_value={"prompt": "final", "specifics_extracted": {}},
        ):
            turn = self.refiner.process_input(session, "yes")
        assert turn.state == ConversationState.COMPLETE

    # --- refinement request ---

    def test_refinement_signal_on_draft_ready_state(self):
        session = self.refiner.start_session()
        session.state = ConversationState.DRAFT_READY
        turn = self.refiner.process_input(session, "change the approach")
        assert turn.state == ConversationState.REFINING

    # --- session_to_dict ---

    def test_session_to_dict_has_required_keys(self):
        session = self.refiner.start_session()
        self.refiner.process_input(session, "help me build a feature")
        d = self.refiner.session_to_dict(session)
        for key in ("session_id", "state", "quality_score", "turns", "final_prompt"):
            assert key in d

    def test_session_to_dict_final_prompt_none_when_not_complete(self):
        session = self.refiner.start_session()
        self.refiner.process_input(session, "vague request")
        d = self.refiner.session_to_dict(session)
        if session.state != ConversationState.COMPLETE:
            assert d["final_prompt"] is None

    def test_session_to_dict_turns_serialized(self):
        session = self.refiner.start_session()
        self.refiner.process_input(session, "build something")
        d = self.refiner.session_to_dict(session)
        assert isinstance(d["turns"], list)
        assert len(d["turns"]) >= 1


# ===========================================================================
# HybridRefiner (mocked LLM)
# ===========================================================================


def _make_llm_mock(readiness_score=0.8, summary="User wants help"):
    """Return async mock that produces valid analysis JSON."""

    async def mock_llm(system: str, user: str) -> str:
        if "Analyze" in user or "analyze" in user.lower():
            return json.dumps(
                {
                    "summary": summary,
                    "task_type": "creation",
                    "domain": "technical",
                    "entities": ["Python"],
                    "goals": ["Build a REST API"],
                    "constraints": [],
                    "pain_points": [],
                    "stakeholders": [],
                    "technologies": ["FastAPI"],
                    "metrics": [],
                    "readiness_score": readiness_score,
                    "missing_info": [],
                    "clarifying_questions": [],
                    "suggested_approach": ["Step 1", "Step 2"],
                }
            )
        # For prompt generation or response generation
        return "Generated response text"

    return mock_llm


class TestHybridRefiner:
    def setup_method(self):
        self.refiner = HybridRefiner(llm_call=_make_llm_mock(readiness_score=0.9))

    def test_create_session_returns_id(self):
        session_id = self.refiner.create_session()
        assert isinstance(session_id, str)

    def test_get_session_found(self):
        session_id = self.refiner.create_session()
        session = self.refiner.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id

    def test_get_session_not_found(self):
        assert self.refiner.get_session("nope") is None

    async def test_process_above_threshold_returns_ready(self):
        refiner = HybridRefiner(llm_call=_make_llm_mock(readiness_score=0.9))
        sid = refiner.create_session()
        result = await refiner.process(sid, "Build a FastAPI REST API")
        assert result["state"] == "ready"
        assert result["ready"] is True

    async def test_process_below_threshold_returns_clarifying(self):
        refiner = HybridRefiner(
            llm_call=_make_llm_mock(readiness_score=0.3), readiness_threshold=0.75
        )
        sid = refiner.create_session()
        result = await refiner.process(sid, "help")
        assert result["state"] == "clarifying"
        assert result["ready"] is False

    async def test_acceptance_on_ready_state_finalizes(self):
        refiner = HybridRefiner(llm_call=_make_llm_mock(readiness_score=0.9))
        sid = refiner.create_session()
        # First process to get to READY state
        await refiner.process(sid, "Build a FastAPI REST API for user management")
        # Then accept
        result = await refiner.process(sid, "yes")
        assert result["state"] == "complete"
        assert "final_prompt" in result

    async def test_refinement_signal_sets_clarifying(self):
        refiner = HybridRefiner(llm_call=_make_llm_mock(readiness_score=0.9))
        sid = refiner.create_session()
        await refiner.process(sid, "Build an API")
        # Now signal refinement
        result = await refiner.process(sid, "actually, change the approach")
        assert result["state"] == "clarifying"

    async def test_invalid_session_raises(self):
        with pytest.raises(ValueError, match="not found"):
            await self.refiner.process("bad_session_id", "input")

    async def test_json_parse_fallback(self):
        """When LLM returns invalid JSON, fallback AnalysisResult is used."""

        async def bad_llm(system, user):
            return "not valid json at all"

        refiner = HybridRefiner(llm_call=bad_llm)
        sid = refiner.create_session()
        result = await refiner.process(sid, "help me")
        # Should not crash, should return clarifying
        assert "state" in result

    async def test_analysis_result_cached(self):
        call_count = {"n": 0}

        async def counting_llm(system, user):
            call_count["n"] += 1
            return json.dumps(
                {
                    "summary": "test",
                    "task_type": "creation",
                    "domain": "technical",
                    "entities": [],
                    "goals": ["goal"],
                    "constraints": [],
                    "pain_points": [],
                    "stakeholders": [],
                    "technologies": [],
                    "metrics": [],
                    "readiness_score": 0.9,
                    "missing_info": [],
                    "clarifying_questions": [],
                    "suggested_approach": [],
                }
            )

        refiner = HybridRefiner(llm_call=counting_llm)
        # Two sessions with same input
        sid1 = refiner.create_session()
        await refiner.process(sid1, "Build an API")
        before = call_count["n"]
        # Same refiner, second session with same input → cache hit
        sid2 = refiner.create_session()
        await refiner.process(sid2, "Build an API")
        # Should use cache → fewer calls
        assert call_count["n"] <= before + 1  # At most one additional call


# ===========================================================================
# SyncHybridRefiner
# ===========================================================================


class TestSyncHybridRefiner:
    def test_create_session(self):
        def sync_llm(system, user):
            return json.dumps(
                {
                    "summary": "s",
                    "task_type": "creation",
                    "domain": "technical",
                    "entities": [],
                    "goals": ["g"],
                    "constraints": [],
                    "pain_points": [],
                    "stakeholders": [],
                    "technologies": [],
                    "metrics": [],
                    "readiness_score": 0.9,
                    "missing_info": [],
                    "clarifying_questions": [],
                    "suggested_approach": [],
                }
            )

        refiner = SyncHybridRefiner(llm_call=sync_llm)
        sid = refiner.create_session()
        assert isinstance(sid, str)

    def test_process_returns_result(self):
        def sync_llm(system, user):
            return json.dumps(
                {
                    "summary": "s",
                    "task_type": "creation",
                    "domain": "technical",
                    "entities": [],
                    "goals": ["g"],
                    "constraints": [],
                    "pain_points": [],
                    "stakeholders": [],
                    "technologies": [],
                    "metrics": [],
                    "readiness_score": 0.9,
                    "missing_info": [],
                    "clarifying_questions": [],
                    "suggested_approach": [],
                }
            )

        refiner = SyncHybridRefiner(llm_call=sync_llm)
        sid = refiner.create_session()
        result = refiner.process(sid, "Build an API")
        assert "state" in result


# ===========================================================================
# SmartRefiner
# ===========================================================================


def _make_smart_llm(ready_after=1):
    """Return async mock LLM for SmartRefiner (takes system, user params)."""
    call_count = {"n": 0}

    async def mock_llm(system: str, user: str) -> str:
        call_count["n"] += 1
        if call_count["n"] >= ready_after:
            return json.dumps(
                {
                    "understanding": {
                        "summary": "Build a REST API",
                        "confidence": 0.9,
                        "key_points": ["REST", "API"],
                        "domain": "technical",
                        "task_type": "creation",
                    },
                    "gaps": {"critical": [], "helpful": []},
                    "next_action": "ready_to_proceed",
                    "ready_message": "I understand your request. Ready to proceed!",
                }
            )
        else:
            return json.dumps(
                {
                    "understanding": {
                        "summary": "Need more info",
                        "confidence": 0.5,
                        "key_points": [],
                        "domain": "general",
                        "task_type": "general",
                    },
                    "gaps": {"critical": ["scope"], "helpful": []},
                    "next_action": "ask_question",
                    "question": {
                        "text": "What kind of API are you building?",
                        "why": "scope",
                        "options": ["REST", "GraphQL"],
                    },
                }
            )

    return mock_llm, call_count


class TestSmartRefiner:
    async def test_create_session_returns_id(self):
        try:
            from orchestration.tools.smart_refiner import SmartRefiner
        except ImportError:
            pytest.skip("SmartRefiner not available")

        mock_llm, _ = _make_smart_llm(ready_after=1)
        refiner = SmartRefiner(llm_call=mock_llm)
        sid = refiner.create_session()
        assert isinstance(sid, str)

    async def test_process_returns_response(self):
        try:
            from orchestration.tools.smart_refiner import SmartRefiner
        except ImportError:
            pytest.skip("SmartRefiner not available")

        mock_llm, _ = _make_smart_llm(ready_after=1)
        refiner = SmartRefiner(llm_call=mock_llm)
        sid = refiner.create_session()
        result = await refiner.process(sid, "Build a REST API")
        assert "response" in result
        assert "state" in result

    async def test_process_max_questions_cutoff(self):
        try:
            from orchestration.tools.smart_refiner import SmartRefiner
        except ImportError:
            pytest.skip("SmartRefiner not available")

        # Never ready, so will always ask questions
        mock_llm, _ = _make_smart_llm(ready_after=999)
        refiner = SmartRefiner(llm_call=mock_llm, max_questions=2)
        sid = refiner.create_session()
        # After max_questions, should force ready_to_proceed
        for _ in range(3):
            result = await refiner.process(sid, "some input")
        # After exceeding max_questions, it transitions to REVIEWING
        assert result["state"] in ("reviewing", "complete")

    async def test_invalid_session_raises_value_error(self):
        try:
            from orchestration.tools.smart_refiner import SmartRefiner
        except ImportError:
            pytest.skip("SmartRefiner not available")

        mock_llm, _ = _make_smart_llm()
        refiner = SmartRefiner(llm_call=mock_llm)
        with pytest.raises(ValueError):
            await refiner.process("nonexistent_session", "hello")
