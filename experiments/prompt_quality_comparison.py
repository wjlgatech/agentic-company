"""
Side-by-Side Comparison: Mechanical Stacking vs Coherent Synthesis

Shows the quality difference between:
- OLD: Template-filled, bullet-point stacking
- NEW: LLM-synthesized coherent prompt
"""

# =============================================================================
# OLD APPROACH OUTPUT (Mechanical Stacking)
# =============================================================================

OLD_HYBRID_OUTPUT = """
## Role
You are a B2B Marketing Strategy Assistant specializing in lead generation.

## Key Details Extracted:
- **Business Type**: B2B SaaS company
- **Challenge**: Lead generation struggles
- **Tried Approaches**: Content marketing, LinkedIn outreach
- **Problems**: Low engagement, poor lead quality
- **Goal**: Systematic approach for qualified leads

## Instructions:
1. Analyze the user's marketing challenges
2. Provide actionable recommendations
3. Consider their B2B SaaS context
4. Focus on lead generation strategies

## Constraints:
- Stay focused on B2B marketing
- Provide specific, actionable advice
- Consider resource limitations

## Success Criteria:
- Clear action items provided
- Addresses lead generation specifically
- Accounts for B2B SaaS context
"""

# =============================================================================
# NEW APPROACH OUTPUT (Coherent Synthesis)
# =============================================================================

NEW_SMART_OUTPUT = """
You are a B2B growth strategist who has helped dozens of SaaS companies break through their lead generation plateaus. You combine deep expertise in demand generation with a practical, results-focused mindset.

Your client is a B2B SaaS company that's hit a wall with their current marketing approach. They've invested in content marketing and LinkedIn outreach, but the results have been disappointing—low engagement on their content and poor quality leads from their outreach efforts. They're looking for a more systematic approach that actually delivers qualified leads who convert.

Your task is to diagnose what's likely going wrong and provide a concrete, actionable plan. Think about this holistically:

First, understand that low engagement usually signals a targeting or messaging problem, not just a distribution problem. Their content might be too generic, targeting the wrong pain points, or speaking to the wrong stage of the buyer journey.

For LinkedIn specifically, cold outreach fails when it feels like cold outreach. The most effective B2B LinkedIn strategies build relationships before asking for anything. Consider how they might warm up prospects before direct contact.

When you provide recommendations, be specific enough to act on. Don't just say "improve your content strategy"—tell them exactly what kind of content works for B2B SaaS lead gen and why. If you suggest a specific tactic, explain the implementation steps.

Focus on strategies that can show results within 30-60 days, since companies struggling with lead gen usually need to see progress quickly. However, also mention any foundational work that will pay off over longer timeframes.

Be direct about what's likely not working and why. If their approach sounds like common mistakes you've seen, say so. They need honest assessment, not validation.
"""

# =============================================================================
# QUALITY ANALYSIS
# =============================================================================

def analyze_prompt(name: str, prompt: str) -> dict:
    """Analyze prompt quality on key dimensions."""

    # Count mechanical indicators
    has_header_sections = prompt.count("##") > 0
    has_bullet_points = prompt.count("- **") > 0 or prompt.count("1.") > 0
    has_template_markers = any(x in prompt for x in ["Key Details Extracted", "Instructions:", "Constraints:", "Success Criteria:"])

    # Count quality indicators
    reads_naturally = "Your client" in prompt or "Your task" in prompt
    has_persona_depth = "who has helped" in prompt or "You combine" in prompt
    has_strategic_insight = "usually signals" in prompt or "fails when" in prompt
    has_actionable_guidance = "Tell them exactly" in prompt or "explain the implementation" in prompt

    mechanical_score = sum([has_header_sections, has_bullet_points, has_template_markers])
    quality_score = sum([reads_naturally, has_persona_depth, has_strategic_insight, has_actionable_guidance])

    return {
        "name": name,
        "word_count": len(prompt.split()),
        "mechanical_indicators": mechanical_score,
        "quality_indicators": quality_score,
        "has_header_sections": has_header_sections,
        "has_bullet_points": has_bullet_points,
        "has_template_markers": has_template_markers,
        "reads_naturally": reads_naturally,
        "has_persona_depth": has_persona_depth,
        "has_strategic_insight": has_strategic_insight,
        "coherence_rating": "LOW" if mechanical_score >= 2 else ("HIGH" if quality_score >= 3 else "MEDIUM")
    }


def main():
    print("=" * 80)
    print("PROMPT QUALITY COMPARISON")
    print("Mechanical Stacking vs Coherent Synthesis")
    print("=" * 80)

    # Analyze both
    old_analysis = analyze_prompt("OLD (Hybrid/Template)", OLD_HYBRID_OUTPUT)
    new_analysis = analyze_prompt("NEW (Smart Synthesis)", NEW_SMART_OUTPUT)

    # Print comparison
    print("\n" + "=" * 40)
    print("📉 OLD APPROACH (Hybrid/Template)")
    print("=" * 40)
    print(OLD_HYBRID_OUTPUT)

    print("\n" + "-" * 40)
    print("Analysis:")
    print(f"  • Word count: {old_analysis['word_count']}")
    print(f"  • Has ## sections: {old_analysis['has_header_sections']}")
    print(f"  • Has bullet points: {old_analysis['has_bullet_points']}")
    print(f"  • Has template markers: {old_analysis['has_template_markers']}")
    print(f"  • Mechanical indicators: {old_analysis['mechanical_indicators']}/3")
    print(f"  • Quality indicators: {old_analysis['quality_indicators']}/4")
    print(f"  • COHERENCE RATING: {old_analysis['coherence_rating']}")

    print("\n" + "=" * 40)
    print("📈 NEW APPROACH (Smart Synthesis)")
    print("=" * 40)
    print(NEW_SMART_OUTPUT)

    print("\n" + "-" * 40)
    print("Analysis:")
    print(f"  • Word count: {new_analysis['word_count']}")
    print(f"  • Has ## sections: {new_analysis['has_header_sections']}")
    print(f"  • Has bullet points: {new_analysis['has_bullet_points']}")
    print(f"  • Has template markers: {new_analysis['has_template_markers']}")
    print(f"  • Mechanical indicators: {new_analysis['mechanical_indicators']}/3")
    print(f"  • Quality indicators: {new_analysis['quality_indicators']}/4")
    print(f"  • COHERENCE RATING: {new_analysis['coherence_rating']}")

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES")
    print("=" * 80)
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ OLD (Template-Filled)              │ NEW (LLM-Synthesized)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ## Role                            │ Natural opening paragraph              │
│ ## Key Details Extracted:          │ Context woven into narrative           │
│ - **Business Type**: B2B SaaS      │ "Your client is a B2B SaaS company..." │
│ ## Instructions:                   │ Strategic insights embedded            │
│ 1. Analyze the user's...           │ "low engagement usually signals..."    │
│ ## Constraints:                    │ Actionable guidance integrated         │
│ ## Success Criteria:               │ "tell them exactly what kind of..."    │
├─────────────────────────────────────────────────────────────────────────────┤
│ ❌ Looks like a form was filled    │ ✅ Reads like an expert wrote it       │
│ ❌ Mechanical bullet points        │ ✅ Natural prose flow                  │
│ ❌ Generic instructions            │ ✅ Domain-specific wisdom              │
│ ❌ No strategic depth              │ ✅ Thoughtful guidance                 │
└─────────────────────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    main()
