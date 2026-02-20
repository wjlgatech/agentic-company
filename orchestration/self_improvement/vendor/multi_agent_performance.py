import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any


class MultiAgentPerformanceOptimizer:
    def __init__(self, quality_threshold: float = 0.85):
        """
        Initialize Multi-Agent Performance Optimization System

        :param quality_threshold: Minimum performance threshold
        """
        self.agents: dict[str, dict[str, Any]] = {}
        self.performance_history: list[dict[str, Any]] = []
        self.quality_threshold = quality_threshold
        self.optimization_strategies: list[Callable] = []
        self.metric_weights: dict[str, float] = {
            "accuracy": 0.4,
            "efficiency": 0.35,
            "adaptability": 0.25,
        }

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - MultiAgentPerformance - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def register_agent(self, agent_details: dict[str, Any]) -> str:
        """
        Register a new agent in the system

        :param agent_details: Dictionary containing agent information
        :return: Unique agent ID
        """
        agent_id = str(uuid.uuid4())
        agent_details["id"] = agent_id
        agent_details["registration_time"] = datetime.now().isoformat()
        agent_details["performance_score"] = 0.0

        self.agents[agent_id] = agent_details
        return agent_id

    def update_agent_performance(
        self, agent_id: str, performance_data: dict[str, Any]
    ) -> None:
        """
        Update performance metrics for a specific agent

        :param agent_id: Unique identifier for the agent
        :param performance_data: Dictionary of performance metrics
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")

        # Calculate performance score
        performance_score = self._calculate_performance_score(performance_data)

        # Update agent record
        self.agents[agent_id]["last_performance_update"] = datetime.now().isoformat()
        self.agents[agent_id]["performance_score"] = performance_score

        # Log performance history
        performance_log = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "performance_data": performance_data,
            "performance_score": performance_score,
        }
        self.performance_history.append(performance_log)

        # Check if optimization is needed
        if performance_score < self.quality_threshold:
            self._trigger_optimization(agent_id)

    def _calculate_performance_score(self, performance_data: dict[str, Any]) -> float:
        """
        Calculate a weighted performance score.

        Uses metric_weights to produce a weighted average of available metrics.
        Returns 0.0 if no valid metrics are present.

        :param performance_data: Dictionary of performance metrics
        :return: Calculated performance score
        """
        weighted_sum = 0.0
        total_weight = 0.0

        for metric, weight in self.metric_weights.items():
            value = performance_data.get(metric)
            if isinstance(value, (int, float)):
                weighted_sum += float(value) * weight
                total_weight += weight

        if total_weight == 0.0:
            return 0.0
        return weighted_sum / total_weight

    def register_optimization_strategy(self, strategy: Callable) -> None:
        """
        Register a custom optimization strategy

        :param strategy: Function to call for agent optimization
        """
        self.optimization_strategies.append(strategy)

    def _trigger_optimization(self, agent_id: str) -> None:
        """
        Trigger optimization strategies for underperforming agent

        :param agent_id: ID of the agent needing optimization
        """
        self.logger.warning(f"Optimization needed for agent {agent_id}")

        for strategy in self.optimization_strategies:
            try:
                strategy(self.agents[agent_id])
            except Exception as e:
                self.logger.error(f"Optimization strategy failed: {e}")

    def get_top_performing_agents(self, n: int = 5) -> list[dict[str, Any]]:
        """
        Retrieve top performing agents

        :param n: Number of top agents to return
        :return: List of top performing agents
        """
        sorted_agents = sorted(
            self.agents.values(),
            key=lambda x: x.get("performance_score", 0),
            reverse=True,
        )
        return sorted_agents[:n]

    def generate_performance_report(self, time_window: int = 30) -> dict[str, Any]:
        """
        Generate a comprehensive performance report

        :param time_window: Number of days to include in the report
        :return: Performance report dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=time_window)

        # Filter recent performance history
        recent_history = [
            log
            for log in self.performance_history
            if datetime.fromisoformat(log["timestamp"]) > cutoff_date
        ]

        report = {
            "total_agents": len(self.agents),
            "average_performance": self._calculate_average_performance(),
            "top_performers": self.get_top_performing_agents(),
            "performance_trends": self._analyze_performance_trends(recent_history),
        }

        return report

    def _calculate_average_performance(self) -> float:
        """
        Calculate the average performance across all agents

        :return: Average performance score
        """
        performance_scores = [
            agent.get("performance_score", 0) for agent in self.agents.values()
        ]

        return (
            sum(performance_scores) / len(performance_scores)
            if performance_scores
            else 0
        )

    def _analyze_performance_trends(
        self, performance_logs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze performance trends from recent logs.

        Groups logs by agent_id, splits into first-half vs second-half,
        and computes % change. >5% = improving, <-5% = declining.

        :param performance_logs: List of recent performance logs
        :return: Performance trend analysis with real agent data
        """
        if not performance_logs:
            return {
                "overall_trend": "stable",
                "improving_agents": [],
                "declining_agents": [],
            }

        # Group by agent_id
        agent_scores: dict[str, list[float]] = {}
        for log in performance_logs:
            aid = log.get("agent_id", "unknown")
            score = log.get("performance_score")
            if isinstance(score, (int, float)):
                agent_scores.setdefault(aid, []).append(float(score))

        improving: list[str] = []
        declining: list[str] = []

        for aid, scores in agent_scores.items():
            if len(scores) < 2:
                continue
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / len(scores[mid:])

            if first_half_avg == 0:
                continue
            pct_change = (second_half_avg - first_half_avg) / first_half_avg * 100

            if pct_change > 5:
                improving.append(aid)
            elif pct_change < -5:
                declining.append(aid)

        if len(improving) > len(declining):
            overall = "improving"
        elif len(declining) > len(improving):
            overall = "declining"
        else:
            overall = "stable"

        return {
            "overall_trend": overall,
            "improving_agents": improving,
            "declining_agents": declining,
        }
