"""Collaborative success criteria builder (Phase 5)."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SuccessCriteria:
    """AI-proposed and human-authenticated success criteria.

    Attributes:
        task: Original task description
        criteria: List of success criteria
        questions_asked: Questions asked during criteria building
        human_responses: Human responses to questions
        confidence: AI confidence in criteria (0-1)
        metadata: Additional metadata
    """

    task: str
    criteria: list[str] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    human_responses: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "criteria": self.criteria,
            "questions_asked": self.questions_asked,
            "human_responses": self.human_responses,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class CriteriaBuilder:
    """Interactive criteria building with AI-human collaboration.

    This class implements a multi-turn interview process where the AI proposes
    success criteria, asks clarifying questions, and refines criteria based on
    human feedback.

    Note: This is a Phase 5 feature. Basic structure is provided but full
    implementation will be added in Phase 5.

    Example:
        ```python
        builder = CriteriaBuilder(executor)
        criteria = await builder.build_criteria(
            task="Build a login page",
            context={"framework": "React"}
        )
        ```
    """

    def __init__(
        self,
        executor: Any,
        max_questions: int = 5,
        question_callback: Callable[[str], str] | None = None,
    ):
        """Initialize criteria builder.

        Args:
            executor: LLM executor for generating questions and criteria
            max_questions: Maximum number of clarifying questions to ask
            question_callback: Optional callback for interactive Q&A (for CLI)
        """
        self.executor = executor
        self.max_questions = max_questions
        self.question_callback = question_callback

    async def build_criteria(
        self, task: str, context: dict[str, Any] | None = None
    ) -> SuccessCriteria:
        """Build success criteria interactively.

        Args:
            task: Task description
            context: Additional context (optional)

        Returns:
            SuccessCriteria with AI-proposed criteria
        """
        logger.info("Building success criteria", task=task)

        context = context or {}
        questions_asked = []
        human_responses = []

        # Step 1: Propose initial criteria
        logger.debug("Proposing initial criteria")
        initial_criteria = await self._propose_initial_criteria(task, context)

        # Step 2: Ask clarifying questions (up to max_questions)
        logger.debug("Generating clarifying questions")
        questions = await self._generate_questions(task, context, initial_criteria)

        # Limit to max_questions
        questions = questions[: self.max_questions]

        # Step 3: Collect responses
        for i, question in enumerate(questions, 1):
            logger.debug(f"Asking question {i}/{len(questions)}", question=question)
            questions_asked.append(question)

            # Get response (interactive if callback provided)
            if self.question_callback:
                response = self.question_callback(question)
            else:
                # Non-interactive mode: skip questions
                response = "No response provided"

            human_responses.append(response)

        # Step 4: Refine criteria based on responses
        logger.debug("Refining criteria based on responses")
        final_criteria = await self._refine_criteria(
            task, context, initial_criteria, questions_asked, human_responses
        )

        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(
            len(questions_asked),
            len([r for r in human_responses if r and r != "No response provided"]),
        )

        logger.info(
            "Criteria building complete",
            criteria_count=len(final_criteria),
            questions_asked=len(questions_asked),
            confidence=confidence,
        )

        return SuccessCriteria(
            task=task,
            criteria=final_criteria,
            questions_asked=questions_asked,
            human_responses=human_responses,
            confidence=confidence,
            metadata={
                "initial_criteria_count": len(initial_criteria),
                "questions_count": len(questions_asked),
                "responses_provided": len(
                    [r for r in human_responses if r and r != "No response provided"]
                ),
            },
        )

    async def _propose_initial_criteria(
        self, task: str, context: dict[str, Any]
    ) -> list[str]:
        """Propose initial success criteria based on task.

        Args:
            task: Task description
            context: Additional context

        Returns:
            List of initial criteria
        """
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())

        prompt = f"""You are an expert software architect proposing success criteria for a task.

## Task
{task}

## Context
{context_str if context_str else "None provided"}

## Your Task
Propose 3-5 clear, measurable success criteria for this task.

## Guidelines
- Be specific and measurable
- Focus on outcomes, not implementation details
- Include both functional and non-functional criteria
- Consider edge cases and error handling

## Response Format
Provide criteria as a JSON array:

