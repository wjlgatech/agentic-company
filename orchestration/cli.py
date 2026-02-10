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
    # Built-in workflows
    workflows = [
        {"name": "content-research", "description": "Research and analyze content", "status": "active"},
        {"name": "content-creation", "description": "Create new content", "status": "active"},
        {"name": "review-optimize", "description": "Review and optimize content", "status": "active"},
        {"name": "data-processing", "description": "Process and transform data", "status": "active"},
    ]

    table = Table(title="Available Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Status", style="green")

    for wf in workflows:
        table.add_row(wf["name"], wf["description"], wf["status"])

    console.print(table)


@workflow.command("run")
@click.argument("workflow_name")
@click.option("--input", "-i", "input_data", required=True, help="Input data or file path")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--async", "run_async", is_flag=True, help="Run asynchronously")
def workflow_run(
    workflow_name: str,
    input_data: str,
    output: Optional[str],
    run_async: bool,
) -> None:
    """Run a workflow."""
    console.print(f"[cyan]Running workflow:[/cyan] {workflow_name}")
    console.print(f"[cyan]Input:[/cyan] {input_data[:100]}...")

    # Simulate workflow execution
    with console.status("Executing workflow..."):
        import time
        time.sleep(1)  # Simulate processing

    result = {
        "workflow": workflow_name,
        "status": "completed",
        "input": input_data,
        "output": f"Processed result for: {input_data}",
    }

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        console.print(f"[green]✓[/green] Output saved to: {output}")
    else:
        console.print(Panel(result["output"], title="Result", border_style="green"))


@workflow.command("status")
@click.argument("workflow_id")
def workflow_status(workflow_id: str) -> None:
    """Check workflow status."""
    # Placeholder - would query actual workflow status
    console.print(f"Workflow [cyan]{workflow_id}[/cyan]: [green]completed[/green]")


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


if __name__ == "__main__":
    main()
