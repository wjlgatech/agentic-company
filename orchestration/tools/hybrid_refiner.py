"""
Hybrid Intent Refiner: Rules for speed + LLM for quality.

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│                         HYBRID REFINER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   User Input                                                             │
│       │                                                                  │
│       ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ RULES: Quick Pattern Detection (FREE, <10ms)                     │   │
│   │   - Is this acceptance? ("yes", "proceed")                       │   │
│   │   - Is this refinement? ("change", "actually")                   │   │
│   │   - Basic keyword extraction                                     │   │
│   └──────────────────────────┬──────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ LLM #1: Deep Analysis (~1s)                                      │   │
│   │   - Understand nuance and context                                │   │
│   │   - Extract entities, goals, constraints                         │   │
│   │   - Assess readiness (do we have enough?)                        │   │
│   │   - Generate clarifying questions if needed                      │   │
│   │   OUTPUT: Structured JSON                                        │   │
│   └──────────────────────────┬──────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ LLM #2: Generate Final Prompt (~1s)                              │   │
│   │   - Create natural, comprehensive prompt                         │   │
│   │   - Preserve ALL specific details                                │   │
│   │   - Tailored role, approach, guardrails                          │   │
│   │   OUTPUT: High-quality system prompt                             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Key Insight: LLM generates the FINAL PROMPT, not templates!
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
class AnalysisResult:
    """Structured analysis from LLM."""

    # Understanding
    summary: str = ""
    task_type: str = "general"
    domain: str = "general"

    # Extracted details
    entities: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)

    # Readiness
    readiness_score: float = 0.0
    missing_info: list[str] = field(default_factory=list)
    clarifying_questions: list[dict] = field(default_factory=list)

    # Approach
    suggested_approach: list[str] = field(default_factory=list)


class SessionState(Enum):
    INITIAL = "initial"
    CLARIFYING = "clarifying"
    READY = "ready"
    COMPLETE = "complete"


@dataclass
class Session:
    """Conversation session."""

    session_id: str
    state: SessionState = SessionState.INITIAL
    user_inputs: list[str] = field(default_factory=list)
    analysis: AnalysisResult | None = None
    final_prompt: str = ""


# =============================================================================
# SYSTEM PROMPTS FOR LLM
# =============================================================================

ANALYSIS_PROMPT = """You are an expert at understanding user intent. Analyze the user's request and extract structured information.

Your job is to:
1. Deeply understand what they REALLY want (not just what they said)
2. Extract ALL specific details mentioned
3. Assess if you have enough information to help them well
4. If not, generate 1-2 natural clarifying questions

Return a JSON object with this EXACT structure:
{
    "summary": "One clear sentence describing what they want",
    "task_type": "analysis|creation|research|decision|transformation|automation",
    "domain": "business|technical|creative|science|finance|health|legal|education|personal",

    "entities": ["specific things mentioned: companies, products, people, projects"],
    "goals": ["what they want to achieve - be specific and preserve their words"],
    "constraints": ["limitations, budgets, restrictions, deadlines mentioned"],
    "pain_points": ["problems or frustrations they expressed"],
    "stakeholders": ["who is involved or will use the output"],
    "technologies": ["tech, tools, platforms mentioned"],
    "metrics": ["numbers, KPIs, targets mentioned"],

    "readiness_score": 0.0 to 1.0,
    "missing_info": ["what key information is unclear or missing"],
    "clarifying_questions": [
        {
            "question": "A natural, conversational question",
            "why": "What this clarifies",
            "options": ["Option 1", "Option 2", "Option 3"]
        }
    ],

    "suggested_approach": ["Step 1: ...", "Step 2: ...", "Step 3: ..."]
}

