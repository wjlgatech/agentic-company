#!/usr/bin/env python3
"""
Run comprehensive evaluation on diversified test cases.
Generates detailed CSV with domain-level analysis.
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.tools.intent_refiner import refine_intent
from experiments.diversified_test_cases import ALL_TEST_CASES, get_summary


def count_input_issues(input_text: str) -> dict:
    """Analyze issues in the input."""
    issues = {
        "word_count": len(input_text.split()) if input_text else 0,
        "vague_words": 0,
        "missing_specifics": 0,
    }

    if not input_text:
        issues["missing_specifics"] = 5
        return issues

    text_lower = input_text.lower()
    vague_words = ["something", "stuff", "thing", "help", "better", "good", "it", "this", "that"]
    issues["vague_words"] = sum(1 for w in vague_words if w in text_lower.split())

    # Check missing specifics
    if not any(w in text_lower for w in ["want", "need", "goal", "create", "build", "analyze"]):
        issues["missing_specifics"] += 1
    if not any(w in text_lower for w in ["for", "to", "audience", "client", "user"]):
        issues["missing_specifics"] += 1

    return issues


def evaluate_output(result: dict) -> dict:
    """Evaluate the quality of refinement output."""
    eval_result = {
        "has_classification": bool(result.get("classification")),
        "has_questions": bool(result.get("questions")),
        "has_model": bool(result.get("model")),
        "has_prompt": bool(result.get("prompt")),
        "confidence": 0,
        "num_questions": 0,
        "prompt_length": 0,
        "prompt_sections": 0,
        "score": 0,
    }

    classification = result.get("classification", {})
    if classification:
        eval_result["confidence"] = classification.get("confidence", 0)
        eval_result["task_type"] = classification.get("task_type", "unknown")
        eval_result["detected_domain"] = classification.get("domain", "unknown")

    questions = result.get("questions", [])
    eval_result["num_questions"] = len(questions)

    prompt = result.get("prompt", "")
    eval_result["prompt_length"] = len(prompt)

    # Count sections in prompt
    sections = ["context", "task", "approach", "output", "success", "guardrail", "role"]
    eval_result["prompt_sections"] = sum(1 for s in sections if s in prompt.lower())

    # Calculate score
    score = 0
    if eval_result["has_classification"]: score += 1
    if eval_result["has_questions"]: score += 1
    if eval_result["has_model"]: score += 1
    if eval_result["has_prompt"]: score += 1
    if eval_result["prompt_sections"] >= 4: score += 1
    eval_result["score"] = score

    return eval_result


def run_evaluation():
    """Run evaluation on all test cases."""

    print("="*70)
    print("DIVERSIFIED INTENT REFINER EVALUATION")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Total test cases: {len(ALL_TEST_CASES)}")
    print()

    results = []
    domain_stats = {}

    for i, case in enumerate(ALL_TEST_CASES):
        # Progress indicator
        if (i + 1) % 20 == 0 or i == 0:
            print(f"Processing {i+1}/{len(ALL_TEST_CASES)}...")

        try:
            # Run refiner
            result = refine_intent(case.input_text)

            # Analyze input
            input_issues = count_input_issues(case.input_text)

            # Evaluate output
            eval_result = evaluate_output(result)

            # Calculate expansion ratio
            input_words = input_issues["word_count"]
            prompt_words = len(result.get("prompt", "").split())
            expansion_ratio = prompt_words / max(input_words, 1)

            # Build row
            row = {
                "ID": case.id,
                "Domain": case.domain,
                "Subdomain": case.subdomain,
                "Description": case.description,

                # Input Analysis
                "Input_X": case.input_text[:200] + ("..." if len(case.input_text) > 200 else ""),
                "Input_Words": input_words,
                "Input_Vague_Words": input_issues["vague_words"],
                "Input_Missing_Specifics": input_issues["missing_specifics"],

                # Process Analysis
                "Detected_Task_Type": eval_result.get("task_type", "unknown"),
                "Detected_Domain": eval_result.get("detected_domain", "unknown"),
                "Confidence": f"{eval_result['confidence']:.0%}",
                "Questions_Generated": eval_result["num_questions"],

                # Output Analysis
                "Output_Y_Prompt": result.get("prompt", "")[:500] + "...",
                "Prompt_Words": prompt_words,
                "Prompt_Sections": eval_result["prompt_sections"],
                "Has_Visual_Model": "Yes" if result.get("model", {}).get("ascii") else "No",

                # Evaluation
                "Expansion_Ratio": f"{expansion_ratio:.1f}x",
                "Score": f"{eval_result['score']}/5",

                # Status
                "Status": "SUCCESS",
            }

            # Track domain stats
            if case.domain not in domain_stats:
                domain_stats[case.domain] = {"total": 0, "scores": [], "expansions": []}
            domain_stats[case.domain]["total"] += 1
            domain_stats[case.domain]["scores"].append(eval_result["score"])
            domain_stats[case.domain]["expansions"].append(expansion_ratio)

        except Exception as e:
            row = {
                "ID": case.id,
                "Domain": case.domain,
                "Subdomain": case.subdomain,
                "Description": case.description,
                "Input_X": case.input_text[:200],
                "Input_Words": len(case.input_text.split()) if case.input_text else 0,
                "Input_Vague_Words": 0,
                "Input_Missing_Specifics": 0,
                "Detected_Task_Type": "ERROR",
                "Detected_Domain": "ERROR",
                "Confidence": "0%",
                "Questions_Generated": 0,
                "Output_Y_Prompt": f"ERROR: {str(e)[:100]}",
                "Prompt_Words": 0,
                "Prompt_Sections": 0,
                "Has_Visual_Model": "No",
                "Expansion_Ratio": "0x",
                "Score": "0/5",
                "Status": "ERROR",
            }

        results.append(row)

    return results, domain_stats


def generate_csv(results: list, output_path: Path):
    """Write results to CSV."""
    fieldnames = list(results[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✅ CSV saved to: {output_path}")


def print_domain_summary(domain_stats: dict):
    """Print summary by domain."""
    print("\n" + "="*70)
    print("📊 SUMMARY BY DOMAIN")
    print("="*70)

    print(f"\n{'Domain':<20} {'Cases':>8} {'Avg Score':>12} {'Avg Expansion':>15}")
    print("-"*60)

    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        avg_score = sum(stats["scores"]) / len(stats["scores"])
        avg_expansion = sum(stats["expansions"]) / len(stats["expansions"])
        print(f"{domain:<20} {stats['total']:>8} {avg_score:>10.1f}/5 {avg_expansion:>13.1f}x")

    # Overall
    all_scores = [s for d in domain_stats.values() for s in d["scores"]]
    all_expansions = [e for d in domain_stats.values() for e in d["expansions"]]
    print("-"*60)
    print(f"{'OVERALL':<20} {len(all_scores):>8} {sum(all_scores)/len(all_scores):>10.1f}/5 {sum(all_expansions)/len(all_expansions):>13.1f}x")


def print_wow_examples(results: list):
    """Print standout before/after examples."""
    print("\n" + "="*70)
    print("🌟 WOW EXAMPLES BY DOMAIN")
    print("="*70)

    # Group by domain and pick best example from each
    domains = {}
    for r in results:
        if r["Status"] == "SUCCESS":
            d = r["Domain"]
            if d not in domains:
                domains[d] = r
            elif r["Score"] > domains[d]["Score"]:
                domains[d] = r

    for domain in ["Science", "Business", "Finance", "Technology", "Health"]:
        if domain in domains:
            r = domains[domain]
            print(f"\n{'─'*70}")
            print(f"📋 {domain} | {r['Subdomain']} | {r['Description']}")
            print(f"{'─'*70}")
            print(f"📥 BEFORE: \"{r['Input_X'][:60]}...\" ({r['Input_Words']} words)")
            print(f"📤 AFTER: {r['Prompt_Words']} words | {r['Prompt_Sections']} sections | {r['Expansion_Ratio']} expansion")
            print(f"⭐ Score: {r['Score']} | Confidence: {r['Confidence']}")


if __name__ == "__main__":
    # Run evaluation
    results, domain_stats = run_evaluation()

    # Save CSV
    output_path = Path(__file__).parent / "diversified_evaluation_results.csv"
    generate_csv(results, output_path)

    # Print summaries
    print_domain_summary(domain_stats)
    print_wow_examples(results)

    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)
