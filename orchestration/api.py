"""
FastAPI REST API for Agentic Company orchestration system.

Provides HTTP endpoints for workflow management, health checks, and metrics.
Includes a user-friendly web dashboard at the root URL.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from orchestration._version import __version__
from orchestration.config import get_config, validate_config
from orchestration.observability import get_observability
from orchestration.memory import LocalMemoryStore
from orchestration.approval import ApprovalRequest, ApprovalStatus, HumanApprovalGate

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
    config: Optional[dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_name: str
    status: str
    created_at: str
    result: Optional[Any] = None


class MemoryStoreRequest(BaseModel):
    content: str
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


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
    backend: Optional[str] = "auto"


class ChatResponse(BaseModel):
    response: str
    backend_used: str


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_ai(request: ChatRequest):
    """Send a message to the AI and get a response."""
    try:
        from orchestration.integrations import auto_setup_executor

        executor = auto_setup_executor(preferred=request.backend or "auto")
        response = executor.execute_sync(request.message)

        return ChatResponse(
            response=response,
            backend_used=executor.active_backend.value if executor.active_backend else "unknown"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        {"name": "content-research", "description": "Research and analyze content", "status": "active"},
        {"name": "content-creation", "description": "Create new content", "status": "active"},
        {"name": "review-optimize", "description": "Review and optimize content", "status": "active"},
        {"name": "data-processing", "description": "Process and transform data", "status": "active"},
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
async def decide_approval(request_id: str, decision: ApprovalDecision) -> dict[str, Any]:
    """Approve or reject a request."""
    if decision.approved:
        result = await approval_gate.approve(request_id, decision.decided_by, decision.reason)
    else:
        result = await approval_gate.reject(request_id, decision.decided_by, decision.reason)

    if not result:
        raise HTTPException(status_code=404, detail="Approval request not found or already decided")

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
        clean_name = name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
        lines.append(f"agentic_{clean_name} {value}")

    for name, value in metrics["gauges"].items():
        clean_name = name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
        lines.append(f"agentic_{clean_name} {value}")

    for name, stats in metrics["histograms"].items():
        clean_name = name.replace("{", "_").replace("}", "_").replace(",", "_").replace("=", "_")
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
    message = {"type": event_type, "data": data, "timestamp": datetime.now().isoformat()}
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
