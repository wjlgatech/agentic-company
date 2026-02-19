"""
Test Critical Fixes for Agenticom

This test verifies the fixes for the issues identified in the capability test:
1. CRITICAL #1: CLI workflow execution was mocked (now real)
2. CRITICAL #2: YAML parser used wrong field for role mapping (now fixed)
"""

from pathlib import Path


class TestYAMLParserFix:
    """Test that the YAML parser correctly handles bundled workflows."""

    def test_feature_dev_workflow_loads(self):
        """Test that feature-dev.yaml loads successfully."""
        from orchestration.workflows.parser import load_workflow

        team = load_workflow("agenticom/bundled_workflows/feature-dev.yaml")

        # Verify agents are loaded
        assert len(team.agents) == 5, f"Expected 5 agents, got {len(team.agents)}"

        # Verify agent roles are correct
        from orchestration.agents.base import AgentRole

        expected_roles = {
            AgentRole.PLANNER,
            AgentRole.DEVELOPER,
            AgentRole.VERIFIER,
            AgentRole.TESTER,
            AgentRole.REVIEWER,
        }
        actual_roles = set(team.agents.keys())
        assert actual_roles == expected_roles, (
            f"Expected {expected_roles}, got {actual_roles}"
        )

        # Verify steps are loaded
        assert len(team.steps) == 5, f"Expected 5 steps, got {len(team.steps)}"

        print("✅ feature-dev.yaml loads correctly")

    def test_marketing_campaign_workflow_loads(self):
        """Test that marketing-campaign.yaml loads successfully."""
        from orchestration.workflows.parser import load_workflow

        team = load_workflow("agenticom/bundled_workflows/marketing-campaign.yaml")

        # Verify agents are loaded (some map to same role so count is less than 5)
        assert len(team.agents) >= 4, (
            f"Expected at least 4 agents, got {len(team.agents)}"
        )

        # Verify steps are loaded
        assert len(team.steps) == 5, f"Expected 5 steps, got {len(team.steps)}"

        print("✅ marketing-campaign.yaml loads correctly")

    def test_parser_reads_id_for_role(self):
        """Test that parser uses 'id' field for role mapping."""
        from orchestration.workflows.parser import WorkflowParser

        parser = WorkflowParser()
        definition = parser.parse_file(
            Path("agenticom/bundled_workflows/feature-dev.yaml")
        )

        # Check that agents have correct role keys
        for agent in definition.agents:
            assert agent.role in [
                "planner",
                "developer",
                "verifier",
                "tester",
                "reviewer",
            ], f"Agent role should be a valid key, got: {agent.role}"

        print("✅ Parser correctly uses 'id' for role mapping")

    def test_parser_preserves_persona_from_prompt(self):
        """Test that parser preserves persona/prompt content."""
        from orchestration.workflows.parser import WorkflowParser

        parser = WorkflowParser()
        definition = parser.parse_file(
            Path("agenticom/bundled_workflows/feature-dev.yaml")
        )

        for agent in definition.agents:
            assert agent.persona, f"Agent {agent.name} should have persona"
            assert len(agent.persona) > 50, (
                f"Agent {agent.name} persona should be substantive"
            )

        print("✅ Parser preserves persona from prompt field")


