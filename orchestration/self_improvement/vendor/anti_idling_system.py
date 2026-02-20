import logging
import time
from collections.abc import Callable
from typing import Any


class AntiIdlingSystem:
    def __init__(
        self, idle_threshold: float = 0.10, minimum_productive_actions: int = 10
    ):
        """
        Initialize Anti-Idling System

        :param idle_threshold: Maximum allowed idle percentage
        :param minimum_productive_actions: Minimum number of productive actions per day
        """
        if not 0.0 <= idle_threshold <= 1.0:
            raise ValueError(
                f"idle_threshold must be between 0.0 and 1.0, got {idle_threshold}"
            )
        if minimum_productive_actions < 0:
            raise ValueError(
                f"minimum_productive_actions must be >= 0, got {minimum_productive_actions}"
            )
        self.idle_threshold = idle_threshold
        self.minimum_productive_actions = minimum_productive_actions
        self._running = False
        self.activity_log: list[dict[str, Any]] = []
        self.intervention_callbacks: list[Callable] = []

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - AntiIdlingSystem - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def log_activity(self, activity: dict[str, Any]) -> None:
        """
        Log a system activity

        :param activity: Dictionary containing activity details
        """
        if not isinstance(activity, dict):
            raise TypeError(f"activity must be a dict, got {type(activity).__name__}")
        current_time = time.time()
        entry = {**activity, "timestamp": current_time}
        self.activity_log.append(entry)

        # Periodically clean old logs (keep last 100 entries)
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]

    def calculate_idle_rate(self, time_window: int = 86400) -> float:
        """
        Calculate idle rate within a given time window

        :param time_window: Time window in seconds (default: 24 hours)
        :return: Percentage of idle time
        """
        if time_window <= 0:
            raise ValueError(f"time_window must be > 0, got {time_window}")

        current_time = time.time()
        recent_activities = [
            activity
            for activity in self.activity_log
            if current_time - activity["timestamp"] <= time_window
        ]

        total_time = time_window
        productive_time = sum(
            activity.get("duration", 0)
            for activity in recent_activities
            if activity.get("is_productive", False)
        )

        idle_rate: float = 1 - (productive_time / total_time)
        return max(0.0, min(1.0, idle_rate))

    def register_intervention_callback(self, callback: Callable) -> None:
        """
        Register a callback function for idle state intervention

        :param callback: Function to call when idle state is detected
        """
        if not callable(callback):
            raise TypeError(f"callback must be callable, got {type(callback).__name__}")
        self.intervention_callbacks.append(callback)

    def detect_and_interrupt_idle_state(self) -> None:
        """
        Detect idle state and trigger interventions
        """
        idle_rate = self.calculate_idle_rate()

        if idle_rate > self.idle_threshold:
            self.logger.warning(f"High idle rate detected: {idle_rate}")

            # Trigger intervention callbacks
            for callback in self.intervention_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Intervention callback failed: {e}")

            # Generate emergency actions
            emergency_actions = self.generate_emergency_actions()

            # Log and potentially execute emergency actions
            for action in emergency_actions:
                self.logger.info(f"Emergency Action: {action}")

    def generate_emergency_actions(self) -> list[str]:
        """
        Generate emergency actions to break idle state.

        Context-aware: analyzes recent activity_log to suggest contrasting actions.
        If activity_log is empty, returns the full action pool for backward compatibility.

        :return: List of emergency action descriptions
        """
        full_pool = [
            "start_research_sprint",
            "design_experimental_prototype",
            "initiate_user_feedback_loop",
            "conduct_strategic_analysis",
            "explore_new_skill_development",
        ]

        # Backward compatible: empty log returns full pool
        if not self.activity_log:
            return full_pool

        # Analyze last 20 entries for type distribution
        recent = self.activity_log[-20:]
        type_counts: dict[str, int] = {}
        for entry in recent:
            activity_type = entry.get("type", "unknown")
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1

        # Map activity types to contrasting actions
        contrast_map: dict[str, list[str]] = {
            "research": [
                "design_experimental_prototype",
                "initiate_user_feedback_loop",
            ],
            "coding": ["initiate_user_feedback_loop", "conduct_strategic_analysis"],
            "meeting": ["start_research_sprint", "explore_new_skill_development"],
            "browsing": ["start_research_sprint", "design_experimental_prototype"],
            "break": ["start_research_sprint", "conduct_strategic_analysis"],
        }

        # Find the dominant type
        if type_counts:
            dominant_type = max(type_counts, key=lambda t: type_counts[t])
        else:
            return full_pool

        # Build context-aware suggestions
        suggestions: list[str] = []

        # Add contrasting actions for dominant type
        contrasts = contrast_map.get(dominant_type, [])
        suggestions.extend(contrasts)

        # If agent stuck on one type (>60% of recent), add strategic pivot
        total = sum(type_counts.values())
        if type_counts.get(dominant_type, 0) / total > 0.6:
            suggestions.append("conduct_strategic_analysis")
            suggestions.append("explore_new_skill_development")

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        # Always return at least 1 action
        return unique if unique else full_pool[:1]

    def stop(self) -> None:
        """Stop the periodic check loop."""
        self._running = False

    def run_periodic_check(self, interval: int = 3600) -> None:
        """
        Run periodic idle state detection

        :param interval: Check interval in seconds
        """
        self._running = True
        while self._running:
            self.detect_and_interrupt_idle_state()
            time.sleep(interval)
