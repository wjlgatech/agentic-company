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
        "planner": AgentRole.PLANNER,
        "developer": AgentRole.DEVELOPER,
        "verifier": AgentRole.VERIFIER,
        "tester": AgentRole.TESTER,
        "reviewer": AgentRole.REVIEWER,
        "researcher": AgentRole.RESEARCHER,
        "writer": AgentRole.WRITER,
        "analyst": AgentRole.ANALYST,
    }

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
            agents.append(AgentDefinition(
                role=agent_data.get('role'),
                name=agent_data.get('name'),
                persona=agent_data.get('persona'),
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
            role = self.ROLE_MAP.get(agent_def.role.lower())
            if role is None:
                raise ValueError(f"Unknown agent role: {agent_def.role}")

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
            )
            team.add_step(step)

        return team


def load_workflow(file_path: str | Path) -> AgentTeam:
    """
    Load workflow from YAML file and return executable AgentTeam.

    Args:
        file_path: Path to YAML workflow file

    Returns:
        AgentTeam ready to execute
    """
    parser = WorkflowParser()
    definition = parser.parse_file(Path(file_path))
    return parser.to_team(definition)


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
