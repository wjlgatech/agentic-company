#!/usr/bin/env python3
"""
Generate a comprehensive WOW comparison CSV showing before/after transformations.
"""

import csv
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.tools.intent_refiner import IntentRefiner, refine_intent


@dataclass
class TestCase:
    id: str
    category: str
    input_text: str
    description: str


# Real-life cases (10)
REAL_LIFE_CASES = [
    TestCase("RL01", "real_life", "help me with my marketing", "Extremely vague business request"),
    TestCase("RL02", "real_life", "I need to analyze some data", "Generic data analysis request"),
    TestCase("RL03", "real_life", "write something for my boss about the project", "Vague writing request"),
    TestCase("RL04", "real_life", "my app is slow, fix it", "Technical complaint without details"),
    TestCase("RL05", "real_life", "prepare me for my interview tomorrow", "Urgent request lacking context"),
    TestCase("RL06", "real_life", "i want to learn programming", "Broad learning goal"),
    TestCase("RL07", "real_life", "make my resume better", "Improvement request without baseline"),
    TestCase("RL08", "real_life", "help me decide if i should take this job offer", "Personal decision request"),
    TestCase("RL09", "real_life", "create a presentation about AI", "Content creation with broad topic"),
    TestCase("RL10", "real_life", "my team isn't performing well, what should i do", "Management challenge"),
]

# Edge cases (7)
EDGE_CASES = [
    TestCase("EC01", "edge_case", "", "Empty input"),
    TestCase("EC02", "edge_case", "asdfghjkl qwerty zxcvbnm", "Gibberish/keyboard mashing"),
    TestCase("EC03", "edge_case", "I want to write code and also analyze sales data and maybe create some marketing content and plan a product launch and review legal documents", "Multi-intent overload"),
    TestCase("EC04", "edge_case", "do the thing with the stuff for the person", "Maximally vague (all pronouns)"),
    TestCase("EC05", "edge_case", "DON'T help me with anything, I just want to complain that AI is ruining everything", "Adversarial/hostile"),
    TestCase("EC06", "edge_case", "私のビジネスを助けてください。我想要分析数据。Помогите мне с проектом.", "Multi-language"),
    TestCase("EC07", "edge_case", "I need help with something but I can't tell you what it is because it's confidential but it's really important!!!", "Contradictory constraints"),
]


def count_issues(input_text: str) -> dict:
    """Count input issues for before analysis."""
    issues = {
        "vague": 0,
        "missing_goal": 0,
        "missing_audience": 0,
        "missing_format": 0,
        "missing_timeline": 0,
        "total": 0,
    }

    text_lower = input_text.lower()

    # Check for vagueness
    vague_words = ["something", "stuff", "thing", "help", "better", "good", "it"]
    issues["vague"] = sum(1 for w in vague_words if w in text_lower)

    # Missing specifics
    if not any(w in text_lower for w in ["want to", "need to", "goal", "objective", "achieve"]):
        issues["missing_goal"] = 1
    if not any(w in text_lower for w in ["for", "to", "audience", "reader", "viewer"]):
        issues["missing_audience"] = 1
    if not any(w in text_lower for w in ["format", "style", "document", "report", "email", "slides"]):
        issues["missing_format"] = 1
    if not any(w in text_lower for w in ["deadline", "by", "when", "timeline", "tomorrow", "today"]):
        issues["missing_timeline"] = 1

    issues["total"] = issues["vague"] + issues["missing_goal"] + issues["missing_audience"] + issues["missing_format"] + issues["missing_timeline"]
    return issues


def count_improvements(prompt: str, model: dict) -> dict:
    """Count improvements made by the refiner."""
    improvements = {
        "role_added": 0,
        "context_added": 0,
        "structure_added": 0,
        "guardrails_added": 0,
        "success_criteria": 0,
        "visual_model": 0,
        "total": 0,
    }

    prompt_lower = prompt.lower()

    if "you are" in prompt_lower:
        improvements["role_added"] = 1
    if "context" in prompt_lower or "domain" in prompt_lower:
        improvements["context_added"] = 1
    if "##" in prompt or "approach" in prompt_lower:
        improvements["structure_added"] = 1
    if "guardrail" in prompt_lower or "constraint" in prompt_lower:
        improvements["guardrails_added"] = 1
    if "success" in prompt_lower or "criteria" in prompt_lower:
        improvements["success_criteria"] = 1
    if model and model.get("ascii"):
        improvements["visual_model"] = 1

    improvements["total"] = sum(v for k, v in improvements.items() if k != "total")
    return improvements