class TestCLIWorkflowExecution:
    """Test that CLI workflow execution is real, not mocked."""

    def test_workflow_run_not_mocked(self):
        """Verify the workflow run command doesn't use time.sleep mock."""
        from pathlib import Path

        # Read the CLI source file directly
        cli_path = Path("orchestration/cli.py")
        source = cli_path.read_text()

        # Check that it doesn't have the old mock pattern
        assert "time.sleep(1)  # Simulate processing" not in source, (
            "CLI still contains mock sleep pattern!"
        )

        # Check that it doesn't have the fake result pattern
        assert 'output": f"Processed result for:' not in source, (
            "CLI still contains fake result pattern!"
        )

        # Check that it imports real workflow execution
        assert "load_workflow" in source, "CLI should use real workflow loading"
        assert "auto_setup_executor" in source, "CLI should use auto_setup_executor"

        print("✅ CLI workflow run is not mocked")

    def test_workflow_dry_run_works(self):
        """Test that dry-run mode shows workflow plan without executing."""
        from click.testing import CliRunner

        from orchestration.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["workflow", "run", "feature-dev", "-i", "Test task", "--dry-run"]
        )

        # Should succeed with dry run
        assert result.exit_code == 0, f"Dry run failed: {result.output}"

        # Should show workflow plan
        assert "Workflow Plan" in result.output, "Dry run should show workflow plan"
        assert "plan" in result.output, "Should show plan step"
        assert "implement" in result.output, "Should show implement step"

        print("✅ CLI dry-run mode works")

    def test_workflow_run_requires_backend(self):
        """Test that running workflow fails gracefully without LLM backend."""
        import os
        from unittest.mock import patch

        from click.testing import CliRunner

        from orchestration.cli import main

        # Ensure no API keys are set
        old_keys = {}
        for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            if key in os.environ:
                old_keys[key] = os.environ.pop(key)

        try:
            runner = CliRunner()
            # Also mock out Ollama so it doesn't accidentally connect to a local instance
            with (
                patch(
                    "orchestration.integrations.ollama.is_ollama_running",
                    return_value=False,
                ),
                patch(
                    "orchestration.integrations.unified.is_ollama_running",
                    return_value=False,
                ),
            ):
                result = runner.invoke(
                    main, ["workflow", "run", "feature-dev", "-i", "Test task"]
                )

            # Should fail with helpful message
            assert result.exit_code == 1, "Should fail without LLM backend"
            assert (
                "No LLM backend ready" in result.output
                or "ANTHROPIC_API_KEY" in result.output
            ), "Should show helpful error about missing backend"

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
        result = runner.invoke(main, ["workflow", "list"])

        assert result.exit_code == 0, f"Workflow list failed: {result.output}"

        # Should find bundled workflows
        assert "feature-dev" in result.output, "Should find feature-dev workflow"
        assert "marketing-campaign" in result.output, (
            "Should find marketing-campaign workflow"
        )

        # Should show agent and step counts (from real parsing)
        assert "5" in result.output, "Should show step count of 5"

        print("✅ Workflow list discovers actual YAML files")


class TestAgentTeamExecution:
    """Test that AgentTeam execution works correctly."""

    def test_team_has_run_method(self):
        """Test that AgentTeam has async run method."""
        from orchestration.agents.team import AgentTeam, TeamConfig

        team = AgentTeam(TeamConfig(name="test"))
        assert hasattr(team, "run"), "AgentTeam should have run method"
        assert callable(team.run), "run should be callable"

        import asyncio

        assert asyncio.iscoroutinefunction(team.run), "run should be async"

        print("✅ AgentTeam has async run method")

    def test_agent_requires_executor(self):
        """Test that agents require executor to be set."""
        import asyncio

        from orchestration.agents.specialized import PlannerAgent

        agent = PlannerAgent()
        assert agent._executor is None, "New agent should not have executor"

        # Executing without executor should return failure result
        async def try_execute():
            return await agent.execute("test task")

        result = asyncio.run(try_execute())

        # Should return AgentResult with success=False
        assert not result.success, "Should fail without executor"
        assert "executor not set" in result.error.lower(), (
            f"Error should mention executor: {result.error}"
        )

        print("✅ Agent correctly requires executor")


class TestWorkflowExecutorWiring:
    """Test that workflow loading can wire executors correctly."""

    def test_load_workflow_without_auto_setup(self):
        """Test that load_workflow() without auto_setup doesn't set executors."""
        from orchestration.workflows import load_workflow

        team = load_workflow("agenticom/bundled_workflows/feature-dev.yaml")

        # Verify agents don't have executors
        for role, agent in team.agents.items():
            assert agent._executor is None, (
                f"Agent {role} should not have executor without auto_setup"
            )

        print("✅ load_workflow() correctly leaves executors unset")

    def test_load_workflow_with_auto_setup_needs_backend(self):
        """Test that load_workflow(auto_setup=True) requires LLM backend."""
        import os

        from orchestration.workflows import load_workflow

        # Ensure no API keys
        old_keys = {}
        for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            if key in os.environ:
                old_keys[key] = os.environ.pop(key)

        try:
            try:
                load_workflow(
                    "agenticom/bundled_workflows/feature-dev.yaml", auto_setup=True
                )
                # If we get here, a backend was available
                print("✅ load_workflow(auto_setup=True) configured executors")
            except RuntimeError as e:
                assert "No LLM backend" in str(e), (
                    f"Should mention missing backend: {e}"
                )
                print(
                    "✅ load_workflow(auto_setup=True) correctly requires LLM backend"
                )
        finally:
            for key, value in old_keys.items():
                os.environ[key] = value

    def test_load_ready_workflow_requires_backend(self):
        """Test that load_ready_workflow() requires LLM backend."""
        import os

        from orchestration.workflows import load_ready_workflow

        # Ensure no API keys
        old_keys = {}
        for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            if key in os.environ:
                old_keys[key] = os.environ.pop(key)

        try:
            try:
                load_ready_workflow(
                    "agenticom/bundled_workflows/feature-dev.yaml"
                )
                print(
                    "✅ load_ready_workflow() configured executors (backend available)"
                )
            except RuntimeError as e:
                assert "No LLM backend" in str(e), (
                    f"Should mention missing backend: {e}"
                )
                print("✅ load_ready_workflow() correctly requires LLM backend")
        finally:
            for key, value in old_keys.items():
                os.environ[key] = value

    def test_load_ready_workflow_exported(self):
        """Test that load_ready_workflow is properly exported."""
        from orchestration import load_ready_workflow
        from orchestration.workflows import load_ready_workflow as lr2

        assert load_ready_workflow is lr2, "Should be same function"
        assert callable(load_ready_workflow), "Should be callable"

        print("✅ load_ready_workflow correctly exported")


