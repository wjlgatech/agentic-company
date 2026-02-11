"""
Intent Refiner: Transform vague user input into well-defined prompts.

This module implements Progressive Intent Refinement (PIR):
1. PARSE - Classify intent and domain
2. PROBE - Ask smart clarification questions
3. MODEL - Build visual mental model
4. GENERATE - Create optimized system prompt

Based on research in:
- Requirements Engineering (Goal-Oriented RE)
- Task-Oriented Dialogue Systems
- Cognitive Load Theory
- Prompt Engineering Best Practices
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable, Any
from enum import Enum


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

class TaskType(Enum):
    """Primary task categories."""
    ANALYSIS = "analysis"           # Understanding something
    CREATION = "creation"           # Making something new
    TRANSFORMATION = "transformation"  # Changing something existing
    DECISION = "decision"           # Choosing between options
    RESEARCH = "research"           # Finding information
    AUTOMATION = "automation"       # Recurring process


class Complexity(Enum):
    """Task complexity levels."""
    ATOMIC = "atomic"               # Single step, clear outcome
    COMPOSITE = "composite"         # Multiple steps, single goal
    EXPLORATORY = "exploratory"     # Goal discovered during work


class Domain(Enum):
    """Knowledge domains."""
    TECHNICAL = "technical"         # Code, systems, data
    BUSINESS = "business"           # Strategy, operations, finance
    CREATIVE = "creative"           # Writing, design, content
    RESEARCH = "research"           # Academic, scientific
    PERSONAL = "personal"           # Life, productivity


@dataclass
class IntentClassification:
    """Classification of user intent."""
    task_type: TaskType
    complexity: Complexity
    domain: Domain
    confidence: float
    signals: list[str] = field(default_factory=list)


# =============================================================================
# ELICITATION FRAMEWORK
# =============================================================================

@dataclass
class ClarificationQuestion:
    """A question to clarify user intent."""
    question: str
    dimension: str          # What aspect this clarifies
    priority: int           # 1=must ask, 2=should ask, 3=nice to have
    options: list[str] = field(default_factory=list)  # Multiple choice options
    default: Optional[str] = None  # Assumed if not asked
    information_gain: float = 0.5  # How much this changes the output


@dataclass
class ElicitedContext:
    """Context gathered through elicitation."""
    goal: str = ""                  # What user ultimately wants
    success_criteria: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    audience: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    assumptions: dict[str, str] = field(default_factory=dict)
    uncertainties: list[str] = field(default_factory=list)


# =============================================================================
# MENTAL MODEL
# =============================================================================

@dataclass
class IntentModel:
    """Visual mental model of user intent."""

    # Core elements
    inputs: list[dict] = field(default_factory=list)
    process: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)

    # Metadata
    assumptions: list[dict] = field(default_factory=list)
    uncertainties: list[dict] = field(default_factory=list)
    success_criteria: list[dict] = field(default_factory=list)

    def to_ascii(self) -> str:
        """Render as ASCII diagram."""
        lines = []
        lines.append("┌" + "─" * 60 + "┐")
        lines.append("│" + " INTENT MODEL".center(60) + "│")
        lines.append("├" + "─" * 60 + "┤")

        # Inputs
        lines.append("│ INPUTS:".ljust(61) + "│")
        for inp in self.inputs:
            status = "✓" if inp.get("confirmed") else "○"
            lines.append(f"│   {status} {inp.get('name', '?')}: {inp.get('description', '')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ PROCESS:".ljust(61) + "│")
        for proc in self.process:
            lines.append(f"│   → {proc.get('action', '?')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ OUTPUTS:".ljust(61) + "│")
        for out in self.outputs:
            lines.append(f"│   ◆ {out.get('name', '?')}: {out.get('format', '')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ ASSUMPTIONS (inferred):".ljust(61) + "│")
        for assumption in self.assumptions:
            lines.append(f"│   ○ {assumption.get('key', '?')}: {assumption.get('value', '')}".ljust(61)[:61] + "│")

        if self.uncertainties:
            lines.append("│".ljust(61) + "│")
            lines.append("│ UNCERTAINTIES (need clarification):".ljust(61) + "│")
            for unc in self.uncertainties:
                lines.append(f"│   ? {unc.get('question', '?')}".ljust(61)[:61] + "│")

        lines.append("│".ljust(61) + "│")
        lines.append("│ SUCCESS CRITERIA:".ljust(61) + "│")
        for crit in self.success_criteria:
            lines.append(f"│   □ {crit.get('criterion', '?')}".ljust(61)[:61] + "│")

        lines.append("└" + "─" * 60 + "┘")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Render as Mermaid flowchart."""
        lines = ["flowchart LR"]

        # Inputs
        for i, inp in enumerate(self.inputs):
            lines.append(f"    I{i}[{inp.get('name', 'Input')}]")

        # Process
        for i, proc in enumerate(self.process):
            lines.append(f"    P{i}{{{proc.get('action', 'Process')}}}")

        # Outputs
        for i, out in enumerate(self.outputs):
            lines.append(f"    O{i}[/{out.get('name', 'Output')}/]")

        # Connections
        for i in range(len(self.inputs)):
            lines.append(f"    I{i} --> P0")
        for i in range(len(self.process) - 1):
            lines.append(f"    P{i} --> P{i+1}")
        if self.process:
            for i in range(len(self.outputs)):
                lines.append(f"    P{len(self.process)-1} --> O{i}")

        return "\n".join(lines)


