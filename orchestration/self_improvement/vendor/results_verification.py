import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any


class ResultsVerificationFramework:
    def __init__(self, max_history: int = 1000):
        """
        Initialize Results Verification System

        :param max_history: Maximum number of verification history entries (FIFO pruning)
        """
        self.verification_criteria = {
            "specific": self._check_specificity,
            "measurable": self._check_measurability,
            "actionable": self._check_actionability,
            "reusable": self._check_reusability,
            "compoundable": self._check_compoundability,
        }

        self.verification_history: list[dict[str, Any]] = []
        self.max_history = max_history

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - ResultsVerification - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def add_custom_verification_criterion(
        self, name: str, verification_func: Callable
    ) -> None:
        """
        Add a custom verification criterion

        :param name: Name of the criterion
        :param verification_func: Function to verify the criterion
        """
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        if not callable(verification_func):
            raise TypeError(
                f"verification_func must be callable, got {type(verification_func).__name__}"
            )
        self.verification_criteria[name] = verification_func

    def verify_results(self, results: dict[str, Any]) -> dict[str, bool]:
        """
        Verify results against predefined criteria

        :param results: Dictionary of results to verify
        :return: Verification results for each criterion
        """
        if not isinstance(results, dict):
            raise TypeError(f"results must be a dict, got {type(results).__name__}")
        verification_results = {}
        for criterion, check_func in self.verification_criteria.items():
            try:
                verification_results[criterion] = check_func(results)
            except Exception as e:
                self.logger.error(f"Error in {criterion} verification: {e}")
                verification_results[criterion] = False

        # Log verification attempt
        verification_log = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "verification_results": verification_results,
            "overall_valid": all(verification_results.values()),
        }
        self.verification_history.append(verification_log)

        # FIFO pruning (Bug #10 fix)
        if len(self.verification_history) > self.max_history:
            self.verification_history = self.verification_history[-self.max_history :]

        return verification_results

    def _check_specificity(self, results: dict[str, Any]) -> bool:
        """
        Check if results are specific and well-defined

        :param results: Results to check
        :return: Whether results are specific
        """
        return (
            results is not None
            and isinstance(results, dict)
            and len(results) > 0
            and all(value is not None for value in results.values())
        )

    def _check_measurability(self, results: dict[str, Any]) -> bool:
        """
        Check if results can be quantitatively measured

        :param results: Results to check
        :return: Whether results are measurable
        """
        if not results:
            return False
        return any(isinstance(value, (int, float, str)) for value in results.values())

    def _check_actionability(self, results: dict[str, Any]) -> bool:
        """
        Check if results can be immediately acted upon

        :param results: Results to check
        :return: Whether results are actionable
        """
        return "next_step" in results or "recommendation" in results

    def _check_reusability(self, results: dict[str, Any]) -> bool:
        """
        Check if results can be applied to other contexts

        :param results: Results to check
        :return: Whether results are reusable
        """
        return len(results) > 1  # Multiple applicable insights

    def _check_compoundability(self, results: dict[str, Any]) -> bool:
        """
        Check if results can generate further insights

        :param results: Results to check
        :return: Whether results are compoundable
        """
        return any(isinstance(value, (list, dict)) for value in results.values())

    def export_verification_history(
        self, filename: str = "verification_history.json"
    ) -> None:
        """
        Export verification history to a JSON file

        :param filename: Name of the file to export
        """
        with open(filename, "w") as f:
            json.dump(self.verification_history, f, indent=2)

        self.logger.info(f"Verification history exported to {filename}")

    def get_verification_success_rate(self) -> float:
        """
        Calculate overall verification success rate

        :return: Percentage of successful verifications
        """
        if not self.verification_history:
            return 0.0

        successful_verifications = sum(
            1 for log in self.verification_history if log["overall_valid"]
        )

        return (successful_verifications / len(self.verification_history)) * 100
