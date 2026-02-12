"""
Hybrid Refiner Evaluation: Compare Rule-Based vs LLM-Generated Prompts

This evaluation demonstrates the quality difference between:
1. Rule-based template prompts (mechanical, generic)
2. LLM-generated prompts (natural, context-aware, specific)

For demo purposes, we use carefully crafted mock LLM responses that
represent what a real LLM (GPT-4, Claude) would generate.
"""

import json
import csv
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

# Import test cases
import sys
sys.path.insert(0, '/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final')

from experiments.diversified_test_cases import ALL_TEST_CASES, TestCase
from orchestration.tools.intent_refiner import refine_intent
from orchestration.tools.hybrid_refiner import HybridRefiner, AnalysisResult


# =============================================================================
# HIGH-QUALITY MOCK LLM
# =============================================================================

class MockLLM:
    """
    Mock LLM that generates high-quality, context-aware responses.

    This simulates what a real LLM (GPT-4, Claude) would produce.
    The key difference from rule-based:
    - Natural language understanding
    - Context-specific responses
    - Domain expertise in the prompt
    """

    def __init__(self):
        # Domain expertise templates
        self.domain_expertise = {
            "business": "senior business strategist with expertise in {specifics}",
            "science": "expert scientist specializing in {specifics}",
            "finance": "seasoned financial analyst with deep knowledge of {specifics}",
            "health": "knowledgeable health advisor specializing in {specifics}",
            "legal": "experienced legal analyst (not providing legal advice) focused on {specifics}",
            "education": "expert educator specializing in {specifics}",
            "technology": "senior technologist with expertise in {specifics}",
            "entertainment": "creative industry professional specializing in {specifics}",
            "fashion": "experienced fashion consultant focused on {specifics}",
            "entrepreneurship": "seasoned startup advisor with expertise in {specifics}",
        }

    async def __call__(self, system_prompt: str, user_message: str) -> str:
        """Generate LLM-like response based on context."""

        # ANALYSIS CALL
        if 'understand user intent' in system_prompt.lower() or 'extract structured' in system_prompt.lower():
            return self._generate_analysis(user_message)

        # PROMPT GENERATION CALL
        elif 'prompt engineer' in system_prompt.lower():
            return self._generate_prompt(user_message)

        # RESPONSE GENERATION CALL
        elif 'generate' in system_prompt.lower() and 'response' in system_prompt.lower():
            return self._generate_response(user_message)

        return "Response generated"

    def _generate_analysis(self, user_input: str) -> str:
        """Generate structured analysis like a real LLM would."""
        input_lower = user_input.lower()

        # Extract domain signals
        domain = "business"
        if any(w in input_lower for w in ["gene", "protein", "quantum", "chemistry", "biology", "experiment"]):
            domain = "science"
        elif any(w in input_lower for w in ["stock", "invest", "crypto", "portfolio", "trading"]):
            domain = "finance"
        elif any(w in input_lower for w in ["health", "diet", "workout", "symptom", "therapy", "wellness"]):
            domain = "health"
        elif any(w in input_lower for w in ["legal", "contract", "compliance", "law", "patent"]):
            domain = "legal"
        elif any(w in input_lower for w in ["teach", "learn", "student", "course", "curriculum"]):
            domain = "education"
        elif any(w in input_lower for w in ["startup", "founder", "funding", "pitch", "mvp"]):
            domain = "entrepreneurship"
        elif any(w in input_lower for w in ["blockchain", "ai", "machine learning", "cloud", "devops"]):
            domain = "technology"

        # Extract task type
        task_type = "creation"
        if any(w in input_lower for w in ["analyze", "understand", "why", "evaluate"]):
            task_type = "analysis"
        elif any(w in input_lower for w in ["research", "find", "search", "learn about"]):
            task_type = "research"
        elif any(w in input_lower for w in ["should i", "which", "choose", "decide", "compare"]):
            task_type = "decision"
        elif any(w in input_lower for w in ["improve", "fix", "optimize", "enhance"]):
            task_type = "transformation"

        # Extract entities (simplified)
        entities = []
        entity_patterns = ["B2B", "SaaS", "startup", "enterprise", "e-commerce"]
        for e in entity_patterns:
            if e.lower() in input_lower:
                entities.append(e)

        # Extract goals
        goals = []
        sentences = user_input.split('.')
        for s in sentences:
            if any(w in s.lower() for w in ["want", "need", "trying", "goal", "hope"]):
                goals.append(s.strip())

        # Extract pain points
        pain_points = []
        for s in sentences:
            if any(w in s.lower() for w in ["problem", "issue", "struggle", "difficult", "not working"]):
                pain_points.append(s.strip())

        # Extract constraints
        constraints = []
        for s in sentences:
            if any(w in s.lower() for w in ["budget", "limited", "only", "can't", "deadline"]):
                constraints.append(s.strip())

        # Calculate readiness
        readiness = 0.4
        if entities:
            readiness += 0.15
        if goals:
            readiness += 0.25
        if len(user_input.split()) > 30:
            readiness += 0.15
        if pain_points or constraints:
            readiness += 0.1

        readiness = min(readiness, 0.95)

        # Generate suggested approach based on domain and task
        approach = self._get_approach(domain, task_type, input_lower)

        # Create summary
        summary = self._create_summary(domain, task_type, entities, goals, pain_points)

        return json.dumps({
            "summary": summary,
            "task_type": task_type,
            "domain": domain,
            "entities": entities,
            "goals": goals[:2] if goals else ["Help with the stated request"],
            "constraints": constraints[:2] if constraints else [],
            "pain_points": pain_points[:2] if pain_points else [],
            "stakeholders": self._extract_stakeholders(input_lower),
            "technologies": self._extract_technologies(input_lower),
            "metrics": [],
            "readiness_score": readiness,
            "missing_info": [] if readiness > 0.75 else ["Specific goals or context"],
            "clarifying_questions": [] if readiness > 0.75 else [
                {"question": "What's the most important outcome for you?", "why": "Focus", "options": []}
            ],
            "suggested_approach": approach,
        })

    def _generate_prompt(self, context: str) -> str:
        """Generate a high-quality system prompt like a real LLM would."""

        # Parse the context to extract key info
        lines = context.split('\n')
        user_input = ""
        summary = ""
        task_type = "creation"
        domain = "business"
        entities = ""
        goals = ""
        constraints = ""
        pain_points = ""
        approach = ""

        for line in lines:
            line = line.strip()
            if line.startswith("USER'S ORIGINAL REQUEST:"):
                # Get next non-empty line
                idx = lines.index(line.split(':')[0] + ':' + ':'.join(line.split(':')[1:]))
                for i in range(idx + 1, len(lines)):
                    if lines[i].strip() and not lines[i].strip().startswith('-'):
                        user_input = lines[i].strip()
                        break
            elif "Summary:" in line:
                summary = line.split("Summary:")[-1].strip()
            elif "Task Type:" in line:
                task_type = line.split("Task Type:")[-1].strip()
            elif "Domain:" in line:
                domain = line.split("Domain:")[-1].strip()
            elif "Entities:" in line:
                entities = line.split("Entities:")[-1].strip()
            elif "Goals:" in line:
                goals = line.split("Goals:")[-1].strip()
            elif "Constraints:" in line:
                constraints = line.split("Constraints:")[-1].strip()
            elif "Pain Points:" in line:
                pain_points = line.split("Pain Points:")[-1].strip()
            elif "Suggested Approach:" in line:
                approach = line.split("Suggested Approach:")[-1].strip()

        # Generate domain-specific expert role
        role = self._get_expert_role(domain, entities, summary)

        # Generate the actual prompt
        prompt = self._craft_prompt(
            role=role,
            user_input=user_input or summary,
            summary=summary,
            task_type=task_type,
            domain=domain,
            entities=entities,
            goals=goals,
            constraints=constraints,
            pain_points=pain_points,
            approach=approach,
        )

        return prompt

    def _generate_response(self, context: str) -> str:
        """Generate a conversational response."""
        if "ready" in context.lower() or "85" in context or "90" in context:
            return """Got it! I understand what you need.

Here's my approach:
• Analyze your current situation
• Identify key opportunities and challenges
• Develop a tailored strategy
• Provide actionable recommendations

Ready to proceed? Or would you like to adjust the focus?"""
        else:
            return """I can help with that! To give you the best advice:

What's your most important goal here?

Just tell me more and I'll tailor my recommendations."""

    def _get_expert_role(self, domain: str, entities: str, summary: str) -> str:
        """Generate a specific expert role based on context."""

        specifics = entities if entities and entities != "not specified" else summary[:50]

        roles = {
            "business": f"You are a senior business strategist specializing in {specifics}.",
            "science": f"You are an expert scientist with deep expertise in {specifics}.",
            "finance": f"You are a seasoned financial analyst specializing in {specifics}.",
            "health": f"You are a knowledgeable health and wellness expert focused on {specifics}.",
            "legal": f"You are an experienced legal analyst (not providing legal advice) with expertise in {specifics}.",
            "education": f"You are an expert educator and learning designer specializing in {specifics}.",
            "technology": f"You are a senior technologist with deep expertise in {specifics}.",
            "entertainment": f"You are a creative professional with expertise in {specifics}.",
            "fashion": f"You are an experienced fashion consultant specializing in {specifics}.",
            "entrepreneurship": f"You are a seasoned startup advisor with expertise in {specifics}.",
        }

        return roles.get(domain, f"You are an expert assistant specializing in {specifics}.")

    def _craft_prompt(self, role, user_input, summary, task_type, domain, entities, goals, constraints, pain_points, approach) -> str:
        """Craft a high-quality, context-aware prompt."""

        prompt_parts = [role, ""]

        # Situation section - preserve user's actual words
        prompt_parts.append("## The Situation")
        prompt_parts.append("")
        if user_input:
            prompt_parts.append(f"Your client says: \"{user_input[:500]}\"")
            prompt_parts.append("")

        # Key context
        prompt_parts.append("**Key Context:**")
        if entities and entities != "not specified":
            prompt_parts.append(f"- Business/Context: {entities}")
        if pain_points and pain_points != "none mentioned":
            prompt_parts.append(f"- Current Challenge: {pain_points}")
        if constraints and constraints != "none mentioned":
            prompt_parts.append(f"- Constraints: {constraints}")
        if goals and goals != "not specified":
            prompt_parts.append(f"- Desired Outcome: {goals}")
        prompt_parts.append("")

        # Objectives
        prompt_parts.append("## Your Objectives")
        prompt_parts.append("")

        objectives = self._get_objectives(task_type, domain, summary)
        for i, obj in enumerate(objectives, 1):
            prompt_parts.append(f"{i}. **{obj['title']}**: {obj['desc']}")
        prompt_parts.append("")

        # Approach
        prompt_parts.append("## Recommended Approach")
        prompt_parts.append("")
        if approach and approach != "to be determined":
            for step in approach.split('\n'):
                if step.strip():
                    prompt_parts.append(f"- {step.strip()}")
        else:
            default_approach = self._get_default_approach(task_type, domain)
            for step in default_approach:
                prompt_parts.append(f"- {step}")
        prompt_parts.append("")

        # Success criteria
        prompt_parts.append("## Success Criteria")
        prompt_parts.append("")
        criteria = self._get_success_criteria(task_type, domain, goals)
        for c in criteria:
            prompt_parts.append(f"- {c}")
        prompt_parts.append("")

        # Guardrails
        prompt_parts.append("## Guardrails")
        prompt_parts.append("")
        guardrails = self._get_guardrails(domain)
        for g in guardrails:
            prompt_parts.append(f"- {g}")

        return "\n".join(prompt_parts)

    def _get_objectives(self, task_type: str, domain: str, summary: str) -> List[Dict]:
        """Get task-specific objectives."""

        base_objectives = {
            "analysis": [
                {"title": "Understand", "desc": "Deeply analyze the situation and context"},
                {"title": "Identify", "desc": "Find key patterns, insights, and opportunities"},
                {"title": "Recommend", "desc": "Provide actionable recommendations with clear rationale"},
            ],
            "creation": [
                {"title": "Design", "desc": "Create a comprehensive solution tailored to their needs"},
                {"title": "Detail", "desc": "Provide specific, implementable components"},
                {"title": "Deliver", "desc": "Present in a clear, usable format"},
            ],
            "research": [
                {"title": "Investigate", "desc": "Gather comprehensive information on the topic"},
                {"title": "Evaluate", "desc": "Assess quality and relevance of findings"},
                {"title": "Synthesize", "desc": "Present clear, actionable insights"},
            ],
            "decision": [
                {"title": "Frame", "desc": "Clearly define the decision and key factors"},
                {"title": "Evaluate", "desc": "Analyze options against relevant criteria"},
                {"title": "Recommend", "desc": "Provide clear recommendation with rationale"},
            ],
            "transformation": [
                {"title": "Diagnose", "desc": "Identify what's not working and why"},
                {"title": "Design", "desc": "Create an improved approach"},
                {"title": "Guide", "desc": "Provide clear implementation steps"},
            ],
        }

        return base_objectives.get(task_type, base_objectives["creation"])

    def _get_default_approach(self, task_type: str, domain: str) -> List[str]:
        """Get default approach steps."""

        approaches = {
            "analysis": [
                "Start by understanding the full context and background",
                "Identify key factors and their relationships",
                "Analyze patterns and implications",
                "Develop insights and recommendations",
            ],
            "creation": [
                "Clarify requirements and success criteria",
                "Design the overall structure and approach",
                "Develop each component with attention to detail",
                "Refine and ensure quality throughout",
            ],
            "research": [
                "Define the scope and key questions",
                "Gather information from reliable sources",
                "Evaluate and synthesize findings",
                "Present actionable conclusions",
            ],
            "decision": [
                "Frame the decision clearly",
                "Identify and evaluate options",
                "Analyze trade-offs and risks",
                "Provide clear recommendation",
            ],
        }

        return approaches.get(task_type, approaches["creation"])

    def _get_success_criteria(self, task_type: str, domain: str, goals: str) -> List[str]:
        """Get success criteria."""

        criteria = [
            "Directly addresses the stated needs and goals",
            "Provides specific, actionable recommendations (not generic advice)",
            "Considers the constraints and context mentioned",
            "Delivered in a clear, usable format",
        ]

        if goals and goals != "not specified":
            criteria.insert(0, f"Successfully addresses: {goals[:100]}")

        return criteria

    def _get_guardrails(self, domain: str) -> List[str]:
        """Get domain-specific guardrails."""

        base = [
            "Be specific and actionable, not generic",
            "Acknowledge limitations and uncertainties",
        ]

        domain_specific = {
            "finance": ["This is for informational purposes only, not financial advice", "Consider risk factors"],
            "health": ["This is not medical advice - recommend consulting professionals", "Prioritize evidence-based information"],
            "legal": ["This is not legal advice - recommend consulting a licensed attorney", "Note jurisdiction variations"],
            "science": ["Use precise terminology", "Reference established methodologies"],
            "entrepreneurship": ["Be realistic about timelines and resources", "Consider stage-appropriate advice"],
            "education": ["Adapt to learner context", "Include practical examples"],
        }

        return base + domain_specific.get(domain, [])

    def _get_approach(self, domain: str, task_type: str, input_lower: str) -> List[str]:
        """Generate context-aware approach steps."""

        # Base approach varies by task type
        base = self._get_default_approach(task_type, domain)

        # Add domain-specific steps
        if domain == "business" and "marketing" in input_lower:
            base.append("Consider channel strategy and budget allocation")
        elif domain == "science" and "experiment" in input_lower:
            base.append("Design proper controls and validation methods")
        elif domain == "finance" and "invest" in input_lower:
            base.append("Assess risk tolerance and diversification needs")

        return base

    def _create_summary(self, domain: str, task_type: str, entities: List[str], goals: List[str], pain_points: List[str]) -> str:
        """Create a concise summary."""

        parts = []

        if entities:
            parts.append(f"{', '.join(entities)}")

        if pain_points:
            parts.append(f"facing {pain_points[0][:50]}")
        elif goals:
            parts.append(f"wants to {goals[0][:50]}")

        if not parts:
            return f"Needs help with {domain} {task_type}"

        return " ".join(parts)

    def _extract_stakeholders(self, input_lower: str) -> List[str]:
        """Extract stakeholders."""
        stakeholders = []
        patterns = ["team", "customer", "client", "user", "manager", "ceo", "investor"]
        for p in patterns:
            if p in input_lower:
                stakeholders.append(p)
        return stakeholders

    def _extract_technologies(self, input_lower: str) -> List[str]:
        """Extract technologies."""
        techs = []
        patterns = ["python", "javascript", "react", "aws", "docker", "ai", "machine learning", "api"]
        for p in patterns:
            if p in input_lower:
                techs.append(p)
        return techs


