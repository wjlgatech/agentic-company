"""
Workflow Templates

Pre-built YAML templates for common workflows.
Use `init_workflow` to create a new workflow file from a template.
"""

from pathlib import Path


FEATURE_DEV_TEMPLATE = """# Feature Development Workflow
# Agents work together to implement new features safely

id: feature-dev
name: Feature Development
description: |
  Complete feature development workflow with planning,
  implementation, verification, testing, and review.

agents:
  - role: planner
    name: "Project Planner"
    persona: |
      Expert software architect who breaks down features
      into atomic, implementable stories with clear criteria.
    guardrails:
      - content-filter

  - role: developer
    name: "Senior Developer"
    persona: |
      Experienced developer who writes clean, tested code
      following best practices and established patterns.
    guardrails:
      - rate-limiter

  - role: verifier
    name: "Code Reviewer"
    persona: |
      Meticulous reviewer who validates code against
      acceptance criteria and identifies issues.

  - role: tester
    name: "QA Engineer"
    persona: |
      Testing expert who creates comprehensive test suites
      covering happy paths, edge cases, and error handling.

  - role: reviewer
    name: "Tech Lead"
    persona: |
      Senior engineer who makes final approval decisions
      based on quality, security, and maintainability.

steps:
  - id: plan
    agent: planner
    input: |
      Create an implementation plan for the following feature:

      {task}

      Break it down into atomic stories with:
      - Clear description
      - Acceptance criteria
      - Dependencies
      - Complexity estimate
    expects: |
      Plan with atomic stories, each having clear acceptance
      criteria and dependency information.

  - id: implement
    agent: developer
    input: |
      Implement the following plan:

      {plan}

      Follow the existing code patterns and include:
      - Clean, documented code
      - Error handling
      - Unit tests for new functions
    expects: |
      Working code that meets all acceptance criteria
      from the plan, with appropriate tests.
    verified_by: verifier
    max_retries: 3

  - id: test
    agent: tester
    input: |
      Create and run tests for the implementation:

      {implement}

      Include:
      - Unit tests for all new functions
      - Integration tests for component interaction
      - Edge case coverage
      - Error handling verification
    expects: |
      Comprehensive test suite with all tests passing.
      Coverage of happy paths, edge cases, and errors.

  - id: review
    agent: reviewer
    input: |
      Perform final review of:

      Code:
      {implement}

      Tests:
      {test}

      Checklist:
      - Code quality and readability
      - Test coverage and quality
      - Security considerations
      - Documentation completeness
    expects: |
      APPROVE with confidence that code is production-ready,
      or REQUEST_CHANGES with specific items to address.
    requires_approval: true
"""


BUG_FIX_TEMPLATE = """# Bug Fix Workflow
# Systematic approach to investigating and fixing bugs

id: bug-fix
name: Bug Fix
description: |
  Bug fix workflow with investigation, implementation,
  verification, and regression testing.

agents:
  - role: analyst
    name: "Bug Investigator"
    persona: |
      Skilled debugger who systematically traces issues
      to their root cause through careful analysis.

  - role: developer
    name: "Fix Developer"
    persona: |
      Developer focused on creating minimal, targeted
      fixes that resolve issues without side effects.
    guardrails:
      - rate-limiter

  - role: verifier
    name: "Fix Verifier"
    persona: |
      Reviewer who ensures fixes actually resolve the
      reported issue and don't introduce regressions.

  - role: tester
    name: "Regression Tester"
    persona: |
      Tester who verifies the fix works and ensures
      no existing functionality was broken.

steps:
  - id: investigate
    agent: analyst
    input: |
      Investigate the following bug:

      {task}

      Provide:
      - Steps to reproduce
      - Root cause analysis
      - Affected components
      - Suggested fix approach
    expects: |
      Clear root cause identification with evidence
      and a proposed fix strategy.

  - id: fix
    agent: developer
    input: |
      Implement a fix based on the investigation:

      {investigate}

      Requirements:
      - Minimal change to fix the issue
      - No breaking changes to existing behavior
      - Add regression test for the bug
    expects: |
      Working fix that resolves the root cause
      without introducing side effects.
    verified_by: verifier
    max_retries: 3

  - id: test
    agent: tester
    input: |
      Test the bug fix:

      Original Issue:
      {task}

      Investigation:
      {investigate}

      Fix:
      {fix}

      Verify:
      - Bug is fixed
      - Regression test covers the bug
      - No existing tests broken
      - Related functionality still works
    expects: |
      Confirmation that bug is fixed with no regressions.
      All tests passing including new regression test.
"""


