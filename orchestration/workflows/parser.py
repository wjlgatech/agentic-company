"""
YAML Workflow Parser

Parse workflow definitions from YAML files into executable AgentTeam instances.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
import yaml

from orchestration.agents.base import AgentRole, AgentConfig
from orchestration.agents.team import (
    AgentTeam,
    TeamConfig,
    WorkflowStep,
)
from orchestration.agents.specialized import create_agent


@dataclass
class AgentDefinition:
    """Agent definition from YAML"""
    role: str
    name: Optional[str] = None
    persona: Optional[str] = None
    guardrails: list[str] = field(default_factory=list)
    workspace_files: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


@dataclass
class StepDefinition:
    """Step definition from YAML"""
    id: str
    agent: str  # Role name
    input: str
    expects: str = ""
    verified_by: Optional[str] = None
    requires_approval: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
    on_fail: str = "retry"
    execute: Optional[str] = None  # Command to execute after step
    artifacts_required: bool = False  # Require artifacts to be created


@dataclass
class WorkflowDefinition:
    """Complete workflow definition from YAML"""
    id: str
    name: str
    description: str = ""
    agents: list[AgentDefinition] = field(default_factory=list)
    steps: list[StepDefinition] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    timeout_seconds: int = 3600
    metadata: dict = field(default_factory=dict)


class WorkflowParser:
    """
    Parse YAML workflow definitions.

    Example YAML format:
    ```yaml
    id: feature-dev
    name: Feature Development
    description: Complete feature development workflow

    agents:
      - role: planner
        name: "Project Planner"
        guardrails: [content-filter, pii-detection]

      - role: developer
        name: "Senior Developer"
        guardrails: [rate-limiter]

      - role: verifier
        name: "Code Reviewer"

    steps:
      - id: plan
        agent: planner
        input: "Create implementation plan for: {task}"
        expects: "Plan with atomic stories and acceptance criteria"

      - id: implement
        agent: developer
        input: "Implement: {plan}"
        expects: "Working code that meets acceptance criteria"
        verified_by: verifier

      - id: review
        agent: verifier
        input: "Final review: {implement}"
        expects: "Code approved for merge"
        requires_approval: true
    ```
    """

    ROLE_MAP = {
        # Standard roles
        "planner": AgentRole.PLANNER,
        "developer": AgentRole.DEVELOPER,
        "verifier": AgentRole.VERIFIER,
        "tester": AgentRole.TESTER,
        "reviewer": AgentRole.REVIEWER,
        "researcher": AgentRole.RESEARCHER,
        "writer": AgentRole.WRITER,
        "analyst": AgentRole.ANALYST,
        "custom": AgentRole.CUSTOM,

        # Marketing workflow roles
        "social-intel": AgentRole.RESEARCHER,
        "competitor-analyst": AgentRole.ANALYST,
        "content-creator": AgentRole.WRITER,
        "community-manager": AgentRole.WRITER,
        "campaign-lead": AgentRole.PLANNER,

        # M&A Due Diligence roles
        "financial-analyst": AgentRole.ANALYST,
        "legal-reviewer": AgentRole.REVIEWER,
        "market-analyst": AgentRole.ANALYST,
        "technical-assessor": AgentRole.VERIFIER,
        "deal-lead": AgentRole.PLANNER,

        # Compliance Audit roles
        "compliance-scanner": AgentRole.ANALYST,
        "gap-analyst": AgentRole.ANALYST,
        "risk-assessor": AgentRole.ANALYST,
        "remediation-planner": AgentRole.PLANNER,
        "audit-documenter": AgentRole.WRITER,

        # Patent Landscape roles
        "patent-searcher": AgentRole.RESEARCHER,
        "claim-analyst": AgentRole.ANALYST,
        "landscape-mapper": AgentRole.ANALYST,
        "fto-assessor": AgentRole.ANALYST,
        "ip-strategist": AgentRole.PLANNER,

        # Security Assessment roles
        "threat-modeler": AgentRole.ANALYST,
        "vuln-scanner": AgentRole.ANALYST,
        "risk-analyst": AgentRole.ANALYST,
        "remediation-engineer": AgentRole.DEVELOPER,
        "security-architect": AgentRole.PLANNER,

        # Churn Analysis roles
        "data-analyst": AgentRole.ANALYST,
        "customer-researcher": AgentRole.RESEARCHER,
        "segment-strategist": AgentRole.PLANNER,
        "retention-strategist": AgentRole.PLANNER,
        "executive-advisor": AgentRole.PLANNER,

        # Grant Proposal roles
        "requirements-analyst": AgentRole.ANALYST,
        "research-synthesizer": AgentRole.RESEARCHER,
        "proposal-architect": AgentRole.PLANNER,
        "budget-specialist": AgentRole.ANALYST,
        "proposal-writer": AgentRole.WRITER,

        # Incident Post-Mortem roles
        "timeline-analyst": AgentRole.ANALYST,
        "rca-specialist": AgentRole.ANALYST,
        "impact-assessor": AgentRole.ANALYST,
        "prevention-engineer": AgentRole.DEVELOPER,
        "postmortem-author": AgentRole.WRITER,
    }

    # Fallback patterns for auto-mapping unknown roles
    ROLE_PATTERNS = {
        "analyst": AgentRole.ANALYST,
        "researcher": AgentRole.RESEARCHER,
        "writer": AgentRole.WRITER,
        "planner": AgentRole.PLANNER,
        "developer": AgentRole.DEVELOPER,
        "engineer": AgentRole.DEVELOPER,
        "reviewer": AgentRole.REVIEWER,
        "verifier": AgentRole.VERIFIER,
        "tester": AgentRole.TESTER,
        "lead": AgentRole.PLANNER,
        "strategist": AgentRole.PLANNER,
        "specialist": AgentRole.ANALYST,
        "assessor": AgentRole.ANALYST,
        "advisor": AgentRole.PLANNER,
        "architect": AgentRole.PLANNER,
        "scanner": AgentRole.ANALYST,
        "modeler": AgentRole.ANALYST,
    }

    @classmethod
    def resolve_role(cls, role_id: str) -> AgentRole:
        """
        Resolve a role ID to an AgentRole.

        First checks explicit mappings, then uses pattern matching,
        finally falls back to CUSTOM.

        Args:
            role_id: The role identifier from YAML

        Returns:
            Appropriate AgentRole
        """
        role_lower = role_id.lower()

        # Check explicit mapping
        if role_lower in cls.ROLE_MAP:
            return cls.ROLE_MAP[role_lower]

        # Try pattern matching (look for keywords in role name)
        for pattern, role in cls.ROLE_PATTERNS.items():
            if pattern in role_lower:
                return role

        # Fallback to CUSTOM
        return AgentRole.CUSTOM

    def parse(self, yaml_content: str) -> WorkflowDefinition:
        """Parse YAML string into WorkflowDefinition"""
        data = yaml.safe_load(yaml_content)
        return self._parse_dict(data)

    def parse_file(self, file_path: Path) -> WorkflowDefinition:
        """Parse YAML file into WorkflowDefinition"""
        with open(file_path, 'r') as f:
            return self.parse(f.read())

    def _parse_dict(self, data: dict) -> WorkflowDefinition:
        """Parse dictionary into WorkflowDefinition"""
        # Parse agents
        agents = []
        for agent_data in data.get('agents', []):
            # Use 'id' for role mapping (e.g., "planner", "developer")
            # Fall back to 'role' for backward compatibility with simple formats
            role_key = agent_data.get('id') or agent_data.get('role')

            # Use 'prompt' for persona, fall back to 'persona' field
            # The 'role' field in bundled YAMLs is a description, append it to persona
            persona = agent_data.get('prompt') or agent_data.get('persona') or ''
            role_desc = agent_data.get('role', '')
            if role_desc and role_desc != role_key:
                persona = f"Role: {role_desc}\n\n{persona}".strip()

            agents.append(AgentDefinition(
                role=role_key,
                name=agent_data.get('name'),
                persona=persona,
                guardrails=agent_data.get('guardrails', []),
                workspace_files=agent_data.get('workspace_files', []),
                tools=agent_data.get('tools', []),
            ))

        # Parse steps
        steps = []
        for step_data in data.get('steps', []):
            steps.append(StepDefinition(
                id=step_data.get('id'),
                agent=step_data.get('agent'),
                input=step_data.get('input'),
                expects=step_data.get('expects', ''),
                verified_by=step_data.get('verified_by'),
                requires_approval=step_data.get('requires_approval', False),
                max_retries=step_data.get('max_retries', 3),
                timeout_seconds=step_data.get('timeout_seconds', 300),
                on_fail=step_data.get('on_fail', 'retry'),
            ))

        return WorkflowDefinition(
            id=data.get('id'),
            name=data.get('name', data.get('id')),
            description=data.get('description', ''),
            agents=agents,
            steps=steps,
            guardrails=data.get('guardrails', []),
            timeout_seconds=data.get('timeout_seconds', 3600),
            metadata=data.get('metadata', {}),
        )

    def to_team(self, definition: WorkflowDefinition) -> AgentTeam:
        """Convert WorkflowDefinition to executable AgentTeam"""
        # Create team config
        team_config = TeamConfig(
            name=definition.name,
            description=definition.description,
            timeout_seconds=definition.timeout_seconds,
            metadata=definition.metadata,
        )

        team = AgentTeam(team_config)

        # Create and add agents
        agent_map = {}
        for agent_def in definition.agents:
            # Use dynamic role resolution with fallback to CUSTOM
            role = self.resolve_role(agent_def.role)

            agent = create_agent(
                role,
                name=agent_def.name,
                persona=agent_def.persona,
                guardrails=agent_def.guardrails,
                workspace_files=agent_def.workspace_files,
                tools=agent_def.tools,
            )
            team.add_agent(agent)
            agent_map[agent_def.role.lower()] = role

        # Create and add steps
        for step_def in definition.steps:
            agent_role = agent_map.get(step_def.agent.lower())
            if agent_role is None:
                raise ValueError(f"Unknown agent in step: {step_def.agent}")

            verified_by = None
            if step_def.verified_by:
                verified_by = agent_map.get(step_def.verified_by.lower())

            step = WorkflowStep(
                id=step_def.id,
                name=step_def.id,
                agent_role=agent_role,
                input_template=step_def.input,
                expects=step_def.expects,
                verified_by=verified_by,
                requires_approval=step_def.requires_approval,
                max_retries=step_def.max_retries,
                timeout_seconds=step_def.timeout_seconds,
                on_fail=step_def.on_fail,
                execute=step_def.execute,
                artifacts_required=step_def.artifacts_required,
            )
            team.add_step(step)

        return team


def load_workflow(file_path: str | Path, auto_setup: bool = False) -> AgentTeam:
    """
    Load workflow from YAML file and return AgentTeam.

    Args:
        file_path: Path to YAML workflow file
        auto_setup: If True, automatically configure LLM executor for all agents

    Returns:
        AgentTeam (ready to execute if auto_setup=True)

    Example:
        # Without auto_setup (need to manually set executor):
        team = load_workflow('workflow.yaml')
        executor = auto_setup_executor()
        for agent in team.agents.values():
            agent.set_executor(lambda p, c: executor.execute(p, c))
        result = await team.run("task")

        # With auto_setup (ready to run):
        team = load_workflow('workflow.yaml', auto_setup=True)
        result = await team.run("task")
    """
    parser = WorkflowParser()
    definition = parser.parse_file(Path(file_path))
    team = parser.to_team(definition)

    if auto_setup:
        _setup_team_executor(team)

    return team


def load_ready_workflow(file_path: str | Path) -> AgentTeam:
    """
    Load workflow from YAML and configure with LLM executor - ready to run!

    This is the recommended way to load workflows for execution.
    Automatically detects and configures the best available LLM backend.

    Args:
        file_path: Path to YAML workflow file

    Returns:
        AgentTeam ready to execute immediately

    Raises:
        RuntimeError: If no LLM backend is available

    Example:
        team = load_ready_workflow('feature-dev.yaml')
        result = await team.run("Build a login page")
        print(result.final_output)
    """
    team = load_workflow(file_path, auto_setup=False)
    _setup_team_executor(team)
    return team


def _setup_team_executor(team: AgentTeam) -> None:
    """
    Configure all agents in a team with the auto-detected LLM executor.

    Args:
        team: AgentTeam to configure

    Raises:
        RuntimeError: If no LLM backend is available
    """
    from orchestration.integrations import auto_setup_executor
    from orchestration.integrations.unified import get_ready_backends

    ready = get_ready_backends()
    if not ready:
        raise RuntimeError(
            "No LLM backend available. Configure one of:\n"
            "  1. Set ANTHROPIC_API_KEY for Claude\n"
            "  2. Set OPENAI_API_KEY for GPT-4\n"
            "  3. Start Ollama locally: ollama serve"
        )

    # eager_init=True ensures executor is ready immediately
    executor = auto_setup_executor(eager_init=True)

    async def agent_executor(prompt: str, context) -> str:
        return await executor.execute(prompt, context)

    for agent in team.agents.values():
        agent.set_executor(agent_executor)


def load_workflows_from_directory(directory: str | Path) -> dict[str, AgentTeam]:
    """
    Load all workflows from a directory.

    Args:
        directory: Path to directory containing YAML files

    Returns:
        Dictionary mapping workflow IDs to AgentTeams
    """
    parser = WorkflowParser()
    workflows = {}

    dir_path = Path(directory)
    for yaml_file in dir_path.glob("*.yaml"):
        try:
            definition = parser.parse_file(yaml_file)
            team = parser.to_team(definition)
            workflows[definition.id] = team
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}")

    for yml_file in dir_path.glob("*.yml"):
        try:
            definition = parser.parse_file(yml_file)
            team = parser.to_team(definition)
            workflows[definition.id] = team
        except Exception as e:
            print(f"Warning: Failed to load {yml_file}: {e}")

    return workflows


def workflow_to_yaml(team: AgentTeam) -> str:
    """
    Export an AgentTeam back to YAML format.

    Args:
        team: AgentTeam to export

    Returns:
        YAML string representation
    """
    data = {
        'id': team.config.name.lower().replace(' ', '-'),
        'name': team.config.name,
        'description': team.config.description,
        'timeout_seconds': team.config.timeout_seconds,
        'agents': [],
        'steps': [],
    }

    # Export agents
    for role, agent in team.agents.items():
        data['agents'].append({
            'role': role.value,
            'name': agent.name,
            'persona': agent.persona if agent.persona else None,
            'guardrails': agent.config.guardrails,
        })

    # Export steps
    for step in team.steps:
        step_data = {
            'id': step.id,
            'agent': step.agent_role.value,
            'input': step.input_template,
        }
        if step.expects:
            step_data['expects'] = step.expects
        if step.verified_by:
            step_data['verified_by'] = step.verified_by.value
        if step.requires_approval:
            step_data['requires_approval'] = True
        if step.max_retries != 3:
            step_data['max_retries'] = step.max_retries
        if step.on_fail != 'retry':
            step_data['on_fail'] = step.on_fail

        data['steps'].append(step_data)

    return yaml.dump(data, default_flow_style=False, sort_keys=False)