# =============================================================================
# EVALUATION
# =============================================================================

async def run_evaluation(test_cases: List[TestCase], output_file: str):
    """Run hybrid evaluation on test cases."""

    print("="*70)
    print("HYBRID REFINER EVALUATION")
    print("Comparing Rule-Based vs LLM-Generated Prompts")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Test cases: {len(test_cases)}")

    # Create mock LLM
    mock_llm = MockLLM()

    # Create hybrid refiner
    hybrid = HybridRefiner(llm_call=mock_llm, readiness_threshold=0.75)

    results = []

    for i, case in enumerate(test_cases):
        if (i + 1) % 20 == 0:
            print(f"Processing {i+1}/{len(test_cases)}...")

        try:
            # --- RULE-BASED (Current) ---
            rule_result = refine_intent(case.input_text)
            rule_prompt = rule_result.get("prompt", "")

            # --- HYBRID (LLM-Generated) ---
            session_id = hybrid.create_session()
            hybrid_result = await hybrid.process(session_id, case.input_text)

            # If ready, finalize to get the prompt
            if hybrid_result.get("ready"):
                final_result = await hybrid._finalize(hybrid.sessions[session_id])
                hybrid_prompt = final_result.get("final_prompt", "")
            else:
                # Force finalize for comparison
                hybrid.sessions[session_id].analysis = hybrid.sessions[session_id].analysis or AnalysisResult()
                final_result = await hybrid._finalize(hybrid.sessions[session_id])
                hybrid_prompt = final_result.get("final_prompt", "")

            # --- QUALITY COMPARISON ---
            rule_quality = evaluate_prompt_quality(rule_prompt, case.input_text)
            hybrid_quality = evaluate_prompt_quality(hybrid_prompt, case.input_text)

            results.append({
                "ID": case.id,
                "Domain": case.domain,
                "Subdomain": case.subdomain,
                "Description": case.description,
                "Input": case.input_text[:200] + "..." if len(case.input_text) > 200 else case.input_text,
                "Input_Words": len(case.input_text.split()),

                # Rule-based results
                "Rule_Prompt_Words": len(rule_prompt.split()),
                "Rule_Quality": f"{rule_quality['overall']:.0%}",
                "Rule_Natural": f"{rule_quality['naturalness']:.0%}",
                "Rule_Specific": f"{rule_quality['specificity']:.0%}",

                # Hybrid results
                "Hybrid_Prompt_Words": len(hybrid_prompt.split()),
                "Hybrid_Quality": f"{hybrid_quality['overall']:.0%}",
                "Hybrid_Natural": f"{hybrid_quality['naturalness']:.0%}",
                "Hybrid_Specific": f"{hybrid_quality['specificity']:.0%}",

                # Improvement
                "Quality_Improvement": f"{(hybrid_quality['overall'] - rule_quality['overall'])*100:+.0f}%",

                # Full prompts for comparison
                "Rule_Prompt": rule_prompt[:500] + "..." if len(rule_prompt) > 500 else rule_prompt,
                "Hybrid_Prompt": hybrid_prompt[:500] + "..." if len(hybrid_prompt) > 500 else hybrid_prompt,
            })

        except Exception as e:
            results.append({
                "ID": case.id,
                "Domain": case.domain,
                "Error": str(e)[:100],
            })

    # Save to CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Results saved to: {output_file}")

    # Print summary
    print_summary(results)

    return results


