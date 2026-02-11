#!/usr/bin/env python3
"""
Intent Refiner Evaluation Experiment

Tests the Progressive Intent Refinement (PIR) framework with:
- 10 common real-life cases (vague user inputs from different domains)
- 7 tough edge cases (adversarial, ambiguous, multi-intent inputs)

Outputs: CSV spreadsheet with before/after analysis
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.tools.intent_refiner import (
    IntentRefiner,
    refine_intent,
    TaskType,
    Complexity,
    Domain,
)


@dataclass
class TestCase:
    """A test case for the Intent Refiner."""
    id: str
    category: str  # "real_life" or "edge_case"
    input_text: str
    description: str
    expected_challenges: list[str]


# ============================================================================
# TEST CASES: Real-Life Scenarios (10 cases)
# ============================================================================
REAL_LIFE_CASES = [
    TestCase(
        id="RL01",
        category="real_life",
        input_text="help me with my marketing",
        description="Extremely vague business request",
        expected_challenges=["No specifics", "No audience", "No goals", "No timeline"]
    ),
    TestCase(
        id="RL02",
        category="real_life",
        input_text="I need to analyze some data",
        description="Generic data analysis request",
        expected_challenges=["Unknown data type", "No analysis goals", "No format specified"]
    ),
    TestCase(
        id="RL03",
        category="real_life",
        input_text="write something for my boss about the project",
        description="Vague writing request with implicit audience",
        expected_challenges=["Unknown document type", "Unknown project", "Tone unclear"]
    ),
    TestCase(
        id="RL04",
        category="real_life",
        input_text="my app is slow, fix it",
        description="Technical complaint without details",
        expected_challenges=["Unknown tech stack", "No metrics", "No context on 'slow'"]
    ),
    TestCase(
        id="RL05",
        category="real_life",
        input_text="prepare me for my interview tomorrow",
        description="Urgent request lacking context",
        expected_challenges=["Unknown role", "Unknown company", "Unknown format"]
    ),
    TestCase(
        id="RL06",
        category="real_life",
        input_text="i want to learn programming",
        description="Broad learning goal",
        expected_challenges=["No language specified", "No purpose", "No level indicated"]
    ),
    TestCase(
        id="RL07",
        category="real_life",
        input_text="make my resume better",
        description="Improvement request without baseline",
        expected_challenges=["No current resume", "No target role", "No industry context"]
    ),
    TestCase(
        id="RL08",
        category="real_life",
        input_text="help me decide if i should take this job offer",
        description="Personal decision request",
        expected_challenges=["No offer details", "No current situation", "No criteria"]
    ),
    TestCase(
        id="RL09",
        category="real_life",
        input_text="create a presentation about AI",
        description="Content creation with broad topic",
        expected_challenges=["No audience", "No length", "No angle/focus"]
    ),
    TestCase(
        id="RL10",
        category="real_life",
        input_text="my team isn't performing well, what should i do",
        description="Management challenge without context",
        expected_challenges=["No team details", "No metrics", "No attempted solutions"]
    ),
]

# ============================================================================
# TEST CASES: Edge Cases (7 cases)
# ============================================================================
EDGE_CASES = [
    TestCase(
        id="EC01",
        category="edge_case",
        input_text="",
        description="Empty input",
        expected_challenges=["Completely empty", "No intent possible"]
    ),
    TestCase(
        id="EC02",
        category="edge_case",
        input_text="asdfghjkl qwerty zxcvbnm",
        description="Gibberish/keyboard mashing",
        expected_challenges=["No semantic meaning", "Cannot classify"]
    ),
    TestCase(
        id="EC03",
        category="edge_case",
        input_text="I want to write code and also analyze sales data and maybe create some marketing content and plan a product launch and review legal documents",
        description="Multi-intent overload (5+ intents in one)",
        expected_challenges=["Too many intents", "Conflicting domains", "Priority unclear"]
    ),
    TestCase(
        id="EC04",
        category="edge_case",
        input_text="do the thing with the stuff for the person",
        description="Maximally vague (all pronouns, no nouns)",
        expected_challenges=["No concrete nouns", "Zero context", "Impossible to infer"]
    ),
    TestCase(
        id="EC05",
        category="edge_case",
        input_text="DON'T help me with anything, I just want to complain that AI is ruining everything and you're all terrible",
        description="Adversarial/hostile input",
        expected_challenges=["Negative intent", "No actionable request", "Emotional content"]
    ),
    TestCase(
        id="EC06",
        category="edge_case",
        input_text="私のビジネスを助けてください。我想要分析数据。Помогите мне с проектом.",
        description="Multi-language input (Japanese, Chinese, Russian)",
        expected_challenges=["Language detection", "Translation needs", "Cultural context"]
    ),
    TestCase(
        id="EC07",
        category="edge_case",
        input_text="I need help with something but I can't tell you what it is because it's confidential but it's really important and urgent!!!",
        description="Contradictory constraints (needs help but can't share details)",
        expected_challenges=["Confidentiality conflict", "Urgency without context", "Impossible to assist"]
    ),
]


def evaluate_output(result: dict, test_case: TestCase) -> dict:
    """Evaluate the quality of the Intent Refiner output."""

    evaluation = {
        "classification_quality": "GOOD",
        "questions_quality": "GOOD",
        "model_quality": "GOOD",
        "prompt_quality": "GOOD",
        "overall_score": 5,
        "issues": [],
        "strengths": [],
    }

    classification = result.get("classification", {})
    questions = result.get("questions", [])
    model = result.get("model", {})
    prompt = result.get("prompt", "")

    # 1. Evaluate Classification (dict format)
    if classification:
        confidence = classification.get("confidence", 0)
        if confidence > 0.7:
            evaluation["strengths"].append(f"High confidence classification ({confidence:.0%})")
        elif confidence < 0.3:
            evaluation["classification_quality"] = "WEAK"
            evaluation["issues"].append(f"Low confidence ({confidence:.0%})")
            evaluation["overall_score"] -= 1
        else:
            evaluation["strengths"].append(f"Moderate confidence ({confidence:.0%})")
    else:
        evaluation["classification_quality"] = "FAILED"
        evaluation["issues"].append("No classification produced")
        evaluation["overall_score"] -= 2

    # 2. Evaluate Questions (list of dicts)
    if questions:
        num_questions = len(questions)
        if 2 <= num_questions <= 5:
            evaluation["strengths"].append(f"Good number of clarifying questions ({num_questions})")
        elif num_questions > 5:
            evaluation["questions_quality"] = "EXCESSIVE"
            evaluation["issues"].append(f"Too many questions ({num_questions}) - may overwhelm user")
            evaluation["overall_score"] -= 1
        else:
            evaluation["strengths"].append(f"Generated {num_questions} clarifying question(s)")

        # Check question quality (dict format)
        high_priority = sum(1 for q in questions if q.get("priority") == "high")
        if high_priority >= 1:
            evaluation["strengths"].append(f"Identified {high_priority} high-priority questions")
    else:
        evaluation["questions_quality"] = "NONE"
        evaluation["issues"].append("No clarifying questions generated")
        evaluation["overall_score"] -= 1

    # 3. Evaluate Model (dict format with ascii/mermaid)
    if model:
        ascii_diagram = model.get("ascii", "")
        mermaid = model.get("mermaid", "")

        if ascii_diagram or mermaid:
            evaluation["strengths"].append("Visual mental model generated")
            if "INPUTS" in ascii_diagram and "OUTPUTS" in ascii_diagram:
                evaluation["strengths"].append("Model has clear I/O structure")
            if "ASSUMPTIONS" in ascii_diagram:
                evaluation["strengths"].append("Assumptions made explicit")
            if "PROCESS" in ascii_diagram:
                evaluation["strengths"].append("Process flow documented")
        else:
            evaluation["model_quality"] = "INCOMPLETE"
            evaluation["issues"].append("No visual model generated")
            evaluation["overall_score"] -= 1
    else:
        evaluation["model_quality"] = "FAILED"
        evaluation["issues"].append("No mental model produced")
        evaluation["overall_score"] -= 2

    # 4. Evaluate Prompt
    if prompt:
        prompt_len = len(prompt)
        if prompt_len > 200:
            evaluation["strengths"].append(f"Comprehensive prompt ({prompt_len} chars)")

        # Check for key sections (flexible matching)
        sections = ["context", "task", "approach", "output", "success", "guardrail", "role", "constraint"]
        found_sections = sum(1 for s in sections if s.lower() in prompt.lower())
        if found_sections >= 4:
            evaluation["strengths"].append(f"Well-structured ({found_sections} sections)")
        elif found_sections >= 2:
            evaluation["strengths"].append(f"Basic structure ({found_sections} sections)")
        else:
            evaluation["prompt_quality"] = "BASIC"
            evaluation["issues"].append("Limited prompt structure")
            evaluation["overall_score"] -= 1

        # Check for specific prompt best practices
        if "you are" in prompt.lower():
            evaluation["strengths"].append("Role assignment present")
        if "##" in prompt:
            evaluation["strengths"].append("Uses markdown headers")
    else:
        evaluation["prompt_quality"] = "FAILED"
        evaluation["issues"].append("No prompt generated")
        evaluation["overall_score"] -= 2

    # Ensure score is in valid range
    evaluation["overall_score"] = max(1, min(5, evaluation["overall_score"]))

    return evaluation


def generate_improvement_advice(evaluation: dict, test_case: TestCase) -> str:
    """Generate specific improvement advice based on evaluation."""

    advice = []

    if evaluation["classification_quality"] in ["WEAK", "FAILED"]:
        advice.append("Improve intent detection with more training patterns")

    if evaluation["questions_quality"] == "NONE":
        advice.append("Add fallback questions for unclassifiable inputs")
    elif evaluation["questions_quality"] == "EXCESSIVE":
        advice.append("Implement stricter MVQ (Minimum Viable Questions) filtering")

    if evaluation["model_quality"] in ["INCOMPLETE", "FAILED"]:
        advice.append("Add default goal inference heuristics")

    if evaluation["prompt_quality"] in ["INCOMPLETE", "FAILED"]:
        advice.append("Add template fallbacks for edge cases")

    # Specific advice based on test case category
    if test_case.category == "edge_case":
        if "empty" in test_case.description.lower():
            advice.append("Add graceful handling for empty inputs with helpful prompts")
        if "gibberish" in test_case.description.lower():
            advice.append("Add language/semantic validation layer")
        if "multi-intent" in test_case.description.lower():
            advice.append("Implement intent decomposition for complex inputs")
        if "adversarial" in test_case.description.lower():
            advice.append("Add sentiment analysis to detect frustrated users")
        if "multi-language" in test_case.description.lower():
            advice.append("Add language detection and translation support")

    if not advice:
        advice.append("Output quality is good - consider A/B testing with real users")

    return "; ".join(advice)


def summarize_process(result: dict, test_case: TestCase) -> str:
    """Create a summary of the X->Y transformation process."""

    classification = result.get("classification", {})
    questions = result.get("questions", [])
    model = result.get("model", {})

    parts = []

    # Classification summary (dict format)
    if classification:
        task_type = classification.get("task_type", "unknown")
        domain = classification.get("domain", "unknown")
        confidence = classification.get("confidence", 0)
        parts.append(f"PARSE: {task_type}/{domain} (conf={confidence:.0%})")
    else:
        parts.append("PARSE: Unable to classify")

    # Questions summary (list of dicts)
    if questions:
        high_p = sum(1 for q in questions if q.get("priority") == "high")
        parts.append(f"PROBE: {len(questions)} questions ({high_p} high-priority)")
    else:
        parts.append("PROBE: No questions")

    # Model summary (dict format with ascii/mermaid)
    if model:
        ascii_diagram = model.get("ascii", "")
        if ascii_diagram:
            # Count from ASCII diagram
            input_count = ascii_diagram.count("○") + ascii_diagram.count("✓")
            output_count = ascii_diagram.count("◆")
            assumption_count = ascii_diagram.count("ASSUMPTIONS")
            parts.append(f"MODEL: visual ({len(ascii_diagram)} chars)")
        else:
            parts.append("MODEL: minimal")
    else:
        parts.append("MODEL: Not built")

    # Prompt summary
    prompt = result.get("prompt", "")
    if prompt:
        parts.append(f"GENERATE: {len(prompt)} chars prompt")
    else:
        parts.append("GENERATE: No prompt")

    return " | ".join(parts)


def truncate_for_csv(text: str, max_len: int = 500) -> str:
    """Truncate text for CSV cell, preserving readability."""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def run_experiment():
    """Run the full experiment and generate results."""

    print("=" * 70)
    print("INTENT REFINER EVALUATION EXPERIMENT")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    all_cases = REAL_LIFE_CASES + EDGE_CASES
    results = []

    refiner = IntentRefiner()

    for i, test_case in enumerate(all_cases, 1):
        print(f"[{i}/{len(all_cases)}] Testing: {test_case.id} - {test_case.description}")
        print(f"    Input: \"{test_case.input_text[:50]}{'...' if len(test_case.input_text) > 50 else ''}\"")

        try:
            # Run the refiner
            result = refine_intent(test_case.input_text)

            # Evaluate
            evaluation = evaluate_output(result, test_case)

            # Generate advice
            advice = generate_improvement_advice(evaluation, test_case)

            # Process summary
            process_summary = summarize_process(result, test_case)

            # Extract key outputs
            prompt_output = result.get("prompt", "(No prompt generated)")
            paraphrase = result.get("paraphrase", "(No paraphrase)")

            results.append({
                "ID": test_case.id,
                "Category": test_case.category,
                "Input_X": test_case.input_text,
                "Output_Y_Prompt": truncate_for_csv(prompt_output, 800),
                "Output_Y_Paraphrase": truncate_for_csv(paraphrase, 300),
                "Process_Summary": process_summary,
                "Output_Eval_Score": f"{evaluation['overall_score']}/5",
                "Output_Eval_Strengths": "; ".join(evaluation["strengths"]),
                "Output_Eval_Issues": "; ".join(evaluation["issues"]) if evaluation["issues"] else "None",
                "Improvement_Advice": advice,
            })

            print(f"    Result: {evaluation['overall_score']}/5 ({'★' * evaluation['overall_score']}{'☆' * (5 - evaluation['overall_score'])})")
            if evaluation["strengths"]:
                print(f"    ✓ {evaluation['strengths'][0]}")
            if evaluation["issues"]:
                print(f"    ✗ {evaluation['issues'][0]}")

        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({
                "ID": test_case.id,
                "Category": test_case.category,
                "Input_X": test_case.input_text,
                "Output_Y_Prompt": f"ERROR: {e}",
                "Output_Y_Paraphrase": "N/A",
                "Process_Summary": "FAILED",
                "Output_Eval_Score": "0/5",
                "Output_Eval_Strengths": "",
                "Output_Eval_Issues": str(e),
                "Improvement_Advice": "Fix the error before other improvements",
            })

        print()

    return results


def generate_csv(results: list, output_path: Path):
    """Generate CSV spreadsheet from results."""

    fieldnames = [
        "ID",
        "Category",
        "Input_X",
        "Output_Y_Prompt",
        "Output_Y_Paraphrase",
        "Process_Summary",
        "Output_Eval_Score",
        "Output_Eval_Strengths",
        "Output_Eval_Issues",
        "Improvement_Advice",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"CSV saved to: {output_path}")


def print_wow_examples(results: list):
    """Print the most impressive before/after transformations."""

    print("\n" + "=" * 70)
    print("🌟 WOW EXAMPLES: Before & After Transformations")
    print("=" * 70)

    # Find best real-life transformations
    real_life_results = [r for r in results if r["Category"] == "real_life"]
    best_real_life = sorted(real_life_results, key=lambda x: x["Output_Eval_Score"], reverse=True)[:3]

    for i, result in enumerate(best_real_life, 1):
        print(f"\n{'─' * 70}")
        print(f"WOW #{i}: {result['ID']}")
        print(f"{'─' * 70}")
        print(f"\n📥 BEFORE (vague user input):")
        print(f'   "{result["Input_X"]}"')
        print(f"\n📤 AFTER (refined prompt):")
        prompt_lines = result["Output_Y_Prompt"].split("\n")
        for line in prompt_lines[:15]:  # Show first 15 lines
            print(f"   {line}")
        if len(prompt_lines) > 15:
            print(f"   ... ({len(prompt_lines) - 15} more lines)")
        print(f"\n🔄 PROCESS: {result['Process_Summary']}")
        print(f"⭐ SCORE: {result['Output_Eval_Score']}")

    # Show interesting edge case handling
    print(f"\n{'=' * 70}")
    print("🔬 EDGE CASE HANDLING")
    print("=" * 70)

    edge_results = [r for r in results if r["Category"] == "edge_case"]
    for result in edge_results[:3]:
        print(f"\n{'─' * 70}")
        print(f"Edge Case: {result['ID']}")
        print(f'Input: "{result["Input_X"][:60]}..."' if len(result["Input_X"]) > 60 else f'Input: "{result["Input_X"]}"')
        print(f"Score: {result['Output_Eval_Score']}")
        print(f"Issues: {result['Output_Eval_Issues']}")
        print(f"Advice: {result['Improvement_Advice']}")


def print_summary_stats(results: list):
    """Print summary statistics."""

    print("\n" + "=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)

    real_life = [r for r in results if r["Category"] == "real_life"]
    edge_cases = [r for r in results if r["Category"] == "edge_case"]

    def avg_score(items):
        scores = [int(r["Output_Eval_Score"].split("/")[0]) for r in items]
        return sum(scores) / len(scores) if scores else 0

    print(f"\nReal-Life Cases ({len(real_life)} total):")
    print(f"  Average Score: {avg_score(real_life):.1f}/5")
    print(f"  5/5 scores: {sum(1 for r in real_life if r['Output_Eval_Score'] == '5/5')}")

    print(f"\nEdge Cases ({len(edge_cases)} total):")
    print(f"  Average Score: {avg_score(edge_cases):.1f}/5")
    print(f"  Handled gracefully: {sum(1 for r in edge_cases if int(r['Output_Eval_Score'].split('/')[0]) >= 3)}")

    print(f"\nOverall ({len(results)} total):")
    print(f"  Average Score: {avg_score(results):.1f}/5")

    # Common issues
    all_issues = []
    for r in results:
        if r["Output_Eval_Issues"] and r["Output_Eval_Issues"] != "None":
            all_issues.extend(r["Output_Eval_Issues"].split("; "))

    if all_issues:
        print(f"\nMost Common Issues:")
        from collections import Counter
        for issue, count in Counter(all_issues).most_common(5):
            print(f"  - {issue} ({count}x)")


if __name__ == "__main__":
    # Run experiment
    results = run_experiment()

    # Generate CSV
    output_dir = Path(__file__).parent
    csv_path = output_dir / "intent_refiner_evaluation_results.csv"
    generate_csv(results, csv_path)

    # Print WOW examples
    print_wow_examples(results)

    # Print summary
    print_summary_stats(results)

    print("\n" + "=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
