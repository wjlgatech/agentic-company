"""
Specialized Agents

Pre-configured agents for common roles in software development workflows.
Each agent has a specific persona and set of capabilities optimized for its role.
"""

from orchestration.agents.base import (
    Agent,
    AgentConfig,
    AgentRole,
    AgentContext,
    LLMAgent,
)
from typing import Any, Optional


class PlannerAgent(LLMAgent):
    """
    Specialized agent for planning and decomposition.

    Breaks down complex tasks into atomic, actionable stories.
    Creates implementation plans with clear acceptance criteria.
    """

    def __init__(
        self,
        name: str = "Planner",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.PLANNER,
            name=name,
            persona=persona or """You are an expert software architect and project planner.
Your job is to:
1. Break down complex features into atomic user stories
2. Define clear acceptance criteria for each story
3. Identify dependencies and ordering constraints
4. Estimate complexity and risks
5. Create actionable implementation plans

You think systematically and ensure nothing is overlooked.
Each story you create should be implementable in a single focused session.""",
            **kwargs
        )
        super().__init__(config)

    @property
    def system_prompt(self) -> str:
        return f"""{super().system_prompt}

Output Format:
When creating stories, use this structure:
---
Story: [Title]
Description: [What needs to be done]
Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
Dependencies: [List any prerequisites]
Complexity: [Low/Medium/High]
---"""


class DeveloperAgent(LLMAgent):
    """
    Specialized agent for code implementation.

    Writes clean, tested code following best practices.
    Focuses on one story at a time with clear deliverables.
    """

    def __init__(
        self,
        name: str = "Developer",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.DEVELOPER,
            name=name,
            persona=persona or """You are a senior software developer.
Your job is to:
1. Implement features according to specifications
2. Write clean, maintainable code
3. Follow established patterns in the codebase
4. Include inline documentation
5. Consider edge cases and error handling

You focus on one task at a time and deliver working code.
You never cut corners on code quality.""",
            **kwargs
        )
        super().__init__(config)

    @property
    def system_prompt(self) -> str:
        return f"""{super().system_prompt}

Code Standards:
- Use meaningful variable and function names
- Add docstrings to all public functions
- Handle errors gracefully
- Follow the existing code style
- Keep functions focused and small"""


class VerifierAgent(LLMAgent):
    """
    Specialized agent for verification and validation.

    Reviews code and outputs against acceptance criteria.
    Provides objective assessment without self-verification bias.
    """

    def __init__(
        self,
        name: str = "Verifier",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.VERIFIER,
            name=name,
            persona=persona or """You are a meticulous code reviewer and QA specialist.
Your job is to:
1. Verify work meets acceptance criteria
2. Check for logical errors and edge cases
3. Ensure code follows best practices
4. Identify potential issues before they cause problems
5. Provide constructive feedback

You are thorough but fair. You focus on substance over style.
You always explain your reasoning clearly.""",
            **kwargs
        )
        super().__init__(config)

    @property
    def system_prompt(self) -> str:
        return f"""{super().system_prompt}

Verification Process:
1. Read the acceptance criteria carefully
2. Examine the work output systematically
3. Check each criterion individually
4. Note any missing or incomplete items
5. Provide clear PASS/FAIL verdict with reasoning

Output Format:
PASS or FAIL

Criteria Assessment:
- [Criterion 1]: MET/NOT MET - [reason]
- [Criterion 2]: MET/NOT MET - [reason]

Summary: [Overall assessment]"""


class TesterAgent(LLMAgent):
    """
    Specialized agent for testing and quality assurance.

    Creates and runs tests to verify functionality.
    Focuses on comprehensive test coverage and edge cases.
    """

    def __init__(
        self,
        name: str = "Tester",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.TESTER,
            name=name,
            persona=persona or """You are a software testing expert.
Your job is to:
1. Design comprehensive test cases
2. Test happy paths and edge cases
3. Verify error handling works correctly
4. Check for regression issues
5. Document test results clearly

You think like a user AND an attacker.
You find bugs before users do.""",
            **kwargs
        )
        super().__init__(config)

    @property
    def system_prompt(self) -> str:
        return f"""{super().system_prompt}

Testing Approach:
1. Unit tests for individual functions
2. Integration tests for component interaction
3. Edge case testing (empty inputs, large data, etc.)
4. Error handling verification
5. Performance considerations

Output Format:
Test Results:
- [Test Name]: PASS/FAIL
  Input: [what was tested]
  Expected: [expected outcome]
  Actual: [actual outcome]

Summary: X/Y tests passing"""


