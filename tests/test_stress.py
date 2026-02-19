"""Stress tests for real-world usage scenarios."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from orchestration.api import app
from orchestration.evaluator import RuleBasedEvaluator
from orchestration.guardrails import ContentFilter, GuardrailPipeline, RateLimiter
from orchestration.memory import LocalMemoryStore
from orchestration.observability import MetricsCollector, ObservabilityStack


class TestConcurrentWorkflows:
    """Test concurrent workflow execution."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_concurrent_api_requests(self, client):
        """API should handle concurrent requests."""

        def make_request(i):
            response = client.post(
                "/workflows/run",
                json={
                    "workflow_name": "test",
                    "input_data": f"Test input {i}",
                },
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(code == 200 for code in results)

    def test_concurrent_memory_operations(self):
        """Memory store should handle concurrent operations."""
        memory = LocalMemoryStore()

        def store_and_search(i):
            # Store
            memory.remember(f"Content number {i}", tags=[f"tag{i}"])
            # Search
            results = memory.search(f"Content number {i}")
            return len(results) > 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(store_and_search, i) for i in range(50)]
            results = [f.result() for f in futures]

        assert all(results)
        assert memory.count() == 50


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_guardrail_throughput(self):
        """Guardrails should process quickly."""
        pipeline = GuardrailPipeline(
            [
                ContentFilter(),
                RateLimiter(max_requests=10000, window_seconds=60),
            ]
        )

        content = "This is a test content for benchmarking guardrail throughput."
        start = time.time()

        for _ in range(1000):
            pipeline.check(content)

        elapsed = time.time() - start
        ops_per_second = 1000 / elapsed

        # Should process at least 1000 ops/second
        assert ops_per_second > 1000, f"Too slow: {ops_per_second:.0f} ops/sec"

    def test_memory_search_performance(self):
        """Memory search should be fast."""
        memory = LocalMemoryStore()

        # Populate with data
        for i in range(500):
            memory.remember(
                f"Document {i} about topic {i % 10}", tags=[f"topic{i % 10}"]
            )

        start = time.time()
        for _ in range(100):
            memory.search("topic 5", limit=10)

        elapsed = time.time() - start
        avg_time_ms = (elapsed / 100) * 1000

        # Average search should be under 10ms
        assert avg_time_ms < 10, f"Too slow: {avg_time_ms:.2f}ms"

    def test_evaluator_performance(self):
        """Evaluator should process quickly."""
        evaluator = RuleBasedEvaluator(
            min_length=10,
            max_length=10000,
            required_elements=["test"],
        )

        content = "This is test content " * 50  # ~1000 chars

        start = time.time()
        for _ in range(500):
            evaluator.evaluate(content)

        elapsed = time.time() - start
        avg_time_ms = (elapsed / 500) * 1000

        # Average evaluation should be under 5ms
        assert avg_time_ms < 5, f"Too slow: {avg_time_ms:.2f}ms"

    def test_api_latency(self):
        """API endpoints should respond quickly."""
        client = TestClient(app)

        # Warmup
        client.get("/health")

        latencies = []
        for _ in range(50):
            start = time.time()
            response = client.get("/health")
            elapsed = (time.time() - start) * 1000
            latencies.append(elapsed)
            assert response.status_code == 200

        avg = sum(latencies) / len(latencies)
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        # Average should be under 50ms, P99 under 100ms
        assert avg < 50, f"Average too high: {avg:.2f}ms"
        assert p99 < 100, f"P99 too high: {p99:.2f}ms"


