"""
Tests for orchestration/security.py — RateLimiter, AuditLogger, sanitize_input,
validate_workflow_name, sign/verify, API keys, JWT.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from orchestration.security import (
    AuditLogger,
    RateLimiter,
    generate_api_key,
    sanitize_input,
    sign_payload,
    validate_api_key,
    validate_workflow_name,
    verify_signature,
)

# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_allowed_within_limit(self):
        rl = RateLimiter(max_requests=5, window_seconds=60)
        allowed, info = rl.is_allowed("user1")
        assert allowed is True
        assert info["remaining"] == 4

    def test_blocked_at_limit(self):
        rl = RateLimiter(max_requests=2, window_seconds=60)
        rl.is_allowed("u")
        rl.is_allowed("u")
        allowed, info = rl.is_allowed("u")
        assert allowed is False
        assert info["remaining"] == 0

    def test_per_key_isolation(self):
        rl = RateLimiter(max_requests=1, window_seconds=60)
        rl.is_allowed("alice")
        # alice exhausted
        allowed_alice, _ = rl.is_allowed("alice")
        # bob still fresh
        allowed_bob, _ = rl.is_allowed("bob")
        assert allowed_alice is False
        assert allowed_bob is True

    def test_reset_clears_requests(self):
        rl = RateLimiter(max_requests=1, window_seconds=60)
        rl.is_allowed("u")
        # Simulate window expiry
        rl.requests["u"] = []
        allowed, _ = rl.is_allowed("u")
        assert allowed is True

    def test_info_contains_limit(self):
        rl = RateLimiter(max_requests=10, window_seconds=30)
        _, info = rl.is_allowed("x")
        assert info["limit"] == 10


# ---------------------------------------------------------------------------
# AuditLogger
# ---------------------------------------------------------------------------


class TestAuditLogger:
    def test_log_and_get_events(self):
        logger = AuditLogger()
        logger.log("login", user_id="alice", resource="/api")
        events = logger.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "login"

    def test_filter_by_user_id(self):
        logger = AuditLogger()
        logger.log("login", user_id="alice")
        logger.log("logout", user_id="bob")
        events = logger.get_events(user_id="alice")
        assert len(events) == 1
        assert events[0]["user_id"] == "alice"

    def test_filter_by_action(self):
        logger = AuditLogger()
        logger.log("login", user_id="alice")
        logger.log("access", user_id="alice")
        events = logger.get_events(action="access")
        assert len(events) == 1
        assert events[0]["action"] == "access"

    def test_truncation_at_10000_entries(self):
        logger = AuditLogger()
        for i in range(10001):
            logger.log(f"action_{i}")
        # After 10001 inserts, logs are trimmed to last 5000
        assert len(logger.logs) <= 10000

    def test_event_has_timestamp(self):
        logger = AuditLogger()
        logger.log("test")
        events = logger.get_events()
        assert "timestamp" in events[0]

    def test_event_details_default_empty_dict(self):
        logger = AuditLogger()
        logger.log("ev")
        events = logger.get_events()
        assert events[0]["details"] == {}


# ---------------------------------------------------------------------------
# sanitize_input
# ---------------------------------------------------------------------------


class TestSanitizeInput:
    def test_strips_null_bytes(self):
        result = sanitize_input("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result

    def test_truncates_to_max_length(self):
        text = "a" * 200
        result = sanitize_input(text, max_length=50)
        assert len(result) == 50

    def test_empty_string_returns_empty(self):
        assert sanitize_input("") == ""

    def test_normal_text_unchanged(self):
        text = "Hello, world!"
        assert sanitize_input(text) == text


# ---------------------------------------------------------------------------
# validate_workflow_name
# ---------------------------------------------------------------------------


class TestValidateWorkflowName:
    def test_valid_name(self):
        assert validate_workflow_name("my-workflow") is True

    def test_valid_with_underscores(self):
        assert validate_workflow_name("my_workflow_v2") is True

    def test_starts_with_digit_invalid(self):
        assert validate_workflow_name("1bad") is False

    def test_special_chars_invalid(self):
        assert validate_workflow_name("bad@name") is False

    def test_too_long_invalid(self):
        assert validate_workflow_name("a" * 65) is False

    def test_max_length_valid(self):
        # Max 64 chars after first letter
        name = "a" + "b" * 63  # 64 chars total
        assert validate_workflow_name(name) is True


# ---------------------------------------------------------------------------
# sign_payload / verify_signature
# ---------------------------------------------------------------------------


class TestSignPayload:
    def test_sign_and_verify_correct(self):
        sig = sign_payload("payload", "secret")
        assert verify_signature("payload", sig, "secret") is True

    def test_verify_tampered_payload(self):
        sig = sign_payload("payload", "secret")
        assert verify_signature("DIFFERENT", sig, "secret") is False

    def test_verify_different_secret(self):
        sig = sign_payload("payload", "secret1")
        assert verify_signature("payload", sig, "secret2") is False


# ---------------------------------------------------------------------------
# generate_api_key / validate_api_key
# ---------------------------------------------------------------------------


class TestApiKey:
    def test_key_has_correct_prefix(self):
        key = generate_api_key("user1")
        assert key.startswith("epi_")

    def test_validate_correct_key(self):
        key = generate_api_key("user1", name="mykey")
        data = validate_api_key(key)
        assert data is not None
        assert data["user_id"] == "user1"

    def test_validate_updates_last_used(self):
        key = generate_api_key("user2")
        data = validate_api_key(key)
        assert data["last_used"] is not None

    def test_validate_wrong_key_returns_none(self):
        result = validate_api_key("epi_totally_wrong_key")
        assert result is None

    def test_validate_empty_key_returns_none(self):
        result = validate_api_key("")
        assert result is None


# ---------------------------------------------------------------------------
# JWT (mock jwt module)
# ---------------------------------------------------------------------------


class TestJWT:
    def test_create_jwt_token(self):
        """create_jwt_token should return a string when jwt is available."""
        from orchestration import security as sec

        if not sec.JWT_AVAILABLE:
            pytest.skip("PyJWT not installed")

        from orchestration.security import create_jwt_token

        token = create_jwt_token("user1", roles=["admin"])
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_jwt_token_valid(self):
        """Verify a freshly created token should succeed."""
        from orchestration import security as sec

        if not sec.JWT_AVAILABLE:
            pytest.skip("PyJWT not installed")

        from orchestration.security import create_jwt_token, verify_jwt_token

        token = create_jwt_token("user123")
        payload = verify_jwt_token(token)
        assert payload["sub"] == "user123"

    def test_create_jwt_token_raises_when_jwt_unavailable(self):
        with patch("orchestration.security.JWT_AVAILABLE", False):
            from orchestration.security import create_jwt_token

            with pytest.raises(ImportError):
                create_jwt_token("user")
