"""
Test Real LLM Integration - Complete Conversation Flow

NO MOCKS - Real Claude API calls.
"""

import os
import sys
import asyncio

sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("Set ANTHROPIC_API_KEY first!")
    sys.exit(1)

import anthropic
import httpx
from orchestration.tools.smart_refiner import SmartRefiner


class RealClaude:
    """Real Claude API - NO MOCKS."""

    def __init__(self):
        http_client = httpx.AsyncClient(verify=False)
        self.client = anthropic.AsyncAnthropic(
            api_key=ANTHROPIC_API_KEY,
            http_client=http_client
        )
        self.calls = 0

    async def __call__(self, system: str, user: str) -> str:
        self.calls += 1
        print(f"  [API Call #{self.calls}]")

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return response.content[0].text


async def test_real_conversation():
    """Run a real multi-turn conversation."""

    print("=" * 70)
    print("REAL LLM CONVERSATION TEST")
    print("Using actual Claude API - NO MOCKS")
    print("=" * 70)

    claude = RealClaude()
    refiner = SmartRefiner(llm_call=claude, max_questions=4)
    session_id = refiner.create_session()

    # Conversation turns
    conversation = [
        "I need help with my marketing",
        "We're a B2B SaaS company, our product is a security monitoring tool. We've been trying content marketing but engagement is really low.",
        "Our target audience is IT directors at mid-size companies. We post weekly blog articles and some LinkedIn posts.",
        "Yes, that captures it well. Please proceed."
    ]

    for i, user_input in enumerate(conversation):
        print(f"\n{'='*70}")
        print(f"TURN {i+1}")
        print(f"{'='*70}")
        print(f"\n👤 USER: {user_input}")

        result = await refiner.process(session_id, user_input)

        print(f"\n🤖 ASSISTANT: {result['response']}")
        print(f"\n📊 State: {result['state']} | Confidence: {result['understanding']['confidence']*100:.0f}%")

        if result.get('final_prompt'):
            print(f"\n{'='*70}")
            print("✨ FINAL SYNTHESIZED PROMPT (Real Claude Output)")
            print("="*70)
            print(result['final_prompt'])
            print("="*70)
            break

        # If complete, stop
        if result['state'] == 'complete':
            break

    print(f"\n📈 Total API calls: {claude.calls}")


if __name__ == "__main__":
    asyncio.run(test_real_conversation())
