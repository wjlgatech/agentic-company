"""
Get the final synthesized prompt from Real Claude.
"""

import os
import sys
import asyncio

sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

import anthropic
import httpx
from orchestration.tools.smart_refiner import SmartRefiner


class RealClaude:
    def __init__(self):
        http_client = httpx.AsyncClient(verify=False)
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)
        self.calls = 0

    async def __call__(self, system: str, user: str) -> str:
        self.calls += 1
        print(f"  [API #{self.calls}]", end=" ", flush=True)
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        print("✓")
        return response.content[0].text


async def get_final_prompt():
    print("=" * 70)
    print("GETTING FINAL SYNTHESIZED PROMPT FROM REAL CLAUDE")
    print("=" * 70)

    claude = RealClaude()
    refiner = SmartRefiner(llm_call=claude, max_questions=4)
    session_id = refiner.create_session()

    # Fast-track through conversation
    inputs = [
        "I need help with my marketing",
        "B2B SaaS security monitoring tool. Content marketing has low engagement.",
        "IT directors at mid-size companies. Weekly blogs, LinkedIn posts.",
        "Yes, proceed with creating the prompt"
    ]

    for i, msg in enumerate(inputs):
        print(f"\n[Turn {i+1}] {msg[:50]}...")
        result = await refiner.process(session_id, msg)
        print(f"  State: {result['state']} | Confidence: {result['understanding']['confidence']*100:.0f}%")

        if result.get('final_prompt'):
            print("\n" + "=" * 70)
            print("✨ FINAL SYNTHESIZED PROMPT")
            print("=" * 70)
            print(result['final_prompt'])
            print("=" * 70)
            print(f"\n📈 Total API calls: {claude.calls}")
            return

        if result['state'] == 'complete':
            break

    # One more turn to complete
    print("\n[Confirming to get final prompt]")
    result = await refiner.process(session_id, "Yes, create the prompt now")
    print(f"  State: {result['state']}")

    if result.get('final_prompt'):
        print("\n" + "=" * 70)
        print("✨ FINAL SYNTHESIZED PROMPT")
        print("=" * 70)
        print(result['final_prompt'])
        print("=" * 70)

    print(f"\n📈 Total API calls: {claude.calls}")


if __name__ == "__main__":
    asyncio.run(get_final_prompt())
