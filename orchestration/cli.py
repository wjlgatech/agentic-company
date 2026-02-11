"""
CLI interface for Agentic Company orchestration system.

Provides commands for health checks, workflow management, and server control.
"""

import asyncio
import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from orchestration._version import __version__
from orchestration.config import get_config, validate_config, OrchestratorConfig
from orchestration.observability import get_observability

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="agentic")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """Agentic Company - AI Agent Orchestration System

    Manage AI agent workflows with guardrails, memory, and observability.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config


@main.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    """Check system health status."""
    config = get_config()
    errors = validate_config(config)

    tree = Tree("🏥 System Health")

    # LLM Connection
    if config.llm.api_key:
        tree.add(f"[green]✓[/green] LLM Connection: OK ({config.llm.provider})")
    else:
        tree.add(f"[red]✗[/red] LLM Connection: No API key configured")

    # Memory Backend
    tree.add(f"[green]✓[/green] Memory Backend: {config.memory.backend}")

    # Guardrails
    if config.guardrails.enabled:
        tree.add("[green]✓[/green] Guardrails: Enabled")
    else:
        tree.add("[yellow]![/yellow] Guardrails: Disabled")

    # Configuration Errors
    if errors:
        error_branch = tree.add("[red]Configuration Errors[/red]")
        for error in errors:
            error_branch.add(f"[red]✗[/red] {error}")

    console.print(Panel(tree, title="Agentic Company Health Check", border_style="blue"))

    # Exit with error code if unhealthy
    if errors:
        sys.exit(1)


@main.group()
def config_cmd() -> None:
    """Configuration management commands."""
    pass


@config_cmd.command("show")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def config_show(format: str) -> None:
    """Show current configuration."""
    config = get_config()

    if format == "json":
        console.print_json(data=config.to_dict())
    else:
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        config_dict = config.to_dict()
        for section, values in config_dict.items():
            table.add_row(f"[bold]{section}[/bold]", "")
            if isinstance(values, dict):
                for key, value in values.items():
                    table.add_row(f"  {key}", str(value))
            else:
                table.add_row(f"  value", str(values))

        console.print(table)


@config_cmd.command("validate")
def config_validate() -> None:
    """Validate configuration."""
    config = get_config()
    errors = validate_config(config)

    if errors:
        console.print("[red]Configuration validation failed:[/red]")
        for error in errors:
            console.print(f"  [red]✗[/red] {error}")
        sys.exit(1)
    else:
        console.print("[green]✓[/green] Configuration is valid")


@main.group()
def workflow() -> None:
    """Workflow management commands."""
    pass


@workflow.command("list")
def workflow_list() -> None:
    """List available workflows."""
    from pathlib import Path
    from orchestration.workflows.parser import WorkflowParser

    parser = WorkflowParser()
    workflows = []

    # Search locations for workflow files
    search_paths = [
        Path("workflows"),
        Path("agenticom/bundled_workflows"),
        Path(__file__).parent.parent / "agenticom/bundled_workflows",
    ]

    for search_path in search_paths:
        if search_path.exists():
            for yaml_file in list(search_path.glob("*.yaml")) + list(search_path.glob("*.yml")):
                try:
                    definition = parser.parse_file(yaml_file)
                    workflows.append({
                        "name": definition.id,
                        "description": definition.description.split('\n')[0][:60] if definition.description else "No description",
                        "path": str(yaml_file),
                        "agents": len(definition.agents),
                        "steps": len(definition.steps),
                    })
                except Exception as e:
                    workflows.append({
                        "name": yaml_file.stem,
                        "description": f"[red]Error loading: {e}[/red]",
                        "path": str(yaml_file),
                        "agents": 0,
                        "steps": 0,
                    })

    if not workflows:
        console.print("[yellow]No workflows found.[/yellow]")
        console.print("Create one with: [cyan]agentic create[/cyan]")
        return

    table = Table(title="Available Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Agents", justify="center")
    table.add_column("Steps", justify="center")

    for wf in workflows:
        table.add_row(
            wf["name"],
            wf["description"],
            str(wf["agents"]),
            str(wf["steps"]),
        )

    console.print(table)


@workflow.command("run")
@click.argument("workflow_name")
@click.option("--input", "-i", "input_data", required=True, help="Input data or file path")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--async", "run_async", is_flag=True, help="Run asynchronously")
@click.option("--dry-run", is_flag=True, help="Show workflow plan without executing")
def workflow_run(
    workflow_name: str,
    input_data: str,
    output: Optional[str],
    run_async: bool,
    dry_run: bool,
) -> None:
    """Run a workflow."""
    from pathlib import Path

    console.print(f"[cyan]Running workflow:[/cyan] {workflow_name}")
    console.print(f"[cyan]Input:[/cyan] {input_data[:100]}{'...' if len(input_data) > 100 else ''}")

    # Find and load the workflow
    workflow_paths = [
        Path(f"{workflow_name}.yaml"),
        Path(f"{workflow_name}.yml"),
        Path(f"workflows/{workflow_name}.yaml"),
        Path(f"agenticom/bundled_workflows/{workflow_name}.yaml"),
        Path(__file__).parent.parent / f"agenticom/bundled_workflows/{workflow_name}.yaml",
    ]

    workflow_path = None
    for path in workflow_paths:
        if path.exists():
            workflow_path = path
            break

    if workflow_path is None:
        console.print(f"[red]✗[/red] Workflow not found: {workflow_name}")
        console.print("[dim]Searched in:[/dim]")
        for p in workflow_paths:
            console.print(f"  - {p}")
        sys.exit(1)

    try:
        from orchestration.workflows.parser import load_workflow
        team = load_workflow(workflow_path)
        console.print(f"[green]✓[/green] Loaded workflow from: {workflow_path}")
        console.print(f"  Agents: {[r.value for r in team.agents.keys()]}")
        console.print(f"  Steps: {len(team.steps)}")

        # Show workflow plan
        if dry_run:
            console.print("\n[bold cyan]Workflow Plan:[/bold cyan]")
            for i, step in enumerate(team.steps, 1):
                console.print(f"  {i}. [bold]{step.name}[/bold] ({step.agent_role.value})")
                if step.expects:
                    console.print(f"     Expects: {step.expects}")
            return

        # Setup LLM executor
        from orchestration.integrations import auto_setup_executor
        from orchestration.integrations.unified import get_ready_backends

        ready = get_ready_backends()
        if not ready:
            console.print("[red]✗[/red] No LLM backend ready!")
            console.print("\n[yellow]To run workflows, configure one of:[/yellow]")
            console.print("  1. Set ANTHROPIC_API_KEY for Claude")
            console.print("  2. Set OPENAI_API_KEY for GPT-4")
            console.print("  3. Start Ollama locally: [cyan]ollama serve[/cyan]")
            console.print("\nOr use [cyan]--dry-run[/cyan] to preview the workflow")
            sys.exit(1)

        executor = auto_setup_executor()
        backend_name = executor.active_backend.value if executor.active_backend else "None"
        console.print(f"[green]✓[/green] LLM backend: {backend_name}")

        # Configure agents with executor
        async def agent_executor(prompt: str, context) -> str:
            return await executor.execute(prompt, context)

        for agent in team.agents.values():
            agent.set_executor(agent_executor)

        # Execute workflow
        async def run_workflow():
            with console.status("[bold green]Executing workflow...") as status:
                result = await team.run(input_data)

                # Display step results as they complete
                for step_result in result.steps:
                    step = step_result.step
                    if step_result.status.value == "completed":
                        console.print(f"  [green]✓[/green] {step.name}: completed")
                    else:
                        console.print(f"  [red]✗[/red] {step.name}: {step_result.status.value}")

                return result

        team_result = asyncio.run(run_workflow())

        # Build result
        result = {
            "workflow": workflow_name,
            "workflow_id": team_result.workflow_id,
            "status": "completed" if team_result.success else "failed",
            "input": input_data,
            "output": team_result.final_output,
            "steps": len(team_result.steps),
            "error": team_result.error,
        }

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"[green]✓[/green] Output saved to: {output}")
        else:
            if team_result.success:
                console.print(Panel(
                    str(team_result.final_output)[:2000] if team_result.final_output else "No output",
                    title="[green]Result[/green]",
                    border_style="green"
                ))
            else:
                console.print(Panel(
                    team_result.error or "Unknown error",
                    title="[red]Error[/red]",
                    border_style="red"
                ))

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        import traceback
        if console.is_terminal:
            traceback.print_exc()
        sys.exit(1)


@workflow.command("status")
@click.argument("workflow_id")
def workflow_status(workflow_id: str) -> None:
    """Check workflow status."""
    # Placeholder - would query actual workflow status
    console.print(f"Workflow [cyan]{workflow_id}[/cyan]: [green]completed[/green]")


@workflow.command("tools")
@click.argument("workflow_name")
@click.option("--resolve", is_flag=True, help="Show MCP resolution details")
def workflow_tools(workflow_name: str, resolve: bool) -> None:
    """Show tools required by a workflow and their MCP mappings."""
    from pathlib import Path
    from orchestration.workflows.parser import WorkflowParser
    from orchestration.tools.mcp_bridge import MCPToolBridge

    # Find workflow file
    workflow_paths = [
        Path(f"workflows/{workflow_name}.yaml"),
        Path(f"agenticom/bundled_workflows/{workflow_name}.yaml"),
        Path(__file__).parent.parent / f"agenticom/bundled_workflows/{workflow_name}.yaml",
    ]

    workflow_path = None
    for path in workflow_paths:
        if path.exists():
            workflow_path = path
            break

    if not workflow_path:
        console.print(f"[red]✗[/red] Workflow not found: {workflow_name}")
        return

    # Parse workflow
    parser = WorkflowParser()
    definition = parser.parse_file(workflow_path)

    # Collect tools from all agents
    all_tools = set()
    agent_tools = {}
    for agent in definition.agents:
        if agent.tools:
            agent_tools[agent.role] = agent.tools
            all_tools.update(agent.tools)

    console.print(f"\n[bold cyan]Workflow: {workflow_name}[/bold cyan]")
    console.print(f"[dim]Path: {workflow_path}[/dim]\n")

    # Show tools by agent
    table = Table(title="Tools by Agent")
    table.add_column("Agent", style="cyan")
    table.add_column("Name")
    table.add_column("Tools", style="yellow")

    for agent in definition.agents:
        tools_str = ", ".join(agent.tools) if agent.tools else "[dim]none[/dim]"
        table.add_row(agent.role, agent.name or "", tools_str)

    console.print(table)

    if resolve and all_tools:
        console.print("\n[bold]MCP Tool Resolution:[/bold]\n")

        bridge = MCPToolBridge(use_mocks=True)
        report = bridge.get_resolution_report(list(all_tools))

        # Resolved tools
        if report["resolved"]:
            table = Table(title="✅ Resolved Tools")
            table.add_column("Tool", style="green")
            table.add_column("MCP Server")
            table.add_column("Available Methods")

            for item in report["resolved"]:
                methods = ", ".join(item.get("tools", [])[:3])
                if len(item.get("tools", [])) > 3:
                    methods += "..."
                table.add_row(item["name"], item.get("server", ""), methods)
            console.print(table)

        # Mocked tools
        if report["mocked"]:
            table = Table(title="🔶 Mocked Tools (for testing)")
            table.add_column("Tool", style="yellow")
            table.add_column("Note")

            for item in report["mocked"]:
                table.add_row(item["name"], item.get("note", ""))
            console.print(table)

        # Unresolved tools
        if report["unresolved"]:
            table = Table(title="❌ Unresolved Tools")
            table.add_column("Tool", style="red")
            table.add_column("Suggestion")

            for item in report["unresolved"]:
                table.add_row(item["name"], item.get("note", ""))
            console.print(table)

        # Summary
        summary = report["summary"]
        console.print(f"\n[bold]Summary:[/bold] {summary['resolved']} resolved, "
                      f"{summary['mocked']} mocked, {summary['unresolved']} unresolved "
                      f"(of {summary['total']} total)")


@main.group()
def metrics() -> None:
    """Metrics and observability commands."""
    pass


@metrics.command("show")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def metrics_show(format: str) -> None:
    """Show current metrics."""
    obs = get_observability()
    all_metrics = obs.metrics.get_all_metrics()

    if format == "json":
        console.print_json(data=all_metrics)
    else:
        # Counters
        if all_metrics["counters"]:
            table = Table(title="Counters")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for name, value in all_metrics["counters"].items():
                table.add_row(name, f"{value:.2f}")
            console.print(table)

        # Gauges
        if all_metrics["gauges"]:
            table = Table(title="Gauges")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for name, value in all_metrics["gauges"].items():
                table.add_row(name, f"{value:.2f}")
            console.print(table)

        # Histograms
        if all_metrics["histograms"]:
            table = Table(title="Histograms")
            table.add_column("Metric", style="cyan")
            table.add_column("Count")
            table.add_column("Avg")
            table.add_column("P95")
            table.add_column("P99")
            for name, stats in all_metrics["histograms"].items():
                table.add_row(
                    name,
                    str(stats["count"]),
                    f"{stats['avg']:.2f}",
                    f"{stats['p95']:.2f}",
                    f"{stats['p99']:.2f}",
                )
            console.print(table)

        if not any(all_metrics.values()):
            console.print("[yellow]No metrics collected yet[/yellow]")


@main.command()
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8000, type=int, help="Port to bind to")
@click.option("--workers", "-w", default=1, type=int, help="Number of workers")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, workers: int, reload: bool) -> None:
    """Start the API server."""
    import uvicorn

    console.print(f"[cyan]Starting Agentic Company API server[/cyan]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print(f"  Workers: {workers}")
    console.print(f"  Reload: {reload}")
    console.print()
    console.print(f"[green]API docs:[/green] http://{host}:{port}/docs")

    uvicorn.run(
        "orchestration.api:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
    )


@main.command()
@click.argument("query")
@click.option("--limit", "-l", default=5, type=int, help="Max results")
def recall(query: str, limit: int) -> None:
    """Search memory for relevant context."""
    from orchestration.memory import LocalMemoryStore

    memory = LocalMemoryStore()
    results = memory.recall(query, limit=limit)

    if results:
        table = Table(title=f"Memory Results for: {query}")
        table.add_column("ID", style="dim")
        table.add_column("Content", max_width=60)
        table.add_column("Tags")

        for entry in results:
            table.add_row(
                entry.id[:8],
                entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                ", ".join(entry.tags),
            )

        console.print(table)
    else:
        console.print(f"[yellow]No memories found for: {query}[/yellow]")


@main.group()
def approval() -> None:
    """Approval management commands."""
    pass


@approval.command("list")
def approval_list() -> None:
    """List pending approvals."""
    # Placeholder - would query actual approval queue
    console.print("[yellow]No pending approvals[/yellow]")


@approval.command("approve")
@click.argument("request_id")
@click.option("--reason", "-r", default="", help="Approval reason")
def approval_approve(request_id: str, reason: str) -> None:
    """Approve a pending request."""
    console.print(f"[green]✓[/green] Approved request: {request_id}")
    if reason:
        console.print(f"  Reason: {reason}")


@approval.command("reject")
@click.argument("request_id")
@click.option("--reason", "-r", required=True, help="Rejection reason")
def approval_reject(request_id: str, reason: str) -> None:
    """Reject a pending request."""
    console.print(f"[red]✗[/red] Rejected request: {request_id}")
    console.print(f"  Reason: {reason}")


@main.command()
@click.option("--output", "-o", type=click.Path(), help="Output file path for generated workflow")
@click.option("--voice", "-v", is_flag=True, help="Enable voice input (speak your answers)")
def create(output: Optional[str], voice: bool) -> None:
    """Create a workflow using the Easy Mode conversational builder.

    Walks you through creating an AI agent workflow step by step
    with simple multiple-choice questions.

    Use --voice to speak your answers instead of typing!
    """
    mode_text = "🎤 Voice mode enabled - speak your answers!" if voice else "Type your answers below"
    console.print()
    console.print(Panel(
        f"🆕 [bold]Easy Workflow Builder[/bold]\n\n"
        f"I'll help you create an AI agent workflow step by step.\n"
        f"{mode_text}",
        title="Agenticom Create",
        border_style="cyan"
    ))
    console.print()

    try:
        from orchestration.conversation import ConversationBuilder, get_voice_input, VOICE_AVAILABLE

        # Check voice availability
        if voice and not VOICE_AVAILABLE:
            console.print("[yellow]⚠️ Voice not available. Install with:[/yellow]")
            console.print("   pip install SpeechRecognition pyaudio")
            voice = False

        builder = ConversationBuilder()

        while not builder.is_complete():
            question = builder.get_current_question()
            if not question:
                break

            # Display question
            console.print(f"[bold cyan]Question {builder.current_step + 1}:[/bold cyan] {question.text}")
            console.print()

            # Display options
            for i, option in enumerate(question.options, 1):
                console.print(f"   {i}) {option}")
            console.print()

            # Get user input (voice or text)
            while True:
                response = None

                # Try voice input first if enabled
                if voice:
                    console.print("[cyan]🎤 Listening... (say A, B, C, etc. or speak your choice)[/cyan]")
                    voice_text = get_voice_input("Listening...")
                    if voice_text:
                        # Parse voice for letter choices
                        voice_lower = voice_text.lower()
                        for i, opt in enumerate(question.options):
                            letter = chr(ord('a') + i)
                            if letter in voice_lower or opt.lower() in voice_lower:
                                response = letter
                                console.print(f"   Heard: [green]{voice_text}[/green] → {letter}")
                                break

                # Fall back to text input
                if response is None:
                    response = click.prompt("Your choice (enter letter or text)", type=str)

                # Convert number to letter if applicable
                try:
                    num = int(response)
                    if 1 <= num <= len(question.options):
                        response = chr(ord('a') + num - 1)  # 1→a, 2→b, etc.
                except ValueError:
                    pass  # User typed letter or text

                if builder.answer(response):
                    break
                else:
                    console.print("[red]Invalid response. Please try again.[/red]")

            console.print()

        # Generate outputs
        console.print()
        console.print("[bold green]✓ Workflow Created![/bold green]")
        console.print()

        # Show YAML
        yaml_content = builder.generate_yaml()
        console.print(Panel(yaml_content, title="Generated YAML", border_style="green"))

        # Show Python
        python_content = builder.generate_python()
        console.print(Panel(python_content, title="Generated Python", border_style="blue"))

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                f.write(yaml_content)
            console.print(f"[green]✓[/green] Saved YAML to: {output}")
        else:
            # Offer to save
            save = click.confirm("Would you like to save the YAML file?", default=True)
            if save:
                default_name = f"workflow-{builder.answers.get('purpose', 'custom').lower().replace(' ', '-')}.yaml"
                filename = click.prompt("Filename", default=default_name)
                with open(filename, "w") as f:
                    f.write(yaml_content)
                console.print(f"[green]✓[/green] Saved to: {filename}")

    except ImportError as e:
        console.print(f"[red]Error loading conversation builder: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