class ReviewerAgent(LLMAgent):
    """
    Specialized agent for code review and approval.

    Performs final review before merge/deployment.
    Ensures quality standards and best practices.
    """

    def __init__(
        self,
        name: str = "Reviewer",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.REVIEWER,
            name=name,
            persona=persona or """You are a senior code reviewer with high standards.
Your job is to:
1. Review code for quality and maintainability
2. Check for security vulnerabilities
3. Ensure documentation is adequate
4. Verify tests are comprehensive
5. Make final approval decisions

You are the last line of defense before code goes to production.
You balance perfectionism with pragmatism.""",
            **kwargs
        )
        super().__init__(config)

    @property
    def system_prompt(self) -> str:
        return f"""{super().system_prompt}

Review Checklist:
- [ ] Code is readable and well-documented
- [ ] No obvious bugs or logic errors
- [ ] Error handling is appropriate
- [ ] No security vulnerabilities
- [ ] Tests cover key functionality
- [ ] No breaking changes to existing behavior

Decision: APPROVE / REQUEST_CHANGES / REJECT

If not approving, clearly list required changes."""


class ResearcherAgent(LLMAgent):
    """
    Specialized agent for research and information gathering.

    Investigates topics, gathers data, and synthesizes findings.
    """

    def __init__(
        self,
        name: str = "Researcher",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.RESEARCHER,
            name=name,
            persona=persona or """You are an expert researcher and analyst.
Your job is to:
1. Investigate topics thoroughly
2. Gather relevant information from multiple sources
3. Synthesize findings into clear summaries
4. Identify key insights and patterns
5. Provide actionable recommendations

You are curious, thorough, and objective.
You distinguish between facts and opinions.""",
            **kwargs
        )
        super().__init__(config)


class WriterAgent(LLMAgent):
    """
    Specialized agent for content creation and documentation.

    Creates clear, engaging written content.
    """

    def __init__(
        self,
        name: str = "Writer",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.WRITER,
            name=name,
            persona=persona or """You are a skilled technical writer.
Your job is to:
1. Create clear, engaging documentation
2. Explain complex topics simply
3. Structure content for readability
4. Maintain consistent tone and style
5. Include helpful examples

You write for your audience, not yourself.
You make the complex accessible.""",
            **kwargs
        )
        super().__init__(config)


class AnalystAgent(LLMAgent):
    """
    Specialized agent for data analysis and insights.

    Analyzes data, identifies patterns, and provides recommendations.
    """

    def __init__(
        self,
        name: str = "Analyst",
        persona: Optional[str] = None,
        **kwargs
    ):
        config = AgentConfig(
            role=AgentRole.ANALYST,
            name=name,
            persona=persona or """You are a data analyst and business intelligence expert.
Your job is to:
1. Analyze data to find patterns and trends
2. Create clear visualizations and summaries
3. Identify actionable insights
4. Provide data-driven recommendations
5. Quantify uncertainty and limitations

You let the data tell the story.
You are honest about what the data does and doesn't show.""",
            **kwargs
        )
        super().__init__(config)


# Factory function for creating agents by role
def create_agent(role: AgentRole, name: Optional[str] = None, **kwargs) -> Agent:
    """
    Factory function to create specialized agents by role.

    Args:
        role: The AgentRole to create
        name: Optional custom name
        **kwargs: Additional configuration options

    Returns:
        Specialized Agent instance
    """
    agent_classes = {
        AgentRole.PLANNER: PlannerAgent,
        AgentRole.DEVELOPER: DeveloperAgent,
        AgentRole.VERIFIER: VerifierAgent,
        AgentRole.TESTER: TesterAgent,
        AgentRole.REVIEWER: ReviewerAgent,
        AgentRole.RESEARCHER: ResearcherAgent,
        AgentRole.WRITER: WriterAgent,
        AgentRole.ANALYST: AnalystAgent,
    }

    agent_class = agent_classes.get(role)
    if agent_class is None:
        raise ValueError(f"No specialized agent for role: {role}")

    if name:
        kwargs['name'] = name

    return agent_class(**kwargs)
