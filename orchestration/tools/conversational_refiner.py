"""
Conversational Intent Refiner: Single-chatbox iterative refinement.

This module implements a conversational approach to intent refinement
that works naturally within a single chat interface.

Design Philosophy:
- NO separate "refinement mode" - everything happens in the chat
- Progressive disclosure - start simple, add detail as needed
- Smart defaults - generate immediately, refine on request
- Natural language - questions feel like conversation, not forms

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                     SINGLE CHATBOX UI                           │
├─────────────────────────────────────────────────────────────────┤
│  User: "help me with marketing"                                 │
│                                                                 │
│  AI: [Quick Response Card]                                      │
│      ┌─────────────────────────────────────────────────────┐   │
│      │ I can help with marketing! To give you the best     │   │
│      │ advice, I'm curious about a few things:             │   │
│      │                                                     │   │
│      │ • What type of business? [B2B] [B2C] [Both]        │   │
│      │ • Main goal? [Growth] [Retention] [Brand]          │   │
│      │                                                     │   │
│      │ Or just tell me more in your own words...          │   │
│      └─────────────────────────────────────────────────────┘   │
│                                                                 │
│  User: "B2B SaaS, we need more leads"                          │
│                                                                 │
│  AI: [Refined Response with Draft]                              │
│      Got it - B2B SaaS lead generation. Here's my approach:    │
│      [Draft Preview]                                            │
│      Want me to proceed, or should we refine further?          │
└─────────────────────────────────────────────────────────────────┘
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

from .intent_refiner import (
    IntentRefiner,
    IntentClassification,
    ExtractedSpecifics,
    QualityScore,
    TaskType,
    Domain,
)


class ConversationState(Enum):
    """States in the refinement conversation."""
    INITIAL = "initial"              # Just received first input
    CLARIFYING = "clarifying"        # Asking clarification questions
    DRAFT_READY = "draft_ready"      # Have enough to generate draft
    REFINING = "refining"            # User is refining the draft
    COMPLETE = "complete"            # User accepted the output


@dataclass
class QuickOption:
    """A clickable option in the chat UI."""
    label: str
    value: str
    description: str = ""
    selected: bool = False


@dataclass
class ClarificationCard:
    """An inline clarification card for the chat UI."""
    question: str
    options: List[QuickOption] = field(default_factory=list)
    allow_freeform: bool = True
    priority: int = 1  # 1=critical, 2=helpful, 3=optional
    dimension: str = ""  # What this clarifies


@dataclass
class DraftPreview:
    """A preview of the generated output."""
    summary: str           # Short summary of what will be done
    approach: List[str]    # Key steps
    output_type: str       # What will be delivered
    confidence: float      # How confident we are this is right
    can_proceed: bool      # Whether we have enough to proceed


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    turn_id: str
    user_input: str
    ai_response: str
    cards: List[ClarificationCard] = field(default_factory=list)
    draft: Optional[DraftPreview] = None
    state: ConversationState = ConversationState.INITIAL
    extracted: Optional[Dict] = None


@dataclass
class RefinementSession:
    """Tracks an entire refinement conversation."""
    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    state: ConversationState = ConversationState.INITIAL

    # Accumulated context
    classification: Optional[IntentClassification] = None
    specifics: Optional[ExtractedSpecifics] = None
    answers: Dict[str, str] = field(default_factory=dict)

    # Quality tracking
    quality_score: float = 0.0
    quality_threshold: float = 0.7

    # Final output
    final_prompt: str = ""

    def get_context_summary(self) -> str:
        """Get a summary of what we know so far."""
        parts = []
        if self.classification:
            parts.append(f"Task: {self.classification.task_type.value}")
            parts.append(f"Domain: {self.classification.domain.value}")
        if self.specifics:
            if self.specifics.entities:
                parts.append(f"Context: {', '.join(self.specifics.entities[:3])}")
            if self.specifics.goals:
                parts.append(f"Goal: {self.specifics.goals[0][:50]}...")
        return " | ".join(parts) if parts else "Getting started..."


class ConversationalRefiner:
    """
    Implements conversational intent refinement in a single chatbox.

    Key Features:
    1. Stateful sessions - remembers conversation history
    2. Inline cards - clickable options within chat messages
    3. Draft previews - show what will be generated before committing
    4. Natural flow - questions feel conversational, not form-like

    Usage:
        refiner = ConversationalRefiner()
        session = refiner.start_session()

        # First user message
        response = refiner.process_input(session, "help me with marketing")
        # Returns response with inline clarification cards

        # User clicks option or types more
        response = refiner.process_input(session, "B2B SaaS")
        # Returns refined response, possibly with draft preview

        # User accepts or continues refining
        response = refiner.process_input(session, "looks good, proceed")
        # Returns final output
    """

    def __init__(self, quality_threshold: float = 0.7):
        self.refiner = IntentRefiner()
        self.quality_threshold = quality_threshold
        self.sessions: Dict[str, RefinementSession] = {}

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def start_session(self) -> RefinementSession:
        """Start a new refinement session."""
        session_id = str(uuid.uuid4())[:8]
        session = RefinementSession(
            session_id=session_id,
            quality_threshold=self.quality_threshold,
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[RefinementSession]:
        """Retrieve an existing session."""
        return self.sessions.get(session_id)

    # =========================================================================
    # MAIN PROCESSING
    # =========================================================================

    def process_input(
        self,
        session: RefinementSession,
        user_input: str,
    ) -> ConversationTurn:
        """
        Process user input and return appropriate response.

        This is the main entry point for the chatbox integration.
        It handles:
        - Initial vague requests → clarification cards
        - Answers to clarifications → updated understanding
        - Refinement requests → modified draft
        - Acceptance signals → final output

        Args:
            session: The refinement session
            user_input: User's message

        Returns:
            ConversationTurn with response, cards, and/or draft
        """
        turn_id = f"turn_{len(session.turns) + 1}"

        # Detect user intent within the refinement conversation
        input_lower = user_input.lower().strip()

        # Check for acceptance signals
        if self._is_acceptance(input_lower) and session.state == ConversationState.DRAFT_READY:
            return self._handle_acceptance(session, turn_id, user_input)

        # Check for refinement requests
        if self._is_refinement_request(input_lower) and session.state == ConversationState.DRAFT_READY:
            return self._handle_refinement_request(session, turn_id, user_input)

        # Otherwise, process as new/additional context
        return self._handle_context_input(session, turn_id, user_input)

    # =========================================================================
    # INPUT HANDLERS
    # =========================================================================

    def _handle_context_input(
        self,
        session: RefinementSession,
        turn_id: str,
        user_input: str,
    ) -> ConversationTurn:
        """Handle input that provides context (initial or additional)."""

        # Combine with previous context
        all_input = self._get_combined_input(session, user_input)

        # Parse and extract
        classification = self.refiner.parse(all_input)
        specifics = self.refiner.extract_specifics(all_input, classification)

        # Update session
        session.classification = classification
        session.specifics = specifics

        # Evaluate quality
        quality = self._evaluate_readiness(session)
        session.quality_score = quality

        # Decide response based on quality
        if quality >= session.quality_threshold:
            # Ready to generate draft
            return self._create_draft_response(session, turn_id, user_input)
        else:
            # Need more clarification
            return self._create_clarification_response(session, turn_id, user_input)

    def _handle_acceptance(
        self,
        session: RefinementSession,
        turn_id: str,
        user_input: str,
    ) -> ConversationTurn:
        """Handle user accepting the draft."""

        # Generate final prompt
        all_input = self._get_combined_input(session, user_input)
        result = self.refiner.refine(all_input, session.answers)
        session.final_prompt = result["prompt"]
        session.state = ConversationState.COMPLETE

        response = f"""Perfect! I've prepared your optimized prompt.

