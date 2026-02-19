"""Tests for guardrails system."""

from orchestration.guardrails import (
    ContentFilter,
    GuardrailPipeline,
    LengthGuardrail,
    PIIGuardrail,
    RateLimiter,
    RelevanceGuardrail,
    create_default_pipeline,
)


class TestContentFilter:
    """Tests for ContentFilter guardrail."""

    def test_passes_clean_content(self):
        """Clean content should pass."""
        filter = ContentFilter(blocked_topics=["harmful", "illegal"])
        result = filter.check("This is a helpful article about cooking.")
        assert result.passed
        assert result.guardrail_name == "content_filter"

    def test_blocks_harmful_content(self):
        """Content with blocked topics should be blocked."""
        filter = ContentFilter(blocked_topics=["harmful", "violence"])
        result = filter.check("This contains harmful information.")
        assert not result.passed
        assert "harmful" in result.message.lower()

    def test_case_insensitive_by_default(self):
        """Blocking should be case insensitive by default."""
        filter = ContentFilter(blocked_topics=["harmful"])
        result = filter.check("This is HARMFUL content.")
        assert not result.passed

    def test_case_sensitive_option(self):
        """Case sensitive mode should only match exact case."""
        filter = ContentFilter(blocked_topics=["Harmful"], case_sensitive=True)
        result = filter.check("This is harmful content.")
        assert result.passed  # lowercase doesn't match

    def test_blocked_patterns(self):
        """Regex patterns should be blocked."""
        filter = ContentFilter(blocked_patterns=[r"\d{3}-\d{2}-\d{4}"])
        result = filter.check("My SSN is 123-45-6789.")
        assert not result.passed


class TestRelevanceGuardrail:
    """Tests for RelevanceGuardrail."""

    def test_passes_relevant_content(self):
        """Content matching allowed topics should pass."""
        guard = RelevanceGuardrail(allowed_topics=["python", "coding", "tutorial"])
        result = guard.check("Learn Python coding in this tutorial.")
        assert result.passed
        assert "python" in result.details.get("matched_topics", [])

    def test_blocks_irrelevant_content(self):
        """Content not matching allowed topics should be blocked."""
        guard = RelevanceGuardrail(allowed_topics=["python", "coding"])
        result = guard.check("Best recipes for chocolate cake.")
        assert not result.passed

    def test_no_restrictions_passes(self):
        """Empty topic list should pass all content."""
        guard = RelevanceGuardrail(allowed_topics=[])
        result = guard.check("Any random content here.")
        assert result.passed


class TestRateLimiter:
    """Tests for RateLimiter guardrail."""

    def test_allows_within_limit(self):
        """Requests within limit should pass."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _i in range(5):
            result = limiter.check("request", {"user_id": "user1"})
            assert result.passed

    def test_blocks_over_limit(self):
        """Requests over limit should be blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("request", {"user_id": "user1"})

        result = limiter.check("request", {"user_id": "user1"})
        assert not result.passed
        assert "exceeded" in result.message.lower()

    def test_separate_user_limits(self):
        """Different users should have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # User 1 makes 2 requests
        limiter.check("request", {"user_id": "user1"})
        limiter.check("request", {"user_id": "user1"})

        # User 2 should still be able to make requests
        result = limiter.check("request", {"user_id": "user2"})
        assert result.passed

    def test_reset_clears_counters(self):
        """Reset should clear counters."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("request", {"user_id": "user1"})

        limiter.reset("user1")

        result = limiter.check("request", {"user_id": "user1"})
        assert result.passed


class TestLengthGuardrail:
    """Tests for LengthGuardrail."""

    def test_passes_valid_length(self):
        """Content within bounds should pass."""
        guard = LengthGuardrail(min_length=10, max_length=100)
        result = guard.check("This is a valid length string.")
        assert result.passed

    def test_blocks_too_short(self):
        """Content below min length should be blocked."""
        guard = LengthGuardrail(min_length=50)
        result = guard.check("Too short")
        assert not result.passed
        assert "short" in result.message.lower()

    def test_blocks_too_long(self):
        """Content above max length should be blocked."""
        guard = LengthGuardrail(max_length=10)
        result = guard.check("This content is way too long for the limit")
        assert not result.passed
        assert "long" in result.message.lower()


class TestPIIGuardrail:
    """Tests for PIIGuardrail."""

    def test_detects_email(self):
        """Should detect email addresses."""
        guard = PIIGuardrail(check_email=True)
        result = guard.check("Contact me at john@example.com")
        assert not result.passed
        assert "email" in result.details.get("pii_types", [])

    def test_detects_phone(self):
        """Should detect phone numbers."""
        guard = PIIGuardrail(check_phone=True)
        result = guard.check("Call me at 555-123-4567")
        assert not result.passed
        assert "phone" in result.details.get("pii_types", [])

    def test_detects_ssn(self):
        """Should detect SSN patterns."""
        guard = PIIGuardrail(check_ssn=True)
        result = guard.check("My SSN is 123-45-6789")
        assert not result.passed
        assert "ssn" in result.details.get("pii_types", [])

    def test_passes_clean_content(self):
        """Content without PII should pass."""
        guard = PIIGuardrail()
        result = guard.check("This is clean content with no personal info.")
        assert result.passed


class TestGuardrailPipeline:
    """Tests for GuardrailPipeline."""

    def test_runs_all_guardrails(self):
        """Pipeline should run all guardrails."""
        pipeline = GuardrailPipeline(
            [
                ContentFilter(),
                LengthGuardrail(min_length=1),
            ]
        )
        results = pipeline.check("Valid content")
        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_check_all_pass(self):
        """check_all_pass should return overall status."""
        pipeline = GuardrailPipeline(
            [
                ContentFilter(blocked_topics=["bad"]),
                LengthGuardrail(min_length=1),
            ]
        )

        passed, results = pipeline.check_all_pass("Good content")
        assert passed
        assert len(results) == 2

    def test_check_stop_on_fail(self):
        """check_stop_on_fail should stop at first failure."""
        pipeline = GuardrailPipeline(
            [
                ContentFilter(blocked_topics=["stop"]),
                LengthGuardrail(min_length=1000),  # Would fail
            ]
        )

        passed, results = pipeline.check_stop_on_fail("Please stop here")
        assert not passed
        assert len(results) == 1  # Stopped at first failure

    def test_add_method(self):
        """add() should append guardrails."""
        pipeline = GuardrailPipeline()
        pipeline.add(ContentFilter()).add(LengthGuardrail())
        assert len(pipeline) == 2

    def test_default_pipeline(self):
        """create_default_pipeline should create usable pipeline."""
        pipeline = create_default_pipeline()
        assert len(pipeline) == 3
        passed, _ = pipeline.check_all_pass("Valid content here")
        assert passed
