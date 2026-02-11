"""
Agenticom MCP Server - Multi-Agent Orchestration as a Tool

This turns Agenticom into an MCP server that Claude Code, Cursor,
or any MCP-compatible AI assistant can use.

Usage:
    # Add to Claude Code's MCP config (~/.claude/claude_desktop_config.json):
    {
        "mcpServers": {
            "agenticom": {
                "command": "python",
                "args": ["-m", "orchestration.mcp_server"]
            }
        }
    }

    # Or run standalone:
    python -m orchestration.mcp_server
"""

import asyncio
import json
from typing import Any

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not installed. Run: pip install mcp")


# ============== AGENT TEAM DEFINITIONS ==============

TEAMS = {
    "marketing": {
        "name": "Viral Marketing Team",
        "description": "5-agent team for growth campaigns: social listening, competitor analysis, content creation, community engagement",
        "agents": [
            {"name": "SocialIntelAgent", "role": "Scans X/Reddit/HN for pain points and opportunities"},
            {"name": "CompetitorAnalyst", "role": "Creates battle cards, finds market gaps"},
            {"name": "ContentCreator", "role": "Writes viral threads, memes, technical posts"},
            {"name": "CommunityManager", "role": "Authentic outreach, relationship building"},
            {"name": "CampaignLead", "role": "Coordinates team, tracks metrics"},
        ],
        "workflow": "research → analyze → create → engage → report"
    },
    "development": {
        "name": "Feature Development Team",
        "description": "5-agent team for coding: planning, implementation, verification, testing, review",
        "agents": [
            {"name": "Planner", "role": "Breaks down requirements into tasks"},
            {"name": "Developer", "role": "Writes clean, tested code"},
            {"name": "Verifier", "role": "Cross-checks implementation against spec"},
            {"name": "Tester", "role": "Creates and runs test suites"},
            {"name": "Reviewer", "role": "Code review, suggests improvements"},
        ],
        "workflow": "plan → develop → verify → test → review"
    },
    "research": {
        "name": "Research & Analysis Team",
        "description": "5-agent team for deep research: discovery, analysis, synthesis, fact-checking, reporting",
        "agents": [
            {"name": "Researcher", "role": "Gathers information from multiple sources"},
            {"name": "DataAnalyst", "role": "Processes and analyzes data"},
            {"name": "Synthesizer", "role": "Combines findings into insights"},
            {"name": "FactChecker", "role": "Verifies claims and sources"},
            {"name": "ReportWriter", "role": "Creates comprehensive reports"},
        ],
        "workflow": "research → analyze → synthesize → verify → report"
    },
    "content": {
        "name": "Content Production Team",
        "description": "5-agent team for content at scale: ideation, writing, editing, SEO, publishing",
        "agents": [
            {"name": "IdeaGenerator", "role": "Brainstorms topics and angles"},
            {"name": "Writer", "role": "Creates first drafts"},
            {"name": "Editor", "role": "Refines and polishes content"},
            {"name": "SEOOptimizer", "role": "Optimizes for search and discovery"},
            {"name": "Publisher", "role": "Formats and distributes content"},
        ],
        "workflow": "ideate → write → edit → optimize → publish"
    },
    "security": {
        "name": "Security Audit Team",
        "description": "4-agent team for security: scanning, analysis, recommendations, verification",
        "agents": [
            {"name": "Scanner", "role": "Identifies potential vulnerabilities"},
            {"name": "Analyzer", "role": "Assesses severity and impact"},
            {"name": "Recommender", "role": "Suggests fixes and mitigations"},
            {"name": "Verifier", "role": "Confirms fixes are effective"},
        ],
        "workflow": "scan → analyze → recommend → verify"
    }
}


# ============== MCP TOOL IMPLEMENTATIONS ==============

async def list_teams() -> dict[str, Any]:
    """List all available agent teams."""
    return {
        "teams": [
            {
                "id": team_id,
                "name": team["name"],
                "description": team["description"],
                "agent_count": len(team["agents"]),
                "workflow": team["workflow"]
            }
            for team_id, team in TEAMS.items()
        ]
    }