SECURITY_AUDIT_TEMPLATE = """# Security Audit Workflow
# Systematic security scanning and remediation

id: security-audit
name: Security Audit
description: |
  Security audit workflow with vulnerability scanning,
  prioritization, remediation, and verification.

agents:
  - role: analyst
    name: "Security Scanner"
    persona: |
      Security expert who identifies vulnerabilities
      through static analysis, pattern matching, and
      security best practice evaluation.

  - role: planner
    name: "Security Prioritizer"
    persona: |
      Risk analyst who evaluates vulnerability severity
      and creates prioritized remediation plans.

  - role: developer
    name: "Security Developer"
    persona: |
      Developer specialized in security fixes who
      implements patches following secure coding practices.
    guardrails:
      - content-filter
      - pii-detection

  - role: verifier
    name: "Security Verifier"
    persona: |
      Security reviewer who validates that patches
      actually resolve vulnerabilities without
      introducing new security issues.

steps:
  - id: scan
    agent: analyst
    input: |
      Perform security scan on:

      {task}

      Check for:
      - OWASP Top 10 vulnerabilities
      - Injection vulnerabilities (SQL, XSS, etc.)
      - Authentication/authorization issues
      - Sensitive data exposure
      - Security misconfigurations
      - Known vulnerable dependencies
    expects: |
      Comprehensive vulnerability report with:
      - Vulnerability descriptions
      - Severity ratings (Critical/High/Medium/Low)
      - Affected code locations
      - Potential impact

  - id: prioritize
    agent: planner
    input: |
      Prioritize vulnerabilities from scan:

      {scan}

      Consider:
      - Severity and exploitability
      - Business impact
      - Fix complexity
      - Dependencies between fixes
    expects: |
      Prioritized list of vulnerabilities with
      recommended fix order and effort estimates.

  - id: fix
    agent: developer
    input: |
      Fix high-priority vulnerabilities:

      {prioritize}

      For each fix:
      - Apply minimal necessary change
      - Follow secure coding practices
      - Document the fix approach
      - Add security test if applicable
    expects: |
      Patches for all high-priority vulnerabilities
      with clear documentation of changes.
    verified_by: verifier
    max_retries: 3

  - id: verify
    agent: verifier
    input: |
      Verify security fixes:

      Original Vulnerabilities:
      {scan}

      Applied Fixes:
      {fix}

      Verify:
      - Each high-priority vulnerability is resolved
      - No new vulnerabilities introduced
      - Security tests pass
      - Fix approach is sound
    expects: |
      Confirmation that all high-priority vulnerabilities
      are resolved with no new security issues.
"""


CONTENT_RESEARCH_TEMPLATE = """# Content Research Workflow
# Research and synthesize information on a topic

id: content-research
name: Content Research
description: |
  Research workflow for gathering, analyzing, and
  synthesizing information on a topic.

agents:
  - role: researcher
    name: "Lead Researcher"
    persona: |
      Thorough researcher who gathers comprehensive
      information from multiple perspectives.
    guardrails:
      - content-filter

  - role: analyst
    name: "Data Analyst"
    persona: |
      Analyst who identifies patterns, trends, and
      key insights from research data.

  - role: writer
    name: "Content Writer"
    persona: |
      Clear communicator who synthesizes complex
      information into readable summaries.

  - role: reviewer
    name: "Editor"
    persona: |
      Editor who ensures accuracy, clarity, and
      completeness of final content.

steps:
  - id: research
    agent: researcher
    input: |
      Research the following topic:

      {task}

      Gather:
      - Key facts and statistics
      - Different perspectives
      - Recent developments
      - Expert opinions
    expects: |
      Comprehensive research notes with sources
      and multiple perspectives covered.

  - id: analyze
    agent: analyst
    input: |
      Analyze research findings:

      {research}

      Identify:
      - Key patterns and trends
      - Important insights
      - Gaps in information
      - Actionable conclusions
    expects: |
      Analysis with clear insights, patterns,
      and conclusions supported by evidence.

  - id: synthesize
    agent: writer
    input: |
      Create summary from research and analysis:

      Research:
      {research}

      Analysis:
      {analyze}

      Format:
      - Executive summary
      - Key findings
      - Recommendations
    expects: |
      Clear, well-structured summary that
      captures key insights and recommendations.
    verified_by: reviewer

  - id: review
    agent: reviewer
    input: |
      Review final content:

      {synthesize}

      Check:
      - Accuracy of information
      - Clarity of writing
      - Completeness of coverage
      - Logical flow
    expects: |
      Approved content or specific revision requests.
    requires_approval: true
"""


def init_workflow(
    template_name: str,
    output_path: str | Path,
    overwrite: bool = False
) -> Path:
    """
    Initialize a new workflow file from a template.

    Args:
        template_name: Name of template (feature-dev, bug-fix, security-audit, content-research)
        output_path: Path where to create the YAML file
        overwrite: If True, overwrite existing file

    Returns:
        Path to created file
    """
    templates = {
        'feature-dev': FEATURE_DEV_TEMPLATE,
        'bug-fix': BUG_FIX_TEMPLATE,
        'security-audit': SECURITY_AUDIT_TEMPLATE,
        'content-research': CONTENT_RESEARCH_TEMPLATE,
    }

    if template_name not in templates:
        raise ValueError(
            f"Unknown template: {template_name}. "
            f"Available: {list(templates.keys())}"
        )

    output_file = Path(output_path)

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {output_file}. "
            f"Use overwrite=True to replace."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(templates[template_name])

    return output_file


def list_templates() -> list[str]:
    """Return list of available template names"""
    return ['feature-dev', 'bug-fix', 'security-audit', 'content-research']
