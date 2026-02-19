"""
FastAPI REST API for Agentic Company orchestration system.

Provides HTTP endpoints for workflow management, health checks, and metrics.
Includes a user-friendly web dashboard at the root URL.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from orchestration._version import __version__
from orchestration.approval import ApprovalRequest, HumanApprovalGate
from orchestration.config import get_config, validate_config
from orchestration.memory import LocalMemoryStore
from orchestration.observability import get_observability

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Company API",
    description="AI Agent Orchestration System with Guardrails, Memory, and Observability",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
memory_store = LocalMemoryStore()
approval_gate = HumanApprovalGate()
obs = get_observability()


# ============== Models ==============


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    components: dict[str, Any]


class WorkflowRequest(BaseModel):
    workflow_name: str
    input_data: str
    config: dict[str, Any] | None = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_name: str
    status: str
    created_at: str
    result: Any | None = None


class MemoryStoreRequest(BaseModel):
    content: str
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=100)


class ApprovalDecision(BaseModel):
    approved: bool
    reason: str = ""
    decided_by: str = "api"


# ============== Dashboard & Static Files ==============


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    """Serve the user-friendly web dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # Fallback: redirect to API docs
        return HTMLResponse("""
        <html>
        <head><meta http-equiv="refresh" content="0;url=/docs"></head>
        <body>Redirecting to API docs...</body>
        </html>
        """)


# ============== Health Endpoints ==============


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """Check backend status for dashboard."""
    from orchestration.integrations import get_available_backends, get_ready_backends

    available = get_available_backends()
    ready = get_ready_backends()

    return {
        "status": "ok" if ready else "needs_setup",
        "available_backends": [b.value for b in available],
        "ready_backends": [b.value for b in ready],
        "version": __version__,
    }


# ============== Chat Endpoint ==============


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    backend: str | None = "auto"


class ChatResponse(BaseModel):
    response: str
    backend_used: str
    session_id: str
    suggestions: list[str] | None = None
    workflow_ready: bool = False
    workflow_config: dict | None = None


# In-memory conversation state (in production, use Redis)
conversation_sessions: dict[str, dict] = {}


TEAM_TEMPLATES = {
    "marketing": {
        "name": "Viral Marketing Team",
        "agents": [
            "SocialIntelAgent",
            "CompetitorAnalyst",
            "ContentCreator",
            "CommunityManager",
            "CampaignLead",
        ],
        "description": "Automates pain point discovery, competitor analysis, content creation, and community engagement",
    },
    "development": {
        "name": "Feature Development Team",
        "agents": ["Planner", "Developer", "Verifier", "Tester", "Reviewer"],
        "description": "Plans, builds, tests, and reviews code with cross-verification",
    },
    "research": {
        "name": "Research & Analysis Team",
        "agents": [
            "Researcher",
            "DataAnalyst",
            "Synthesizer",
            "FactChecker",
            "ReportWriter",
        ],
        "description": "Deep research, data analysis, and comprehensive report generation",
    },
    "customer": {
        "name": "Customer Success Team",
        "agents": [
            "TicketTriager",
            "SupportAgent",
            "EscalationManager",
            "FeedbackAnalyzer",
            "KnowledgeWriter",
        ],
        "description": "Handles support tickets, analyzes feedback, updates documentation",
    },
    "content": {
        "name": "Content Production Team",
        "agents": ["IdeaGenerator", "Writer", "Editor", "SEOOptimizer", "Publisher"],
        "description": "Creates, edits, optimizes, and publishes content at scale",
    },
}


