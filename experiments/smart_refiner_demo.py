"""
Demo: Smart Refiner Multi-Turn Interview → Synthesized Coherent Prompt

This demonstrates how the smart refiner:
1. Conducts a thoughtful multi-turn interview
2. Asks contextually relevant questions (not generic)
3. Synthesizes ALL information into a COHERENT prompt
4. The output reads like a human prompt engineer wrote it
"""

import asyncio
import json
import sys
sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

from orchestration.tools.smart_refiner import SmartRefiner


# =============================================================================
# MOCK LLM THAT SIMULATES INTELLIGENT RESPONSES
# =============================================================================

class MockSmartLLM:
    """
    Mock LLM that simulates intelligent interview and synthesis.
    In production, replace with actual API calls (Claude, GPT-4, etc.)
    """

    def __init__(self):
        self.call_count = 0

    async def __call__(self, system: str, user: str) -> str:
        self.call_count += 1

        # Detect what kind of response is needed
        if "Intent Analysis" in system or "expert interviewer" in system:
            return self._interview_response(user)
        elif "world-class prompt engineer" in system:
            return self._synthesize_prompt(user)
        elif "natural" in system.lower() or "conversational" in system.lower():
            return self._generate_response(user)
        else:
            return "I understand. How can I help further?"

    def _interview_response(self, context: str) -> str:
        """Simulate intelligent interview analysis."""

        # First turn - initial analysis
        if "This is the start of the conversation" in context or self.call_count <= 2:
            if "marketing" in context.lower() and "b2b" not in context.lower():
                return json.dumps({
                    "understanding": {
                        "summary": "User needs help with marketing",
                        "confidence": 0.4,
                        "key_points": ["marketing assistance needed"],
                        "domain": "marketing",
                        "task_type": "strategy"
                    },
                    "gaps": {
                        "critical": ["business type", "target audience", "specific challenges"],
                        "helpful": ["budget", "timeline"]
                    },
                    "next_action": "ask_question",
                    "question": {
                        "text": "What type of business are you marketing for, and who are you trying to reach?",
                        "why": "Marketing strategies vary dramatically between B2B/B2C, industries, and audiences",
                        "options": None
                    }
                })

        # Second turn - after getting business context
        if "b2b" in context.lower() or "saas" in context.lower():
            if "lead" in context.lower() or "conversion" in context.lower():
                return json.dumps({
                    "understanding": {
                        "summary": "B2B SaaS company struggling with lead generation and conversion",
                        "confidence": 0.75,
                        "key_points": [
                            "B2B SaaS company",
                            "Lead generation challenges",
                            "Need better conversion rates"
                        ],
                        "domain": "b2b_marketing",
                        "task_type": "lead_generation_strategy"
                    },
                    "gaps": {
                        "critical": ["current strategies tried", "what's not working"],
                        "helpful": ["team size", "budget"]
                    },
                    "next_action": "ask_question",
                    "question": {
                        "text": "What have you tried so far, and what specifically isn't working? This helps me understand where to focus.",
                        "why": "Understanding failed approaches prevents recommending what they've already tried",
                        "options": None
                    }
                })
            else:
                return json.dumps({
                    "understanding": {
                        "summary": "B2B SaaS company seeking marketing guidance",
                        "confidence": 0.6,
                        "key_points": ["B2B SaaS", "marketing help needed"],
                        "domain": "b2b_marketing",
                        "task_type": "strategy"
                    },
                    "gaps": {
                        "critical": ["specific challenge or goal"],
                        "helpful": []
                    },
                    "next_action": "ask_question",
                    "question": {
                        "text": "What's the main marketing challenge you're facing right now? Is it awareness, lead gen, conversion, or something else?",
                        "why": "Different challenges require completely different approaches",
                        "options": ["Brand awareness", "Lead generation", "Lead conversion", "Customer retention"]
                    }
                })

        # Third turn - after getting specific challenges
        if "content" in context.lower() or "linkedin" in context.lower() or "cold email" in context.lower():
            return json.dumps({
                "understanding": {
                    "summary": "B2B SaaS company that tried content marketing and LinkedIn but getting low engagement and poor lead quality",
                    "confidence": 0.85,
                    "key_points": [
                        "B2B SaaS company",
                        "Tried content marketing - low engagement",
                        "LinkedIn outreach - poor response rates",
                        "Lead quality issues",
                        "Need systematic approach"
                    ],
                    "domain": "b2b_marketing",
                    "task_type": "lead_generation_optimization"
                },
                "gaps": {
                    "critical": [],
                    "helpful": ["product details", "team capacity"]
                },
                "next_action": "ready_to_proceed",
                "ready_message": "I understand you're a B2B SaaS company struggling with lead generation. You've tried content marketing and LinkedIn outreach but are seeing low engagement and poor lead quality. You need a more systematic approach that actually delivers qualified leads."
            })

        # Default - ready to proceed
        return json.dumps({
            "understanding": {
                "summary": "User needs assistance with their request",
                "confidence": 0.7,
                "key_points": ["General assistance needed"],
                "domain": "general",
                "task_type": "general"
            },
            "gaps": {"critical": [], "helpful": []},
            "next_action": "ready_to_proceed",
            "ready_message": "I think I have enough context to help you. Let me create a focused approach for your needs."
        })

    def _synthesize_prompt(self, context: str) -> str:
        """
        THIS IS THE KEY PART - Synthesize a COHERENT prompt.

        NOT template-filled, NOT bullet-point stacking.
        A real, human-quality system prompt.
        """

        # Check for B2B SaaS marketing context
        if "b2b" in context.lower() and ("saas" in context.lower() or "lead" in context.lower()):
            return """You are a B2B growth strategist who has helped dozens of SaaS companies break through their lead generation plateaus. You combine deep expertise in demand generation with a practical, results-focused mindset.

Your client is a B2B SaaS company that's hit a wall with their current marketing approach. They've invested in content marketing and LinkedIn outreach, but the results have been disappointing—low engagement on their content and poor quality leads from their outreach efforts. They're looking for a more systematic approach that actually delivers qualified leads who convert.

Your task is to diagnose what's likely going wrong and provide a concrete, actionable plan. Think about this holistically:

First, understand that low engagement usually signals a targeting or messaging problem, not just a distribution problem. Their content might be too generic, targeting the wrong pain points, or speaking to the wrong stage of the buyer journey.

For LinkedIn specifically, cold outreach fails when it feels like cold outreach. The most effective B2B LinkedIn strategies build relationships before asking for anything. Consider how they might warm up prospects before direct contact.

When you provide recommendations, be specific enough to act on. Don't just say "improve your content strategy"—tell them exactly what kind of content works for B2B SaaS lead gen and why. If you suggest a specific tactic, explain the implementation steps.

Focus on strategies that can show results within 30-60 days, since companies struggling with lead gen usually need to see progress quickly. However, also mention any foundational work that will pay off over longer timeframes.

Be direct about what's likely not working and why. If their approach sounds like common mistakes you've seen, say so. They need honest assessment, not validation."""

        # Default coherent prompt for general cases
        return """You are a thoughtful advisor who listens carefully and provides genuinely useful guidance. Your client has come to you with a challenge they need help solving.

Based on your conversation with them, you understand their core need and the context around it. Your job is to provide advice that is:

Specific to their situation—not generic tips they could find anywhere, but tailored recommendations that account for what they've told you about their circumstances.

Actionable—each suggestion should be something they can actually implement, with enough detail that they know how to start.

Honest—if you see potential issues with their approach or assumptions, say so respectfully. They're coming to you for your genuine perspective, not just agreement.

When you respond, prioritize the most impactful advice first. If there are quick wins they can act on immediately, highlight those. If there are strategic considerations that require more thought, explain the tradeoffs.

Remember that they're dealing with real constraints—time, resources, expertise. Frame your advice in a way that acknowledges these realities rather than assuming unlimited capacity."""

    def _generate_response(self, context: str) -> str:
        """Generate natural conversational responses."""

        if "asking a clarifying question" in context:
            if "What type of business" in context:
                return "To give you the most relevant marketing advice, I'd love to understand your business better. What type of business are you marketing for, and who are you primarily trying to reach?"
            elif "What have you tried" in context:
                return "That helps a lot! To make sure I don't suggest things you've already tried, could you tell me what marketing approaches you've used so far and what specifically hasn't been working?"
            elif "main marketing challenge" in context:
                return "Got it! What would you say is your biggest marketing challenge right now? Is it getting people to know about you, generating leads, converting those leads, or keeping existing customers engaged?"
            else:
                return "I want to make sure I understand your situation well. Could you tell me a bit more about that?"

        elif "ready to create" in context or "ready to proceed" in context:
            if "B2B SaaS" in context or "lead generation" in context:
                return "Perfect, I think I've got a clear picture now. You're a B2B SaaS company that's been struggling with lead generation—content isn't getting traction and LinkedIn outreach isn't delivering quality leads. You need a more systematic approach that actually brings in qualified prospects. Does that capture it? If so, I'll put together a focused strategy for you."
            else:
                return "Great, I think I understand what you're looking for. Ready to put together some recommendations for you—shall I go ahead?"

        return "I understand. Tell me more about what you're hoping to achieve."