IMPORTANT RULES:
1. PRESERVE THEIR EXACT WORDS for entities, goals, pain points - don't paraphrase away specifics
2. readiness_score >= 0.75 means you have enough to proceed well
3. Only ask clarifying questions if truly needed (max 2)
4. Make questions conversational, not interrogative
5. Always return valid JSON"""


PROMPT_GENERATION_PROMPT = """You are a world-class prompt engineer. Your task is to create an excellent system prompt based on the user's request and extracted context.

USER'S ORIGINAL REQUEST:
{user_input}

EXTRACTED CONTEXT:
- Summary: {summary}
- Task Type: {task_type}
- Domain: {domain}
- Entities: {entities}
- Goals: {goals}
- Constraints: {constraints}
- Pain Points: {pain_points}
- Stakeholders: {stakeholders}
- Technologies: {technologies}
- Metrics: {metrics}
- Suggested Approach: {approach}

CREATE A SYSTEM PROMPT that:

1. **Sets the right role** - An expert persona appropriate for this domain and task

2. **Captures the full context** - Include ALL the specific details from their request
   Don't generalize "B2B SaaS startup" into just "business"

3. **Defines clear objectives** - What exactly should be accomplished

4. **Specifies the approach** - How to tackle this task step by step

5. **Sets success criteria** - How to know if the output is good

6. **Adds appropriate guardrails** - Domain-specific cautions (e.g., "not financial advice")