CONVERSATION_FLOW = {
    "start": {
        "message": """👋 Hi! I'm your AI Team Builder. I'll help you create the perfect agent team.

**What type of team do you want to build?**

1️⃣ **Marketing** - Social listening, competitor analysis, viral content
2️⃣ **Development** - Code planning, building, testing, review
3️⃣ **Research** - Deep research, data analysis, reports
4️⃣ **Customer Success** - Support, feedback analysis, docs
5️⃣ **Content** - Writing, editing, SEO, publishing
6️⃣ **Custom** - Build your own from scratch

Just type a number or describe what you need!""",
        "suggestions": ["1", "2", "3", "4", "5", "Tell me more about marketing"],
        "next_step": "team_type",
    },
    "team_type_marketing": {
        "message": """🎯 Great choice! Marketing teams are powerful for growth.

**The Viral Marketing Team includes:**
• **SocialIntelAgent** - Scans X, Reddit, HN for pain points
• **CompetitorAnalyst** - Creates battle cards, finds gaps
• **ContentCreator** - Threads, memes, technical posts
• **CommunityManager** - Authentic outreach & engagement
• **CampaignLead** - Coordinates everything, tracks metrics

**Now, tell me about YOUR campaign:**

1. What product/service are you marketing?
2. Who is your target audience?
3. Who are your main competitors?

Example: "I'm building an AI coding assistant for React developers. Competitors are Copilot and Cursor."
""",
        "suggestions": ["Skip - use defaults", "Show me an example prompt"],
        "next_step": "marketing_details",
    },
    "marketing_details": {
        "message": """📝 Perfect! Let me understand your goals better.

**What are your campaign priorities?** (pick 1-3)

1️⃣ **Waitlist Growth** - Get signups for launch
2️⃣ **Brand Awareness** - Get your name out there
3️⃣ **Community Building** - Build a loyal following
4️⃣ **Competitor Positioning** - Differentiate from alternatives
5️⃣ **Content Virality** - Create shareable content
6️⃣ **Lead Generation** - Capture potential customers

And how long is your campaign? (e.g., "30 days", "3 months")
""",
        "suggestions": ["1, 3, 5 for 30 days", "All of them for 90 days"],
        "next_step": "marketing_platforms",
    },
    "marketing_platforms": {
        "message": """🌐 Which platforms should we focus on?

**Select your primary platforms:**

• **X/Twitter** - Best for dev audiences, threads go viral
• **Reddit** - r/programming, r/startups, niche subreddits
• **Hacker News** - Technical credibility, Show HN posts
• **LinkedIn** - B2B, professional content
• **YouTube** - Tutorials, demos, long-form
• **TikTok** - Short-form, younger devs
• **Dev.to/Hashnode** - Technical blog posts
• **Discord** - Community building

Example: "Twitter, Reddit, and Hacker News"
""",
        "suggestions": ["Twitter, Reddit, HN", "All platforms", "Just Twitter"],
        "next_step": "generate_workflow",
    },
    "generate_workflow": {
        "message": """🚀 Excellent! I have everything I need.

**Here's your customized Marketing Team workflow:**

```yaml
team: viral-marketing-campaign
duration: {duration}
platforms: {platforms}

agents:
  - SocialIntelAgent: Pain point discovery on {platforms}
  - CompetitorAnalyst: Battle cards for {competitors}
  - ContentCreator: Daily posts + weekly deep-dives
  - CommunityManager: 15 engagements/day
  - CampaignLead: Metrics tracking & coordination

daily_workflow:
  morning: Research & scan for opportunities
  midday: Create and publish content
  afternoon: Engage with community
  evening: Report metrics & plan tomorrow
```

**Ready to launch?**
1️⃣ **Generate Full Workflow** - Get the complete YAML + Python code
2️⃣ **Customize Agents** - Modify individual agent prompts
3️⃣ **Start Over** - Begin fresh with different settings
""",
        "suggestions": ["Generate Full Workflow", "Customize Agents", "Start Over"],
        "next_step": "finalize",
    },
}


