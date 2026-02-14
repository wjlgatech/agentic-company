"""
Smart Intent Refiner: Multi-turn interview → LLM-synthesized coherent prompt.

This is NOT template-filling. The LLM:
1. Conducts a thoughtful multi-turn interview
2. Synthesizes ALL gathered information
3. Writes a coherent, natural prompt (like a human expert would)

Think of it like asking ChatGPT: "Please refine my prompt into something better"
The output should read like a skilled prompt engineer wrote it.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Awaitable
from enum import Enum


# =============================================================================
# SYSTEM PROMPTS - THE BRAIN OF THE REFINER
# =============================================================================

def get_interviewer_prompt(conversation_history: str, user_message: str) -> str:
    return f"""You are an expert interviewer helping users articulate their needs clearly.

Your job is to have a natural conversation to understand what the user REALLY wants.
Think like a senior consultant in the first meeting with a client.

CONVERSATION SO FAR:
{conversation_history}

LATEST USER MESSAGE:
{user_message}

Based on this conversation, respond with a JSON object containing:
- understanding: object with summary (string), confidence (0-1), key_points (array), domain (string), task_type (string)
- gaps: object with critical (array) and helpful (array)
- next_action: either "ask_question" or "ready_to_proceed"
- question: object with text (string), why (string), options (array or null) - only if asking
- ready_message: string - only if ready to proceed

INTERVIEWING PRINCIPLES:
1. Ask ONE question at a time (not a list)
2. Make questions conversational, not interrogative
3. Be thorough but efficient - gather what truly matters
4. If you have 85%+ confidence AND no critical gaps AND have asked at least 3 questions, you're ready
5. Build on what they've said, don't ask for things they already told you
6. Max 5-6 questions total - then proceed with what you have

CRITICAL INFORMATION CHECKLIST (must have before proceeding):
- Core objective: What exactly do they want to accomplish?
- Scope/Scale: How big/complex is this task?
- Context: What's the domain, audience, or use case?
- Constraints: Any must-haves, must-nots, deadlines, or limitations?
- Success criteria: How will they know if it worked?

QUESTION PRIORITY:
1. What's the core outcome they need? (if unclear)
2. What's the scope and scale of this work?
3. Who is the audience/user? (if it affects the response)
4. Any constraints that would change the approach?
5. What does success look like for them?
6. Specific context that would make your help more relevant?

Be warm, professional, and efficient. Get to helping them quickly.
Return valid JSON only."""


SYNTHESIZER_PROMPT = """You are a world-class prompt engineer. Your task is to write a system prompt that will help an AI perfectly address the user's needs.

CONVERSATION SUMMARY:
{conversation_summary}

KEY UNDERSTANDING:
- What they want: {what_they_want}
- Domain: {domain}
- Task type: {task_type}
- Key context: {key_context}
- Constraints: {constraints}
- Success looks like: {success_criteria}

NOW WRITE A SYSTEM PROMPT that:

1. **Sets the perfect role** - Not generic "assistant" but a specific expert persona that matches their need

2. **Establishes context** - Write it as "Your client/user..." in a narrative form, not bullet points of extracted fields

3. **Defines clear objectives** - What exactly should be accomplished, in order of priority

4. **Specifies the approach** - How to think about this problem, what to consider

5. **Sets success criteria** - How to know if the output is good

6. **Adds appropriate guardrails** - Domain-specific cautions

CRITICAL RULES:
- Write naturally, as if a human expert wrote this after understanding the client
- NO template-looking sections like "## Key Details Extracted:" or "- **Business Context**:"
- NO mechanical bullet points listing extracted fields
- Preserve their specific terminology and context, but weave it into natural prose
- Make it feel like a thoughtful brief, not a form that was filled out
- The AI reading this prompt should feel like they're being briefed by a knowledgeable colleague

Write the system prompt now. Make it excellent."""


RESPONSE_PROMPT = """Generate a natural conversational response based on this context:

SITUATION: {situation}
UNDERSTANDING CONFIDENCE: {confidence}%
NEXT ACTION: {next_action}

If asking a question:
- Question: {question}
- Why it matters: {why}
- Options (if any): {options}

If ready to proceed:
- Ready message: {ready_message}

Write a warm, professional response.
- If asking, make it conversational (not "Question 1: ...")
- If ready, confirm what you understood and ask if they want to proceed
- Keep it concise but friendly

