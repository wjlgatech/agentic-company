"""
Test Critical Fixes for Agenticom

This test verifies the fixes for the issues identified in the capability test:
1. CRITICAL #1: CLI workflow execution was mocked (now real)
2. CRITICAL #2: YAML parser used wrong field for role mapping (now fixed)
"""

import pytest
from pathlib import Path


class TestYAMLParserFix:
    """Test that the YAML parser correctly handles bundled workflows."""

    def test_feature_dev_workflow_loads(self):
        """Test that feature-dev.yaml loads successfully."""
        from orchestration.workflows.parser import load_workflow

        team = load_workflow('agenticom/bundled_workflows/feature-dev.yaml')

        # Verify agents are loaded
        assert len(team.agents) == 5, f"Expected 5 agents, got {len(team.agents)}"

        # Verify agent roles are correct
        from orchestration.agents.base import AgentRole
        expected_roles = {AgentRole.PLANNER, AgentRole.DEVELOPER, AgentRole.VERIFIER, AgentRole.TESTER, AgentRole.REVIEWER}
        actual_roles = set(team.agents.keys())
        assert actual_roles == expected_roles, f"Expected {expected_roles}, got {actual_roles}"

        # Verify steps are loaded
        assert len(team.steps) == 5, f"Expected 5 steps, got {len(team.steps)}"

        print("✅ feature-dev.yaml loads correctly")

    def test_marketing_campaign_workflow_loads(self):
        """Test that marketing-campaign.yaml loads successfully."""
        from orchestration.workflows.parser import load_workflow

        team = load_workflow('agenticom/bundled_workflows/marketing-campaign.yaml')

        # Verify agents are loaded (some map to same role so count is less than 5)
        assert len(team.agents) >= 4, f"Expected at least 4 agents, got {len(team.agents)}"

        # Verify steps are loaded
        assert len(team.steps) == 5, f"Expected 5 steps, got {len(team.steps)}"

        print("✅ marketing-campaign.yaml loads correctly")

    def test_parser_reads_id_for_role(self):
        """Test that parser uses 'id' field for role mapping."""
        from orchestration.workflows.parser import WorkflowParser

        parser = WorkflowParser()
        definition = parser.parse_file(Path('agenticom/bundled_workflows/feature-dev.yaml'))

        # Check that agents have correct role keys
        for agent in definition.agents:
            assert agent.role in ['planner', 'developer', 'verifier', 'tester', 'reviewer'], \
                f"Agent role should be a valid key, got: {agent.role}"

        print("✅ Parser correctly uses 'id' for role mapping")

    def test_parser_preserves_persona_from_prompt(self):
        """Test that parser preserves persona/prompt content."""
        from orchestration.workflows.parser import WorkflowParser

        parser = WorkflowParser()
        definition = parser.parse_file(Path('agenticom/bundled_workflows/feature-dev.yaml'))

        for agent in definition.agents:
            assert agent.persona, f"Agent {agent.name} should have persona"
            assert len(agent.persona) > 50, f"Agent {agent.name} persona should be substantive"

        print("✅ Parser preserves persona from prompt field")


