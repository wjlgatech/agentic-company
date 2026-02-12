"""
REST API for Conversational Intent Refinement.

This API enables the single-chatbox UI to communicate with the
ConversationalRefiner backend.

Endpoints:
- POST /session/start      → Start new refinement session
- POST /session/{id}/input → Process user input
- GET  /session/{id}       → Get session state
- POST /session/{id}/accept → Accept draft and get final prompt

All responses include the latest turn with inline cards/draft if applicable.
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

# Simulated FastAPI-style definitions (actual implementation would use FastAPI)


@dataclass
class ChatMessage:
    """A message in the chat UI."""
    role: str  # "user" or "assistant"
    content: str
    cards: Optional[list] = None  # Inline clarification cards
    draft: Optional[dict] = None  # Draft preview
    metadata: Optional[dict] = None


@dataclass
class SessionResponse:
    """API response containing session state."""
    session_id: str
    state: str
    messages: list[ChatMessage]
    quality_score: float
    can_proceed: bool
    final_prompt: Optional[str] = None


class RefinementAPI:
    """
    API handler for conversational refinement.

    This class would typically be integrated with FastAPI, Flask, or similar.
    Here we show the interface design.
    """

    def __init__(self):
        from ..tools.conversational_refiner import ConversationalRefiner
        self.refiner = ConversationalRefiner()

    def start_session(self) -> SessionResponse:
        """
        Start a new refinement session.

        POST /api/refinement/session/start

        Returns:
            SessionResponse with empty message list, ready for first input
        """
        session = self.refiner.start_session()
        return SessionResponse(
            session_id=session.session_id,
            state="initial",
            messages=[],
            quality_score=0.0,
            can_proceed=False,
        )

    def process_input(self, session_id: str, user_input: str) -> SessionResponse:
        """
        Process user input in an existing session.

        POST /api/refinement/session/{session_id}/input
        Body: {"message": "user input text"}

        This is the main endpoint called when user sends a message.

        Returns:
            SessionResponse with updated messages including AI response
        """
        session = self.refiner.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Process the input
        turn = self.refiner.process_input(session, user_input)

        # Convert to API response
        messages = []
        for t in session.turns:
            # User message
            messages.append(ChatMessage(
                role="user",
                content=t.user_input,
            ))
            # Assistant response
            messages.append(ChatMessage(
                role="assistant",
                content=t.ai_response,
                cards=[
                    {
                        "question": c.question,
                        "options": [
                            {"label": o.label, "value": o.value, "description": o.description}
                            for o in c.options
                        ],
                        "allowFreeform": c.allow_freeform,
                        "dimension": c.dimension,
                    }
                    for c in t.cards
                ] if t.cards else None,
                draft={
                    "summary": t.draft.summary,
                    "approach": t.draft.approach,
                    "outputType": t.draft.output_type,
                    "confidence": t.draft.confidence,
                    "canProceed": t.draft.can_proceed,
                } if t.draft else None,
                metadata={"turnId": t.turn_id, "state": t.state.value}
            ))

        return SessionResponse(
            session_id=session.session_id,
            state=session.state.value,
            messages=messages,
            quality_score=session.quality_score,
            can_proceed=session.quality_score >= session.quality_threshold,
            final_prompt=session.final_prompt if session.final_prompt else None,
        )

    def get_session(self, session_id: str) -> SessionResponse:
        """
        Get current session state.

        GET /api/refinement/session/{session_id}

        Returns:
            Current session state with all messages
        """
        session = self.refiner.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Convert to response (same as process_input but without processing)
        return self._session_to_response(session)

    def _session_to_response(self, session) -> SessionResponse:
        """Convert session to API response."""
        messages = []
        for t in session.turns:
            messages.append(ChatMessage(role="user", content=t.user_input))
            messages.append(ChatMessage(
                role="assistant",
                content=t.ai_response,
                cards=[
                    {
                        "question": c.question,
                        "options": [{"label": o.label, "value": o.value} for o in c.options],
                        "allowFreeform": c.allow_freeform,
                    }
                    for c in t.cards
                ] if t.cards else None,
                draft={
                    "summary": t.draft.summary,
                    "approach": t.draft.approach,
                    "confidence": t.draft.confidence,
                } if t.draft else None,
            ))

        return SessionResponse(
            session_id=session.session_id,
            state=session.state.value,
            messages=messages,
            quality_score=session.quality_score,
            can_proceed=session.quality_score >= session.quality_threshold,
            final_prompt=session.final_prompt if session.final_prompt else None,
        )


# =============================================================================
# FASTAPI INTEGRATION EXAMPLE
# =============================================================================

FASTAPI_EXAMPLE = '''
"""
Example FastAPI integration (would go in main.py or routes/refinement.py)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
api = RefinementAPI()

class InputMessage(BaseModel):
    message: str

@app.post("/api/refinement/session/start")
def start_session():
    return api.start_session()

@app.post("/api/refinement/session/{session_id}/input")
def process_input(session_id: str, body: InputMessage):
    try:
        return api.process_input(session_id, body.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/refinement/session/{session_id}")
def get_session(session_id: str):
    try:
        return api.get_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
'''