def get_conversation_response(
    session: dict, user_message: str
) -> tuple[str, list[str], bool, dict | None]:
    """Process user message and return conversational response."""

    step = session.get("step", "start")
    context = session.get("context", {})
    message_lower = user_message.lower().strip()

    # Handle step transitions
    if step == "start" or step == "team_type":
        if any(
            x in message_lower for x in ["1", "marketing", "viral", "growth", "social"]
        ):
            session["step"] = "marketing_details"
            session["context"]["team_type"] = "marketing"
            flow = CONVERSATION_FLOW["team_type_marketing"]
            return flow["message"], flow["suggestions"], False, None

        elif any(
            x in message_lower for x in ["2", "development", "dev", "code", "build"]
        ):
            session["step"] = "dev_details"
            session["context"]["team_type"] = "development"
            return (
                """🔧 Great! Let's build a Development Team.

**Tell me about your project:**
1. What are you building? (e.g., "REST API", "React app", "CLI tool")
2. What's your tech stack?
3. What stage? (greenfield, refactor, bug fixes)

Example: "Building a FastAPI backend with PostgreSQL, need help with new features"
""",
                ["Show example workflow", "Use defaults"],
                False,
                None,
            )

        elif any(x in message_lower for x in ["3", "research", "analysis", "data"]):
            session["step"] = "research_details"
            session["context"]["team_type"] = "research"
            return (
                """🔬 Research Team - excellent choice!

**What kind of research do you need?**
1. Market research & competitive analysis
2. Technical deep-dives & documentation
3. User research & interviews
4. Data analysis & insights
5. Academic/scientific literature review

Example: "I need to research the AI agent landscape and write a comprehensive report"
""",
                ["Market research", "Technical research", "Data analysis"],
                False,
                None,
            )

        else:
            # Default to asking for clarification
            return (
                """I didn't quite catch that. Let me help you choose:

**What type of team do you need?**
• Type **"marketing"** for viral growth campaigns
• Type **"dev"** for code development
• Type **"research"** for deep analysis
• Or just describe what you're trying to accomplish!
""",
                ["marketing", "dev", "research", "I need help with..."],
                False,
                None,
            )

    elif step == "marketing_details":
        # Extract product/competitor info from message
        context["product_description"] = user_message
        session["context"] = context
        session["step"] = "marketing_platforms"
        flow = CONVERSATION_FLOW["marketing_platforms"]
        return flow["message"], flow["suggestions"], False, None

    elif step == "marketing_platforms":
        # Extract platforms
        context["platforms"] = user_message
        session["context"] = context
        session["step"] = "generate_workflow"

        # Generate the summary
        product = context.get("product_description", "your product")
        platforms = context.get("platforms", "Twitter, Reddit")

        return (
            f"""🚀 Perfect! Here's your customized Marketing Team:

**Campaign Overview:**
• Product: {product[:100]}...
• Platforms: {platforms}
• Team: 5 specialized agents

**Your Workflow:**
```
1. SocialIntelAgent → Discovers pain points on {platforms}
2. CompetitorAnalyst → Creates battle cards
3. ContentCreator → Daily posts + viral content
4. CommunityManager → Engages 15+ conversations/day
5. CampaignLead → Tracks metrics, adjusts strategy
```

**What's next?**
1️⃣ **Generate Code** - Get Python + YAML files
2️⃣ **See Example Output** - Preview what agents produce
3️⃣ **Customize Prompts** - Fine-tune agent behaviors
4️⃣ **Start Campaign** - Launch immediately
""",
            ["Generate Code", "See Example Output", "Start Campaign"],
            True,
            {
                "team_type": "marketing",
                "product": product,
                "platforms": platforms,
            },
        )

    elif step == "generate_workflow":
        if any(
            x in message_lower for x in ["generate", "code", "yes", "launch", "start"]
        ):
            # Return the workflow configuration
            return (
                """✅ **Your Marketing Team is ready!**

I've generated the complete workflow. Here's what you get:

📁 **Files Created:**
• `workflows/your-campaign.yaml` - Workflow definition
• `examples/your_marketing_team.py` - Python implementation

🚀 **To run your campaign:**
```bash
python examples/your_marketing_team.py --campaign "YourProduct" --duration 30
```

Or use the CLI:
```bash
agentic workflow run marketing-campaign
```

**The team will:**
1. Scan social media for pain points (Day 1-3)
2. Analyze competitors & create battle cards (Day 2-4)
3. Build your landing page (Day 4-5)
4. Create 30-day content calendar (Day 5-7)
5. Execute daily: content + engagement + metrics

Would you like me to explain any specific agent in detail?
""",
                [
                    "Explain SocialIntelAgent",
                    "Explain ContentCreator",
                    "Show sample output",
                ],
                True,
                {
                    "ready": True,
                    "files": [
                        "workflows/marketing-campaign.yaml",
                        "examples/marketing_team.py",
                    ],
                },
            )

    # Default fallback
    return (
        """I'm here to help! You can:

• **Start fresh**: Type "start" or "new team"
• **Marketing team**: Type "marketing"
• **Dev team**: Type "dev"
• **Ask questions**: "How does the ContentCreator work?"

What would you like to do?
""",
        ["Start fresh", "marketing", "dev", "Help"],
        False,
        None,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_ai(request: ChatRequest):
    """Conversational AI Team Builder - guides users to refined prompts."""
    import uuid

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = {
            "step": "start",
            "context": {},
            "history": [],
        }

    session = conversation_sessions[session_id]

    # Check if this is the first message (start the conversation)
    if not session["history"]:
        flow = CONVERSATION_FLOW["start"]
        session["history"].append({"role": "assistant", "content": flow["message"]})
        return ChatResponse(
            response=flow["message"],
            backend_used="conversation_builder",
            session_id=session_id,
            suggestions=flow["suggestions"],
            workflow_ready=False,
        )

    # Process user message
    session["history"].append({"role": "user", "content": request.message})

    response_text, suggestions, workflow_ready, workflow_config = (
        get_conversation_response(session, request.message)
    )

    session["history"].append({"role": "assistant", "content": response_text})

    return ChatResponse(
        response=response_text,
        backend_used="conversation_builder",
        session_id=session_id,
        suggestions=suggestions,
        workflow_ready=workflow_ready,
        workflow_config=workflow_config,
    )


# ============== Config Endpoint ==============


class ApiKeyRequest(BaseModel):
    provider: str  # "anthropic" or "openai"
    key: str


@app.post("/api/config/key", tags=["Config"])
async def save_api_key(request: ApiKeyRequest):
    """Save an API key (session only - not persisted)."""
    if request.provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = request.key
    elif request.provider == "openai":
        os.environ["OPENAI_API_KEY"] = request.key
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

    return {"status": "ok", "provider": request.provider}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check overall system health."""
    config = get_config()
    errors = validate_config(config)

    return HealthResponse(
        status="healthy" if not errors else "degraded",
        version=__version__,
        timestamp=datetime.now().isoformat(),
        components={
            "llm": {
                "status": "ok" if config.llm.api_key else "no_api_key",
                "provider": config.llm.provider,
            },
            "memory": {
                "status": "ok",
                "backend": config.memory.backend,
                "entries": memory_store.count(),
            },
            "guardrails": {
                "status": "ok" if config.guardrails.enabled else "disabled",
            },
            "config_errors": errors,
        },
    )


@app.get("/live", tags=["Health"])
async def liveness_probe() -> dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/ready", tags=["Health"])
async def readiness_probe() -> dict[str, Any]:
    """Kubernetes readiness probe."""
    config = get_config()
    errors = validate_config(config)

    # Consider ready if we have at least API key configured
    is_ready = config.llm.api_key is not None or len(errors) < 2

    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {
        "status": "ready",
        "checks": {
            "config": len(errors) == 0,
            "memory": True,
        },
    }


# ============== Workflow Endpoints ==============


@app.get("/workflows", tags=["Workflows"])
async def list_workflows() -> dict[str, Any]:
    """List available workflows."""
    workflows = [
        {
            "name": "content-research",
            "description": "Research and analyze content",
            "status": "active",
        },
        {
            "name": "content-creation",
            "description": "Create new content",
            "status": "active",
        },
        {
            "name": "review-optimize",
            "description": "Review and optimize content",
            "status": "active",
        },
        {
            "name": "data-processing",
            "description": "Process and transform data",
            "status": "active",
        },
    ]
    return {"workflows": workflows, "count": len(workflows)}


@app.post("/workflows/run", response_model=WorkflowResponse, tags=["Workflows"])
async def run_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
) -> WorkflowResponse:
    """Run a workflow."""
    import uuid

    workflow_id = str(uuid.uuid4())

    with obs.observe("api_workflow_run", {"workflow": request.workflow_name}):
        # Simulate workflow execution
        result = {
            "input": request.input_data,
            "output": f"Processed: {request.input_data}",
            "steps_completed": 3,
        }

    return WorkflowResponse(
        workflow_id=workflow_id,
        workflow_name=request.workflow_name,
        status="completed",
        created_at=datetime.now().isoformat(),
        result=result,
    )


@app.get("/workflows/{workflow_id}", tags=["Workflows"])
async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get workflow status by ID."""
    # Placeholder - would query actual workflow store
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "progress": 100,
        "created_at": datetime.now().isoformat(),
    }


