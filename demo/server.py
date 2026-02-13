"""
Real LLM-Powered SmartChatbox Server

NO MOCKS - Uses actual Claude API for multi-turn interview and prompt synthesis.
"""

import os
import sys
import uuid
import asyncio
from typing import Dict, Optional

# Add project to path
sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Check API key
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("⚠️  ANTHROPIC_API_KEY not set!")
    print("   Run: export ANTHROPIC_API_KEY='your-key'")
    sys.exit(1)

import anthropic
import httpx
from orchestration.tools.smart_refiner import SmartRefiner

# =============================================================================
# REAL CLAUDE CLIENT
# =============================================================================

class RealClaudeClient:
    """Real Claude API client - NO MOCKS."""

    def __init__(self):
        # SSL bypass for VM proxy
        http_client = httpx.AsyncClient(verify=False)
        self.client = anthropic.AsyncAnthropic(
            api_key=ANTHROPIC_API_KEY,
            http_client=http_client
        )
        self.model = "claude-sonnet-4-20250514"
        self.call_count = 0

    async def __call__(self, system: str, user: str) -> str:
        """Make real API call to Claude."""
        self.call_count += 1
        print(f"   [API Call #{self.call_count}] System: {system[:50]}...")

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            result = response.content[0].text
            print(f"   [Response] {result[:100]}...")
            return result
        except Exception as e:
            print(f"   [API Error] {e}")
            raise

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="SmartChatbox Demo - Real LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
claude_client = RealClaudeClient()
refiner = SmartRefiner(llm_call=claude_client, max_questions=3)
sessions: Dict[str, str] = {}  # Maps API session ID to refiner session ID

# =============================================================================
# MODELS
# =============================================================================

class MessageInput(BaseModel):
    message: str

class SessionResponse(BaseModel):
    session_id: str

class ChatResponse(BaseModel):
    state: str
    response: str
    confidence: float
    final_prompt: Optional[str] = None
    understanding: Optional[dict] = None

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    return FileResponse('/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/demo/index.html')

@app.post("/api/session/start", response_model=SessionResponse)
async def start_session():
    """Start a new refinement session."""
    api_session_id = str(uuid.uuid4())
    refiner_session_id = refiner.create_session()
    sessions[api_session_id] = refiner_session_id
    print(f"[Session Created] {api_session_id}")
    return {"session_id": api_session_id}

@app.post("/api/session/{session_id}/message", response_model=ChatResponse)
async def send_message(session_id: str, input: MessageInput):
    """Send a message to the refiner."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    refiner_session_id = sessions[session_id]
    print(f"\n[Message] Session: {session_id[:8]}...")
    print(f"[User Input] {input.message}")

    try:
        result = await refiner.process(refiner_session_id, input.message)

        print(f"[State] {result['state']}")
        print(f"[Confidence] {result['understanding']['confidence']}")
        print(f"[Response] {result['response'][:100]}...")

        return ChatResponse(
            state=result['state'],
            response=result['response'],
            confidence=result['understanding']['confidence'],
            final_prompt=result.get('final_prompt'),
            understanding=result.get('understanding')
        )
    except Exception as e:
        print(f"[Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get API usage stats."""
    return {
        "api_calls": claude_client.call_count,
        "active_sessions": len(sessions)
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SmartChatbox Demo Server - REAL LLM")
    print("=" * 60)
    print(f"Model: {claude_client.model}")
    print(f"API Key: {ANTHROPIC_API_KEY[:20]}...")
    print()
    print("Starting server at http://localhost:8000")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