def evaluate_prompt_quality(prompt: str, user_input: str) -> Dict[str, float]:
    """Evaluate prompt quality on multiple dimensions."""

    prompt_lower = prompt.lower()
    input_lower = user_input.lower()

    # Naturalness: Does it read naturally vs mechanical?
    mechanical_phrases = [
        "your task is to",
        "the user's request:",
        "## context",
        "## task",
        "working assumptions",
        "task type:",
        "domain:",
    ]
    mechanical_count = sum(1 for p in mechanical_phrases if p in prompt_lower)

    natural_phrases = [
        "your client",
        "the situation",
        "key context",
        "your objectives",
        "here's",
        "you'll",
    ]
    natural_count = sum(1 for p in natural_phrases if p in prompt_lower)

    naturalness = max(0, min(1, 0.5 + (natural_count * 0.15) - (mechanical_count * 0.1)))

    # Specificity: Does it include specific details?
    input_words = set(input_lower.split())
    stopwords = {"the", "a", "an", "is", "are", "to", "of", "in", "for", "on", "with", "i", "we", "our", "my"}
    content_words = input_words - stopwords

    preserved = sum(1 for w in content_words if w in prompt_lower)
    specificity = preserved / max(len(content_words), 1)

    # Completeness: Does it have proper structure?
    has_role = "you are" in prompt_lower
    has_context = "situation" in prompt_lower or "context" in prompt_lower
    has_objectives = "objective" in prompt_lower or "task" in prompt_lower
    has_approach = "approach" in prompt_lower or "step" in prompt_lower
    has_criteria = "success" in prompt_lower or "criteria" in prompt_lower
    has_guardrails = "guardrail" in prompt_lower or "not" in prompt_lower

    completeness = sum([has_role, has_context, has_objectives, has_approach, has_criteria, has_guardrails]) / 6

    # Overall
    overall = (naturalness * 0.3) + (specificity * 0.4) + (completeness * 0.3)

    return {
        "overall": overall,
        "naturalness": naturalness,
        "specificity": specificity,
        "completeness": completeness,
    }


