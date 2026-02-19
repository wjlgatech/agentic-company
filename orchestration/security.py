"""
Security module for authentication, authorization, and rate limiting.

Provides JWT-based auth, API key validation, and RBAC.
"""

import hashlib
import hmac
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

# Try to import JWT library
try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None


# ============== Configuration ==============


@dataclass
class SecurityConfig:
    """Security configuration."""

    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    allowed_origins: list = None
    enable_cors: bool = True


# Default config
_security_config = SecurityConfig()


def configure_security(config: SecurityConfig) -> None:
    """Configure security settings."""
    global _security_config
    _security_config = config


# ============== JWT Authentication ==============


def create_jwt_token(
    user_id: str,
    roles: list[str] = None,
    expiry_hours: int | None = None,
) -> str:
    """Create a JWT token."""
    if not JWT_AVAILABLE:
        raise ImportError("PyJWT not installed. Run: pip install PyJWT")

    expiry = expiry_hours or _security_config.jwt_expiry_hours
    payload = {
        "sub": user_id,
        "roles": roles or ["user"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expiry),
    }

    return jwt.encode(
        payload,
        _security_config.jwt_secret,
        algorithm=_security_config.jwt_algorithm,
    )


def verify_jwt_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT token."""
    if not JWT_AVAILABLE:
        raise ImportError("PyJWT not installed. Run: pip install PyJWT")

    try:
        payload = jwt.decode(
            token,
            _security_config.jwt_secret,
            algorithms=[_security_config.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# FastAPI security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict[str, Any]:
    """Get current user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return verify_jwt_token(credentials.credentials)


def require_roles(*required_roles: str):
    """Decorator to require specific roles."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, user: dict = None, **kwargs):
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            user_roles = set(user.get("roles", []))
            if not user_roles.intersection(required_roles):
                raise HTTPException(
                    status_code=403, detail=f"Requires one of roles: {required_roles}"
                )

            return await func(*args, user=user, **kwargs)

        return wrapper

    return decorator


# ============== API Key Authentication ==============

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory API key store (use database in production)
_api_keys: dict[str, dict] = {}


def generate_api_key(user_id: str, name: str = "default") -> str:
    """Generate a new API key."""
    key = f"epi_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    _api_keys[key_hash] = {
        "user_id": user_id,
        "name": name,
        "created_at": datetime.utcnow(),
        "last_used": None,
    }

    return key


def validate_api_key(key: str) -> dict | None:
    """Validate an API key."""
    if not key:
        return None

    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_data = _api_keys.get(key_hash)

    if key_data:
        key_data["last_used"] = datetime.utcnow()
        return key_data

    return None


async def get_api_key_user(
    api_key: str = Security(api_key_header),
) -> dict | None:
    """Get user from API key."""
    if not api_key:
        return None

    key_data = validate_api_key(api_key)
    if not key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"user_id": key_data["user_id"], "roles": ["api"]}


# ============== Rate Limiting ==============


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        if key in self.requests:
            self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]
        else:
            self.requests[key] = []

        current = len(self.requests[key])
        remaining = max(0, self.max_requests - current)

        if current >= self.max_requests:
            reset_time = self.requests[key][0] + self.window_seconds
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset": int(reset_time),
            }

        self.requests[key].append(now)
        return True, {
            "limit": self.max_requests,
            "remaining": remaining - 1,
            "reset": int(now + self.window_seconds),
        }


# Global rate limiter
_rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for FastAPI."""
    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "")
    identifier = api_key or client_ip

    allowed, info = _rate_limiter.is_allowed(identifier)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset"]),
            },
        )

    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(info["reset"])

    return response


# ============== Input Validation ==============


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input."""
    if not text:
        return ""

    # Truncate
    text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    return text


def validate_workflow_name(name: str) -> bool:
    """Validate workflow name."""
    import re

    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$", name))


# ============== HMAC Signature Verification ==============


def sign_payload(payload: str, secret: str) -> str:
    """Sign a payload with HMAC."""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature."""
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


# ============== Audit Logging ==============


class AuditLogger:
    """Audit logging for security events."""

    def __init__(self):
        self.logs: list[dict] = []

    def log(
        self,
        action: str,
        user_id: str | None = None,
        resource: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log an audit event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address,
        }
        self.logs.append(event)

        # Keep only last 10000 events in memory
        if len(self.logs) > 10000:
            self.logs = self.logs[-5000:]

    def get_events(
        self,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get audit events."""
        events = self.logs
        if user_id:
            events = [e for e in events if e["user_id"] == user_id]
        if action:
            events = [e for e in events if e["action"] == action]
        return events[-limit:]


# Global audit logger
audit_logger = AuditLogger()