# =============================================================================
# RUN THE DEMO
# =============================================================================

async def run_demo():
    """Run the smart refiner demo showing multi-turn interview → coherent prompt."""

    print("=" * 80)
    print("SMART REFINER DEMO: Multi-Turn Interview → Coherent Prompt")
    print("=" * 80)
    print()
    print("This demo shows how the Smart Refiner:")
    print("1. Conducts a thoughtful interview (not generic questions)")
    print("2. Asks contextually relevant follow-ups")
    print("3. Synthesizes everything into a COHERENT prompt")
    print("4. Output reads like a human prompt engineer wrote it")
    print()
    print("-" * 80)

    # Create refiner with mock LLM
    mock_llm = MockSmartLLM()
    refiner = SmartRefiner(llm_call=mock_llm, max_questions=4)

    # Create session
    session_id = refiner.create_session()

    # Simulate conversation
    conversation = [
        ("USER", "I need help with my marketing"),
        ("USER", "We're a B2B SaaS company, struggling with lead generation"),
        ("USER", "We've tried content marketing and LinkedIn outreach but engagement is low and leads aren't qualified"),
        ("USER", "yes, that's right - proceed"),
    ]

    for role, message in conversation:
        print(f"\n{'='*40}")
        print(f"💬 {role}: {message}")
        print(f"{'='*40}")

        result = await refiner.process(session_id, message)

        print(f"\n🤖 ASSISTANT: {result['response']}")
        print(f"\n📊 State: {result['state']} | Confidence: {result['understanding']['confidence']:.0%}")

        if result.get('final_prompt'):
            print("\n" + "=" * 80)
            print("✨ FINAL SYNTHESIZED PROMPT")
            print("=" * 80)
            print()
            print(result['final_prompt'])
            print()
            print("=" * 80)
            print("Notice how this prompt:")
            print("• Reads like a human expert wrote it")
            print("• Sets a specific persona (B2B growth strategist)")
            print("• Weaves in ALL the context naturally")
            print("• NO template sections or mechanical bullet points")
            print("• Feels like a thoughtful brief, not a filled form")
            print("=" * 80)
            break

    print(f"\n📈 Total LLM calls: {mock_llm.call_count}")


if __name__ == "__main__":
    asyncio.run(run_demo())