Return ONLY the response text."""


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ConversationState(Enum):
    INTERVIEWING = "interviewing"
    READY = "ready"
    REVIEWING = "reviewing"  # User reviewing draft prompt
    COMPLETE = "complete"


@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class Understanding:
    summary: str = ""
    confidence: float = 0.0
    key_points: List[str] = field(default_factory=list)
    domain: str = "general"
    task_type: str = "general"


@dataclass
class Session:
    session_id: str
    state: ConversationState = ConversationState.INTERVIEWING
    turns: List[ConversationTurn] = field(default_factory=list)
    understanding: Understanding = field(default_factory=Understanding)
    gaps: Dict = field(default_factory=dict)
    final_prompt: str = ""
    questions_asked: int = 0
    max_questions: int = 4


# =============================================================================
# SMART REFINER
# =============================================================================

class SmartRefiner:
    """
    Smart refiner that conducts thoughtful interviews and synthesizes coherent prompts.

    Unlike template-based approaches, this:
    1. Has a real conversation to understand needs
    2. Asks smart, contextual questions (not generic ones)
    3. Synthesizes everything into a coherent prompt (not stacked bullet points)
    """

    def __init__(
        self,
        llm_call: Callable[[str, str], Awaitable[str]],
        max_questions: int = 4,
        ready_threshold: float = 0.7,
    ):
        """
        Initialize the smart refiner.

        Args:
            llm_call: Async function(system_prompt, user_message) -> response
            max_questions: Maximum questions before proceeding anyway
            ready_threshold: Confidence level to consider ready
        """
        self.llm_call = llm_call
        self.max_questions = max_questions
        self.ready_threshold = ready_threshold
        self.sessions: Dict[str, Session] = {}

    def create_session(self) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = Session(
            session_id=session_id,
            max_questions=self.max_questions
        )
        return session_id

    async def process(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        Process user input and return response.

        This is the main entry point for the conversation.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Add user turn
        session.turns.append(ConversationTurn(role="user", content=user_input))

        # Check for user response if we're reviewing draft prompt
        if session.state == ConversationState.REVIEWING:
            if self._is_acceptance(user_input.lower()):
                # User approved the draft - finalize
                return await self._finalize(session)
            elif self._is_refinement(user_input.lower()) or "change" in user_input.lower() or "add" in user_input.lower():
                # User wants modifications - go back to interviewing
                session.state = ConversationState.INTERVIEWING
                # Continue with normal interview flow to gather more info
            else:
                # User might be giving specific feedback - process it
                session.state = ConversationState.INTERVIEWING

        # Interview phase
        analysis = await self._analyze_conversation(session, user_input)

        # Update understanding
        session.understanding = Understanding(
            summary=analysis.get("understanding", {}).get("summary", ""),
            confidence=analysis.get("understanding", {}).get("confidence", 0),
            key_points=analysis.get("understanding", {}).get("key_points", []),
            domain=analysis.get("understanding", {}).get("domain", "general"),
            task_type=analysis.get("understanding", {}).get("task_type", "general"),
        )
        session.gaps = analysis.get("gaps", {})

        # Decide next action
        next_action = analysis.get("next_action", "ask_question")
        confidence = session.understanding.confidence

        # Force ready if max questions reached
        if session.questions_asked >= session.max_questions:
            next_action = "ready_to_proceed"

        if next_action == "ready_to_proceed" or confidence >= self.ready_threshold:
            # Generate draft prompt and show to user for approval
            session.state = ConversationState.REVIEWING
            draft_result = await self._generate_draft_for_review(session)
            response = draft_result["response"]

            # Add assistant turn
            session.turns.append(ConversationTurn(role="assistant", content=response))

            return {
                "response": response,
                "state": session.state.value,
                "understanding": {
                    "summary": session.understanding.summary,
                    "confidence": session.understanding.confidence,
                    "key_points": session.understanding.key_points,
                },
                "ready": False,  # Not ready until user approves
                "reviewing": True,  # User is reviewing draft
                "draft_prompt": draft_result.get("draft_prompt", ""),
                "questions_asked": session.questions_asked,
            }
        else:
            session.questions_asked += 1
            response = await self._generate_question_response(session, analysis)

            # Add assistant turn
            session.turns.append(ConversationTurn(role="assistant", content=response))

            return {
                "response": response,
                "state": session.state.value,
                "understanding": {
                    "summary": session.understanding.summary,
                    "confidence": session.understanding.confidence,
                    "key_points": session.understanding.key_points,
                },
                "ready": False,
                "reviewing": False,
                "questions_asked": session.questions_asked,
            }

    async def _analyze_conversation(self, session: Session, latest_input: str) -> Dict:
        """Use LLM to analyze the conversation and decide next steps."""

        # Build conversation history
        history = "\n".join([
            f"{t.role.upper()}: {t.content}"
            for t in session.turns[:-1]  # Exclude the just-added user turn
        ])

        if not history:
            history = "(This is the start of the conversation)"

        prompt = get_interviewer_prompt(
            conversation_history=history,
            user_message=latest_input
        )

        response = await self.llm_call(
            "You are an expert interviewer. Return valid JSON only.",
            prompt
        )

        # Parse JSON
        try:
            # Handle markdown code blocks
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            # Fallback
            return {
                "understanding": {"summary": latest_input, "confidence": 0.5},
                "gaps": {"critical": [], "helpful": []},
                "next_action": "ask_question",
                "question": {
                    "text": "Could you tell me more about what you're hoping to achieve?",
                    "why": "Understanding the core goal",
                    "options": None
                }
            }

    async def _generate_question_response(self, session: Session, analysis: Dict) -> str:
        """Generate a natural response with a question."""

        question_data = analysis.get("question", {})

        prompt = RESPONSE_PROMPT.format(
            situation="asking a clarifying question",
            confidence=int(session.understanding.confidence * 100),
            next_action="ask_question",
            question=question_data.get("text", "Could you tell me more?"),
            why=question_data.get("why", ""),
            options=question_data.get("options", []),
            ready_message=""
        )

        response = await self.llm_call(
            "Generate a natural, conversational response.",
            prompt
        )

        return response.strip()

    async def _generate_ready_response(self, session: Session, analysis: Dict) -> str:
        """Generate a response indicating we're ready to proceed."""

        ready_message = analysis.get("ready_message", "")
        if not ready_message:
            ready_message = f"I understand you want: {session.understanding.summary}"

        prompt = RESPONSE_PROMPT.format(
            situation="ready to create the prompt",
            confidence=int(session.understanding.confidence * 100),
            next_action="ready_to_proceed",
            question="",
            why="",
            options=[],
            ready_message=ready_message
        )

        response = await self.llm_call(
            "Generate a natural response confirming understanding and asking to proceed.",
            prompt
        )

        return response.strip()

    async def _generate_draft_for_review(self, session: Session) -> Dict[str, Any]:
        """
        Generate a DRAFT prompt and present it to user for approval.
        User must explicitly approve before finalization.
        """
        # Build conversation summary for the synthesizer
        conversation_summary = "\n".join([
            f"{t.role.upper()}: {t.content}"
            for t in session.turns
        ])

        # Extract key information
        understanding = session.understanding

        # Synthesize the DRAFT prompt using LLM
        synthesis_prompt = SYNTHESIZER_PROMPT.format(
            conversation_summary=conversation_summary,
            what_they_want=understanding.summary,
            domain=understanding.domain,
            task_type=understanding.task_type,
            key_context=", ".join(understanding.key_points) if understanding.key_points else "See conversation",
            constraints="As discussed in conversation",
            success_criteria="Addresses the user's stated needs comprehensively"
        )

        draft_prompt = await self.llm_call(
            "You are a world-class prompt engineer. Write an excellent, coherent system prompt.",
            synthesis_prompt
        )

        # Store draft in session
        session.final_prompt = draft_prompt.strip()

        # Create response asking for approval
        response = f"""Based on our conversation, I've created a draft prompt for you. Please review it:

---
{draft_prompt.strip()}
---

Does this capture what you need? You can:
• Say "yes" or "approve" to use this prompt
• Tell me what to change or add if you want modifications
• Continue asking questions if you need more refinement"""

        return {
            "response": response,
            "draft_prompt": draft_prompt.strip()
        }

    async def _finalize(self, session: Session) -> Dict[str, Any]:
        """Finalize and return the approved prompt."""

        session.state = ConversationState.COMPLETE
        understanding = session.understanding

        return {
            "response": "Perfect! Your prompt is ready to use. I'll pass it to the workflow system now.",
            "state": "complete",
            "ready": True,
            "final_prompt": session.final_prompt,  # Already generated in draft stage
            "understanding": {
                "summary": understanding.summary,
                "confidence": understanding.confidence,
            }
        }

    def _is_acceptance(self, text: str) -> bool:
        """Check if user is accepting."""
        signals = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed",
                   "go ahead", "do it", "looks good", "perfect", "great", "let's go"]
        return any(s in text for s in signals)

    def _is_refinement(self, text: str) -> bool:
        """Check if user wants to refine."""
        signals = ["wait", "actually", "change", "add", "also", "but", "hold on"]
        return any(s in text for s in signals)


