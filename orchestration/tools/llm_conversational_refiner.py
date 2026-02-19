"""
LLM-Powered Conversational Refiner

This module implements intent refinement using LLM for intelligent understanding,
combined with structured outputs for reliability.

Design Philosophy:
- LLM for UNDERSTANDING (nuance, context, intent)
- Structured prompts for CONSISTENCY (JSON output, defined schema)
- Rules for SPEED (simple decisions like acceptance detection)
- Caching for EFFICIENCY (don't re-analyze identical inputs)

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM CONVERSATIONAL REFINER                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   User Input                                                             │
│       │                                                                  │
│       ▼                                                                  │
│   ┌─────────────────┐     ┌─────────────────────────────────────────┐   │
│   │ Quick Rules     │────▶│ Is this acceptance? Refinement request? │   │
│   │ (No LLM needed) │     │ Simple pattern match - FAST             │   │
│   └─────────────────┘     └─────────────────────────────────────────┘   │
│       │ No match                                                         │
│       ▼                                                                  │
│   ┌─────────────────┐     ┌─────────────────────────────────────────┐   │
│   │ LLM Analysis    │────▶│ Extract: entities, goals, constraints   │   │
│   │ (Structured)    │     │ Classify: task type, domain, readiness  │   │
│   └─────────────────┘     │ Generate: clarifying questions          │   │
│       │                   └─────────────────────────────────────────┘   │
│       ▼                                                                  │
│   ┌─────────────────┐     ┌─────────────────────────────────────────┐   │
│   │ Response        │────▶│ Natural language + inline cards/draft   │   │
│   │ Generation      │     │ Conversational, not robotic             │   │
│   └─────────────────┘     └─────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
"""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class LLMAnalysisResult:
    """Structured result from LLM analysis."""

    # Classification
    task_type: str = "creation"
    domain: str = "general"
    complexity: str = "moderate"
    confidence: float = 0.5

    # Extracted specifics
    entities: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    timeframes: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)

    # Readiness assessment
    readiness_score: float = 0.0
    missing_info: list[str] = field(default_factory=list)
    suggested_questions: list[dict] = field(default_factory=list)

    # Understanding summary
    understanding_summary: str = ""
    draft_approach: list[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Accumulated context from conversation."""

    all_user_inputs: list[str] = field(default_factory=list)
    all_analyses: list[LLMAnalysisResult] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)

    def get_full_context(self) -> str:
        """Get combined context as text."""
        return " ".join(self.all_user_inputs)


class SessionState(Enum):
    INITIAL = "initial"
    CLARIFYING = "clarifying"
    DRAFT_READY = "draft_ready"
    REFINING = "refining"
    COMPLETE = "complete"


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

ANALYSIS_SYSTEM_PROMPT = """You are an Intent Analysis AI. Your job is to deeply understand what the user wants and extract structured information.

Given a user's request (which may be vague or detailed), analyze it and return a JSON object with this exact structure:

{
  "task_type": "analysis|creation|transformation|decision|research|automation",
  "domain": "technical|business|creative|research|personal|science|finance|health|legal|education|entertainment|fashion|entrepreneurship",
  "complexity": "simple|moderate|complex",
  "confidence": 0.0-1.0,

  "entities": ["specific things mentioned: companies, products, people, projects"],
  "technologies": ["tech stack, tools, platforms mentioned"],
  "metrics": ["numbers, KPIs, targets mentioned"],
  "timeframes": ["deadlines, durations, dates mentioned"],
  "stakeholders": ["who is involved or will use the output"],
  "constraints": ["limitations, budgets, restrictions mentioned"],
  "goals": ["what they want to achieve - be specific"],
  "pain_points": ["problems they're experiencing"],

  "readiness_score": 0.0-1.0,
  "missing_info": ["what information would help clarify the request"],
  "suggested_questions": [
    {
      "question": "natural language question",
      "dimension": "what this clarifies",
      "options": ["option1", "option2", "option3"],
      "priority": 1-3
    }
  ],

  "understanding_summary": "One sentence summary of what you understood",
  "draft_approach": ["Step 1", "Step 2", "Step 3"]
}

IMPORTANT RULES:
1. Extract SPECIFIC details - don't generalize. If they say "B2B SaaS", capture "B2B SaaS" not just "business"
2. readiness_score: 0.8+ means we have enough to proceed, <0.8 means we need clarification
3. suggested_questions: Only ask what's truly needed. Max 2-3 questions. Make them conversational.
4. Be generous with readiness_score if the core intent is clear
5. ALWAYS return valid JSON"""


RESPONSE_GENERATION_PROMPT = """You are a helpful AI assistant having a conversation. Based on the analysis, generate a natural response.

Your response should:
1. Acknowledge what you understood (briefly)
2. If readiness < 0.8: Ask 1-2 clarifying questions naturally
3. If readiness >= 0.8: Present a draft preview of your approach

TONE:
- Conversational, not robotic
- Confident but not presumptuous
- Helpful and efficient

FORMAT (for clarifying):
"I can help with [brief understanding]. To make sure I get this right:
• [Question 1]?
• [Question 2]?

Or just tell me more!"

FORMAT (for draft ready):
"Got it! Here's what I'm thinking:

**Summary:** [one line]

**My approach:**
1. [Step]
2. [Step]
3. [Step]

Ready to proceed, or want to adjust anything?"

Return ONLY the response text, no JSON."""


PROMPT_GENERATION_PROMPT = """You are an expert prompt engineer. Given the user's request and extracted context, generate an optimized system prompt.

The prompt should:
1. Set a clear role appropriate to the domain
2. Include ALL specific details from the user's request (don't lose any context!)
3. Define clear success criteria
4. Include appropriate guardrails
5. Be actionable and specific

