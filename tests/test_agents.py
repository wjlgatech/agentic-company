"""
Tests for Multi-Agent Team Orchestration

Tests the Agent, AgentTeam, and YAML workflow functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from orchestration.agents.base import (
    Agent,
    AgentRole,
    AgentConfig,
    AgentContext,
    AgentResult,
    MockAgent,
    LLMAgent,
)
from orchestration.agents.team import (
    AgentTeam,
    TeamConfig,
    TeamBuilder,
    WorkflowStep,
    StepStatus,
    create_feature_dev_team,
    create_bug_fix_team,
    create_security_audit_team,
)
from orchestration.agents.specialized import (
    PlannerAgent,
    DeveloperAgent,
    VerifierAgent,
    TesterAgent,
    ReviewerAgent,
    create_agent,
)
from orchestration.workflows.parser import (
    WorkflowParser,
    WorkflowDefinition,
    load_workflow,
)
from orchestration.workflows.templates import (
    FEATURE_DEV_TEMPLATE,
    init_workflow,
    list_templates,
)


class TestAgentBase:
    """Test base Agent functionality"""

    def test_agent_config_creation(self):
        """Test creating agent configuration"""
        config = AgentConfig(
            role=AgentRole.DEVELOPER,
            name="Test Developer",
            persona="A helpful developer",
            guardrails=["content-filter"],
        )
        assert config.role == AgentRole.DEVELOPER
        assert config.name == "Test Developer"
        assert "content-filter" in config.guardrails

    def test_mock_agent_creation(self):
        """Test creating mock agent"""
        config = AgentConfig(role=AgentRole.PLANNER, name="Test Planner")
        agent = MockAgent(config, mock_output="Test output")

        assert agent.role == AgentRole.PLANNER
        assert agent.name == "Test Planner"

    @pytest.mark.asyncio
    async def test_mock_agent_execute(self):
        """Test mock agent execution"""
        config = AgentConfig(role=AgentRole.DEVELOPER, name="Dev")
        agent = MockAgent(config, mock_output="Code written")

        result = await agent.execute("Write some code")

        assert result.success
        assert result.output == "Code written"
        assert result.agent_role == AgentRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_mock_agent_execute_without_mock_output(self):
        """Test mock agent returns formatted input when no mock output"""
        config = AgentConfig(role=AgentRole.TESTER, name="Tester")
        agent = MockAgent(config)

        result = await agent.execute("Test the code")

        assert result.success
        assert "[tester] Processed: Test the code" in result.output

    @pytest.mark.asyncio
    async def test_mock_agent_failure(self):
        """Test mock agent failure mode"""
        config = AgentConfig(role=AgentRole.DEVELOPER, name="Dev")
        agent = MockAgent(config, should_fail=True, fail_message="Simulated error")

        result = await agent.execute("Do something")

        assert not result.success
        assert "Simulated error" in result.error

    def test_agent_system_prompt(self):
        """Test agent system prompt generation"""
        config = AgentConfig(
            role=AgentRole.REVIEWER,
            name="Code Reviewer",
            persona="A strict but fair reviewer"
        )
        agent = MockAgent(config)

        prompt = agent.system_prompt
        assert "Code Reviewer" in prompt
        assert "reviewer" in prompt
        assert "strict but fair" in prompt


class TestSpecializedAgents:
    """Test specialized agent classes"""

    def test_planner_agent_creation(self):
        """Test creating planner agent"""
        agent = PlannerAgent(name="Project Planner")
        assert agent.role == AgentRole.PLANNER
        assert "plan" in agent.system_prompt.lower()

    def test_developer_agent_creation(self):
        """Test creating developer agent"""
        agent = DeveloperAgent()
        assert agent.role == AgentRole.DEVELOPER
        assert "code" in agent.system_prompt.lower()

    def test_verifier_agent_creation(self):
        """Test creating verifier agent"""
        agent = VerifierAgent()
        assert agent.role == AgentRole.VERIFIER
        assert "verify" in agent.system_prompt.lower()

    def test_tester_agent_creation(self):
        """Test creating tester agent"""
        agent = TesterAgent()
        assert agent.role == AgentRole.TESTER
        assert "test" in agent.system_prompt.lower()

    def test_reviewer_agent_creation(self):
        """Test creating reviewer agent"""
        agent = ReviewerAgent()
        assert agent.role == AgentRole.REVIEWER
        assert "review" in agent.system_prompt.lower()

    def test_create_agent_factory(self):
        """Test agent factory function"""
        agent = create_agent(AgentRole.PLANNER, name="Custom Planner")
        assert agent.role == AgentRole.PLANNER
        assert agent.name == "Custom Planner"

    def test_create_agent_unknown_role(self):
        """Test factory with unknown role raises error"""
        with pytest.raises(ValueError):
            create_agent(AgentRole.CUSTOM)


class TestAgentTeam:
    """Test AgentTeam orchestration"""

    def test_team_creation(self):
        """Test creating agent team"""
        config = TeamConfig(name="Test Team", description="A test team")
        team = AgentTeam(config)

        assert team.config.name == "Test Team"
        assert len(team.agents) == 0
        assert len(team.steps) == 0

    def test_add_agents_to_team(self):
        """Test adding agents to team"""
        config = TeamConfig(name="Dev Team")
        team = AgentTeam(config)

        planner = MockAgent(AgentConfig(role=AgentRole.PLANNER, name="Planner"))
        developer = MockAgent(AgentConfig(role=AgentRole.DEVELOPER, name="Developer"))

        team.add_agent(planner).add_agent(developer)

        assert AgentRole.PLANNER in team.agents
        assert AgentRole.DEVELOPER in team.agents
        assert len(team.agents) == 2

    def test_add_steps_to_team(self):
        """Test adding workflow steps"""
        config = TeamConfig(name="Dev Team")
        team = AgentTeam(config)

        step = WorkflowStep(
            id="plan",
            name="Planning",
            agent_role=AgentRole.PLANNER,
            input_template="Create plan for: {task}",
            expects="A detailed plan"
        )

        team.add_step(step)

        assert len(team.steps) == 1
        assert team.steps[0].id == "plan"

    @pytest.mark.asyncio
    async def test_team_run_simple_workflow(self):
        """Test running simple workflow"""
        config = TeamConfig(name="Simple Team")
        team = AgentTeam(config)

        # Add mock agents
        planner = MockAgent(
            AgentConfig(role=AgentRole.PLANNER, name="Planner"),
            mock_output="Plan: Step 1, Step 2"
        )
        team.add_agent(planner)

        # Add step
        team.add_step(WorkflowStep(
            id="plan",
            name="Planning",
            agent_role=AgentRole.PLANNER,
            input_template="Create plan for: {task}"
        ))

        result = await team.run("Build a website")

        assert result.success
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_team_run_multi_step_workflow(self):
        """Test running multi-step workflow"""
        config = TeamConfig(name="Full Team")
        team = AgentTeam(config)

        # Add agents
        team.add_agent(MockAgent(
            AgentConfig(role=AgentRole.PLANNER, name="Planner"),
            mock_output="Plan created"
        ))
        team.add_agent(MockAgent(
            AgentConfig(role=AgentRole.DEVELOPER, name="Developer"),
            mock_output="Code written"
        ))

        # Add steps
        team.add_step(WorkflowStep(
            id="plan",
            name="Planning",
            agent_role=AgentRole.PLANNER,
            input_template="Plan: {task}"
        ))
        team.add_step(WorkflowStep(
            id="implement",
            name="Implementation",
            agent_role=AgentRole.DEVELOPER,
            input_template="Implement: {plan}"
        ))

        result = await team.run("Build feature")

        assert result.success
        assert len(result.steps) == 2
        assert result.final_output == "Code written"

    @pytest.mark.asyncio
    async def test_team_step_failure_abort(self):
        """Test workflow aborts on step failure"""
        config = TeamConfig(name="Failing Team")
        team = AgentTeam(config)

        team.add_agent(MockAgent(
            AgentConfig(role=AgentRole.PLANNER, name="Planner"),
            should_fail=True,
            fail_message="Planning failed"
        ))

        team.add_step(WorkflowStep(
            id="plan",
            name="Planning",
            agent_role=AgentRole.PLANNER,
            input_template="Plan: {task}",
            max_retries=0,
            on_fail="abort"
        ))

        result = await team.run("Build feature")

        assert not result.success
        assert "failed" in result.error.lower()


class TestTeamBuilder:
    """Test TeamBuilder fluent API"""

    def test_basic_team_building(self):
        """Test building team with builder"""
        team = (TeamBuilder("test-team", "Test description")
            .with_planner()
            .with_developer()
            .step("plan", AgentRole.PLANNER, "Plan: {task}")
            .step("develop", AgentRole.DEVELOPER, "Develop: {plan}")
            .build())

        assert team.config.name == "test-team"
        assert AgentRole.PLANNER in team.agents
        assert AgentRole.DEVELOPER in team.agents
        assert len(team.steps) == 2

    def test_team_builder_with_all_agents(self):
        """Test builder with all standard agents"""
        team = (TeamBuilder("full-team")
            .with_planner()
            .with_developer()
            .with_verifier()
            .with_tester()
            .with_reviewer()
            .build())

        assert len(team.agents) == 5

    def test_team_builder_with_verification(self):
        """Test builder with cross-verification"""
        team = (TeamBuilder("verified-team")
            .with_developer()
            .with_verifier()
            .step(
                "develop",
                AgentRole.DEVELOPER,
                "Develop: {task}",
                verified_by=AgentRole.VERIFIER,
                expects="Working code"
            )
            .build())

        assert team.steps[0].verified_by == AgentRole.VERIFIER
        assert team.steps[0].expects == "Working code"

    def test_team_builder_with_approval(self):
        """Test builder with approval step"""
        team = (TeamBuilder("approval-team")
            .with_reviewer()
            .step(
                "review",
                AgentRole.REVIEWER,
                "Review: {task}",
                requires_approval=True
            )
            .build())

        assert team.steps[0].requires_approval


class TestPrebuiltTeams:
    """Test pre-built team factories"""

    def test_feature_dev_team(self):
        """Test feature development team"""
        team = create_feature_dev_team()

        assert team.config.name == "feature-dev"
        assert AgentRole.PLANNER in team.agents
        assert AgentRole.DEVELOPER in team.agents
        assert AgentRole.VERIFIER in team.agents
        assert AgentRole.TESTER in team.agents
        assert AgentRole.REVIEWER in team.agents
        assert len(team.steps) == 4

    def test_bug_fix_team(self):
        """Test bug fix team"""
        team = create_bug_fix_team()

        assert team.config.name == "bug-fix"
        assert len(team.steps) == 3

    def test_security_audit_team(self):
        """Test security audit team"""
        team = create_security_audit_team()

        assert team.config.name == "security-audit"
        assert len(team.steps) == 4


class TestWorkflowParser:
    """Test YAML workflow parsing"""

    def test_parse_simple_workflow(self):
        """Test parsing simple YAML workflow"""
        yaml_content = """