async def get_team_details(team_id: str) -> dict[str, Any]:
    """Get detailed info about a specific team."""
    if team_id not in TEAMS:
        return {"error": f"Team '{team_id}' not found. Available: {list(TEAMS.keys())}"}

    team = TEAMS[team_id]
    return {
        "id": team_id,
        "name": team["name"],
        "description": team["description"],
        "agents": team["agents"],
        "workflow": team["workflow"],
        "usage": f"Use 'run_team' with team_id='{team_id}' and your task description"
    }


async def run_team(team_id: str, task: str, config: dict = None) -> dict[str, Any]:
    """
    Run a multi-agent team on a task.

    This orchestrates the agents in sequence, with each agent's output
    feeding into the next agent's input.
    """
    if team_id not in TEAMS:
        return {"error": f"Team '{team_id}' not found"}

    team = TEAMS[team_id]
    config = config or {}

    # Build the execution plan
    execution_plan = {
        "team": team["name"],
        "task": task,
        "steps": []
    }

    for i, agent in enumerate(team["agents"]):
        step = {
            "step": i + 1,
            "agent": agent["name"],
            "role": agent["role"],
            "input": task if i == 0 else f"Output from {team['agents'][i-1]['name']}",
            "prompt": _generate_agent_prompt(agent, task, team_id, config)
        }
        execution_plan["steps"].append(step)

    return {
        "status": "ready",
        "execution_plan": execution_plan,
        "instructions": """
To execute this plan, run each agent's prompt in sequence:

1. Copy each agent's prompt
2. Run it (the AI will act as that agent)
3. Use the output as context for the next agent

Or use the 'execute_step' tool to run individual steps.
"""
    }


async def execute_step(team_id: str, step_number: int, task: str, previous_output: str = "") -> dict[str, Any]:
    """Execute a single step in the team workflow."""
    if team_id not in TEAMS:
        return {"error": f"Team '{team_id}' not found"}

    team = TEAMS[team_id]
    if step_number < 1 or step_number > len(team["agents"]):
        return {"error": f"Invalid step number. Team has {len(team['agents'])} steps."}

    agent = team["agents"][step_number - 1]

    prompt = f"""You are the {agent['name']} agent.

YOUR ROLE: {agent['role']}

TASK: {task}

{"PREVIOUS AGENT OUTPUT:" + chr(10) + previous_output if previous_output else "You are the first agent in the chain."}

Complete your role thoroughly. Your output will be passed to the next agent.
Be specific, actionable, and comprehensive."""

    return {
        "agent": agent["name"],
        "role": agent["role"],
        "prompt": prompt,
        "next_step": step_number + 1 if step_number < len(team["agents"]) else None,
        "is_final": step_number == len(team["agents"])
    }


async def create_custom_team(name: str, agents: list[dict], workflow: str = None) -> dict[str, Any]:
    """Create a custom agent team."""
    team_id = name.lower().replace(" ", "_")

    if team_id in TEAMS:
        return {"error": f"Team '{team_id}' already exists"}

    # Validate agents
    for agent in agents:
        if "name" not in agent or "role" not in agent:
            return {"error": "Each agent must have 'name' and 'role' fields"}

    TEAMS[team_id] = {
        "name": name,
        "description": f"Custom team with {len(agents)} agents",
        "agents": agents,
        "workflow": workflow or " → ".join(a["name"] for a in agents)
    }

    return {
        "status": "created",
        "team_id": team_id,
        "team": TEAMS[team_id]
    }