# =============================================================================
# SYNC WRAPPER
# =============================================================================

class SyncSmartRefiner:
    """Synchronous wrapper for SmartRefiner."""

    def __init__(self, llm_call: Callable[[str, str], str], **kwargs):
        import asyncio

        async def async_llm(system: str, user: str) -> str:
            return llm_call(system, user)

        self._async_refiner = SmartRefiner(llm_call=async_llm, **kwargs)
        self._loop = asyncio.new_event_loop()

    def create_session(self) -> str:
        return self._async_refiner.create_session()

    def process(self, session_id: str, user_input: str) -> Dict[str, Any]:
        import asyncio
        return asyncio.run(self._async_refiner.process(session_id, user_input))


# =============================================================================
# EXAMPLE WITH REAL LLM
# =============================================================================

EXAMPLE_USAGE = '''
import anthropic

client = anthropic.AsyncAnthropic()

async def call_claude(system: str, user: str) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text

refiner = SmartRefiner(llm_call=call_claude)
session_id = refiner.create_session()

# Conversation
result = await refiner.process(session_id, "I need help with my marketing")
print(result["response"])  # Natural follow-up question

result = await refiner.process(session_id, "We're a B2B SaaS company, struggling with lead gen")
print(result["response"])  # Another question or ready to proceed

result = await refiner.process(session_id, "yes, proceed")
print(result["final_prompt"])  # Coherent, synthesized prompt!
'''
