#!/usr/bin/env python3
"""
Agenticom CLI - Multi-Agent Team Orchestration

Usage:
    agenticom install              Install bundled workflows
    agenticom uninstall [--force]  Remove all Agenticom data
    agenticom workflow list        List available workflows
    agenticom workflow run <id> <task>  Run a workflow
    agenticom workflow status <run-id>  Check run status
    agenticom workflow resume <run-id>  Resume failed run
    agenticom stats                Show statistics
    agenticom dashboard            Start web dashboard
"""

import sys
import json
import click
from pathlib import Path

from . import __version__
from .core import AgenticomCore


def format_json(data: dict) -> str:
    """Pretty-print JSON data."""
    return json.dumps(data, indent=2)


@click.group()
@click.version_option(version=__version__, prog_name="agenticom")
@click.pass_context
def cli(ctx):
    """Agenticom - Multi-Agent Team Orchestration for OpenClaw/Claude Code"""
    ctx.ensure_object(dict)
    ctx.obj["core"] = AgenticomCore()


# ============== Install/Uninstall ==============

@cli.command()
@click.pass_context
def install(ctx):
    """Install bundled workflows to ~/.agenticom"""
    core = ctx.obj["core"]

    click.echo("📦 Installing Agenticom workflows...")
    result = core.install()

    if result["workflows"]:
        click.echo(f"✅ Installed {len(result['workflows'])} workflows:")
        for wf in result["workflows"]:
            click.echo(f"   • {wf}")

    if result["agents"]:
        click.echo(f"✅ Installed {len(result['agents'])} agents:")
        for agent in result["agents"]:
            click.echo(f"   • {agent}")

    if result["errors"]:
        click.echo("⚠️ Errors:")
        for err in result["errors"]:
            click.echo(f"   • {err}")

    click.echo(f"\n📁 Installed to: {core.home}")
    click.echo("🚀 Run: agenticom workflow list")


@cli.command()
@click.option("--force", is_flag=True, help="Confirm deletion")
@click.pass_context
def uninstall(ctx, force):
    """Remove all Agenticom data"""
    core = ctx.obj["core"]

    if not force:
        click.echo("⚠️ This will delete all workflows, agents, and run history.")
        click.echo(f"   Path: {core.home}")
        click.echo("\nRun with --force to confirm.")
        return

    result = core.uninstall(force=True)

    if "error" in result:
        click.echo(f"❌ Error: {result['error']}")
    else:
        click.echo(f"✅ Uninstalled Agenticom from {result['path']}")


# ============== Workflow Commands ==============

@cli.group()
def workflow():
    """Workflow management commands"""
    pass


@workflow.command("list")
@click.pass_context
def workflow_list(ctx):
    """List all installed workflows"""
    core = ctx.obj["core"]
    workflows = core.list_workflows()

    if not workflows:
        click.echo("No workflows installed.")
        click.echo("Run: agenticom install")
        return

    click.echo(f"📋 {len(workflows)} workflows available:\n")

    for wf in workflows:
        if "error" in wf:
            click.echo(f"❌ {wf['id']}: {wf['error']}")
        else:
            click.echo(f"🔹 {wf['id']}")
            click.echo(f"   Name: {wf['name']}")
            click.echo(f"   {wf['description'][:60]}..." if len(wf.get('description', '')) > 60 else f"   {wf.get('description', '')}")
            click.echo(f"   Agents: {wf['agents']} | Steps: {wf['steps']}")
            click.echo()