def generate_csv():
    """Generate comprehensive WOW comparison CSV."""

    all_cases = REAL_LIFE_CASES + EDGE_CASES
    rows = []

    print("Generating WOW comparison for", len(all_cases), "test cases...")

    refiner = IntentRefiner()

    for case in all_cases:
        print(f"  Processing {case.id}...")

        # Run refiner
        result = refine_intent(case.input_text)

        classification = result.get("classification", {})
        questions = result.get("questions", [])
        model = result.get("model", {})
        prompt = result.get("prompt", "")

        # Before analysis
        issues = count_issues(case.input_text)

        # After analysis
        improvements = count_improvements(prompt, model)

        # Extract key data
        input_word_count = len(case.input_text.split()) if case.input_text else 0
        prompt_word_count = len(prompt.split()) if prompt else 0

        # Clarification questions summary
        q_summary = "; ".join([q.get("question", "")[:50] for q in questions[:3]])

        # ASCII model preview
        ascii_preview = model.get("ascii", "")[:200] + "..." if model.get("ascii", "") else "(none)"

        rows.append({
            "ID": case.id,
            "Category": case.category,
            "Description": case.description,

            # BEFORE (Input X)
            "Input_X": case.input_text if case.input_text else "(empty)",
            "Input_Word_Count": input_word_count,
            "Input_Issues_Vague_Words": issues["vague"],
            "Input_Issues_Missing_Goal": issues["missing_goal"],
            "Input_Issues_Missing_Audience": issues["missing_audience"],
            "Input_Issues_Missing_Format": issues["missing_format"],
            "Input_Issues_Total": issues["total"],

            # PROCESS (X -> Y)
            "Process_Task_Type": classification.get("task_type", "unknown"),
            "Process_Domain": classification.get("domain", "unknown"),
            "Process_Confidence": f"{classification.get('confidence', 0):.0%}",
            "Process_Signals": ", ".join(classification.get("signals", [])),
            "Process_Questions_Generated": len(questions),
            "Process_Questions_Preview": q_summary,

            # AFTER (Output Y)
            "Output_Y_Prompt": prompt,
            "Output_Prompt_Word_Count": prompt_word_count,
            "Output_Has_Role": improvements["role_added"],
            "Output_Has_Context": improvements["context_added"],
            "Output_Has_Structure": improvements["structure_added"],
            "Output_Has_Guardrails": improvements["guardrails_added"],
            "Output_Has_Success_Criteria": improvements["success_criteria"],
            "Output_Has_Visual_Model": improvements["visual_model"],
            "Output_Improvements_Total": improvements["total"],

            # EVALUATION
            "Eval_Expansion_Ratio": f"{prompt_word_count / max(input_word_count, 1):.1f}x",
            "Eval_Issues_Addressed": f"{improvements['total']}/{issues['total']}",
            "Eval_Score": "5/5" if improvements["total"] >= 4 else f"{improvements['total'] + 1}/5",

            # IMPROVEMENT ADVICE
            "Improvement_Advice": get_advice(case, classification, improvements),
        })

    # Write CSV
    output_path = Path(__file__).parent / "intent_refiner_wow_comparison.csv"

    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ CSV saved to: {output_path}")

    # Print summary stats
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    avg_expansion = sum(int(r["Output_Prompt_Word_Count"]) for r in rows) / sum(max(int(r["Input_Word_Count"]), 1) for r in rows)
    avg_improvements = sum(int(r["Output_Improvements_Total"]) for r in rows) / len(rows)

    print(f"Average expansion ratio: {avg_expansion:.1f}x")
    print(f"Average improvements added: {avg_improvements:.1f}/6")
    print(f"Cases with visual model: {sum(1 for r in rows if r['Output_Has_Visual_Model'])}/{len(rows)}")
    print(f"Cases with role assignment: {sum(1 for r in rows if r['Output_Has_Role'])}/{len(rows)}")
    print(f"Cases with guardrails: {sum(1 for r in rows if r['Output_Has_Guardrails'])}/{len(rows)}")

    return output_path


def get_advice(case, classification, improvements) -> str:
    """Generate specific improvement advice."""
    advice = []

    conf = classification.get("confidence", 0)
    if conf < 0.4:
        advice.append("Consider adding domain-specific keyword detection")

    if not improvements["guardrails_added"]:
        advice.append("Add guardrails for edge cases")

    if case.category == "edge_case":
        if not case.input_text:
            advice.append("Add helpful prompt for empty inputs")
        elif "asdf" in case.input_text.lower():
            advice.append("Add gibberish detection")
        elif len(case.input_text) > 100:
            advice.append("Consider intent decomposition")

    if not advice:
        advice.append("Good - consider A/B testing with users")

    return "; ".join(advice)


if __name__ == "__main__":
    generate_csv()
