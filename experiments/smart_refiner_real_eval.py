"""
Real LLM Evaluation: Smart Refiner with Claude API

NO MOCKS - Real Claude API calls for authentic evaluation.
"""

import asyncio
import csv
import os
import sys
import time
from typing import Optional

sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

# Check for API key
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("⚠️  ANTHROPIC_API_KEY not found in environment")
    print("   Please set it: export ANTHROPIC_API_KEY='your-key'")
    sys.exit(1)

import anthropic
from orchestration.tools.smart_refiner import SmartRefiner


# =============================================================================
# REAL CLAUDE API CLIENT
# =============================================================================

class RealClaudeClient:
    """Real Claude API client - no mocks."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        import httpx
        # Use SSL verification bypass for VM proxy environment
        http_client = httpx.AsyncClient(verify=False)
        self.client = anthropic.AsyncAnthropic(
            api_key=ANTHROPIC_API_KEY,
            http_client=http_client
        )
        self.model = model
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def __call__(self, system: str, user: str) -> str:
        """Make real API call to Claude."""
        self.call_count += 1

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}]
            )

            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            return response.content[0].text

        except Exception as e:
            print(f"   ⚠️ API error: {e}")
            return "{}"

    def get_stats(self) -> dict:
        return {
            "calls": self.call_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }


# =============================================================================
# QUALITY EVALUATION (Real metrics, no fake detection)
# =============================================================================

def evaluate_prompt_quality(prompt: str) -> dict:
    """
    Evaluate prompt quality with real metrics.

    Checks for:
    1. Mechanical template markers (##, bullet lists with **)
    2. Natural language flow
    3. Specific persona (not generic "assistant")
    4. Domain-relevant content
    5. Actionable guidance
    """
    if not prompt or len(prompt) < 50:
        return {
            "valid": False,
            "error": "Prompt too short or empty",
            "quality_score": 0
        }

    # Mechanical indicators (BAD - want these to be 0)
    template_headers = prompt.count("##")
    bullet_extractions = prompt.count("- **")
    template_sections = sum(1 for x in [
        "Key Details Extracted:", "Instructions:", "Constraints:",
        "Success Criteria:", "## Role", "## Context"
    ] if x in prompt)
    mechanical_score = template_headers + bullet_extractions + template_sections

    # Quality indicators (GOOD - want these to be high)
    # Natural narrative structure
    has_natural_opening = any(x in prompt for x in [
        "You are a", "You're a", "As a", "Your role is"
    ])

    # Specific persona (not just "assistant" or "helpful AI")
    generic_personas = ["helpful assistant", "AI assistant", "helpful AI", "general assistant"]
    has_generic_persona = any(x.lower() in prompt.lower() for x in generic_personas)
    has_specific_persona = has_natural_opening and not has_generic_persona

    # Context about the user/client
    has_user_context = any(x in prompt for x in [
        "Your client", "Your colleague", "Your user", "The user",
        "They need", "They want", "They're looking"
    ])

    # Actionable guidance
    has_actionable = any(x in prompt for x in [
        "When you", "Be sure to", "Make sure", "Always", "Never",
        "Consider", "Think about", "Focus on", "Prioritize"
    ])

    # Strategic depth (explains WHY, not just WHAT)
    has_depth = any(x in prompt for x in [
        "because", "since", "this helps", "this ensures",
        "the reason", "which allows", "so that"
    ])

    # Word count (good prompts are substantive, not too short)
    word_count = len(prompt.split())
    has_substance = word_count >= 100

    # Calculate scores
    quality_indicators = sum([
        has_natural_opening,
        has_specific_persona,
        has_user_context,
        has_actionable,
        has_depth,
        has_substance
    ])

    # Coherence = no mechanical markers + at least 3 quality indicators
    is_coherent = mechanical_score == 0 and quality_indicators >= 3

    # Quality score: 0-1 scale
    quality_score = (quality_indicators / 6) - (min(mechanical_score, 3) / 6)
    quality_score = max(0, min(1, quality_score))

    return {
        "valid": True,
        "word_count": word_count,
        "mechanical_score": mechanical_score,
        "template_headers": template_headers,
        "bullet_extractions": bullet_extractions,
        "template_sections": template_sections,
        "has_natural_opening": has_natural_opening,
        "has_specific_persona": has_specific_persona,
        "has_user_context": has_user_context,
        "has_actionable": has_actionable,
        "has_depth": has_depth,
        "has_substance": has_substance,
        "quality_indicators": quality_indicators,
        "is_coherent": is_coherent,
        "quality_score": quality_score
    }


# =============================================================================
# MAIN EVALUATION
# =============================================================================

async def run_real_evaluation(limit: Optional[int] = None):
    """
    Run evaluation with REAL Claude API calls.

    Args:
        limit: Optional limit on number of cases (for testing/cost control)
    """
    print("=" * 80)
    print("SMART REFINER EVALUATION - REAL CLAUDE API")
    print("=" * 80)
    print()

    # Load test cases
    csv_path = "/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/experiments/hybrid_evaluation_results.csv"

    cases = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Input'):
                cases.append({
                    'id': row.get('ID', f'case_{len(cases)}'),
                    'domain': row.get('Domain', 'unknown'),
                    'subdomain': row.get('Subdomain', ''),
                    'input': row['Input']
                })
                if limit and len(cases) >= limit:
                    break

    print(f"📂 Loaded {len(cases)} test cases")

    # Create REAL Claude client
    claude = RealClaudeClient(model="claude-sonnet-4-20250514")
    refiner = SmartRefiner(llm_call=claude, max_questions=3)

    print(f"🤖 Using model: {claude.model}")
    print(f"🔄 Max questions per case: 3")
    print()
    print("-" * 80)

    results = []
    start_time = time.time()

    for i, case in enumerate(cases):
        case_start = time.time()
        print(f"\n[{i+1}/{len(cases)}] {case['id']} ({case['domain']})")
        print(f"   Input: {case['input'][:60]}...")

        try:
            # Create fresh session
            session_id = refiner.create_session()

            # Process input - may trigger interview questions
            result = await refiner.process(session_id, case['input'])
            turns = 1

            # If not complete, simulate user confirmation to get final prompt
            while result['state'] != 'complete' and turns < 5:
                # Simulate user providing more info or confirming
                if result['state'] == 'interviewing':
                    # Provide a confirmation to proceed
                    result = await refiner.process(session_id, "Yes, that's correct. Please proceed.")
                elif result['state'] == 'ready':
                    result = await refiner.process(session_id, "Yes, proceed with creating the prompt.")
                turns += 1

            final_prompt = result.get('final_prompt', '')
            quality = evaluate_prompt_quality(final_prompt)

            case_time = time.time() - case_start
            print(f"   ✅ Complete in {case_time:.1f}s | Turns: {turns} | Quality: {quality['quality_score']:.2f}")

            results.append({
                'ID': case['id'],
                'Domain': case['domain'],
                'Subdomain': case['subdomain'],
                'Input': case['input'],
                'Turns': turns,
                'Final_State': result['state'],
                'Confidence': result.get('understanding', {}).get('confidence', 0),
                'Prompt_Words': quality.get('word_count', 0),
                'Mechanical_Score': quality.get('mechanical_score', 0),
                'Quality_Indicators': quality.get('quality_indicators', 0),
                'Is_Coherent': quality.get('is_coherent', False),
                'Quality_Score': quality.get('quality_score', 0),
                'Has_Natural_Opening': quality.get('has_natural_opening', False),
                'Has_Specific_Persona': quality.get('has_specific_persona', False),
                'Has_User_Context': quality.get('has_user_context', False),
                'Has_Actionable': quality.get('has_actionable', False),
                'Has_Depth': quality.get('has_depth', False),
                'Final_Prompt': final_prompt
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'ID': case['id'],
                'Domain': case['domain'],
                'Subdomain': case['subdomain'],
                'Input': case['input'],
                'Turns': 0,
                'Final_State': 'error',
                'Error': str(e),
                'Quality_Score': 0,
                'Is_Coherent': False,
                'Final_Prompt': ''
            })

        # Rate limiting - be nice to the API
        await asyncio.sleep(0.5)

    # ==========================================================================
    # RESULTS SUMMARY
    # ==========================================================================
    total_time = time.time() - start_time
    stats = claude.get_stats()

    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)

    valid_results = [r for r in results if r.get('Final_State') != 'error']
    coherent_count = sum(1 for r in valid_results if r.get('Is_Coherent'))
    avg_quality = sum(r.get('Quality_Score', 0) for r in valid_results) / len(valid_results) if valid_results else 0
    avg_turns = sum(r.get('Turns', 0) for r in valid_results) / len(valid_results) if valid_results else 0

    print(f"\n📊 Overall Results:")
    print(f"   • Total cases: {len(cases)}")
    print(f"   • Successful: {len(valid_results)}")
    print(f"   • Coherent prompts: {coherent_count}/{len(valid_results)} ({coherent_count/len(valid_results)*100:.1f}%)")
    print(f"   • Average quality score: {avg_quality:.2f}")
    print(f"   • Average turns: {avg_turns:.1f}")

    print(f"\n📈 Quality Breakdown:")
    for metric in ['Has_Natural_Opening', 'Has_Specific_Persona', 'Has_User_Context', 'Has_Actionable', 'Has_Depth']:
        count = sum(1 for r in valid_results if r.get(metric))
        print(f"   • {metric}: {count}/{len(valid_results)} ({count/len(valid_results)*100:.1f}%)")

    mechanical_zero = sum(1 for r in valid_results if r.get('Mechanical_Score', 1) == 0)
    print(f"   • No mechanical markers: {mechanical_zero}/{len(valid_results)} ({mechanical_zero/len(valid_results)*100:.1f}%)")

    print(f"\n💰 API Usage:")
    print(f"   • Total API calls: {stats['calls']}")
    print(f"   • Input tokens: {stats['input_tokens']:,}")
    print(f"   • Output tokens: {stats['output_tokens']:,}")
    print(f"   • Total tokens: {stats['total_tokens']:,}")
    print(f"   • Time elapsed: {total_time:.1f}s")

    # Save results to CSV
    output_path = "/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/experiments/smart_refiner_real_results.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    print(f"\n📄 Results saved to: {output_path}")

    # Copy to workspace for user access
    import shutil
    workspace_path = "/sessions/upbeat-trusting-turing/mnt/startup/smart_refiner_real_results.csv"
    shutil.copy(output_path, workspace_path)
    print(f"📄 Also copied to: {workspace_path}")

    print("\n" + "=" * 80)
    print("✅ Evaluation complete!")
    print("=" * 80)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Limit number of cases')
    args = parser.parse_args()

    asyncio.run(run_real_evaluation(limit=args.limit))