# ============== Memory Endpoints ==============


@app.post("/memory/store", tags=["Memory"])
async def store_memory(request: MemoryStoreRequest) -> dict[str, str]:
    """Store content in memory."""
    with obs.observe("api_memory_store"):
        entry_id = memory_store.remember(
            content=request.content,
            metadata=request.metadata,
            tags=request.tags,
        )

    return {"id": entry_id, "status": "stored"}


@app.post("/memory/search", tags=["Memory"])
async def search_memory(request: MemorySearchRequest) -> dict[str, Any]:
    """Search memory for relevant content."""
    with obs.observe("api_memory_search"):
        results = memory_store.search(request.query, limit=request.limit)

    return {
        "query": request.query,
        "results": [
            {
                "id": entry.id,
                "content": entry.content,
                "tags": entry.tags,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in results
        ],
        "count": len(results),
    }


@app.get("/memory/{entry_id}", tags=["Memory"])
async def get_memory_entry(entry_id: str) -> dict[str, Any]:
    """Get a memory entry by ID."""
    entry = memory_store.retrieve(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")

    return {
        "id": entry.id,
        "content": entry.content,
        "tags": entry.tags,
        "metadata": entry.metadata,
        "created_at": entry.created_at.isoformat(),
    }


@app.delete("/memory/{entry_id}", tags=["Memory"])
async def delete_memory_entry(entry_id: str) -> dict[str, str]:
    """Delete a memory entry."""
    deleted = memory_store.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")

    return {"status": "deleted", "id": entry_id}


# ============== Approval Endpoints ==============


@app.get("/approvals", tags=["Approvals"])
async def list_pending_approvals() -> dict[str, Any]:
    """List all pending approval requests."""
    pending = await approval_gate.list_pending()
    return {
        "pending": [req.to_dict() for req in pending],
        "count": len(pending),
    }


@app.post("/approvals", tags=["Approvals"])
async def create_approval_request(
    workflow_id: str = Query(...),
    step_name: str = Query(...),
    content: str = Query(...),
) -> dict[str, Any]:
    """Create a new approval request."""
    request = ApprovalRequest(
        workflow_id=workflow_id,
        step_name=step_name,
        content=content,
    )
    result = await approval_gate.request_approval(request)
    return result.to_dict()


@app.get("/approvals/{request_id}", tags=["Approvals"])
async def get_approval_status(request_id: str) -> dict[str, Any]:
    """Get approval request status."""
    request = await approval_gate.check_status(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request.to_dict()


@app.post("/approvals/{request_id}/decide", tags=["Approvals"])
async def decide_approval(
    request_id: str, decision: ApprovalDecision
) -> dict[str, Any]:
    """Approve or reject a request."""
    if decision.approved:
        result = await approval_gate.approve(
            request_id, decision.decided_by, decision.reason
        )
    else:
        result = await approval_gate.reject(
            request_id, decision.decided_by, decision.reason
        )

    if not result:
        raise HTTPException(
            status_code=404, detail="Approval request not found or already decided"
        )

    return result.to_dict()


# ============== Metrics Endpoints ==============


@app.get("/metrics", tags=["Metrics"])
async def get_metrics() -> dict[str, Any]:
    """Get all metrics."""
    return obs.metrics.get_all_metrics()


@app.get("/metrics/prometheus", tags=["Metrics"], response_class=PlainTextResponse)
async def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    metrics = obs.metrics.get_all_metrics()
    lines = []

    for name, value in metrics["counters"].items():
        clean_name = (
            name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
        )
        lines.append(f"agentic_{clean_name} {value}")

    for name, value in metrics["gauges"].items():
        clean_name = (
            name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
        )
        lines.append(f"agentic_{clean_name} {value}")

    for name, stats in metrics["histograms"].items():
        clean_name = (
            name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
        )
        lines.append(f"agentic_{clean_name}_count {stats['count']}")
        lines.append(f"agentic_{clean_name}_sum {stats['sum']}")
        lines.append(f"agentic_{clean_name}_avg {stats['avg']}")

    return "\n".join(lines)


# ============== Config Endpoints ==============


@app.get("/config", tags=["Config"])
async def get_config_endpoint() -> dict[str, Any]:
    """Get current configuration."""
    config = get_config()
    return config.to_dict()


@app.get("/config/validate", tags=["Config"])
async def validate_config_endpoint() -> dict[str, Any]:
    """Validate current configuration."""
    config = get_config()
    errors = validate_config(config)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ============== WebSocket for Real-time Updates ==============

from fastapi import WebSocket, WebSocketDisconnect

connected_clients: list[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast_update(event_type: str, data: dict[str, Any]) -> None:
    """Broadcast an update to all connected clients."""
    message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            pass


# Startup/shutdown events
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize on startup."""
    obs.logger.info("Agentic Company API starting", version=__version__)
    obs.metrics.set_gauge("api_startup_time", datetime.now().timestamp())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    obs.logger.info("Agentic Company API shutting down")
