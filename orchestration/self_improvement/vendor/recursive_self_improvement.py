import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any


class RecursiveSelfImprovementProtocol:
    def __init__(self, ethical_constraints: dict[str, Any] | None = None):
        """
        Initialize Recursive Self-Improvement Protocol

        :param ethical_constraints: Dictionary of ethical guidelines
        """
        self.improvement_history: list[dict[str, Any]] = []
        self.learning_strategies: list[Callable] = []
        self.capability_map: dict[str, Any] = {}

        # Default ethical constraints
        self.ethical_constraints = ethical_constraints or {
            "do_no_harm": True,
            "human_alignment": True,
            "transparency": True,
            "reversibility": True,
        }

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - RecursiveSelfImprovement - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def register_learning_strategy(self, strategy: Callable) -> None:
        """
        Register a learning strategy for self-improvement

        :param strategy: Function implementing a learning approach
        """
        self.learning_strategies.append(strategy)

    def update_capability_map(self, new_capabilities: dict[str, Any]) -> None:
        """
        Update the system's capability map

        :param new_capabilities: Dictionary of new or updated capabilities
        """
        for capability, details in new_capabilities.items():
            self.capability_map[capability] = {
                "added_timestamp": datetime.now().isoformat(),
                **details,
            }

        self._log_improvement("capability_update", new_capabilities)

    def generate_improvement_proposals(self) -> list[dict[str, Any]]:
        """
        Generate potential self-improvement strategies

        :return: List of improvement proposals
        """
        proposals = []

        # Analyze current capabilities
        capability_gaps = self._identify_capability_gaps()

        # Generate proposals based on learning strategies
        for strategy in self.learning_strategies:
            try:
                strategy_proposals = strategy(self.capability_map, capability_gaps)
                proposals.extend(strategy_proposals)
            except Exception as e:
                self.logger.error(f"Learning strategy failed: {e}")

        return self._filter_proposals(proposals)

    def _identify_capability_gaps(self) -> dict[str, Any]:
        """
        Identify gaps in current capabilities.

        Rule-based: checks capability_map for low proficiency (<0.5)
        and stale entries (>30 days). Also checks for expected capabilities
        that are missing entirely.

        :return: Dictionary of capability gaps
        """
        expected_capabilities = [
            "task_execution",
            "learning",
            "communication",
            "problem_solving",
            "self_monitoring",
        ]

        low_performance: list[str] = []
        missing: list[str] = []
        potential_improvements: list[str] = []

        now = datetime.now()

        # Check for low-proficiency and stale capabilities
        for cap_name, cap_data in self.capability_map.items():
            proficiency = cap_data.get("proficiency", 0.0)
            if isinstance(proficiency, (int, float)) and proficiency < 0.5:
                low_performance.append(cap_name)

            # Check staleness
            added_ts = cap_data.get("added_timestamp", "")
            if added_ts:
                try:
                    added_dt = datetime.fromisoformat(added_ts)
                    days_old = (now - added_dt).days
                    if days_old > 30:
                        potential_improvements.append(
                            f"{cap_name} (stale: {days_old} days)"
                        )
                except ValueError:
                    pass

        # Check for expected capabilities that are missing
        for expected in expected_capabilities:
            if expected not in self.capability_map:
                missing.append(expected)

        return {
            "low_performance_areas": low_performance,
            "missing_capabilities": missing,
            "potential_improvements": potential_improvements,
        }

    def _filter_proposals(
        self, proposals: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Filter improvement proposals based on ethical constraints

        :param proposals: List of improvement proposals
        :return: Filtered list of proposals
        """
        filtered_proposals = []

        for proposal in proposals:
            if self._validate_proposal(proposal):
                filtered_proposals.append(proposal)

        return filtered_proposals

    def _validate_proposal(self, proposal: dict[str, Any]) -> bool:
        """
        Validate an improvement proposal against ethical constraints

        :param proposal: Improvement proposal to validate
        :return: Whether the proposal passes ethical validation
        """
        # Check against each ethical constraint
        for constraint, required in self.ethical_constraints.items():
            if not proposal.get(f"meets_{constraint}", False) and required:
                self.logger.warning(f"Proposal failed {constraint} constraint")
                return False

        return True

    def execute_improvement(self, proposal: dict[str, Any]) -> None:
        """
        Execute a selected improvement proposal

        :param proposal: Improvement proposal to execute
        """
        try:
            improvement_result = self._implement_improvement(proposal)

            # Log improvement
            self._log_improvement(
                "proposal_execution",
                {"proposal": proposal, "result": improvement_result},
            )
        except Exception as e:
            self.logger.error(f"Improvement execution failed: {e}")

    def _implement_improvement(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """
        Implement a specific improvement proposal.

        If proposal has a 'target' capability: updates or creates it in capability_map.
        Existing capabilities get +0.1 proficiency (capped at 1.0).
        New capabilities start at 0.1 proficiency.

        :param proposal: Improvement proposal to implement
        :return: Detailed change record
        """
        target = proposal.get("target", "")
        result: dict[str, Any] = {
            "status": "implemented",
            "timestamp": datetime.now().isoformat(),
            "changes": [],
        }

        if target:
            if target in self.capability_map:
                old_prof = self.capability_map[target].get("proficiency", 0.0)
                new_prof = min(1.0, old_prof + 0.1)
                self.capability_map[target]["proficiency"] = new_prof
                self.capability_map[target][
                    "last_improved"
                ] = datetime.now().isoformat()
                result["changes"].append(
                    {
                        "action": "improved",
                        "capability": target,
                        "old_proficiency": old_prof,
                        "new_proficiency": new_prof,
                    }
                )
            else:
                self.capability_map[target] = {
                    "added_timestamp": datetime.now().isoformat(),
                    "proficiency": 0.1,
                    "source": proposal.get("type", "improvement"),
                }
                result["changes"].append(
                    {
                        "action": "created",
                        "capability": target,
                        "proficiency": 0.1,
                    }
                )

        return result

    def _log_improvement(self, improvement_type: str, details: dict[str, Any]) -> None:
        """
        Log an improvement event

        :param improvement_type: Type of improvement
        :param details: Details of the improvement
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": improvement_type,
            "details": details,
        }

        self.improvement_history.append(log_entry)

    def generate_improvement_report(self, time_window: int = 30) -> dict[str, Any]:
        """
        Generate a comprehensive improvement report

        :param time_window: Number of days to include in the report
        :return: Improvement report
        """
        cutoff_date = datetime.now() - timedelta(days=time_window)

        recent_improvements = [
            log
            for log in self.improvement_history
            if datetime.fromisoformat(log["timestamp"]) > cutoff_date
        ]

        improvement_types: dict[str, int] = {}
        report: dict[str, Any] = {
            "total_improvements": len(recent_improvements),
            "improvement_types": improvement_types,
            "capability_growth": self._analyze_capability_growth(recent_improvements),
        }

        # Aggregate improvement types
        for log in recent_improvements:
            imp_type = log["type"]
            improvement_types[imp_type] = improvement_types.get(imp_type, 0) + 1

        return report

    def _analyze_capability_growth(
        self, improvements: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze capability growth from recent improvements.

        Counts actual capability_update and proposal_execution entries.
        Calculates growth rate as total changes / number of improvements.

        :param improvements: List of recent improvement logs
        :return: Capability growth analysis with real counts
        """
        new_capabilities = 0
        improved_capabilities = 0

        for entry in improvements:
            imp_type = entry.get("type", "")
            if imp_type == "capability_update":
                details = entry.get("details", {})
                new_capabilities += len(details) if isinstance(details, dict) else 1
            elif imp_type == "proposal_execution":
                details = entry.get("details", {})
                result = details.get("result", {})
                changes = result.get("changes", [])
                for change in changes:
                    if change.get("action") == "created":
                        new_capabilities += 1
                    elif change.get("action") == "improved":
                        improved_capabilities += 1

        total_changes = new_capabilities + improved_capabilities
        growth_rate = total_changes / len(improvements) if improvements else 0.0

        return {
            "new_capabilities": new_capabilities,
            "improved_capabilities": improved_capabilities,
            "growth_rate": growth_rate,
        }