@workflow.command("run")
@click.argument("workflow_id")
@click.argument("task")
@click.option("--context", "-c", help="JSON context string")
@click.pass_context
def workflow_run(ctx, workflow_id, task, context):
    """Run a workflow with the given task"""
    core = ctx.obj["core"]

    ctx_dict = None
    if context:
        try:
            ctx_dict = json.loads(context)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON in --context")
            return

    click.echo(f"🚀 Running workflow: {workflow_id}")
    click.echo(f"📝 Task: {task}")
    click.echo()

    result = core.run_workflow(workflow_id, task, ctx_dict)

    if "error" in result:
        click.echo(f"❌ Error: {result['error']}")
        return

    click.echo(f"✅ Run ID: {result['run_id']}")
    click.echo(f"📊 Status: {result['status']}")
    click.echo(f"📈 Progress: {result['steps_completed']}/{result['total_steps']} steps")
    click.echo()

    click.echo("📋 Step Results:")
    for step in result["results"]:
        status_icon = "✅" if step["status"] == "completed" else "❌"
        click.echo(f"   {status_icon} {step['step']} ({step['agent']}): {step['status']}")

    click.echo(f"\n💡 Check status: agenticom workflow status {result['run_id']}")


@workflow.command("status")
@click.argument("run_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def workflow_status(ctx, run_id, as_json):
    """Check the status of a workflow run"""
    core = ctx.obj["core"]
    result = core.get_run_status(run_id)

    if as_json:
        click.echo(format_json(result))
        return

    if result.get("error"):
        click.echo(f"❌ {result['error']}")
        return

    click.echo(f"🔹 Run ID: {result['run_id']}")
    click.echo(f"📋 Workflow: {result['workflow']}")
    click.echo(f"📝 Task: {result['task']}")
    click.echo(f"📊 Status: {result['status']}")
    click.echo(f"📈 Progress: {result['progress']}")
    click.echo(f"🕐 Started: {result['created_at']}")
    click.echo(f"🕐 Updated: {result['updated_at']}")

    if result.get("error"):
        click.echo(f"❌ Error: {result['error']}")

    if result.get("steps"):
        click.echo("\n📋 Steps:")
        for step in result["steps"]:
            status_icon = "✅" if step["status"] == "completed" else "⏳" if step["status"] == "running" else "❌"
            click.echo(f"   {status_icon} {step['step_id']} ({step['agent']}): {step['status']}")


@workflow.command("resume")
@click.argument("run_id")
@click.pass_context
def workflow_resume(ctx, run_id):
    """Resume a failed workflow run"""
    core = ctx.obj["core"]

    click.echo(f"🔄 Resuming run: {run_id}")
    result = core.resume_run(run_id)

    if "error" in result:
        click.echo(f"❌ {result['error']}")
        return

    click.echo(f"✅ Run ID: {result['run_id']}")
    click.echo(f"📊 Status: {result['status']}")
    click.echo(f"📈 Progress: {result['steps_completed']}/{result['total_steps']} steps")


# ============== Stats ==============

@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def stats(ctx, as_json):
    """Show Agenticom statistics"""
    core = ctx.obj["core"]
    result = core.get_stats()

    if as_json:
        click.echo(format_json(result))
        return

    click.echo("📊 Agenticom Statistics")
    click.echo("=" * 40)
    click.echo(f"📁 Workflows installed: {result['installed_workflows']}")
    click.echo(f"🔹 Workflow names: {', '.join(result['workflow_names']) or 'None'}")
    click.echo(f"📈 Total runs: {result['total_runs']}")
    click.echo(f"📂 Database: {result['db_path']}")

    if result.get("by_status"):
        click.echo("\n📊 Runs by status:")
        for status, count in result["by_status"].items():
            click.echo(f"   • {status}: {count}")


# ============== Dashboard ==============

@cli.command()
@click.option("--port", default=3333, help="Port number")
@click.pass_context
def dashboard(ctx, port):
    """Start the web dashboard"""
    click.echo(f"🌐 Starting Agenticom dashboard on http://localhost:{port}")
    click.echo("   Press Ctrl+C to stop")

    try:
        from .dashboard import run_dashboard
        run_dashboard(port=port)
    except ImportError:
        click.echo("❌ Dashboard dependencies not installed.")
        click.echo("   Run: pip install agenticom[dashboard]")
    except Exception as e:
        click.echo(f"❌ Error starting dashboard: {e}")


# ============== Main ==============

def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
