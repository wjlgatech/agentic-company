"""
Real LLM Evaluation: Smart Refiner with Claude API
Sampled across domains for cost-effective testing.

NO MOCKS - Real Claude API calls.
"""

import asyncio
import csv
import os
import sys
import time
import random
from collections import defaultdict

sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("⚠️  ANTHROPIC_API_KEY not set")
    sys.exit(1)

import anthropic
import httpx
from orchestration.tools.smart_refiner import SmartRefiner


class RealClaudeClient:
    """Real Claude API client."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
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


def evaluate_prompt_quality(prompt: str) -> dict:
    """Evaluate prompt quality."""
    if not prompt or len(prompt) < 50:
        return {"valid": False, "quality_score": 0}

    # Mechanical indicators (BAD)
    template_headers = prompt.count("##")
    bullet_extractions = prompt.count("- **")
    template_sections = sum(1 for x in [
        "Key Details Extracted:", "Instructions:", "Constraints:",
        "Success Criteria:", "## Role", "## Context"
    ] if x in prompt)
    mechanical_score = template_headers + bullet_extractions + template_sections

    # Quality indicators (GOOD)
    has_natural_opening = any(x in prompt for x in ["You are a", "You're a", "As a"])
    generic_personas = ["helpful assistant", "AI assistant", "helpful AI"]
    has_generic_persona = any(x.lower() in prompt.lower() for x in generic_personas)
    has_specific_persona = has_natural_opening and not has_generic_persona
    has_user_context = any(x in prompt for x in [
        "Your client", "Your colleague", "Your user", "The user",
        "They need", "They want", "They're looking"
    ])
    has_actionable = any(x in prompt for x in [
        "When you", "Be sure to", "Make sure", "Always", "Never",
        "Consider", "Think about", "Focus on"
    ])
    has_depth = any(x in prompt for x in [
        "because", "since", "this helps", "this ensures", "the reason", "which allows"
    ])
    word_count = len(prompt.split())
    has_substance = word_count >= 100

    quality_indicators = sum([
        has_natural_opening, has_specific_persona, has_user_context,
        has_actionable, has_depth, has_substance
    ])
    is_coherent = mechanical_score == 0 and quality_indicators >= 3
    quality_score = max(0, min(1, (quality_indicators / 6) - (min(mechanical_score, 3) / 6)))

    return {
        "valid": True,
        "word_count": word_count,
        "mechanical_score": mechanical_score,
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


def sample_cases_by_domain(cases: list, samples_per_domain: int = 3) -> list:
    """Sample cases evenly across domains."""
    by_domain = defaultdict(list)
    for case in cases:
        by_domain[case['domain']].append(case)

    sampled = []
    for domain, domain_cases in by_domain.items():
        random.seed(42)  # Reproducible
        n = min(samples_per_domain, len(domain_cases))
        sampled.extend(random.sample(domain_cases, n))

    return sampled


async def run_sampled_evaluation(samples_per_domain: int = 3):
    """Run evaluation with stratified sampling across domains."""
    print("=" * 80)
    print("SMART REFINER - REAL CLAUDE API EVALUATION")
    print("(Stratified sampling across domains)")
    print("=" * 80)

    # Load all cases
    csv_path = "/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/experiments/hybrid_evaluation_results.csv"
    all_cases = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Input'):
                all_cases.append({
                    'id': row.get('ID', f'case_{len(all_cases)}'),
                    'domain': row.get('Domain', 'unknown'),
                    'subdomain': row.get('Subdomain', ''),
                    'input': row['Input']
                })

    # Sample across domains
    cases = sample_cases_by_domain(all_cases, samples_per_domain)
    print(f"📂 Sampled {len(cases)} cases from {len(set(c['domain'] for c in all_cases))} domains")
    print(f"   ({samples_per_domain} per domain)")

    # Create client
    claude = RealClaudeClient()
    refiner = SmartRefiner(llm_call=claude, max_questions=3)
    print(f"🤖 Model: {claude.model}")
    print("-" * 80)

    results = []
    start_time = time.time()

    for i, case in enumerate(cases):
        print(f"\n[{i+1}/{len(cases)}] {case['id']} ({case['domain']})")
        print(f"   Input: {case['input'][:60]}...")

        try:
            session_id = refiner.create_session()
            result = await refiner.process(session_id, case['input'])
            turns = 1

            while result['state'] != 'complete' and turns < 5:
                if result['state'] == 'interviewing':
                    result = await refiner.process(session_id, "Yes, that's correct. Please proceed.")
                elif result['state'] == 'ready':
                    result = await refiner.process(session_id, "Yes, proceed.")
                turns += 1

            final_prompt = result.get('final_prompt', '')
            quality = evaluate_prompt_quality(final_prompt)
            print(f"   ✅ Turns: {turns} | Quality: {quality['quality_score']:.2f} | Words: {quality.get('word_count', 0)}")

            results.append({
                'ID': case['id'],
                'Domain': case['domain'],
                'Subdomain': case['subdomain'],
                'Input': case['input'],
                'Turns': turns,
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
                'ID': case['id'], 'Domain': case['domain'], 'Error': str(e),
                'Quality_Score': 0, 'Is_Coherent': False
            })

        await asyncio.sleep(0.3)

    # Summary
    total_time = time.time() - start_time
    stats = claude.get_stats()

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    valid_results = [r for r in results if r.get('Quality_Score', 0) > 0]
    coherent = sum(1 for r in valid_results if r.get('Is_Coherent'))
    avg_quality = sum(r['Quality_Score'] for r in valid_results) / len(valid_results) if valid_results else 0

    print(f"\n📊 Overall:")
    print(f"   • Cases evaluated: {len(cases)}")
    print(f"   • Coherent: {coherent}/{len(valid_results)} ({coherent/len(valid_results)*100:.1f}%)")
    print(f"   • Avg quality: {avg_quality:.2f}")

    print(f"\n📈 Quality Breakdown:")
    for m in ['Has_Natural_Opening', 'Has_Specific_Persona', 'Has_User_Context', 'Has_Actionable', 'Has_Depth']:
        c = sum(1 for r in valid_results if r.get(m))
        print(f"   • {m}: {c}/{len(valid_results)} ({c/len(valid_results)*100:.1f}%)")

    print(f"\n📁 By Domain:")
    domain_stats = defaultdict(lambda: {'count': 0, 'quality': 0, 'coherent': 0})
    for r in valid_results:
        d = r['Domain']
        domain_stats[d]['count'] += 1
        domain_stats[d]['quality'] += r['Quality_Score']
        if r['Is_Coherent']:
            domain_stats[d]['coherent'] += 1

    for domain, s in sorted(domain_stats.items(), key=lambda x: -x[1]['count']):
        avg = s['quality'] / s['count']
        coh_pct = s['coherent'] / s['count'] * 100
        print(f"   • {domain}: {s['count']} cases, {coh_pct:.0f}% coherent, {avg:.2f} quality")

    print(f"\n💰 API Usage:")
    print(f"   • Calls: {stats['calls']}")
    print(f"   • Tokens: {stats['total_tokens']:,}")
    print(f"   • Time: {total_time:.1f}s")

    # Save
    output_path = "/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/experiments/smart_refiner_real_results.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    import shutil
    workspace_path = "/sessions/upbeat-trusting-turing/mnt/startup/smart_refiner_real_results.csv"
    shutil.copy(output_path, workspace_path)
    print(f"\n📄 Results: {workspace_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=3, help='Samples per domain')
    args = parser.parse_args()
    asyncio.run(run_sampled_evaluation(samples_per_domain=args.samples))