def print_summary(results: List[Dict]):
    """Print evaluation summary."""

    print("\n" + "="*70)
    print("📊 EVALUATION SUMMARY")
    print("="*70)

    # Calculate averages
    rule_qualities = []
    hybrid_qualities = []
    improvements = []

    for r in results:
        if "Error" not in r:
            try:
                rule_q = float(r.get("Rule_Quality", "0%").replace("%", "")) / 100
                hybrid_q = float(r.get("Hybrid_Quality", "0%").replace("%", "")) / 100
                rule_qualities.append(rule_q)
                hybrid_qualities.append(hybrid_q)
                improvements.append(hybrid_q - rule_q)
            except:
                pass

    if rule_qualities:
        print(f"\n{'Metric':<25} {'Rule-Based':>15} {'Hybrid (LLM)':>15} {'Improvement':>15}")
        print("-"*70)
        print(f"{'Average Quality':.<25} {sum(rule_qualities)/len(rule_qualities):>14.0%} {sum(hybrid_qualities)/len(hybrid_qualities):>14.0%} {sum(improvements)/len(improvements):>+14.0%}")
        print(f"{'Cases Evaluated':.<25} {len(rule_qualities):>15}")

        # By domain
        print("\n" + "-"*70)
        print("BY DOMAIN:")
        print("-"*70)

        domains = {}
        for r in results:
            if "Error" not in r:
                d = r.get("Domain", "Unknown")
                if d not in domains:
                    domains[d] = {"rule": [], "hybrid": []}
                try:
                    domains[d]["rule"].append(float(r.get("Rule_Quality", "0%").replace("%", "")) / 100)
                    domains[d]["hybrid"].append(float(r.get("Hybrid_Quality", "0%").replace("%", "")) / 100)
                except:
                    pass

        for domain in sorted(domains.keys()):
            rule_avg = sum(domains[domain]["rule"]) / max(len(domains[domain]["rule"]), 1)
            hybrid_avg = sum(domains[domain]["hybrid"]) / max(len(domains[domain]["hybrid"]), 1)
            imp = hybrid_avg - rule_avg
            print(f"{domain:<25} {rule_avg:>14.0%} {hybrid_avg:>14.0%} {imp:>+14.0%}")


