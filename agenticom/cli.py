#!/usr/bin/env python3
"""
Agenticom CLI - Multi-Agent Team Orchestration

Usage:
    agenticom install              Install bundled workflows
    agenticom uninstall [--force]  Remove all Agenticom data
    agenticom workflow list        List available workflows
    agenticom workflow run <id> <task>  Run a workflow
    agenticom workflow status <run-id>  Check run status
    agenticom workflow inspect <run-id> View step inputs/outputs
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
@click.option("--dry-run", is_flag=True, help="Show workflow plan without executing")
@click.pass_context
def workflow_run(ctx, workflow_id, task, context, dry_run):
    """Run a workflow with the given task"""
    core = ctx.obj["core"]

    ctx_dict = None
    if context:
        try:
            ctx_dict = json.loads(context)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON in --context")
            return

    workflow = core.get_workflow(workflow_id)
    if not workflow:
        click.echo(f"❌ Workflow '{workflow_id}' not found")
        return

    if dry_run:
        click.echo(f"📋 Workflow: {workflow.name}")
        click.echo(f"📝 Task: {task}")
        click.echo(f"   Agents: {len(workflow.agents)} | Steps: {len(workflow.steps)}")
        click.echo()
        click.echo("📋 Workflow Plan:")
        for i, step in enumerate(workflow.steps, 1):
            click.echo(f"   {i}. {step.id} ({step.agent})")
            if step.expects:
                click.echo(f"      Expects: {step.expects}")
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


@workflow.command("inspect")
@click.argument("run_id")
@click.option("--step", "-s", default=None, help="Show only a specific step")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def workflow_inspect(ctx, run_id, step, as_json):
    """Inspect inputs and outputs of each step in a workflow run"""
    core = ctx.obj["core"]
    result = core.inspect_run(run_id, step_id=step)

    if result.get("error"):
        click.echo(f"❌ {result['error']}")
        return

    if as_json:
        click.echo(format_json(result))
        return

    click.echo(f"🔍 Run: {result['run_id']}  |  Workflow: {result['workflow']}  |  Status: {result['status']}")
    click.echo(f"📝 Task: {result['task']}")
    click.echo("=" * 80)

    for i, s in enumerate(result["steps"], 1):
        status_icon = "✅" if s["status"] == "completed" else "❌"
        click.echo(f"\n{status_icon} Step {i}: {s['step_id']} ({s['agent']})")
        click.echo("-" * 80)

        if s.get("error"):
            click.echo(f"❌ Error: {s['error']}")

        click.echo(f"\n📥 INPUT:")
        click.echo(s["input"].strip())

        click.echo(f"\n📤 OUTPUT:")
        click.echo(s["output"].strip() if s["output"] else "(empty)")

        click.echo(f"\n🕐 {s['started_at']} → {s['completed_at'] or 'n/a'}")
        click.echo("=" * 80)


@workflow.command("archive")
@click.argument("run_id")
@click.pass_context
def workflow_archive(ctx, run_id):
    """Archive a workflow run (soft delete)"""
    from .state import StateManager

    state = StateManager()
    success = state.archive_run(run_id)

    if success:
        click.echo(f"📦 Archived workflow run: {run_id}")
        click.echo("   Use 'agenticom workflow unarchive' to restore")
    else:
        click.echo(f"❌ Failed to archive run: {run_id}")


@workflow.command("unarchive")
@click.argument("run_id")
@click.pass_context
def workflow_unarchive(ctx, run_id):
    """Restore an archived workflow run"""
    from .state import StateManager

    state = StateManager()
    success = state.unarchive_run(run_id)

    if success:
        click.echo(f"📤 Unarchived workflow run: {run_id}")
        click.echo("   Run is now visible in active list")
    else:
        click.echo(f"❌ Failed to unarchive run: {run_id}")


@workflow.command("delete")
@click.argument("run_id")
@click.option("--permanent", is_flag=True, help="Permanently delete (cannot be undone)")
@click.pass_context
def workflow_delete(ctx, run_id, permanent):
    """Delete a workflow run"""
    from .state import StateManager

    state = StateManager()

    if permanent:
        confirm = click.confirm(
            f"⚠️  Permanently delete run {run_id}? This cannot be undone!",
            default=False
        )
        if not confirm:
            click.echo("❌ Delete cancelled")
            return

    success = state.delete_run(run_id, permanent=permanent)

    if success:
        if permanent:
            click.echo(f"🗑️  Permanently deleted workflow run: {run_id}")
        else:
            click.echo(f"📦 Archived workflow run: {run_id}")
            click.echo("   Use 'agenticom workflow unarchive' to restore")
    else:
        click.echo(f"❌ Failed to delete run: {run_id}")


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


# ============== Diagnostics ==============

@cli.command()
@click.pass_context
def diagnostics(ctx):
    """Check diagnostics system status"""
    from orchestration.diagnostics import check_playwright_installation

    click.echo("🔬 Diagnostics System Status")
    click.echo("=" * 40)

    if check_playwright_installation():
        click.echo("✅ Playwright: Installed")
        try:
            import playwright
            version = getattr(playwright, '__version__', 'unknown')
            click.echo(f"   Version: {version}")
        except Exception:
            pass
        click.echo("\n📋 Usage:")
        click.echo("   Add diagnostics_config to workflow YAML")
        click.echo("   Set enabled: true and configure options")
        click.echo("\n📚 Documentation:")
        click.echo("   See docs/diagnostics.md (coming in Phase 6)")
    else:
        click.echo("❌ Playwright: Not installed")
        click.echo("\n📦 Install with:")
        click.echo("   pip install 'agentic-company[diagnostics]'")
        click.echo("\n🌐 Then install browsers:")
        click.echo("   playwright install")
        click.echo("\n   Or install just Chromium:")
        click.echo("   playwright install chromium")


# ============== Dashboard ==============

@cli.command()
@click.option("--port", "-p", default=8081, help="Port number (default: 8081)")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.pass_context
def dashboard(ctx, port, no_browser):
    """Start the web dashboard"""
    try:
        from .dashboard import start_dashboard
        start_dashboard(port=port, open_browser=not no_browser)
    except ImportError as e:
        click.echo(f"❌ Dashboard import error: {e}")
    except Exception as e:
        click.echo(f"❌ Error starting dashboard: {e}")


# ============== Main ==============

def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
