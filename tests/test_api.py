"""Tests for FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient

from orchestration.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Health endpoint should return status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "components" in data

    def test_liveness_probe(self, client):
        """Liveness probe should return alive."""
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness_probe(self, client):
        """Readiness probe should return ready status."""
        response = client.get("/ready")
        # May return 200 or 503 depending on config
        assert response.status_code in [200, 503]


class TestWorkflowEndpoints:
    """Tests for workflow management endpoints."""

    def test_list_workflows(self, client):
        """Should list available workflows."""
        response = client.get("/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "count" in data
        assert len(data["workflows"]) > 0

    def test_run_workflow(self, client):
        """Should run a workflow and return result."""
        response = client.post(
            "/workflows/run",
            json={
                "workflow_name": "content-research",
                "input_data": "AI trends 2024",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_name"] == "content-research"
        assert data["status"] == "completed"
        assert "workflow_id" in data

    def test_get_workflow_status(self, client):
        """Should return workflow status by ID."""
        response = client.get("/workflows/test-workflow-123")
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert "status" in data


class TestMemoryEndpoints:
    """Tests for memory storage endpoints."""

    def test_store_memory(self, client):
        """Should store content in memory."""
        response = client.post(
            "/memory/store",
            json={
                "content": "Important information to remember",
                "tags": ["test", "important"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "stored"

    def test_search_memory(self, client):
        """Should search memory for content."""
        # First store something
        client.post(
            "/memory/store",
            json={
                "content": "Python programming tutorial",
                "tags": ["python"],
            },
        )

        # Then search
        response = client.post(
            "/memory/search",
            json={
                "query": "Python",
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data

    def test_get_memory_entry_not_found(self, client):
        """Should return 404 for non-existent entry."""
        response = client.get("/memory/nonexistent-id")
        assert response.status_code == 404

    def test_delete_memory_entry_not_found(self, client):
        """Should return 404 for deleting non-existent entry."""
        response = client.delete("/memory/nonexistent-id")
        assert response.status_code == 404


class TestApprovalEndpoints:
    """Tests for approval workflow endpoints."""

    def test_list_pending_approvals(self, client):
        """Should list pending approvals."""
        response = client.get("/approvals")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "count" in data

    def test_create_approval_request(self, client):
        """Should create approval request."""
        response = client.post(
            "/approvals",
            params={
                "workflow_id": "test-workflow",
                "step_name": "publish",
                "content": "Content to approve",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"


class TestMetricsEndpoints:
    """Tests for metrics endpoints."""

    def test_get_metrics(self, client):
        """Should return metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data

    def test_get_prometheus_metrics(self, client):
        """Should return Prometheus-formatted metrics."""
        response = client.get("/metrics/prometheus")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/")


class TestConfigEndpoints:
    """Tests for configuration endpoints."""

    def test_get_config(self, client):
        """Should return current configuration."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "llm" in data
        assert "guardrails" in data
        assert "memory" in data

    def test_validate_config(self, client):
        """Should validate configuration."""
        response = client.get("/config/validate")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data


class TestWebSocket:
    """Tests for WebSocket endpoint."""

    def test_websocket_connection(self, client):
        """Should establish WebSocket connection."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("Hello")
            data = websocket.receive_json()
            assert data["type"] == "echo"
            assert data["data"] == "Hello"