```json
{{
  "criteria": [
    "Criterion 1 (specific and measurable)",
    "Criterion 2 (specific and measurable)",
    "Criterion 3 (specific and measurable)"
  ]
}}
```"""

        try:
            response = await self.executor.execute(prompt)

            # Parse response (handle both dict and string)
            if isinstance(response, dict):
                result_text = response.get("content", "")
            else:
                result_text = response

            # Extract JSON
            json_text = self._extract_json(result_text)
            data = json.loads(json_text)

            return data.get("criteria", [])

        except Exception as e:
            logger.error(
                "Failed to propose initial criteria", error=str(e), exc_info=True
            )
            # Fallback
            return [
                "Implementation matches task requirements",
                "No errors or exceptions occur",
                "All edge cases are handled",
            ]

    async def _generate_questions(
        self, task: str, context: dict[str, Any], initial_criteria: list[str]
    ) -> list[str]:
        """Generate clarifying questions.

        Args:
            task: Task description
            context: Additional context
            initial_criteria: Initial proposed criteria

        Returns:
            List of clarifying questions
        """
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        criteria_str = "\n".join(f"{i}. {c}" for i, c in enumerate(initial_criteria, 1))

        prompt = f"""You are refining success criteria through clarifying questions.

## Task
{task}

## Context
{context_str if context_str else "None provided"}

## Initial Criteria
{criteria_str}

## Your Task
Generate {self.max_questions} clarifying questions to refine these criteria.

## Guidelines
- Ask about ambiguous requirements
- Clarify edge cases and error scenarios
- Understand user preferences (UX, performance, etc.)
- Prioritize questions that most impact criteria

## Response Format
Provide questions as a JSON array:

```json
{{
  "questions": [
    "Question 1 (clear and specific)",
    "Question 2 (clear and specific)",
    "Question 3 (clear and specific)"
  ]
}}
```"""

        try:
            response = await self.executor.execute(prompt)

            # Parse response
            if isinstance(response, dict):
                result_text = response.get("content", "")
            else:
                result_text = response

            # Extract JSON
            json_text = self._extract_json(result_text)
            data = json.loads(json_text)

            return data.get("questions", [])

        except Exception as e:
            logger.error("Failed to generate questions", error=str(e), exc_info=True)
            # Fallback
            return [
                "What should happen in error scenarios?",
                "Are there any performance requirements?",
                "What user experience expectations should be met?",
            ]

    async def _refine_criteria(
        self,
        task: str,
        context: dict[str, Any],
        initial_criteria: list[str],
        questions: list[str],
        responses: list[str],
    ) -> list[str]:
        """Refine criteria based on Q&A responses.

        Args:
            task: Task description
            context: Additional context
            initial_criteria: Initial criteria
            questions: Questions asked
            responses: Human responses

        Returns:
            Refined criteria
        """
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        criteria_str = "\n".join(f"{i}. {c}" for i, c in enumerate(initial_criteria, 1))

        # Format Q&A
        qa_str = ""
        for q, a in zip(questions, responses, strict=False):
            qa_str += f"\nQ: {q}\nA: {a}\n"

        prompt = f"""You are refining success criteria based on clarifying Q&A.

## Task
{task}

## Context
{context_str if context_str else "None provided"}

## Initial Criteria
{criteria_str}

## Q&A Session
{qa_str}

## Your Task
Refine the success criteria based on the Q&A responses.

## Guidelines
- Incorporate insights from responses
- Make criteria more specific based on answers
- Add new criteria if responses reveal new requirements
- Remove or merge redundant criteria
- Keep 3-7 criteria total (not too many, not too few)

## Response Format
Provide refined criteria as a JSON array:

```json
{{
  "criteria": [
    "Refined criterion 1 (incorporating Q&A insights)",
    "Refined criterion 2 (incorporating Q&A insights)",
    "Refined criterion 3 (incorporating Q&A insights)"
  ]
}}
```"""

        try:
            response = await self.executor.execute(prompt)

            # Parse response
            if isinstance(response, dict):
                result_text = response.get("content", "")
            else:
                result_text = response

            # Extract JSON
            json_text = self._extract_json(result_text)
            data = json.loads(json_text)

            return data.get("criteria", initial_criteria)

        except Exception as e:
            logger.error("Failed to refine criteria", error=str(e), exc_info=True)
            # Fallback to initial criteria
            return initial_criteria

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text (handles code blocks).

        Args:
            text: Text potentially containing JSON

        Returns:
            Extracted JSON string
        """
        # Try to extract from code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        else:
            # Return as-is and hope it's valid JSON
            return text.strip()

    def _calculate_confidence(
        self, questions_asked: int, responses_provided: int
    ) -> float:
        """Calculate confidence in criteria.

        Args:
            questions_asked: Number of questions asked
            responses_provided: Number of responses provided

        Returns:
            Confidence score (0.0-1.0)
        """
        if questions_asked == 0:
            # No questions asked, low confidence
            return 0.5

        # Base confidence on response rate
        response_rate = responses_provided / questions_asked

        # Full responses = high confidence
        if response_rate >= 0.8:
            return 0.9
        elif response_rate >= 0.6:
            return 0.8
        elif response_rate >= 0.4:
            return 0.7
        elif response_rate >= 0.2:
            return 0.6
        else:
            return 0.5