id: test-workflow
name: Test Workflow
description: A test workflow

agents:
  - role: planner
    name: Test Planner

steps:
  - id: plan
    agent: planner
    input: "Create plan for: {task}"
    expects: "A detailed plan"
"""
        parser = WorkflowParser()
        definition = parser.parse(yaml_content)

        assert definition.id == "test-workflow"
        assert definition.name == "Test Workflow"
        assert len(definition.agents) == 1
        assert len(definition.steps) == 1
        assert definition.agents[0].role == "planner"

    def test_parse_workflow_with_verification(self):
        """Test parsing workflow with verification"""
        yaml_content = """
id: verified-workflow
name: Verified Workflow

agents:
  - role: developer
  - role: verifier

steps:
  - id: develop
    agent: developer
    input: "Develop: {task}"
    verified_by: verifier
    expects: "Working code"
"""
        parser = WorkflowParser()
        definition = parser.parse(yaml_content)

        assert definition.steps[0].verified_by == "verifier"

    def test_convert_to_team(self):
        """Test converting definition to AgentTeam"""
        yaml_content = """
id: team-workflow
name: Team Workflow

agents:
  - role: planner
  - role: developer

steps:
  - id: plan
    agent: planner
    input: "Plan: {task}"
  - id: develop
    agent: developer
    input: "Develop: {plan}"
