"""
Guardrails system for content filtering, rate limiting, and relevance checking.

Provides multiple layers of protection for AI agent workflows.
"""

import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class GuardrailResult:
    """Result from a guardrail check."""

    passed: bool
    guardrail_name: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __bool__(self) -> bool:
        return self.passed


class BaseGuardrail(ABC):
    """Abstract base class for guardrails."""

    name: str = "base"

    @abstractmethod
    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check content against the guardrail."""
        pass


class ContentFilter(BaseGuardrail):
    """Filter content based on blocked topics and patterns."""

    name = "content_filter"

    # Common security patterns for sensitive data
    COMMON_SECURITY_PATTERNS = [
        r"sk-ant-[a-zA-Z0-9\-_]{40,}",  # Anthropic API keys
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API keys
        r"xoxb-[a-zA-Z0-9\-]+",  # Slack bot tokens
        r"ghp_[a-zA-Z0-9]{36,}",  # GitHub personal access tokens
        r"AKIA[0-9A-Z]{16}",  # AWS access key IDs
        r"[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}",  # Credit card numbers
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email addresses (optional - may be too broad)
    ]

    def __init__(
        self,
        blocked_topics: list[str] | None = None,
        blocked_patterns: list[str] | None = None,
        case_sensitive: bool = False,
    ):
        self.blocked_topics = blocked_topics or ["harmful", "illegal", "violence"]
        self.blocked_patterns = [
            re.compile(p, 0 if case_sensitive else re.IGNORECASE)
            for p in (blocked_patterns or [])
        ]
        self.case_sensitive = case_sensitive

    @classmethod
    def with_security_patterns(
        cls,
        blocked_topics: list[str] | None = None,
        additional_patterns: list[str] | None = None,
        case_sensitive: bool = False,
    ) -> "ContentFilter":
        """Create a ContentFilter with common security patterns pre-configured.

        Args:
            blocked_topics: List of blocked topic keywords
            additional_patterns: Additional regex patterns to block (added to security patterns)
            case_sensitive: Whether pattern matching is case-sensitive

        Returns:
            ContentFilter with security patterns enabled

        Example:
            >>> filter = ContentFilter.with_security_patterns()
            >>> result = filter.check("My key is sk-ant-api03-...")
            >>> assert not result.passed  # API key blocked
        """
        patterns = cls.COMMON_SECURITY_PATTERNS.copy()
        if additional_patterns:
            patterns.extend(additional_patterns)
        return cls(
            blocked_topics=blocked_topics,
            blocked_patterns=patterns,
            case_sensitive=case_sensitive,
        )

    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check content for blocked topics and patterns."""
        check_content = content if self.case_sensitive else content.lower()

        # Check blocked topics
        for topic in self.blocked_topics:
            topic_check = topic if self.case_sensitive else topic.lower()
            if topic_check in check_content:
                return GuardrailResult(
                    passed=False,
                    guardrail_name=self.name,
                    message=f"Content contains blocked topic: {topic}",
                    details={"blocked_topic": topic},
                )

        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(content):
                return GuardrailResult(
                    passed=False,
                    guardrail_name=self.name,
                    message=f"Content matches blocked pattern: {pattern.pattern}",
                    details={"blocked_pattern": pattern.pattern},
                )

        return GuardrailResult(
            passed=True,
            guardrail_name=self.name,
            message="Content passed filter",
        )


class RelevanceGuardrail(BaseGuardrail):
    """Check content relevance based on allowed topics."""

    name = "relevance"

    def __init__(
        self,
        allowed_topics: list[str] | None = None,
        threshold: float = 0.5,
    ):
        self.allowed_topics = allowed_topics or []
        self.threshold = threshold

    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check if content is relevant to allowed topics."""
        if not self.allowed_topics:
            return GuardrailResult(
                passed=True,
                guardrail_name=self.name,
                message="No topic restrictions",
            )

        content_lower = content.lower()
        matches = []

        for topic in self.allowed_topics:
            if topic.lower() in content_lower:
                matches.append(topic)

        relevance_score = (
            len(matches) / len(self.allowed_topics) if self.allowed_topics else 0
        )

        if matches:
            return GuardrailResult(
                passed=True,
                guardrail_name=self.name,
                message=f"Content matches topics: {matches}",
                details={"matched_topics": matches, "relevance_score": relevance_score},
            )

        return GuardrailResult(
            passed=False,
            guardrail_name=self.name,
            message="Content does not match any allowed topics",
            details={"allowed_topics": self.allowed_topics, "relevance_score": 0},
        )


class RateLimiter(BaseGuardrail):
    """Rate limiting guardrail."""

    name = "rate_limiter"

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check if request is within rate limit."""
        user_id = (context or {}).get("user_id", "default")
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > window_start
        ]

        current_count = len(self.requests[user_id])

        if current_count >= self.max_requests:
            return GuardrailResult(
                passed=False,
                guardrail_name=self.name,
                message=f"Rate limit exceeded: {current_count}/{self.max_requests}",
                details={
                    "current_requests": current_count,
                    "max_requests": self.max_requests,
                    "window_seconds": self.window_seconds,
                },
            )

        # Record this request
        self.requests[user_id].append(now)

        return GuardrailResult(
            passed=True,
            guardrail_name=self.name,
            message=f"Within rate limit: {current_count + 1}/{self.max_requests}",
            details={
                "current_requests": current_count + 1,
                "max_requests": self.max_requests,
            },
        )

    def reset(self, user_id: str | None = None) -> None:
        """Reset rate limit counters."""
        if user_id:
            self.requests[user_id] = []
        else:
            self.requests.clear()


