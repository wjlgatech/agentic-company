"""
Additional API endpoint tests for orchestration/api.py.

Covers endpoints not exercised by the existing tests/test_api.py:
- /api/health (dashboard backend status check)
- Memory CRUD: store, retrieve, delete, search
- Approvals: list, create, get by ID (not-found 404)
- Chat: session management, response structure
- Metrics: /metrics (JSON), /metrics/prometheus (text)
- Config: /config, /config/validate, /api/config/key
- UX/error quality: 404 detail fields, 422 field identification,
  malformed JSON, missing required fields
"""

import json

import pytest
from fastapi.testclient import TestClient

from orchestration.api import app


@pytest.fixture(scope="module")
def client():
    """Module-scoped TestClient to share app state within this module."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/health — dashboard backend status
# ---------------------------------------------------------------------------


class TestApiHealthEndpoint:
    def test_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_has_status_field(self, client):
        data = client.get("/api/health").json()
        assert "status" in data
        assert data["status"] in ("ok", "needs_setup")

    def test_has_version_field(self, client):
        data = client.get("/api/health").json()
        assert "version" in data

    def test_has_backend_info(self, client):
        data = client.get("/api/health").json()
        assert "available_backends" in data
        assert "ready_backends" in data
        assert isinstance(data["available_backends"], list)


# ---------------------------------------------------------------------------
# Memory CRUD
# ---------------------------------------------------------------------------


class TestMemoryCRUD:
    def test_store_returns_id_and_stored_status(self, client):
        response = client.post(
            "/memory/store",
            json={"content": "test memory content", "tags": ["test"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "stored"
        assert len(data["id"]) > 0

    def test_retrieve_stored_memory_by_id(self, client):
        store_resp = client.post(
            "/memory/store",
            json={"content": "retrievable content", "tags": ["retrieve-test"]},
        )
        entry_id = store_resp.json()["id"]

        response = client.get(f"/memory/{entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "retrievable content"
        assert "retrieve-test" in data["tags"]

    def test_retrieve_nonexistent_returns_404(self, client):
        response = client.get("/memory/nonexistent-id-99999xyz")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_delete_stored_memory_succeeds(self, client):
        store_resp = client.post("/memory/store", json={"content": "to be deleted"})
        entry_id = store_resp.json()["id"]

        response = client.delete(f"/memory/{entry_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_deleted_memory_is_gone(self, client):
        store_resp = client.post("/memory/store", json={"content": "ephemeral"})
        entry_id = store_resp.json()["id"]
        client.delete(f"/memory/{entry_id}")

        response = client.get(f"/memory/{entry_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete("/memory/no-such-memory-xyz")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_search_returns_results_structure(self, client):
        client.post(
            "/memory/store",
            json={"content": "searchable python content", "tags": ["python"]},
        )
        response = client.post(
            "/memory/search", json={"query": "searchable", "limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert "query" in data
        assert isinstance(data["results"], list)

    def test_search_respects_limit(self, client):
        # Store several entries
        for i in range(5):
            client.post("/memory/store", json={"content": f"limit-test-content-{i}"})
        response = client.post(
            "/memory/search", json={"query": "limit-test", "limit": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 2

    def test_store_with_metadata(self, client):
        response = client.post(
            "/memory/store",
            json={
                "content": "content with meta",
                "tags": ["meta-test"],
                "metadata": {"source": "test", "priority": 1},
            },
        )
        assert response.status_code == 200
        entry_id = response.json()["id"]

        get_resp = client.get(f"/memory/{entry_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["metadata"]["source"] == "test"


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


class TestApprovals:
    def test_list_pending_has_correct_structure(self, client):
        response = client.get("/approvals")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "count" in data
        assert isinstance(data["pending"], list)

    def test_create_approval_request_succeeds(self, client):
        response = client.post(
            "/approvals",
            params={
                "workflow_id": "test-workflow",
                "step_name": "deploy",
                "content": "Deploy to production",
            },
        )
        assert response.status_code == 200
        # Response should be the created approval dict
        assert isinstance(response.json(), dict)

    def test_get_nonexistent_approval_returns_404(self, client):
        response = client.get("/approvals/nonexistent-id-99999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_created_approval_appears_in_pending_list(self, client):
        # Create an approval
        create_resp = client.post(
            "/approvals",
            params={
                "workflow_id": "wf-pending-test",
                "step_name": "deploy",
                "content": "content",
            },
        )
        assert create_resp.status_code == 200

        # It should be in the pending list
        list_resp = client.get("/approvals")
        assert list_resp.status_code == 200
        # Pending count should be >= 1 after creating
        assert list_resp.json()["count"] >= 1


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


class TestChatEndpoint:
    def test_first_message_returns_session_id(self, client):
        response = client.post("/api/chat", json={"message": "hello"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_response_has_all_required_fields(self, client):
        response = client.post("/api/chat", json={"message": "marketing"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "backend_used" in data
        assert "session_id" in data
        assert "workflow_ready" in data

    def test_session_continuity_with_session_id(self, client):
        # Start a session
        resp1 = client.post("/api/chat", json={"message": "start"})
        session_id = resp1.json()["session_id"]

        # Continue with same session ID
        resp2 = client.post(
            "/api/chat",
            json={"message": "marketing", "session_id": session_id},
        )
        assert resp2.status_code == 200
        assert resp2.json()["session_id"] == session_id

    def test_suggestions_is_list_or_none(self, client):
        response = client.post("/api/chat", json={"message": "hello"})
        data = response.json()
        if data.get("suggestions") is not None:
            assert isinstance(data["suggestions"], list)

    def test_workflow_ready_is_boolean(self, client):
        response = client.post("/api/chat", json={"message": "hello"})
        assert isinstance(response.json()["workflow_ready"], bool)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_metrics_json_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data

    def test_prometheus_metrics_returns_plain_text(self, client):
        response = client.get("/metrics/prometheus")
        assert response.status_code == 200
        content_type = response.headers["content-type"]
        assert "text/plain" in content_type

    def test_metrics_counters_are_numbers(self, client):
        data = client.get("/metrics").json()
        for name, value in data["counters"].items():
            assert isinstance(value, (int, float)), f"Counter {name} should be numeric"


# ---------------------------------------------------------------------------
# Config endpoints
# ---------------------------------------------------------------------------


class TestConfigEndpoints:
    def test_get_config_returns_dict(self, client):
        response = client.get("/config")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_validate_config_has_valid_and_errors(self, client):
        response = client.get("/config/validate")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert isinstance(data["valid"], bool)

    def test_save_api_key_anthropic(self, client):
        response = client.post(
            "/api/config/key",
            json={"provider": "anthropic", "key": "sk-ant-test-key"},
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "anthropic"
        assert response.json()["status"] == "ok"

    def test_save_api_key_openai(self, client):
        response = client.post(
            "/api/config/key",
            json={"provider": "openai", "key": "sk-test-key"},
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "openai"

    def test_save_api_key_unknown_provider_returns_400(self, client):
        response = client.post(
            "/api/config/key",
            json={"provider": "unknown-llm-provider", "key": "test"},
        )
        assert response.status_code == 400
        assert "detail" in response.json()


# ---------------------------------------------------------------------------
# UX: error quality checks
# ---------------------------------------------------------------------------


class TestErrorQuality:
    def test_404_has_human_readable_detail(self, client):
        """404 responses must include a `detail` key with meaningful text."""
        response = client.get("/memory/absolutely-nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 3

    def test_422_on_missing_required_field_identifies_field(self, client):
        """Sending incomplete body should return 422 with the field name."""
        # /memory/store requires `content` field
        response = client.post("/memory/store", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        error_text = json.dumps(data["detail"])
        assert "content" in error_text

    def test_422_on_malformed_json_body(self, client):
        """Non-JSON body with JSON content-type returns 422."""
        response = client.post(
            "/memory/store",
            content="definitely not json {{{{",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422

    def test_422_when_workflow_run_missing_workflow_name(self, client):
        """POST /workflows/run without workflow_name should be 422."""
        response = client.post(
            "/workflows/run",
            json={"input_data": "some input"},  # Missing workflow_name
        )
        assert response.status_code == 422

    def test_422_memory_search_limit_exceeds_maximum(self, client):
        """limit > 100 violates Pydantic Field(le=100) → 422."""
        response = client.post("/memory/search", json={"query": "test", "limit": 999})
        assert response.status_code == 422

    def test_422_memory_search_limit_below_minimum(self, client):
        """limit < 1 violates Pydantic Field(ge=1) → 422."""
        response = client.post("/memory/search", json={"query": "test", "limit": 0})
        assert response.status_code == 422

    def test_approval_404_detail_is_descriptive(self, client):
        response = client.get("/approvals/no-such-approval")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 5