"""
        parser = WorkflowParser()
        definition = parser.parse(yaml_content)
        team = parser.to_team(definition)

        assert team.config.name == "Team Workflow"
        assert AgentRole.PLANNER in team.agents
        assert AgentRole.DEVELOPER in team.agents
        assert len(team.steps) == 2

    def test_parse_feature_dev_template(self):
        """Test parsing the feature-dev template"""
        parser = WorkflowParser()
        definition = parser.parse(FEATURE_DEV_TEMPLATE)

        assert definition.id == "feature-dev"
        assert len(definition.agents) == 5
        assert len(definition.steps) == 4


class TestWorkflowTemplates:
    """Test workflow templates"""

    def test_list_templates(self):
        """Test listing available templates"""
        templates = list_templates()

        assert "feature-dev" in templates
        assert "bug-fix" in templates
        assert "security-audit" in templates
        assert "content-research" in templates

    def test_init_workflow_creates_file(self, tmp_path):
        """Test init_workflow creates file"""
        output_file = tmp_path / "test-workflow.yaml"

        result = init_workflow("feature-dev", output_file)

        assert result.exists()
        content = result.read_text()
        assert "feature-dev" in content
        assert "planner" in content

    def test_init_workflow_unknown_template(self, tmp_path):
        """Test init_workflow with unknown template raises error"""
        with pytest.raises(ValueError):
            init_workflow("unknown-template", tmp_path / "test.yaml")

    def test_init_workflow_no_overwrite(self, tmp_path):
        """Test init_workflow doesn't overwrite by default"""
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("existing content")

        with pytest.raises(FileExistsError):
            init_workflow("feature-dev", output_file)

    def test_init_workflow_with_overwrite(self, tmp_path):
        """Test init_workflow can overwrite"""
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("existing content")

        result = init_workflow("feature-dev", output_file, overwrite=True)

        assert result.exists()
        assert "feature-dev" in result.read_text()