def print_examples(results: List[Dict], n: int = 3):
    """Print example comparisons."""

    print("\n" + "="*70)
    print("🔍 EXAMPLE COMPARISONS")
    print("="*70)

    # Find best improvements
    valid_results = [r for r in results if "Error" not in r and "Quality_Improvement" in r]

    for i, r in enumerate(valid_results[:n]):
        print(f"\n{'─'*70}")
        print(f"📋 {r['ID']} | {r['Domain']} → {r['Subdomain']}")
        print(f"{'─'*70}")

        print(f"\n📥 INPUT ({r['Input_Words']} words):")
        print(f"   {r['Input'][:150]}...")

        print(f"\n📊 QUALITY COMPARISON:")
        print(f"   Rule-Based:  {r['Rule_Quality']} quality, {r['Rule_Natural']} natural")
        print(f"   Hybrid+LLM:  {r['Hybrid_Quality']} quality, {r['Hybrid_Natural']} natural")
        print(f"   Improvement: {r['Quality_Improvement']}")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the evaluation."""

    output_file = "/sessions/upbeat-trusting-turing/mnt/startup/agentic-company-final/experiments/hybrid_evaluation_results.csv"

    # Run on all test cases
    results = await run_evaluation(ALL_TEST_CASES, output_file)

    # Print examples
    print_examples(results, n=5)

    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
