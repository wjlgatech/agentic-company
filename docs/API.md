# Agentic Company API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

The API supports two authentication methods:

### Bearer Token (JWT)

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/workflows
```

### API Key

```bash
curl -H "X-API-Key: epi_xxxxx" http://localhost:8000/workflows
```

## Rate Limiting

Default: 100 requests per minute per client.

Headers returned:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Endpoints

### Health

#### GET /health
Check overall system health.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "llm": {"status": "ok", "provider": "anthropic"},
    "memory": {"status": "ok", "backend": "local", "entries": 150},
    "guardrails": {"status": "ok"}
  }
}
```

#### GET /live
Kubernetes liveness probe.

**Response:**
```json
{"status": "alive"}
```

#### GET /ready
Kubernetes readiness probe.

**Response:**
```json
{"status": "ready", "checks": {"config": true, "memory": true}}
```

---

### Workflows

#### GET /workflows
List available workflows.

**Response:**
```json
{
  "workflows": [
    {"name": "content-research", "description": "Research and analyze content", "status": "active"},
    {"name": "content-creation", "description": "Create new content", "status": "active"}
  ],
  "count": 2
}
```

#### POST /workflows/run
Run a workflow.

**Request:**
```json
{
  "workflow_name": "content-research",
  "input_data": "AI trends 2024",
  "config": {}
}
```

**Response:**
```json
{
  "workflow_id": "wf-abc123",
  "workflow_name": "content-research",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "result": {
    "output": "Processed result...",
    "steps_completed": 3
  }
}
```

#### GET /workflows/{workflow_id}
Get workflow status.

**Response:**
```json
{
  "workflow_id": "wf-abc123",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Memory

#### POST /memory/store
Store content in memory.

**Request:**
```json
{
  "content": "Important information to remember",
  "tags": ["research", "ai"],
  "metadata": {"source": "web"}
}
```

**Response:**
```json
{"id": "mem-xyz789", "status": "stored"}
```

#### POST /memory/search
Search memory.

**Request:**
```json
{
  "query": "AI research",
  "limit": 10
}
```

**Response:**
```json
{
  "query": "AI research",
  "results": [
    {
      "id": "mem-xyz789",
      "content": "Important information...",
      "tags": ["research", "ai"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### GET /memory/{entry_id}
Get memory entry by ID.

**Response:**
```json
{
  "id": "mem-xyz789",
  "content": "Important information...",
  "tags": ["research", "ai"],
  "metadata": {"source": "web"},
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### DELETE /memory/{entry_id}
Delete memory entry.

**Response:**
```json
{"status": "deleted", "id": "mem-xyz789"}
```

---

### Approvals

#### GET /approvals
List pending approvals.

**Response:**
```json
{
  "pending": [
    {
      "id": "apr-abc123",
      "workflow_id": "wf-xyz789",
      "step_name": "publish",
      "content": "Content to approve...",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### POST /approvals
Create approval request.

**Query Parameters:**
- `workflow_id`: Workflow ID
- `step_name`: Step name
- `content`: Content to approve

**Response:**
```json
{
  "id": "apr-abc123",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /approvals/{request_id}
Get approval status.

**Response:**
```json
{
  "id": "apr-abc123",
  "status": "pending",
  "workflow_id": "wf-xyz789",
  "step_name": "publish"
}
```

#### POST /approvals/{request_id}/decide
Approve or reject request.

**Request:**
```json
{
  "approved": true,
  "reason": "Content looks good",
  "decided_by": "reviewer@example.com"
}
```

**Response:**
```json
{
  "id": "apr-abc123",
  "status": "approved",
  "decided_at": "2024-01-15T10:35:00Z",
  "decided_by": "reviewer@example.com"
}
```

---

### Metrics

#### GET /metrics
Get all metrics in JSON format.

**Response:**
```json
{
  "counters": {
    "api_workflow_run_total": 150,
    "api_memory_store_total": 200
  },
  "gauges": {
    "memory_entries": 150
  },
  "histograms": {
    "api_latency_ms": {
      "count": 1000,
      "avg": 25.5,
      "p50": 20.0,
      "p95": 50.0,
      "p99": 100.0
    }
  }
}
```

#### GET /metrics/prometheus
Get metrics in Prometheus format.

**Response:**
```
agentic_api_workflow_run_total 150
agentic_api_memory_store_total 200
agentic_api_latency_ms_count 1000
agentic_api_latency_ms_sum 25500
```

---

### Configuration

#### GET /config
Get current configuration.

**Response:**
```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096
  },
  "guardrails": {
    "enabled": true,
    "rate_limit_enabled": true
  },
  "memory": {
    "backend": "local",
    "max_entries": 1000
  }
}
```

#### GET /config/validate
Validate configuration.

**Response:**
```json
{
  "valid": true,
  "errors": []
}
```

---

### WebSocket

#### WS /ws
Real-time updates via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // {type: "workflow_completed", data: {...}, timestamp: "..."}
};
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Error |

---

## Pagination

For list endpoints, use query parameters:

- `limit`: Maximum items (default: 100, max: 1000)
- `offset`: Skip items (default: 0)

Example:
```
GET /workflows?limit=20&offset=40
```

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