class TestCrossVerification:
    """Test cross-verification functionality"""

    @pytest.mark.asyncio
    async def test_agent_verify_pass(self):
        """Test verification that passes"""
        config = AgentConfig(role=AgentRole.VERIFIER, name="Verifier")
        verifier = MockAgent(config, mock_output="PASS - All criteria met")

        result = AgentResult(
            agent_id="dev-1",
            agent_role=AgentRole.DEVELOPER,
            step_id="step-1",
            output="Code implementation",
            success=True
        )

        verification = await verifier.verify(result, "Code must compile")

        assert verification.passed
        assert "PASS" in verification.reasoning

    @pytest.mark.asyncio
    async def test_agent_verify_fail(self):
        """Test verification that fails"""
        config = AgentConfig(role=AgentRole.VERIFIER, name="Verifier")
        verifier = MockAgent(config, mock_output="FAIL - Missing error handling")

        result = AgentResult(
            agent_id="dev-1",
            agent_role=AgentRole.DEVELOPER,
            step_id="step-1",
            output="Code implementation",
            success=True
        )

        verification = await verifier.verify(result, "Code must have error handling")

        assert not verification.passed
        assert "FAIL" in verification.reasoning


class TestGuardrailIntegration:
    """Test guardrail integration with agents"""

    @pytest.mark.asyncio
    async def test_agent_with_guardrails(self):
        """Test agent with guardrail pipeline"""
        from orchestration import GuardrailPipeline, ContentFilter

        config = AgentConfig(role=AgentRole.DEVELOPER, name="Dev")
        agent = MockAgent(config, mock_output="Safe output")

        # Create guardrail that blocks "hack"
        guardrails = GuardrailPipeline([
            ContentFilter(blocked_topics=["hack"])
        ])
        agent.set_guardrails(guardrails)

        # Safe input should pass
        result = await agent.execute("Write a function")
        assert result.success

    @pytest.mark.asyncio
    async def test_agent_guardrail_blocks_input(self):
        """Test guardrail blocking harmful input"""
        from orchestration import GuardrailPipeline, ContentFilter

        config = AgentConfig(role=AgentRole.DEVELOPER, name="Dev")
        agent = MockAgent(config, mock_output="Safe output")

        guardrails = GuardrailPipeline([
            ContentFilter(blocked_topics=["hack", "malware"])
        ])
        agent.set_guardrails(guardrails)

        # Harmful input should be blocked
        result = await agent.execute("Write a hack tool")
        assert not result.success
        assert "guardrail" in result.error.lower()