class TestExecutorActuallyWorks:
    """Integration tests that verify actual executor wiring (not just API contracts)."""

    def test_executor_property_exists(self):
        """Test that agents have public executor property."""
        from orchestration.agents.specialized import PlannerAgent

        agent = PlannerAgent()
        assert hasattr(agent, "executor"), "Agent should have executor property"
        assert hasattr(agent, "has_executor"), "Agent should have has_executor property"
        assert agent.executor is None, "New agent should have None executor"
        assert agent.has_executor is False, "New agent should not have executor"

        print("✅ Agent has executor property")

    def test_set_executor_actually_sets(self):
        """Test that set_executor() actually sets the executor."""
        from orchestration.agents.specialized import PlannerAgent

        agent = PlannerAgent()

        # Define a mock executor
        async def mock_executor(prompt, context):
            return "mock response"

        # Set it
        agent.set_executor(mock_executor)

        # Verify it's actually set
        assert agent.executor is not None, "Executor should be set after set_executor()"
        assert agent.has_executor is True, "has_executor should be True"
        assert agent.executor is mock_executor, "Executor should be the one we set"
        assert agent._executor is mock_executor, "_executor should match"

        print("✅ set_executor() actually sets the executor")

    def test_auto_setup_executor_eager_init(self):
        """Test that auto_setup_executor with eager_init=True initializes backend."""

        from orchestration.integrations import auto_setup_executor
        from orchestration.integrations.unified import get_ready_backends

        ready = get_ready_backends()
        if not ready:
            print("⚠️ No backend available - skipping eager_init test")
            return

        executor = auto_setup_executor(eager_init=True)
        assert executor.active_backend is not None, (
            "active_backend should be set with eager_init"
        )
        print(f"✅ auto_setup_executor eager_init works: {executor.active_backend}")

    def test_load_ready_workflow_sets_executors(self):
        """Test that load_ready_workflow actually sets executors on agents."""
        from orchestration.integrations.unified import get_ready_backends

        ready = get_ready_backends()
        if not ready:
            print("⚠️ No backend available - skipping executor wiring test")
            return

        from orchestration.workflows import load_ready_workflow

        team = load_ready_workflow("agenticom/bundled_workflows/feature-dev.yaml")

        # Check every agent has executor set
        for role, agent in team.agents.items():
            assert agent.has_executor, f"Agent {role} should have executor"
            assert agent.executor is not None, (
                f"Agent {role} executor should not be None"
            )

        print(f"✅ load_ready_workflow sets executors on all {len(team.agents)} agents")


def run_all_tests():
    """Run all tests and report results."""
    import traceback

    test_classes = [
        TestYAMLParserFix,
        TestCLIWorkflowExecution,
        TestWorkflowListDiscovery,
        TestAgentTeamExecution,
        TestWorkflowExecutorWiring,
        TestExecutorActuallyWorks,
    ]

    total = 0
    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"Running {test_class.__name__}")
        print("=" * 60)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    passed += 1
                except Exception as e:
                    failed += 1
                    print(f"❌ {method_name}: {e}")
                    traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} tests passed")
    if failed:
        print(f"         {failed} tests FAILED")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    success = run_all_tests()
    sys.exit(0 if success else 1)
