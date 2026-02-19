"""
Tests for orchestration/mcp_server.py — list_teams, get_team_details,
run_team, execute_step, create_custom_team.
"""

import copy

import pytest

from orchestration.mcp_server import (
    TEAMS,
    create_custom_team,
    execute_step,
    get_team_details,
    list_teams,
    run_team,
)

# ---------------------------------------------------------------------------
# list_teams
# ---------------------------------------------------------------------------


class TestListTeams:
    async def test_returns_dict_with_teams(self):
        result = await list_teams()
        assert "teams" in result

    async def test_correct_count(self):
        result = await list_teams()
        assert len(result["teams"]) == len(TEAMS)

    async def test_each_team_has_required_fields(self):
        result = await list_teams()
        for team in result["teams"]:
            for field in ("id", "name", "description", "agent_count", "workflow"):
                assert field in team

    async def test_marketing_team_present(self):
        result = await list_teams()
        ids = [t["id"] for t in result["teams"]]
        assert "marketing" in ids

    async def test_development_team_present(self):
        result = await list_teams()
        ids = [t["id"] for t in result["teams"]]
        assert "development" in ids


# ---------------------------------------------------------------------------
# get_team_details
# ---------------------------------------------------------------------------


class TestGetTeamDetails:
    async def test_found_returns_info(self):
        result = await get_team_details("development")
        assert result["id"] == "development"
        assert "agents" in result
        assert "workflow" in result

    async def test_bad_id_returns_error_dict(self):
        result = await get_team_details("nonexistent_team_xyz")
        assert "error" in result

    async def test_error_mentions_available_teams(self):
        result = await get_team_details("bad_id")
        assert "error" in result
        # Should mention available teams in the error message
        assert "Available" in result["error"] or "not found" in result["error"]

    async def test_research_team_has_agents(self):
        result = await get_team_details("research")
        assert len(result["agents"]) > 0


# ---------------------------------------------------------------------------
# run_team
# ---------------------------------------------------------------------------


class TestRunTeam:
    async def test_returns_status_ready(self):
        result = await run_team("development", "Build a login page")
        assert result["status"] == "ready"

    async def test_execution_plan_has_steps(self):
        result = await run_team("development", "Build a login page")
        steps = result["execution_plan"]["steps"]
        assert len(steps) > 0

    async def test_steps_have_prompts(self):
        result = await run_team("development", "Build a login page")
        for step in result["execution_plan"]["steps"]:
            assert "prompt" in step
            assert len(step["prompt"]) > 0

    async def test_invalid_team_returns_error(self):
        result = await run_team("nonexistent_xyz", "task")
        assert "error" in result

    async def test_step_order_is_sequential(self):
        result = await run_team("development", "Do something")
        steps = result["execution_plan"]["steps"]
        for i, step in enumerate(steps):
            assert step["step"] == i + 1


# ---------------------------------------------------------------------------
# execute_step
# ---------------------------------------------------------------------------


class TestExecuteStep:
    async def test_first_step_not_final(self):
        result = await execute_step("development", 1, "Build feature")
        assert result["is_final"] is False

    async def test_last_step_is_final(self):
        team_agents = TEAMS["development"]["agents"]
        last_step = len(team_agents)
        result = await execute_step("development", last_step, "Build feature")
        assert result["is_final"] is True

    async def test_out_of_range_returns_error(self):
        result = await execute_step("development", 999, "task")
        assert "error" in result

    async def test_with_previous_output(self):
        result = await execute_step(
            "development", 2, "Build feature", previous_output="Previous agent did X"
        )
        assert "PREVIOUS AGENT OUTPUT" in result["prompt"]

    async def test_without_previous_output(self):
        result = await execute_step("development", 1, "Build feature")
        assert (
            "first agent" in result["prompt"].lower()
            or "PREVIOUS" not in result["prompt"]
        )

    async def test_next_step_increments(self):
        result = await execute_step("development", 1, "task")
        assert result["next_step"] == 2

    async def test_last_step_next_is_none(self):
        team_agents = TEAMS["development"]["agents"]
        last_step = len(team_agents)
        result = await execute_step("development", last_step, "task")
        assert result["next_step"] is None

    async def test_returns_agent_name(self):
        result = await execute_step("marketing", 1, "campaign task")
        assert "agent" in result

    async def test_invalid_team_returns_error(self):
        result = await execute_step("bad_team", 1, "task")
        assert "error" in result


# ---------------------------------------------------------------------------
# create_custom_team
# ---------------------------------------------------------------------------


class TestCreateCustomTeam:
    def setup_method(self):
        # Clean up any custom teams created during tests
        self._original_keys = set(TEAMS.keys())

    def teardown_method(self):
        for key in list(TEAMS.keys()):
            if key not in self._original_keys:
                del TEAMS[key]

    async def test_create_success(self):
        agents = [
            {"name": "Alpha", "role": "Does alpha stuff"},
            {"name": "Beta", "role": "Does beta stuff"},
        ]
        result = await create_custom_team("My Custom Team", agents)
        assert result["status"] == "created"
        assert "team_id" in result

    async def test_created_team_appears_in_list(self):
        agents = [{"name": "Agent1", "role": "role1"}]
        await create_custom_team("ListTest Team", agents)
        all_teams = await list_teams()
        ids = [t["id"] for t in all_teams["teams"]]
        assert "listtest_team" in ids

    async def test_missing_agent_role_returns_error(self):
        agents = [{"name": "NoRole"}]  # missing "role"
        result = await create_custom_team("Bad Team", agents)
        assert "error" in result

    async def test_duplicate_id_returns_error(self):
        agents = [{"name": "A", "role": "r"}]
        await create_custom_team("Dup Team", agents)
        result = await create_custom_team("Dup Team", agents)
        assert "error" in result

    async def test_custom_workflow_preserved(self):
        agents = [{"name": "A", "role": "r"}]
        result = await create_custom_team(
            "Workflow Test Team", agents, workflow="step1 → step2"
        )
        assert result["team"]["workflow"] == "step1 → step2"

    async def test_default_workflow_generated(self):
        agents = [{"name": "Alpha", "role": "r"}]
        result = await create_custom_team("Default Flow Team", agents)
        assert "Alpha" in result["team"]["workflow"]