**What I understood:**
- Task: {session.classification.task_type.value if session.classification else 'general'}
- Domain: {session.classification.domain.value if session.classification else 'general'}
- Confidence: {session.quality_score:.0%}

Your prompt is ready to use. It includes:
- Specific context from your request
- Structured approach and success criteria
- Appropriate guardrails

Would you like me to execute this task now, or would you prefer to see the full prompt first?"""

        turn = ConversationTurn(
            turn_id=turn_id,
            user_input=user_input,
            ai_response=response,
            state=ConversationState.COMPLETE,
            extracted=result.get("specifics_extracted"),
        )
        session.turns.append(turn)
        return turn

    def _handle_refinement_request(
        self,
        session: RefinementSession,
        turn_id: str,
        user_input: str,
    ) -> ConversationTurn:
        """Handle user requesting changes to draft."""

        session.state = ConversationState.REFINING

        # Extract what they want to change
        response = """No problem! What would you like to adjust?

You can tell me things like:
- "Focus more on [specific aspect]"
- "Add consideration for [constraint]"
- "Actually, I meant [clarification]"
- "Include [additional requirement]"

Or just describe what you'd like different."""

        turn = ConversationTurn(
            turn_id=turn_id,
            user_input=user_input,
            ai_response=response,
            state=ConversationState.REFINING,
        )
        session.turns.append(turn)
        return turn

    # =========================================================================
    # RESPONSE GENERATORS
    # =========================================================================

    def _create_clarification_response(
        self,
        session: RefinementSession,
        turn_id: str,
        user_input: str,
    ) -> ConversationTurn:
        """Create response with inline clarification cards."""

        session.state = ConversationState.CLARIFYING

        # Get smart questions based on what we know
        cards = self._generate_clarification_cards(session)

        # Build conversational response
        if not session.turns:
            # First turn - warm greeting
            response = self._build_initial_response(session, cards)
        else:
            # Follow-up - acknowledge what we learned
            response = self._build_followup_response(session, cards)

        turn = ConversationTurn(
            turn_id=turn_id,
            user_input=user_input,
            ai_response=response,
            cards=cards,
            state=ConversationState.CLARIFYING,
            extracted={
                "entities": session.specifics.entities if session.specifics else [],
                "goals": session.specifics.goals[:2] if session.specifics else [],
            }
        )
        session.turns.append(turn)
        return turn

    def _create_draft_response(
        self,
        session: RefinementSession,
        turn_id: str,
        user_input: str,
    ) -> ConversationTurn:
        """Create response with draft preview."""

        session.state = ConversationState.DRAFT_READY

        # Build draft preview
        draft = self._build_draft_preview(session)

        # Build response
        response = self._build_draft_response(session, draft)

        turn = ConversationTurn(
            turn_id=turn_id,
            user_input=user_input,
            ai_response=response,
            draft=draft,
            state=ConversationState.DRAFT_READY,
            extracted={
                "entities": session.specifics.entities if session.specifics else [],
                "goals": session.specifics.goals[:2] if session.specifics else [],
            }
        )
        session.turns.append(turn)
        return turn

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _is_acceptance(self, input_lower: str) -> bool:
        """Check if user is accepting the draft."""
        acceptance_signals = [
            "yes", "yep", "yeah", "sure", "ok", "okay", "go ahead",
            "proceed", "do it", "looks good", "perfect", "great",
            "that works", "sounds good", "let's go", "approved",
            "continue", "execute", "run it", "make it so"
        ]
        return any(signal in input_lower for signal in acceptance_signals)

    def _is_refinement_request(self, input_lower: str) -> bool:
        """Check if user wants to refine the draft."""
        refinement_signals = [
            "change", "modify", "adjust", "refine", "tweak",
            "actually", "wait", "hold on", "not quite", "almost",
            "can you", "could you", "what if", "instead",
            "more", "less", "different", "add", "remove"
        ]
        return any(signal in input_lower for signal in refinement_signals)

    def _get_combined_input(self, session: RefinementSession, new_input: str) -> str:
        """Combine all user inputs from the session."""
        all_inputs = [turn.user_input for turn in session.turns]
        all_inputs.append(new_input)
        return " ".join(all_inputs)

    def _evaluate_readiness(self, session: RefinementSession) -> float:
        """Evaluate how ready we are to generate output."""
        score = 0.0

        if session.classification:
            # Higher confidence = more ready
            score += session.classification.confidence * 0.25

        if session.specifics:
            # More specifics = more ready
            specifics_count = (
                len(session.specifics.entities) +
                len(session.specifics.goals) +
                len(session.specifics.constraints) +
                len(session.specifics.pain_points)
            )
            score += min(specifics_count * 0.08, 0.35)

            # Having a clear goal is very important
            if session.specifics.goals:
                score += 0.25

            # Having context (entities) helps
            if session.specifics.entities:
                score += 0.15

            # Having pain points shows understanding
            if session.specifics.pain_points:
                score += 0.1

            # Constraints show depth
            if session.specifics.constraints:
                score += 0.1

        # Bonus for multi-turn conversations (user is engaged)
        if len(session.turns) >= 1:
            score += 0.1

        return min(score, 1.0)

    def _generate_clarification_cards(
        self,
        session: RefinementSession,
    ) -> List[ClarificationCard]:
        """Generate smart clarification cards based on current state."""
        cards = []

        classification = session.classification
        specifics = session.specifics

        # If we don't know the domain well
        if classification and classification.confidence < 0.6:
            if classification.domain == Domain.BUSINESS:
                cards.append(ClarificationCard(
                    question="What type of business is this for?",
                    options=[
                        QuickOption("B2B", "b2b", "Business to business"),
                        QuickOption("B2C", "b2c", "Business to consumer"),
                        QuickOption("SaaS", "saas", "Software as a service"),
                        QuickOption("E-commerce", "ecommerce", "Online retail"),
                    ],
                    dimension="business_type",
                    priority=1,
                ))

        # If we don't have clear goals
        if not specifics or not specifics.goals:
            if classification and classification.task_type == TaskType.ANALYSIS:
                cards.append(ClarificationCard(
                    question="What decision will this analysis inform?",
                    options=[
                        QuickOption("Strategy", "strategy", "Strategic planning"),
                        QuickOption("Investment", "investment", "Investment decision"),
                        QuickOption("Process", "process", "Process improvement"),
                        QuickOption("Hiring", "hiring", "Hiring decision"),
                    ],
                    dimension="goal",
                    priority=1,
                ))
            else:
                cards.append(ClarificationCard(
                    question="What's the main outcome you're looking for?",
                    options=[
                        QuickOption("Quick answer", "quick", "Fast, focused response"),
                        QuickOption("Deep analysis", "deep", "Comprehensive analysis"),
                        QuickOption("Action plan", "plan", "Step-by-step plan"),
                        QuickOption("Creative ideas", "creative", "Brainstorming/ideation"),
                    ],
                    dimension="outcome",
                    priority=1,
                ))

        # If we don't know the audience
        if not specifics or not specifics.stakeholders:
            cards.append(ClarificationCard(
                question="Who will use this output?",
                options=[
                    QuickOption("Just me", "self", "Personal use"),
                    QuickOption("My team", "team", "Internal team"),
                    QuickOption("Leadership", "leadership", "Executives/management"),
                    QuickOption("Clients", "clients", "External clients"),
                ],
                dimension="audience",
                priority=2,
            ))

        # Limit to most important cards
        cards.sort(key=lambda c: c.priority)
        return cards[:3]

    def _build_initial_response(
        self,
        session: RefinementSession,
        cards: List[ClarificationCard],
    ) -> str:
        """Build the initial response with clarification cards."""

        # Acknowledge what we understood
        understood_parts = []
        if session.classification:
            task = session.classification.task_type.value
            domain = session.classification.domain.value
            understood_parts.append(f"I can help you {task} something in the {domain} area")

        if session.specifics and session.specifics.entities:
            understood_parts.append(f"I see this involves: {', '.join(session.specifics.entities[:3])}")

        understood = ". ".join(understood_parts) + "." if understood_parts else "I'd love to help!"

        # Build card questions as conversational text
        questions = []
        for card in cards:
            options_text = " / ".join([f"**{o.label}**" for o in card.options])
            questions.append(f"• {card.question} ({options_text})")

        questions_text = "\n".join(questions) if questions else ""

        response = f"""{understood}

To give you the most relevant help, I'm curious about:

{questions_text}

Feel free to click an option or just tell me more in your own words!"""

        return response

    def _build_followup_response(
        self,
        session: RefinementSession,
        cards: List[ClarificationCard],
    ) -> str:
        """Build follow-up response acknowledging progress."""

        # Acknowledge what we learned
        learned = []
        if session.specifics:
            if session.specifics.entities:
                learned.append(f"Context: {', '.join(session.specifics.entities[:2])}")
            if session.specifics.goals:
                learned.append(f"Goal: {session.specifics.goals[0][:50]}...")

        learned_text = " | ".join(learned) if learned else "Building understanding..."

        # Remaining questions
        questions = []
        for card in cards:
            options_text = " / ".join([f"**{o.label}**" for o in card.options])
            questions.append(f"• {card.question} ({options_text})")

        questions_text = "\n".join(questions) if questions else ""

        if questions_text:
            response = f"""Got it! **{learned_text}**

Just a couple more things would help me nail this:

{questions_text}

Or tell me more and I'll figure it out!"""
        else:
            response = f"""Got it! **{learned_text}**

I think I have enough to work with. Let me put together a draft..."""

        return response

    def _build_draft_preview(self, session: RefinementSession) -> DraftPreview:
        """Build a preview of what will be generated."""

        # Determine output type
        task_outputs = {
            TaskType.ANALYSIS: "Analysis report with insights and recommendations",
            TaskType.CREATION: "Custom content tailored to your needs",
            TaskType.RESEARCH: "Research summary with key findings",
            TaskType.DECISION: "Decision framework with recommendations",
            TaskType.TRANSFORMATION: "Improved/refined version",
            TaskType.AUTOMATION: "Process design with steps",
        }

        task_type = session.classification.task_type if session.classification else TaskType.CREATION
        output_type = task_outputs.get(task_type, "Helpful response")

        # Build approach steps
        approach = []
        if task_type == TaskType.ANALYSIS:
            approach = ["Understand your context", "Analyze key factors", "Identify insights", "Provide recommendations"]
        elif task_type == TaskType.CREATION:
            approach = ["Understand requirements", "Plan structure", "Generate content", "Refine and polish"]
        elif task_type == TaskType.RESEARCH:
            approach = ["Define scope", "Gather information", "Evaluate sources", "Synthesize findings"]
        else:
            approach = ["Understand request", "Process information", "Generate output"]

        # Add specific context to approach
        if session.specifics and session.specifics.entities:
            approach.append(f"Consider: {', '.join(session.specifics.entities[:3])}")

        # Build summary
        summary_parts = []
        if session.specifics:
            if session.specifics.goals:
                summary_parts.append(session.specifics.goals[0][:80])
            if session.specifics.entities:
                summary_parts.append(f"for {', '.join(session.specifics.entities[:2])}")

        summary = " ".join(summary_parts) if summary_parts else "Help with your request"

        return DraftPreview(
            summary=summary,
            approach=approach,
            output_type=output_type,
            confidence=session.quality_score,
            can_proceed=session.quality_score >= session.quality_threshold,
        )

    def _build_draft_response(
        self,
        session: RefinementSession,
        draft: DraftPreview,
    ) -> str:
        """Build response showing draft preview."""

        approach_text = "\n".join([f"  {i+1}. {step}" for i, step in enumerate(draft.approach)])

        confidence_emoji = "🟢" if draft.confidence >= 0.8 else "🟡" if draft.confidence >= 0.6 else "🔴"

        response = f"""Great, I think I understand what you need!

**Summary:** {draft.summary}

**My approach:**
{approach_text}

**Output:** {draft.output_type}

{confidence_emoji} **Confidence:** {draft.confidence:.0%}

---

**Ready to proceed?**
- Say **"yes"** or **"go ahead"** to generate the full output
- Say **"change X"** or **"add Y"** to refine first
- Or ask me anything else!"""

        return response

    # =========================================================================
    # SERIALIZATION (for API/persistence)
    # =========================================================================

    def session_to_dict(self, session: RefinementSession) -> dict:
        """Convert session to dictionary for API response."""
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "quality_score": session.quality_score,
            "context_summary": session.get_context_summary(),
            "turns": [
                {
                    "turn_id": turn.turn_id,
                    "user_input": turn.user_input,
                    "ai_response": turn.ai_response,
                    "cards": [
                        {
                            "question": card.question,
                            "options": [
                                {"label": o.label, "value": o.value, "description": o.description}
                                for o in card.options
                            ],
                            "allow_freeform": card.allow_freeform,
                            "dimension": card.dimension,
                        }
                        for card in turn.cards
                    ],
                    "draft": {
                        "summary": turn.draft.summary,
                        "approach": turn.draft.approach,
                        "output_type": turn.draft.output_type,
                        "confidence": turn.draft.confidence,
                        "can_proceed": turn.draft.can_proceed,
                    } if turn.draft else None,
                    "state": turn.state.value,
                }
                for turn in session.turns
            ],
            "final_prompt": session.final_prompt if session.state == ConversationState.COMPLETE else None,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_refiner() -> ConversationalRefiner:
    """Create a new conversational refiner instance."""
    return ConversationalRefiner()


def quick_refine(user_input: str) -> dict:
    """
    Quick single-turn refinement for simple cases.

    For complex cases, use the full ConversationalRefiner.
    """
    refiner = ConversationalRefiner()
    session = refiner.start_session()
    turn = refiner.process_input(session, user_input)
    return refiner.session_to_dict(session)