def _generate_agent_prompt(agent: dict, task: str, team_id: str, config: dict) -> str:
    """Generate a detailed prompt for an agent."""

    # Team-specific prompt enhancements
    enhancements = {
        "marketing": {
            "SocialIntelAgent": """
Search for:
- Pain points: "{keyword} sucks", "frustrated with {keyword}", "I wish {keyword}"
- Opportunities: "looking for {keyword} alternative", "switched from {keyword}"
- Influencers discussing the topic

Platforms: X/Twitter, Reddit (r/programming, r/startups), Hacker News, LinkedIn
Output: List of 10+ actionable pain points with source links""",

            "CompetitorAnalyst": """
Analyze each competitor:
- Core features & pricing
- Weaknesses (from reviews, complaints)
- Strengths (what users love)
- Market positioning

Output: Battle card for each competitor with attack angles""",

            "ContentCreator": """
Create content for each platform:
- Twitter: Hook + thread (8-12 tweets)
- Reddit: Value-first post for relevant subreddits
- HN: Technical angle for Show HN

Viral mechanics: Contrarian takes, specific numbers, vulnerability, utility""",
        },
        "development": {
            "Planner": """
Break down into:
- Technical requirements
- Implementation tasks (ordered)
- Dependencies
- Estimated complexity

Output: Detailed task list with acceptance criteria""",

            "Developer": """
Write production-quality code:
- Follow existing patterns
- Add type hints
- Include docstrings
- Handle edge cases

Output: Complete, working code""",
        }
    }

    base_prompt = f"""You are {agent['name']}, a specialized AI agent.

ROLE: {agent['role']}

TASK: {task}

"""

    # Add team-specific enhancements if available
    team_enhancements = enhancements.get(team_id, {})
    agent_enhancement = team_enhancements.get(agent['name'], "")

    if agent_enhancement:
        base_prompt += f"""
SPECIFIC INSTRUCTIONS:
{agent_enhancement}

"""

    base_prompt += """
Complete your role thoroughly. Be specific, actionable, and comprehensive.
Your output will be used by subsequent agents in the workflow.
"""

    return base_prompt


# ============== MCP SERVER SETUP ==============

def create_mcp_server() -> Server:
    """Create and configure the MCP server."""

    server = Server("agenticom")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="agenticom_list_teams",
                description="List all available multi-agent teams (marketing, development, research, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="agenticom_get_team",
                description="Get detailed information about a specific agent team",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "Team ID (e.g., 'marketing', 'development', 'research')"
                        }
                    },
                    "required": ["team_id"]
                }
            ),
            Tool(
                name="agenticom_run_team",
                description="Run a multi-agent team on a task. Returns execution plan with prompts for each agent.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "Team ID to run"
                        },
                        "task": {
                            "type": "string",
                            "description": "The task description for the team"
                        },
                        "config": {
                            "type": "object",
                            "description": "Optional configuration (platforms, duration, etc.)"
                        }
                    },
                    "required": ["team_id", "task"]
                }
            ),
            Tool(
                name="agenticom_execute_step",
                description="Execute a single step in a team workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "Team ID"
                        },
                        "step_number": {
                            "type": "integer",
                            "description": "Step number (1-indexed)"
                        },
                        "task": {
                            "type": "string",
                            "description": "Original task"
                        },
                        "previous_output": {
                            "type": "string",
                            "description": "Output from the previous agent (empty for first step)"
                        }
                    },
                    "required": ["team_id", "step_number", "task"]
                }
            ),
            Tool(
                name="agenticom_create_team",
                description="Create a custom agent team with specified agents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Team name"
                        },
                        "agents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "role": {"type": "string"}
                                }
                            },
                            "description": "List of agents with name and role"
                        },
                        "workflow": {
                            "type": "string",
                            "description": "Optional workflow description"
                        }
                    },
                    "required": ["name", "agents"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "agenticom_list_teams":
                result = await list_teams()
            elif name == "agenticom_get_team":
                result = await get_team_details(arguments["team_id"])
            elif name == "agenticom_run_team":
                result = await run_team(
                    arguments["team_id"],
                    arguments["task"],
                    arguments.get("config")
                )
            elif name == "agenticom_execute_step":
                result = await execute_step(
                    arguments["team_id"],
                    arguments["step_number"],
                    arguments["task"],
                    arguments.get("previous_output", "")
                )
            elif name == "agenticom_create_team":
                result = await create_custom_team(
                    arguments["name"],
                    arguments["agents"],
                    arguments.get("workflow")
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


# ============== MAIN ==============

async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("ERROR: MCP SDK not installed")
        print("Run: pip install mcp")
        return

    server = create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