# =============================================================================
# INTENT REFINER
# =============================================================================

class IntentRefiner:
    """
    Transform vague user input into well-defined prompts.

    Implements Progressive Intent Refinement (PIR):
    1. PARSE - Classify intent and domain
    2. PROBE - Ask smart clarification questions
    3. MODEL - Build visual mental model
    4. GENERATE - Create optimized system prompt

    Example:
        refiner = IntentRefiner()

        # User provides vague input
        user_input = "help me with my marketing"

        # Parse intent
        classification = refiner.parse(user_input)

        # Get clarification questions
        questions = refiner.get_questions(user_input, classification)

        # After user answers, build model
        model = refiner.build_model(user_input, answers)

        # Generate optimized prompt
        prompt = refiner.generate_prompt(model)
    """

    # Task type signal words
    TASK_SIGNALS = {
        TaskType.ANALYSIS: [
            "analyze", "understand", "explain", "why", "how does",
            "what causes", "investigate", "assess", "evaluate"
        ],
        TaskType.CREATION: [
            "create", "make", "build", "write", "design", "develop",
            "generate", "produce", "compose", "draft"
        ],
        TaskType.TRANSFORMATION: [
            "improve", "fix", "change", "modify", "update", "convert",
            "refactor", "optimize", "enhance", "revise"
        ],
        TaskType.DECISION: [
            "should i", "which", "choose", "decide", "compare",
            "versus", "better", "recommend", "advise"
        ],
        TaskType.RESEARCH: [
            "find", "search", "look up", "research", "discover",
            "learn about", "what is", "who is", "where"
        ],
        TaskType.AUTOMATION: [
            "automate", "every time", "whenever", "always",
            "recurring", "schedule", "repeat", "workflow"
        ],
    }

    # Domain signal words
    DOMAIN_SIGNALS = {
        Domain.TECHNICAL: [
            "code", "api", "database", "server", "bug", "deploy",
            "function", "class", "error", "debug", "test"
        ],
        Domain.BUSINESS: [
            "revenue", "customer", "market", "strategy", "sales",
            "growth", "profit", "competitor", "stakeholder"
        ],
        Domain.CREATIVE: [
            "story", "design", "content", "brand", "visual",
            "creative", "artistic", "style", "tone"
        ],
        Domain.RESEARCH: [
            "study", "paper", "literature", "hypothesis", "data",
            "experiment", "methodology", "findings", "citation"
        ],
        Domain.PERSONAL: [
            "my life", "personal", "habit", "goal", "productivity",
            "schedule", "organize", "planning"
        ],
    }

    # Elicitation question templates by dimension
    QUESTION_TEMPLATES = {
        "goal": [
            ClarificationQuestion(
                question="What decision or action will this enable?",
                dimension="goal",
                priority=1,
                information_gain=0.9,
            ),
            ClarificationQuestion(
                question="If this works perfectly, what changes for you?",
                dimension="goal",
                priority=1,
                information_gain=0.85,
            ),
        ],
        "success": [
            ClarificationQuestion(
                question="How will you know if the result is good enough?",
                dimension="success",
                priority=1,
                information_gain=0.8,
            ),
            ClarificationQuestion(
                question="What would make you say 'this is exactly what I needed'?",
                dimension="success",
                priority=2,
                information_gain=0.7,
            ),
        ],
        "failure": [
            ClarificationQuestion(
                question="What would make this result useless to you?",
                dimension="failure",
                priority=2,
                information_gain=0.75,
            ),
        ],
        "audience": [
            ClarificationQuestion(
                question="Who will see or use this output?",
                dimension="audience",
                priority=2,
                options=["Just me", "My team", "Executives", "Customers", "Public"],
                default="Just me",
                information_gain=0.6,
            ),
        ],
        "constraints": [
            ClarificationQuestion(
                question="Are there any constraints I should know about?",
                dimension="constraints",
                priority=3,
                options=["Time limit", "Budget", "Format requirements", "Compliance", "None"],
                information_gain=0.5,
            ),
        ],
        "examples": [
            ClarificationQuestion(
                question="Can you show me an example of what good looks like?",
                dimension="examples",
                priority=2,
                information_gain=0.8,
            ),
        ],
        "scope": [
            ClarificationQuestion(
                question="Should this be comprehensive or focused on key points?",
                dimension="scope",
                priority=2,
                options=["Quick overview", "Detailed analysis", "Comprehensive deep-dive"],
                default="Detailed analysis",
                information_gain=0.5,
            ),
        ],
    }

    def __init__(
        self,
        executor: Optional[Callable[[str], Awaitable[str]]] = None,
        min_questions: int = 2,
        max_questions: int = 5,
    ):
        """
        Initialize the Intent Refiner.

        Args:
            executor: Optional LLM executor for advanced parsing
            min_questions: Minimum clarification questions to ask
            max_questions: Maximum clarification questions to ask
        """
        self.executor = executor
        self.min_questions = min_questions
        self.max_questions = max_questions

    # =========================================================================
    # STAGE 1: PARSE
    # =========================================================================

    def parse(self, user_input: str) -> IntentClassification:
        """
        Classify user intent along multiple dimensions.

        Args:
            user_input: Raw user input

        Returns:
            IntentClassification with task type, complexity, and domain
        """
        input_lower = user_input.lower()

        # Detect task type
        task_type = TaskType.CREATION  # Default
        task_confidence = 0.3
        task_signals = []

        for ttype, signals in self.TASK_SIGNALS.items():
            matches = [s for s in signals if s in input_lower]
            if len(matches) > len(task_signals):
                task_type = ttype
                task_signals = matches
                task_confidence = min(0.5 + len(matches) * 0.15, 0.95)

        # Detect domain
        domain = Domain.BUSINESS  # Default
        domain_confidence = 0.3
        domain_signals = []

        for dom, signals in self.DOMAIN_SIGNALS.items():
            matches = [s for s in signals if s in input_lower]
            if len(matches) > len(domain_signals):
                domain = dom
                domain_signals = matches
                domain_confidence = min(0.5 + len(matches) * 0.15, 0.95)

        # Detect complexity
        complexity = Complexity.ATOMIC
        word_count = len(user_input.split())

        if word_count > 50 or "and then" in input_lower or "steps" in input_lower:
            complexity = Complexity.COMPOSITE
        if "explore" in input_lower or "figure out" in input_lower or "not sure" in input_lower:
            complexity = Complexity.EXPLORATORY

        # Overall confidence
        confidence = (task_confidence + domain_confidence) / 2

        return IntentClassification(
            task_type=task_type,
            complexity=complexity,
            domain=domain,
            confidence=confidence,
            signals=task_signals + domain_signals,
        )

    # =========================================================================
    # STAGE 2: PROBE
    # =========================================================================

    def get_questions(
        self,
        user_input: str,
        classification: IntentClassification,
    ) -> list[ClarificationQuestion]:
        """
        Generate smart clarification questions based on classification.

        Uses Minimum Viable Questions (MVQ) principle:
        - Only ask questions that significantly change the output
        - Prioritize based on information gain
        - Skip questions with good defaults

        Args:
            user_input: Original user input
            classification: Intent classification

        Returns:
            List of prioritized clarification questions
        """
        questions = []
        input_lower = user_input.lower()

        # Always ask about goal if vague
        if classification.confidence < 0.7:
            questions.extend(self.QUESTION_TEMPLATES["goal"])

        # Ask about success criteria for creation/analysis
        if classification.task_type in (TaskType.CREATION, TaskType.ANALYSIS):
            questions.extend(self.QUESTION_TEMPLATES["success"])

        # Ask about failure modes for high-stakes tasks
        if classification.domain in (Domain.BUSINESS, Domain.TECHNICAL):
            questions.extend(self.QUESTION_TEMPLATES["failure"])

        # Ask about audience unless it's clearly personal
        if classification.domain != Domain.PERSONAL:
            questions.extend(self.QUESTION_TEMPLATES["audience"])

        # Ask for examples for creative tasks
        if classification.task_type == TaskType.CREATION:
            questions.extend(self.QUESTION_TEMPLATES["examples"])

        # Ask about scope for research/analysis
        if classification.task_type in (TaskType.RESEARCH, TaskType.ANALYSIS):
            questions.extend(self.QUESTION_TEMPLATES["scope"])

        # Sort by information gain and priority
        questions.sort(key=lambda q: (-q.information_gain, q.priority))

        # Apply min/max limits
        return questions[:self.max_questions]

    def get_questions_interactive(
        self,
        user_input: str,
        classification: IntentClassification,
    ) -> list[dict]:
        """
        Get questions formatted for interactive UI.

        Returns:
            List of question dicts with UI metadata
        """
        questions = self.get_questions(user_input, classification)

        return [
            {
                "id": f"q{i}",
                "question": q.question,
                "dimension": q.dimension,
                "type": "multiple_choice" if q.options else "free_text",
                "options": q.options,
                "default": q.default,
                "required": q.priority == 1,
            }
            for i, q in enumerate(questions)
        ]

    # =========================================================================
    # STAGE 3: MODEL
    # =========================================================================

    def build_model(
        self,
        user_input: str,
        classification: IntentClassification,
        answers: Optional[dict] = None,
    ) -> IntentModel:
        """
        Build visual mental model from input and answers.

        Args:
            user_input: Original user input
            classification: Intent classification
            answers: Answers to clarification questions

        Returns:
            IntentModel with structured representation
        """
        answers = answers or {}

        # Extract inputs from user input
        inputs = []
        if "using" in user_input.lower() or "with" in user_input.lower():
            inputs.append({
                "name": "User-provided data",
                "description": "Data or context from user",
                "confirmed": False,
            })

        inputs.append({
            "name": "Task description",
            "description": user_input[:100] + "..." if len(user_input) > 100 else user_input,
            "confirmed": True,
        })

        # Determine process steps based on task type
        process = []
        if classification.task_type == TaskType.ANALYSIS:
            process = [
                {"action": "Understand context"},
                {"action": "Analyze data/situation"},
                {"action": "Identify patterns/insights"},
                {"action": "Synthesize findings"},
            ]
        elif classification.task_type == TaskType.CREATION:
            process = [
                {"action": "Understand requirements"},
                {"action": "Plan structure"},
                {"action": "Generate content"},
                {"action": "Refine and polish"},
            ]
        elif classification.task_type == TaskType.RESEARCH:
            process = [
                {"action": "Define search scope"},
                {"action": "Gather information"},
                {"action": "Evaluate sources"},
                {"action": "Summarize findings"},
            ]
        elif classification.task_type == TaskType.DECISION:
            process = [
                {"action": "Identify options"},
                {"action": "Define criteria"},
                {"action": "Evaluate trade-offs"},
                {"action": "Recommend decision"},
            ]
        else:
            process = [{"action": "Process request"}]

        # Determine outputs
        outputs = []
        if classification.task_type == TaskType.ANALYSIS:
            outputs.append({"name": "Analysis report", "format": "Structured findings"})
        elif classification.task_type == TaskType.CREATION:
            outputs.append({"name": "Created artifact", "format": "As specified"})
        elif classification.task_type == TaskType.RESEARCH:
            outputs.append({"name": "Research summary", "format": "Findings with sources"})
        elif classification.task_type == TaskType.DECISION:
            outputs.append({"name": "Recommendation", "format": "Decision with rationale"})
        else:
            outputs.append({"name": "Response", "format": "Text"})

        # Build assumptions
        assumptions = []
        assumptions.append({
            "key": "Task type",
            "value": classification.task_type.value,
        })
        assumptions.append({
            "key": "Domain",
            "value": classification.domain.value,
        })

        if "audience" not in answers:
            assumptions.append({
                "key": "Audience",
                "value": "Professional/knowledgeable",
            })

        if "scope" not in answers:
            assumptions.append({
                "key": "Scope",
                "value": "Moderate depth",
            })

        # Identify uncertainties
        uncertainties = []
        if classification.confidence < 0.6:
            uncertainties.append({
                "question": "Is this the right interpretation of your goal?",
            })

        if classification.complexity == Complexity.EXPLORATORY:
            uncertainties.append({
                "question": "The goal may evolve as we work - is that okay?",
            })

        # Build success criteria from answers
        success_criteria = []
        if "success" in answers:
            success_criteria.append({"criterion": answers["success"]})
        else:
            success_criteria.append({"criterion": "Addresses the stated request"})
            success_criteria.append({"criterion": "Accurate and well-reasoned"})

        if "failure" in answers:
            success_criteria.append({"criterion": f"Avoids: {answers['failure']}"})

        return IntentModel(
            inputs=inputs,
            process=process,
            outputs=outputs,
            assumptions=assumptions,
            uncertainties=uncertainties,
            success_criteria=success_criteria,
        )

    # =========================================================================
    # STAGE 4: GENERATE
    # =========================================================================

    def generate_prompt(
        self,
        model: IntentModel,
        classification: IntentClassification,
        answers: Optional[dict] = None,
    ) -> str:
        """
        Generate optimized system prompt from mental model.

        Applies prompt engineering best practices:
        - Role setting
        - Context injection
        - Task specification
        - Output format
        - Guardrails

        Args:
            model: Intent model
            classification: Intent classification
            answers: User answers to clarification questions

        Returns:
            Optimized system prompt
        """
        answers = answers or {}

        # Build role based on domain
        role_map = {
            Domain.TECHNICAL: "expert software engineer and technical architect",
            Domain.BUSINESS: "senior business strategist and analyst",
            Domain.CREATIVE: "experienced creative professional and writer",
            Domain.RESEARCH: "thorough researcher and academic analyst",
            Domain.PERSONAL: "helpful personal assistant and productivity coach",
        }
        role = role_map.get(classification.domain, "helpful assistant")

        # Build task verb based on task type
        task_verbs = {
            TaskType.ANALYSIS: "analyze and provide insights on",
            TaskType.CREATION: "create and deliver",
            TaskType.TRANSFORMATION: "improve and refine",
            TaskType.DECISION: "evaluate options and recommend",
            TaskType.RESEARCH: "research and summarize",
            TaskType.AUTOMATION: "design a repeatable process for",
        }
        task_verb = task_verbs.get(classification.task_type, "help with")

        # Build audience context
        audience = answers.get("audience", "a knowledgeable professional")

        # Build success criteria
        criteria_text = "\n".join(
            f"- {c['criterion']}" for c in model.success_criteria
        )

        # Build the prompt
        prompt_parts = []

        # Role
        prompt_parts.append(f"You are a {role}.")
        prompt_parts.append("")

        # Context
        if model.assumptions:
            context_items = [f"{a['key']}: {a['value']}" for a in model.assumptions]
            prompt_parts.append("## Context")
            prompt_parts.append("\n".join(f"- {item}" for item in context_items))
            prompt_parts.append("")

        # Task
        prompt_parts.append("## Task")
        prompt_parts.append(f"Your task is to {task_verb} what the user requests.")
        prompt_parts.append(f"The output is for {audience}.")
        prompt_parts.append("")

        # Process
        prompt_parts.append("## Approach")
        for proc in model.process:
            prompt_parts.append(f"1. {proc['action']}")
        prompt_parts.append("")

        # Output
        prompt_parts.append("## Output Requirements")
        for out in model.outputs:
            prompt_parts.append(f"- Provide: {out['name']} ({out['format']})")
        prompt_parts.append("")

        # Success criteria
        prompt_parts.append("## Success Criteria")
        prompt_parts.append(criteria_text)
        prompt_parts.append("")

        # Guardrails
        prompt_parts.append("## Guardrails")
        prompt_parts.append("- Be accurate and factual")
        prompt_parts.append("- Acknowledge uncertainty when appropriate")
        prompt_parts.append("- Ask for clarification if the request is ambiguous")

        if classification.domain == Domain.TECHNICAL:
            prompt_parts.append("- Provide working, tested solutions")
        if classification.domain == Domain.BUSINESS:
            prompt_parts.append("- Support claims with reasoning or data")
        if classification.domain == Domain.RESEARCH:
            prompt_parts.append("- Cite sources when possible")

        return "\n".join(prompt_parts)

    # =========================================================================
    # CONVENIENCE: FULL PIPELINE
    # =========================================================================

    def refine(
        self,
        user_input: str,
        answers: Optional[dict] = None,
    ) -> dict:
        """
        Run full refinement pipeline.

        Args:
            user_input: Raw user input
            answers: Optional answers to clarification questions

        Returns:
            Dict with classification, model, prompt, and questions
        """
        # Parse
        classification = self.parse(user_input)

        # Get questions (if no answers provided)
        questions = []
        if answers is None:
            questions = self.get_questions_interactive(user_input, classification)

        # Build model
        model = self.build_model(user_input, classification, answers)

        # Generate prompt
        prompt = self.generate_prompt(model, classification, answers)

        return {
            "original_input": user_input,
            "classification": {
                "task_type": classification.task_type.value,
                "complexity": classification.complexity.value,
                "domain": classification.domain.value,
                "confidence": classification.confidence,
                "signals": classification.signals,
            },
            "questions": questions,
            "model": {
                "ascii": model.to_ascii(),
                "mermaid": model.to_mermaid(),
            },
            "prompt": prompt,
        }

    def paraphrase(
        self,
        user_input: str,
        classification: IntentClassification,
        model: IntentModel,
    ) -> str:
        """
        Generate paraphrase for user confirmation.

        Highlights:
        - What was understood
        - What was assumed
        - What is uncertain

        Args:
            user_input: Original input
            classification: Intent classification
            model: Built intent model

        Returns:
            Paraphrase with assumptions highlighted
        """
        parts = []

        parts.append("**Here's what I understood:**")
        parts.append("")
        parts.append(f"You want me to **{classification.task_type.value}** something in the **{classification.domain.value}** domain.")
        parts.append("")

        parts.append("**Process:**")
        for proc in model.process:
            parts.append(f"  → {proc['action']}")
        parts.append("")

        parts.append("**Expected output:**")
        for out in model.outputs:
            parts.append(f"  • {out['name']} ({out['format']})")
        parts.append("")

        if model.assumptions:
            parts.append("**I assumed:**")
            for assumption in model.assumptions:
                parts.append(f"  ○ {assumption['key']}: {assumption['value']}")
            parts.append("")

        if model.uncertainties:
            parts.append("**I'm uncertain about:**")
            for unc in model.uncertainties:
                parts.append(f"  ? {unc['question']}")
            parts.append("")

        parts.append("**Is this correct?** If not, please clarify what I should change.")

        return "\n".join(parts)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def refine_intent(user_input: str, answers: Optional[dict] = None) -> dict:
    """Quick function to refine user intent."""
    refiner = IntentRefiner()
    return refiner.refine(user_input, answers)


def get_clarification_questions(user_input: str) -> list[dict]:
    """Get clarification questions for user input."""
    refiner = IntentRefiner()
    classification = refiner.parse(user_input)
    return refiner.get_questions_interactive(user_input, classification)


def generate_system_prompt(user_input: str, answers: Optional[dict] = None) -> str:
    """Generate optimized system prompt from user input."""
    refiner = IntentRefiner()
    result = refiner.refine(user_input, answers)
    return result["prompt"]