User's original request: {user_input}

Extracted context:
- Task type: {task_type}
- Domain: {domain}
- Entities: {entities}
- Goals: {goals}
- Constraints: {constraints}
- Pain points: {pain_points}
- Stakeholders: {stakeholders}

Generate a comprehensive system prompt that preserves ALL the specific details."""


# =============================================================================
# LLM CONVERSATIONAL REFINER
# =============================================================================


class LLMConversationalRefiner:
    """
    LLM-powered conversational intent refiner.

    Uses LLM for intelligent understanding while maintaining
    structured outputs for reliability.
    """

    def __init__(
        self,
        llm_executor: Callable[[str, str], Awaitable[str]],
        readiness_threshold: float = 0.75,
        cache_enabled: bool = True,
    ):
        """
        Initialize the refiner.

        Args:
            llm_executor: Async function that takes (system_prompt, user_message)
                         and returns the LLM response string.
                         Example: async def execute(system, user) -> str
            readiness_threshold: Score above which we show draft (default 0.75)
            cache_enabled: Whether to cache LLM analysis results
        """
        self.llm_executor = llm_executor
        self.readiness_threshold = readiness_threshold
        self.cache_enabled = cache_enabled
        self._cache: dict[str, LLMAnalysisResult] = {}

        # Sessions storage
        self.sessions: dict[str, dict] = {}

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def start_session(self) -> str:
        """Start a new refinement session."""
        import uuid

        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = {
            "state": SessionState.INITIAL,
            "context": ConversationContext(),
            "turns": [],
            "final_prompt": None,
        }
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    # =========================================================================
    # MAIN PROCESSING
    # =========================================================================

    async def process_input(
        self,
        session_id: str,
        user_input: str,
    ) -> dict[str, Any]:
        """
        Process user input and return response.

        This is the main entry point. It:
        1. Checks for quick patterns (acceptance, refinement)
        2. If needed, calls LLM for deep analysis
        3. Generates appropriate response

        Args:
            session_id: Session identifier
            user_input: User's message

        Returns:
            Dict with response, cards, draft, state
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        input_lower = user_input.lower().strip()

        # --- QUICK PATTERN MATCHING (No LLM needed) ---

        # Check for acceptance
        if session["state"] == SessionState.DRAFT_READY:
            if self._is_acceptance(input_lower):
                return await self._handle_acceptance(session, user_input)

            if self._is_refinement_request(input_lower):
                return await self._handle_refinement(session, user_input)

        # --- LLM ANALYSIS ---

        # Add to context
        session["context"].all_user_inputs.append(user_input)

        # Get full context for analysis
        full_context = session["context"].get_full_context()

        # Analyze with LLM
        analysis = await self._analyze_with_llm(full_context)
        session["context"].all_analyses.append(analysis)

        # Decide response based on readiness
        if analysis.readiness_score >= self.readiness_threshold:
            return await self._generate_draft_response(session, analysis, user_input)
        else:
            return await self._generate_clarification_response(
                session, analysis, user_input
            )

    # =========================================================================
    # LLM CALLS
    # =========================================================================

    async def _analyze_with_llm(self, user_input: str) -> LLMAnalysisResult:
        """Call LLM to analyze user input."""

        # Check cache
        if self.cache_enabled:
            cache_key = hashlib.md5(user_input.encode()).hexdigest()
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Call LLM
        response = await self.llm_executor(
            ANALYSIS_SYSTEM_PROMPT, f"Analyze this request:\n\n{user_input}"
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            result = LLMAnalysisResult(
                task_type=data.get("task_type", "creation"),
                domain=data.get("domain", "general"),
                complexity=data.get("complexity", "moderate"),
                confidence=data.get("confidence", 0.5),
                entities=data.get("entities", []),
                technologies=data.get("technologies", []),
                metrics=data.get("metrics", []),
                timeframes=data.get("timeframes", []),
                stakeholders=data.get("stakeholders", []),
                constraints=data.get("constraints", []),
                goals=data.get("goals", []),
                pain_points=data.get("pain_points", []),
                readiness_score=data.get("readiness_score", 0.5),
                missing_info=data.get("missing_info", []),
                suggested_questions=data.get("suggested_questions", []),
                understanding_summary=data.get("understanding_summary", ""),
                draft_approach=data.get("draft_approach", []),
            )

            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = result

            return result

        except (json.JSONDecodeError, KeyError):
            # Fallback if LLM doesn't return valid JSON
            return LLMAnalysisResult(
                understanding_summary="I understood your request but need to analyze it further.",
                readiness_score=0.5,
                suggested_questions=[
                    {
                        "question": "Could you tell me more about what you're trying to achieve?",
                        "dimension": "goal",
                        "options": [],
                        "priority": 1,
                    }
                ],
            )

    async def _generate_natural_response(
        self,
        analysis: LLMAnalysisResult,
        is_draft_ready: bool,
    ) -> str:
        """Generate natural language response using LLM."""

        context = f"""
Analysis result:
- Understanding: {analysis.understanding_summary}
- Readiness: {analysis.readiness_score:.0%}
- Task: {analysis.task_type} in {analysis.domain}
- Goals: {", ".join(analysis.goals[:3]) if analysis.goals else "not specified"}
- Constraints: {", ".join(analysis.constraints[:2]) if analysis.constraints else "none mentioned"}
- Suggested questions: {json.dumps(analysis.suggested_questions[:2])}
- Draft approach: {json.dumps(analysis.draft_approach)}

Is draft ready: {is_draft_ready}
"""

        response = await self.llm_executor(RESPONSE_GENERATION_PROMPT, context)

        return response.strip()

    async def _generate_final_prompt(self, session: dict) -> str:
        """Generate the final optimized prompt."""

        # Get latest analysis
        analyses = session["context"].all_analyses
        if not analyses:
            return "Please help the user with their request."

        latest = analyses[-1]
        full_input = session["context"].get_full_context()

        prompt_request = PROMPT_GENERATION_PROMPT.format(
            user_input=full_input,
            task_type=latest.task_type,
            domain=latest.domain,
            entities=", ".join(latest.entities) if latest.entities else "not specified",
            goals=", ".join(latest.goals) if latest.goals else "not specified",
            constraints=", ".join(latest.constraints) if latest.constraints else "none",
            pain_points=", ".join(latest.pain_points) if latest.pain_points else "none",
            stakeholders=(
                ", ".join(latest.stakeholders)
                if latest.stakeholders
                else "not specified"
            ),
        )

        final_prompt = await self.llm_executor(
            "You are an expert prompt engineer. Generate a comprehensive, specific system prompt.",
            prompt_request,
        )

        return final_prompt.strip()

    # =========================================================================
    # RESPONSE HANDLERS
    # =========================================================================

    async def _generate_clarification_response(
        self,
        session: dict,
        analysis: LLMAnalysisResult,
        user_input: str,
    ) -> dict[str, Any]:
        """Generate response asking for clarification."""

        session["state"] = SessionState.CLARIFYING

        # Generate natural response
        response_text = await self._generate_natural_response(
            analysis, is_draft_ready=False
        )

        # Build cards from suggested questions
        cards = []
        for q in analysis.suggested_questions[:2]:
            cards.append(
                {
                    "question": q.get("question", ""),
                    "options": [
                        {"label": opt, "value": opt} for opt in q.get("options", [])
                    ],
                    "dimension": q.get("dimension", ""),
                    "allowFreeform": True,
                }
            )

        turn = {
            "user_input": user_input,
            "response": response_text,
            "cards": cards,
            "draft": None,
            "state": SessionState.CLARIFYING.value,
            "analysis": {
                "readiness": analysis.readiness_score,
                "understanding": analysis.understanding_summary,
            },
        }
        session["turns"].append(turn)

        return turn

    async def _generate_draft_response(
        self,
        session: dict,
        analysis: LLMAnalysisResult,
        user_input: str,
    ) -> dict[str, Any]:
        """Generate response with draft preview."""

        session["state"] = SessionState.DRAFT_READY

        # Generate natural response
        response_text = await self._generate_natural_response(
            analysis, is_draft_ready=True
        )

        # Build draft preview
        draft = {
            "summary": analysis.understanding_summary,
            "approach": analysis.draft_approach
            or [
                "Understand your needs",
                "Analyze the situation",
                "Provide recommendations",
            ],
            "outputType": f"{analysis.task_type.title()} in {analysis.domain}",
            "confidence": analysis.readiness_score,
            "canProceed": True,
        }

        turn = {
            "user_input": user_input,
            "response": response_text,
            "cards": [],
            "draft": draft,
            "state": SessionState.DRAFT_READY.value,
            "analysis": {
                "readiness": analysis.readiness_score,
                "understanding": analysis.understanding_summary,
                "entities": analysis.entities,
                "goals": analysis.goals,
            },
        }
        session["turns"].append(turn)

        return turn

    async def _handle_acceptance(
        self,
        session: dict,
        user_input: str,
    ) -> dict[str, Any]:
        """Handle user accepting the draft."""

        session["state"] = SessionState.COMPLETE

        # Generate final prompt
        final_prompt = await self._generate_final_prompt(session)
        session["final_prompt"] = final_prompt

        response_text = """Perfect! I've prepared your optimized prompt.

Your request has been refined into a comprehensive prompt that includes:
- Specific context from your request
- Clear task definition and approach
- Success criteria and guardrails

Ready to execute! Would you like to see the full prompt or proceed directly?"""

        turn = {
            "user_input": user_input,
            "response": response_text,
            "cards": [],
            "draft": None,
            "state": SessionState.COMPLETE.value,
            "final_prompt": final_prompt,
        }
        session["turns"].append(turn)

        return turn

    async def _handle_refinement(
        self,
        session: dict,
        user_input: str,
    ) -> dict[str, Any]:
        """Handle user requesting refinement."""

        session["state"] = SessionState.REFINING

        response_text = """No problem! What would you like to adjust?

You can:
- Add more context or requirements
- Change the focus or approach
- Specify constraints I should consider

Just tell me what to change."""

        turn = {
            "user_input": user_input,
            "response": response_text,
            "cards": [],
            "draft": None,
            "state": SessionState.REFINING.value,
        }
        session["turns"].append(turn)

        return turn

    # =========================================================================
    # QUICK PATTERN MATCHING (No LLM needed)
    # =========================================================================

    def _is_acceptance(self, input_lower: str) -> bool:
        """Quick check for acceptance - no LLM needed."""
        acceptance_patterns = [
            "yes",
            "yep",
            "yeah",
            "sure",
            "ok",
            "okay",
            "go ahead",
            "proceed",
            "do it",
            "looks good",
            "perfect",
            "great",
            "that works",
            "sounds good",
            "let's go",
            "approved",
            "continue",
            "execute",
            "run it",
            "make it so",
            "go for it",
        ]
        return any(p in input_lower for p in acceptance_patterns)

    def _is_refinement_request(self, input_lower: str) -> bool:
        """Quick check for refinement request - no LLM needed."""
        refinement_patterns = [
            "change",
            "modify",
            "adjust",
            "refine",
            "tweak",
            "actually",
            "wait",
            "hold on",
            "not quite",
            "almost",
            "can you",
            "could you",
            "what if",
            "instead",
            "more",
            "less",
            "different",
            "add",
            "remove",
            "focus",
        ]
        return any(p in input_lower for p in refinement_patterns)


# =============================================================================
# SYNC WRAPPER (for non-async code)
# =============================================================================


class SyncLLMConversationalRefiner:
    """Synchronous wrapper for LLMConversationalRefiner."""

    def __init__(self, llm_executor: Callable[[str, str], str], **kwargs):
        """
        Initialize with a synchronous LLM executor.

        Args:
            llm_executor: Sync function that takes (system_prompt, user_message)
                         and returns the LLM response string.
        """

        # Wrap sync executor in async
        async def async_executor(system: str, user: str) -> str:
            return llm_executor(system, user)

        self._async_refiner = LLMConversationalRefiner(
            llm_executor=async_executor, **kwargs
        )

    def start_session(self) -> str:
        return self._async_refiner.start_session()

    def process_input(self, session_id: str, user_input: str) -> dict[str, Any]:
        return asyncio.run(self._async_refiner.process_input(session_id, user_input))


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

EXAMPLE_USAGE = """
# Example with OpenAI
import openai

async def openai_executor(system_prompt: str, user_message: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

# Create refiner
refiner = LLMConversationalRefiner(llm_executor=openai_executor)

# Start session
session_id = refiner.start_session()

# Process user input
result = await refiner.process_input(session_id, "help me with marketing")
print(result["response"])
print(result["cards"])  # Clarification cards if needed

# User provides more context
result = await refiner.process_input(session_id, "B2B SaaS, need more leads")
print(result["response"])
print(result["draft"])  # Draft preview if ready

# User accepts
result = await refiner.process_input(session_id, "looks good, proceed")
print(result["final_prompt"])  # The optimized prompt!
"""