class TestRealUserScenarios:
    """Simulate real user workflows."""

    def test_content_creation_flow(self):
        """Simulate content creation workflow."""
        # Setup
        memory = LocalMemoryStore()
        guardrails = GuardrailPipeline([ContentFilter()])
        evaluator = RuleBasedEvaluator(min_length=50, required_elements=["blog"])

        # User submits content
        content = "This is a blog post about AI technology and its applications in daily life."

        # Step 1: Check guardrails
        passed, results = guardrails.check_all_pass(content)
        assert passed, "Content should pass guardrails"

        # Step 2: Evaluate quality
        eval_result = evaluator.evaluate(content)
        assert eval_result.score > 0.5, "Content should score reasonably"

        # Step 3: Store in memory
        entry_id = memory.remember(content, tags=["blog", "ai"])
        assert entry_id

        # Step 4: Verify retrieval
        results = memory.search("AI technology")
        assert len(results) > 0

    def test_research_workflow(self):
        """Simulate research workflow."""
        client = TestClient(app)

        # User searches for existing knowledge
        response = client.post(
            "/memory/search",
            json={
                "query": "machine learning",
                "limit": 5,
            },
        )
        assert response.status_code == 200

        # User stores new findings
        response = client.post(
            "/memory/store",
            json={
                "content": "New research on transformer architectures",
                "tags": ["research", "ml", "transformers"],
            },
        )
        assert response.status_code == 200

        # User runs workflow
        response = client.post(
            "/workflows/run",
            json={
                "workflow_name": "content-research",
                "input_data": "Summarize transformer research",
            },
        )
        assert response.status_code == 200

    def test_approval_workflow(self):
        """Simulate approval workflow."""
        client = TestClient(app)

        # Create approval request
        response = client.post(
            "/approvals",
            params={
                "workflow_id": "pub-123",
                "step_name": "publish",
                "content": "Ready to publish: New product announcement",
            },
        )
        assert response.status_code == 200
        request_id = response.json()["id"]

        # Check pending
        response = client.get("/approvals")
        assert response.status_code == 200
        assert response.json()["count"] >= 1

        # Approve
        response = client.post(
            f"/approvals/{request_id}/decide",
            json={
                "approved": True,
                "reason": "Content looks good",
                "decided_by": "reviewer@example.com",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] in ["approved", "auto_approved"]


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_invalid_workflow_input(self):
        """Should handle invalid input gracefully."""
        client = TestClient(app)

        # Empty input
        response = client.post(
            "/workflows/run",
            json={
                "workflow_name": "test",
                "input_data": "",
            },
        )
        # Should still process (empty string is valid JSON)
        assert response.status_code == 200

    def test_memory_not_found(self):
        """Should handle not found errors."""
        client = TestClient(app)

        response = client.get("/memory/nonexistent-id-12345")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_rate_limit_recovery(self):
        """Should recover after rate limit expires."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)

        # Hit rate limit
        for _ in range(3):
            limiter.check("test")

        result = limiter.check("test")
        assert not result.passed

        # Wait for window to expire
        time.sleep(1.1)

        # Should work again
        result = limiter.check("test")
        assert result.passed


class TestMetricsCollection:
    """Test metrics collection under load."""

    def test_metrics_accuracy(self):
        """Metrics should accurately track operations."""
        metrics = MetricsCollector()

        # Perform operations
        for i in range(100):
            metrics.increment("test_counter")
            metrics.set_gauge("test_gauge", i)
            metrics.observe("test_histogram", i * 0.1)

        # Verify
        assert metrics.get_counter("test_counter") == 100
        assert metrics.get_gauge("test_gauge") == 99

        stats = metrics.get_histogram_stats("test_histogram")
        assert stats["count"] == 100
        assert stats["avg"] == pytest.approx(4.95, rel=0.1)

    def test_observability_context_manager(self):
        """Observability context manager should work correctly."""
        obs = ObservabilityStack()

        with obs.observe("test_operation"):
            time.sleep(0.01)  # Simulate work

        metrics = obs.metrics.get_all_metrics()
        assert "test_operation_total" in str(metrics)
        assert "test_operation_duration_ms" in str(metrics)


class TestScaleSimulation:
    """Simulate scale scenarios."""

    def test_many_users(self):
        """Simulate many concurrent users."""
        memory = LocalMemoryStore(max_entries=10000)

        def simulate_user(user_id):
            for i in range(10):
                memory.remember(
                    f"User {user_id} content {i}",
                    tags=[f"user{user_id}"],
                )
            return memory.search(f"User {user_id}", limit=5)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(100)]
            results = [f.result() for f in futures]

        # All users should find their content
        assert all(len(r) > 0 for r in results)

    def test_large_content(self):
        """Should handle large content."""
        guardrails = GuardrailPipeline(
            [
                ContentFilter(),
            ]
        )

        # 100KB of content
        large_content = "Test content. " * 10000

        result = guardrails.check(large_content)
        # Should complete without timeout
        assert len(result) > 0