class LengthGuardrail(BaseGuardrail):
    """Check content length constraints."""

    name = "length"

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 100000,
    ):
        self.min_length = min_length
        self.max_length = max_length

    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check if content length is within bounds."""
        length = len(content)

        if length < self.min_length:
            return GuardrailResult(
                passed=False,
                guardrail_name=self.name,
                message=f"Content too short: {length} < {self.min_length}",
                details={"length": length, "min_length": self.min_length},
            )

        if length > self.max_length:
            return GuardrailResult(
                passed=False,
                guardrail_name=self.name,
                message=f"Content too long: {length} > {self.max_length}",
                details={"length": length, "max_length": self.max_length},
            )

        return GuardrailResult(
            passed=True,
            guardrail_name=self.name,
            message=f"Content length OK: {length}",
            details={"length": length},
        )


class PIIGuardrail(BaseGuardrail):
    """Detect and block personally identifiable information."""

    name = "pii"

    def __init__(
        self, check_email: bool = True, check_phone: bool = True, check_ssn: bool = True
    ):
        self.patterns = {}
        if check_email:
            self.patterns["email"] = re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            )
        if check_phone:
            self.patterns["phone"] = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
        if check_ssn:
            self.patterns["ssn"] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    def check(self, content: str, context: dict | None = None) -> GuardrailResult:
        """Check for PII in content."""
        found_pii = []

        for pii_type, pattern in self.patterns.items():
            if pattern.search(content):
                found_pii.append(pii_type)

        if found_pii:
            return GuardrailResult(
                passed=False,
                guardrail_name=self.name,
                message=f"PII detected: {found_pii}",
                details={"pii_types": found_pii},
            )

        return GuardrailResult(
            passed=True,
            guardrail_name=self.name,
            message="No PII detected",
        )


class GuardrailPipeline:
    """Pipeline for running multiple guardrails."""

    def __init__(self, guardrails: list[BaseGuardrail] | None = None):
        self.guardrails = guardrails or []

    def add(self, guardrail: BaseGuardrail) -> "GuardrailPipeline":
        """Add a guardrail to the pipeline."""
        self.guardrails.append(guardrail)
        return self

    def check(self, content: str, context: dict | None = None) -> list[GuardrailResult]:
        """Run all guardrails and return results."""
        results = []
        for guardrail in self.guardrails:
            result = guardrail.check(content, context)
            results.append(result)
        return results

    def check_all_pass(
        self, content: str, context: dict | None = None
    ) -> tuple[bool, list[GuardrailResult]]:
        """Check if all guardrails pass."""
        results = self.check(content, context)
        all_passed = all(r.passed for r in results)
        return all_passed, results

    def check_stop_on_fail(
        self, content: str, context: dict | None = None
    ) -> tuple[bool, list[GuardrailResult]]:
        """Run guardrails and stop on first failure."""
        results = []
        for guardrail in self.guardrails:
            result = guardrail.check(content, context)
            results.append(result)
            if not result.passed:
                return False, results
        return True, results

    def __len__(self) -> int:
        return len(self.guardrails)


# Factory function for common guardrail configurations
def create_default_pipeline() -> GuardrailPipeline:
    """Create a pipeline with default guardrails."""
    return GuardrailPipeline(
        [
            ContentFilter(),
            RateLimiter(),
            LengthGuardrail(min_length=1, max_length=50000),
        ]
    )