STYLE GUIDELINES:
- Write naturally, not mechanically
- Be specific, not generic
- Preserve the user's terminology and context
- Make it actionable
- Keep it focused (don't pad with unnecessary sections)

Write the system prompt now. Return ONLY the prompt text, no JSON or markdown wrapping."""


RESPONSE_GENERATION_PROMPT = """Generate a natural, conversational response based on the analysis.

ANALYSIS:
- Summary: {summary}
- Readiness: {readiness}%
- Missing info: {missing}
- Questions to ask: {questions}

IF READINESS < 75%:
Write a friendly response that:
1. Briefly acknowledges what you understood
2. Asks 1-2 clarifying questions naturally (not like a form)
3. Offers them the option to just tell you more

IF READINESS >= 75%:
Write a response that:
1. Confirms your understanding
2. Shows your planned approach (brief bullets)
3. Asks if they want to proceed or adjust

Keep it conversational and helpful. Don't be robotic.
Return ONLY the response text."""


# =============================================================================
# HYBRID REFINER
# =============================================================================


class HybridRefiner:
    """
    Hybrid refiner using rules for speed and LLM for quality.

    Rules handle:
    - Quick pattern detection (acceptance, refinement)
    - Caching

    LLM handles:
    - Deep understanding and analysis
    - Generating the final prompt (NOT templates!)
    - Natural response generation
    """

    def __init__(
        self,
        llm_call: Callable[[str, str], Awaitable[str]],
        readiness_threshold: float = 0.75,
    ):
        """
        Initialize the hybrid refiner.

        Args:
            llm_call: Async function(system_prompt, user_message) -> response
            readiness_threshold: Score above which we can proceed
        """
        self.llm_call = llm_call
        self.readiness_threshold = readiness_threshold
        self.sessions: dict[str, Session] = {}
        self._cache: dict[str, AnalysisResult] = {}

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def create_session(self) -> str:
        """Create a new session."""
        import uuid

        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = Session(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    async def process(
        self,
        session_id: str,
        user_input: str,
    ) -> dict[str, Any]:
        """
        Process user input and return response.

        This orchestrates the hybrid approach:
        1. Rules for quick decisions
        2. LLM for analysis
        3. LLM for prompt/response generation
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        input_lower = user_input.lower().strip()

        # --- RULE-BASED: Quick pattern detection ---

        # Check for acceptance
        if session.state == SessionState.READY:
            if self._is_acceptance(input_lower):
                return await self._finalize(session)

            if self._is_refinement(input_lower):
                session.state = SessionState.CLARIFYING
                return {
                    "response": "No problem! What would you like to change or add?",
                    "state": "clarifying",
                    "ready": False,
                }

        # --- LLM: Deep analysis ---

        # Add to conversation history
        session.user_inputs.append(user_input)
        full_context = " ".join(session.user_inputs)

        # Analyze with LLM
        analysis = await self._analyze(full_context)
        session.analysis = analysis

        # --- LLM: Generate response ---

        if analysis.readiness_score >= self.readiness_threshold:
            session.state = SessionState.READY
            response = await self._generate_ready_response(analysis)
            return {
                "response": response,
                "state": "ready",
                "ready": True,
                "analysis": {
                    "summary": analysis.summary,
                    "readiness": analysis.readiness_score,
                    "approach": analysis.suggested_approach,
                },
            }
        else:
            session.state = SessionState.CLARIFYING
            response = await self._generate_clarifying_response(analysis)
            return {
                "response": response,
                "state": "clarifying",
                "ready": False,
                "questions": analysis.clarifying_questions,
            }

    async def _finalize(self, session: Session) -> dict[str, Any]:
        """Generate the final prompt using LLM."""

        session.state = SessionState.COMPLETE
        full_context = " ".join(session.user_inputs)
        analysis = session.analysis

        # LLM generates the final prompt - NOT a template!
        final_prompt = await self._generate_prompt(full_context, analysis)
        session.final_prompt = final_prompt

        return {
            "response": "Perfect! I've created your optimized prompt. Ready to execute!",
            "state": "complete",
            "ready": True,
            "final_prompt": final_prompt,
        }

    # =========================================================================
    # LLM CALLS
    # =========================================================================

    async def _analyze(self, user_input: str) -> AnalysisResult:
        """Use LLM to deeply analyze user input."""

        # Check cache
        cache_key = hashlib.md5(user_input.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Call LLM
        response = await self.llm_call(
            ANALYSIS_PROMPT, f"Analyze this request:\n\n{user_input}"
        )

        # Parse JSON
        try:
            # Handle markdown code blocks
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            result = AnalysisResult(
                summary=data.get("summary", ""),
                task_type=data.get("task_type", "general"),
                domain=data.get("domain", "general"),
                entities=data.get("entities", []),
                goals=data.get("goals", []),
                constraints=data.get("constraints", []),
                pain_points=data.get("pain_points", []),
                stakeholders=data.get("stakeholders", []),
                technologies=data.get("technologies", []),
                metrics=data.get("metrics", []),
                readiness_score=data.get("readiness_score", 0.5),
                missing_info=data.get("missing_info", []),
                clarifying_questions=data.get("clarifying_questions", []),
                suggested_approach=data.get("suggested_approach", []),
            )

            # Cache
            self._cache[cache_key] = result
            return result

        except (json.JSONDecodeError, KeyError):
            # Fallback
            return AnalysisResult(
                summary="I need to understand your request better.",
                readiness_score=0.3,
                clarifying_questions=[
                    {
                        "question": "Could you tell me more about what you're trying to accomplish?",
                        "why": "core goal",
                        "options": [],
                    }
                ],
            )

    async def _generate_prompt(
        self,
        user_input: str,
        analysis: AnalysisResult,
    ) -> str:
        """Use LLM to generate the final system prompt."""

        prompt_request = PROMPT_GENERATION_PROMPT.format(
            user_input=user_input,
            summary=analysis.summary,
            task_type=analysis.task_type,
            domain=analysis.domain,
            entities=", ".join(analysis.entities)
            if analysis.entities
            else "not specified",
            goals="; ".join(analysis.goals) if analysis.goals else "not specified",
            constraints="; ".join(analysis.constraints)
            if analysis.constraints
            else "none mentioned",
            pain_points="; ".join(analysis.pain_points)
            if analysis.pain_points
            else "none mentioned",
            stakeholders=", ".join(analysis.stakeholders)
            if analysis.stakeholders
            else "not specified",
            technologies=", ".join(analysis.technologies)
            if analysis.technologies
            else "none mentioned",
            metrics=", ".join(analysis.metrics)
            if analysis.metrics
            else "none mentioned",
            approach="\n".join(analysis.suggested_approach)
            if analysis.suggested_approach
            else "to be determined",
        )

        final_prompt = await self.llm_call(
            "You are a world-class prompt engineer. Generate an excellent, specific system prompt.",
            prompt_request,
        )

        return final_prompt.strip()

    async def _generate_clarifying_response(self, analysis: AnalysisResult) -> str:
        """Use LLM to generate a natural clarifying response."""

        response = await self.llm_call(
            RESPONSE_GENERATION_PROMPT.format(
                summary=analysis.summary,
                readiness=int(analysis.readiness_score * 100),
                missing=", ".join(analysis.missing_info)
                if analysis.missing_info
                else "none",
                questions=json.dumps(analysis.clarifying_questions),
            ),
            "Generate a clarifying response.",
        )

        return response.strip()

    async def _generate_ready_response(self, analysis: AnalysisResult) -> str:
        """Use LLM to generate a ready-to-proceed response."""

        response = await self.llm_call(
            RESPONSE_GENERATION_PROMPT.format(
                summary=analysis.summary,
                readiness=int(analysis.readiness_score * 100),
                missing="none",
                questions="[]",
            ),
            "Generate a ready-to-proceed response.",
        )

        return response.strip()

    # =========================================================================
    # RULE-BASED HELPERS (Fast, no LLM)
    # =========================================================================

    def _is_acceptance(self, text: str) -> bool:
        """Quick check for acceptance signals."""
        signals = [
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
        ]
        return any(s in text for s in signals)

    def _is_refinement(self, text: str) -> bool:
        """Quick check for refinement requests."""
        signals = [
            "change",
            "modify",
            "adjust",
            "refine",
            "tweak",
            "actually",
            "wait",
            "hold on",
            "not quite",
            "can you",
            "could you",
            "what if",
            "instead",
            "more",
            "less",
            "different",
            "add",
            "remove",
        ]
        return any(s in text for s in signals)


# =============================================================================
# SYNC WRAPPER
# =============================================================================


class SyncHybridRefiner:
    """Synchronous wrapper for HybridRefiner."""

    def __init__(self, llm_call: Callable[[str, str], str], **kwargs):
        async def async_llm(system: str, user: str) -> str:
            return llm_call(system, user)

        self._async_refiner = HybridRefiner(llm_call=async_llm, **kwargs)

    def create_session(self) -> str:
        return self._async_refiner.create_session()

    def process(self, session_id: str, user_input: str) -> dict[str, Any]:
        return asyncio.run(self._async_refiner.process(session_id, user_input))


# =============================================================================
# EXAMPLE WITH REAL LLM
# =============================================================================

EXAMPLE_OPENAI = """
import openai
from hybrid_refiner import HybridRefiner

# OpenAI executor
async def call_openai(system_prompt: str, user_message: str) -> str:
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
refiner = HybridRefiner(llm_call=call_openai)

# Use it
session_id = refiner.create_session()

# Turn 1
result = await refiner.process(session_id, "help me with marketing")
print(result["response"])  # Natural clarifying response

# Turn 2
result = await refiner.process(session_id, "B2B SaaS startup, need more leads, budget is tight")
print(result["response"])  # Ready to proceed response
print(result["analysis"])  # Shows understanding

# Turn 3: Accept
result = await refiner.process(session_id, "looks good")
print(result["final_prompt"])  # LLM-generated high-quality prompt!
"""

EXAMPLE_ANTHROPIC = """
import anthropic
from hybrid_refiner import HybridRefiner

client = anthropic.AsyncAnthropic()

async def call_claude(system_prompt: str, user_message: str) -> str:
    response = await client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

refiner = HybridRefiner(llm_call=call_claude)
# ... same usage as above
"""