class TestCLIWorkflowExecution:
    """Test that CLI workflow execution is real, not mocked."""

    def test_workflow_run_not_mocked(self):
        """Verify the workflow run command doesn't use time.sleep mock."""
        from pathlib import Path

        # Read the CLI source file directly
        cli_path = Path('orchestration/cli.py')
        source = cli_path.read_text()

        # Check that it doesn't have the old mock pattern
        assert 'time.sleep(1)  # Simulate processing' not in source, \
            "CLI still contains mock sleep pattern!"

        # Check that it doesn't have the fake result pattern
        assert 'output": f"Processed result for:' not in source, \
            "CLI still contains fake result pattern!"

        # Check that it imports real workflow execution
        assert 'load_workflow' in source, "CLI should use real workflow loading"
        assert 'auto_setup_executor' in source, "CLI should use auto_setup_executor"

        print("✅ CLI workflow run is not mocked")

    def test_workflow_dry_run_works(self):
        """Test that dry-run mode shows workflow plan without executing."""
        from click.testing import CliRunner
        from orchestration.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ['workflow', 'run', 'feature-dev', '-i', 'Test task', '--dry-run'])

        # Should succeed with dry run
        assert result.exit_code == 0, f"Dry run failed: {result.output}"

        # Should show workflow plan
        assert 'Workflow Plan' in result.output, "Dry run should show workflow plan"
        assert 'plan' in result.output, "Should show plan step"
        assert 'implement' in result.output, "Should show implement step"

        print("✅ CLI dry-run mode works")

    def test_workflow_run_requires_backend(self):
        """Test that running workflow fails gracefully without LLM backend."""
        from click.testing import CliRunner
        from orchestration.cli import main
        import os

        # Ensure no API keys are set
        old_keys = {}
        for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']:
            if key in os.environ:
                old_keys[key] = os.environ.pop(key)

        try:
            runner = CliRunner()
            result = runner.invoke(main, ['workflow', 'run', 'feature-dev', '-i', 'Test task'])

            # Should fail with helpful message
            assert result.exit_code == 1, "Should fail without LLM backend"
            assert 'No LLM backend ready' in result.output or 'ANTHROPIC_API_KEY' in result.output, \
                "Should show helpful error about missing backend"

            print("✅ CLI shows helpful error when no LLM backend")
        finally:
            # Restore keys
            for key, value in old_keys.items():
                os.environ[key] = value


class TestWorkflowListDiscovery:
    """Test that workflow list discovers actual workflows."""

    def test_workflow_list_discovers_files(self):
        """Test that workflow list finds actual YAML files."""
        from click.testing import CliRunner
        from orchestration.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ['workflow', 'list'])

        assert result.exit_code == 0, f"Workflow list failed: {result.output}"

        # Should find bundled workflows
        assert 'feature-dev' in result.output, "Should find feature-dev workflow"
        assert 'marketing-campaign' in result.output, "Should find marketing-campaign workflow"

        # Should show agent and step counts (from real parsing)
        assert '5' in result.output, "Should show step count of 5"

        print("✅ Workflow list discovers actual YAML files")


class TestAgentTeamExecution:
    """Test that AgentTeam execution works correctly."""

    def test_team_has_run_method(self):
        """Test that AgentTeam has async run method."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))
        assert hasattr(team, 'run'), "AgentTeam should have run method"
        assert callable(team.run), "run should be callable"

        import asyncio
        assert asyncio.iscoroutinefunction(team.run), "run should be async"

        print("✅ AgentTeam has async run method")

    def test_agent_requires_executor(self):
        """Test that agents require executor to be set."""
        from orchestration.agents.specialized import PlannerAgent
        import asyncio

        agent = PlannerAgent()
        assert agent._executor is None, "New agent should not have executor"

        # Executing without executor should return failure result
        async def try_execute():
            return await agent.execute("test task")

        result = asyncio.run(try_execute())

        # Should return AgentResult with success=False
        assert not result.success, "Should fail without executor"
        assert "executor not set" in result.error.lower(), f"Error should mention executor: {result.error}"

        print("✅ Agent correctly requires executor")


def run_all_tests():
    """Run all tests and report results."""
    import traceback

    test_classes = [
        TestYAMLParserFix,
        TestCLIWorkflowExecution,
        TestWorkflowListDiscovery,
        TestAgentTeamExecution,
    ]

    total = 0
    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                total += 1
                try:
                    getattr(instance, method_name)()
                    passed += 1
                except Exception as e:
                    failed += 1
                    print(f"❌ {method_name}: {e}")
                    traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} tests passed")
    if failed:
        print(f"         {failed} tests FAILED")
    print('='*60)

    return failed == 0


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    success = run_all_tests()
    sys.exit(0 if success else 1)
