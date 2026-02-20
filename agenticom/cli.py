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

import json
from pathlib import Path

import click

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
            click.echo(
                f"   {wf['description'][:60]}..."
                if len(wf.get("description", "")) > 60
                else f"   {wf.get('description', '')}"
            )
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
    click.echo(
        f"📈 Progress: {result['steps_completed']}/{result['total_steps']} steps"
    )
    click.echo()

    click.echo("📋 Step Results:")
    for step in result["results"]:
        status_icon = "✅" if step["status"] == "completed" else "❌"
        click.echo(
            f"   {status_icon} {step['step']} ({step['agent']}): {step['status']}"
        )

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
            status_icon = (
                "✅"
                if step["status"] == "completed"
                else "⏳" if step["status"] == "running" else "❌"
            )
            click.echo(
                f"   {status_icon} {step['step_id']} ({step['agent']}): {step['status']}"
            )


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
    click.echo(
        f"📈 Progress: {result['steps_completed']}/{result['total_steps']} steps"
    )


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

    click.echo(
        f"🔍 Run: {result['run_id']}  |  Workflow: {result['workflow']}  |  Status: {result['status']}"
    )
    click.echo(f"📝 Task: {result['task']}")
    click.echo("=" * 80)

    for i, s in enumerate(result["steps"], 1):
        status_icon = "✅" if s["status"] == "completed" else "❌"
        click.echo(f"\n{status_icon} Step {i}: {s['step_id']} ({s['agent']})")
        click.echo("-" * 80)

        if s.get("error"):
            click.echo(f"❌ Error: {s['error']}")

        click.echo("\n📥 INPUT:")
        click.echo(s["input"].strip())

        click.echo("\n📤 OUTPUT:")
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
            default=False,
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

            version = getattr(playwright, "__version__", "unknown")
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


# ============== Phase 5: Criteria Builder ==============


@cli.command("build-criteria")
@click.argument("task")
@click.option("--context", "-c", help='JSON context (e.g., \'{"framework": "React"}\')')
@click.option("--output", "-o", default="success_criteria.json", help="Output file")
@click.option(
    "--non-interactive", is_flag=True, help="Skip Q&A (use initial criteria only)"
)
@click.pass_context
def build_criteria(ctx, task, context, output, non_interactive):
    """Build success criteria interactively with AI

    Example:
        agenticom build-criteria "Build a login page" -c '{"framework": "React"}'
    """
    import asyncio
    import json as json_lib

    from orchestration.diagnostics.criteria_builder import CriteriaBuilder
    from orchestration.integrations.unified import auto_setup_executor

    try:
        # Parse context
        context_dict = {}
        if context:
            try:
                context_dict = json_lib.loads(context)
            except json_lib.JSONDecodeError:
                click.echo(f"❌ Invalid JSON context: {context}", err=True)
                return

        click.echo("🤖 Building Success Criteria with AI")
        click.echo("=" * 60)
        click.echo(f"Task: {task}")
        if context_dict:
            click.echo(f"Context: {json_lib.dumps(context_dict, indent=2)}")
        click.echo()

        # Setup executor
        click.echo("📡 Connecting to LLM...")
        executor = auto_setup_executor()
        click.echo("   ✅ Connected")
        click.echo()

        # Define question callback for interactive mode
        def ask_question(question: str) -> str:
            if non_interactive:
                return "No response provided"

            click.echo(f"❓ {question}")
            response = click.prompt("   Your answer", type=str, default="")
            click.echo()
            return response

        # Build criteria
        builder = CriteriaBuilder(executor, question_callback=ask_question)

        async def run():
            return await builder.build_criteria(task, context_dict)

        criteria = asyncio.run(run())

        # Display results
        click.echo("=" * 60)
        click.echo("✅ Success Criteria Generated")
        click.echo("=" * 60)
        click.echo()

        click.echo("📋 Criteria:")
        for i, criterion in enumerate(criteria.criteria, 1):
            click.echo(f"  {i}. {criterion}")
        click.echo()

        click.echo(f"📊 Confidence: {criteria.confidence:.2f}")
        click.echo(f"❓ Questions Asked: {len(criteria.questions_asked)}")
        click.echo(
            f"💬 Responses Provided: {len([r for r in criteria.human_responses if r and r != 'No response provided'])}"
        )
        click.echo()

        # Save to file
        with open(output, "w") as f:
            json_lib.dump(criteria.to_dict(), f, indent=2)

        click.echo(f"📝 Saved to: {output}")
        click.echo()
        click.echo(
            "💡 Tip: Use these criteria in your workflow YAML under step metadata"
        )

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback

        traceback.print_exc()


# ============== Phase 6: Diagnostics Testing ==============


@cli.command("test-diagnostics")
@click.argument("url")
@click.option(
    "--actions",
    "-a",
    type=click.Path(exists=True),
    help="JSON file with browser actions",
)
@click.option("--headless/--headed", default=True, help="Run browser in headless mode")
@click.option(
    "--output-dir",
    "-o",
    default="outputs/diagnostics",
    help="Output directory for screenshots",
)
@click.pass_context
def test_diagnostics(ctx, url, actions, headless, output_dir):
    """Test URL with browser automation diagnostics

    Example:
        agenticom test-diagnostics http://localhost:3000 -a login_test.json --headed
    """
    import asyncio
    import json as json_lib

    from orchestration.diagnostics import (
        BrowserAction,
        DiagnosticsConfig,
        PlaywrightCapture,
    )

    try:
        # Load actions
        test_actions = []
        if actions:
            with open(actions) as f:
                actions_data = json_lib.load(f)
                test_actions = actions_data.get("actions", [])
        else:
            # Default actions: navigate and screenshot
            test_actions = [
                {"type": "navigate", "value": url},
                {"type": "screenshot", "value": "page.png"},
            ]

        click.echo("🔬 Running Browser Diagnostics")
        click.echo("=" * 60)
        click.echo(f"URL: {url}")
        click.echo(f"Actions: {len(test_actions)}")
        click.echo(f"Headless: {headless}")
        click.echo(f"Output: {output_dir}")
        click.echo()

        # Create config
        config = DiagnosticsConfig(
            enabled=True,
            playwright_headless=headless,
            capture_screenshots=True,
            capture_console=True,
            capture_network=True,
            output_dir=Path(output_dir),
        )

        # Convert actions to BrowserAction objects
        actions_list = [BrowserAction.from_dict(a) for a in test_actions]

        # Run diagnostics
        async def run():
            capture = PlaywrightCapture(config)
            async with capture:
                result = await capture.execute_actions(actions_list, Path(output_dir))
            return result

        click.echo("🚀 Running browser automation...")
        result = asyncio.run(run())

        # Display results
        click.echo()
        click.echo("=" * 60)
        click.echo("Results")
        click.echo("=" * 60)

        if result.success:
            click.echo("✅ Success: True")
        else:
            click.echo("❌ Success: False")
            if result.error:
                click.echo(f"   Error: {result.error}")

        click.echo(f"📊 Console logs: {len(result.console_logs)}")
        click.echo(f"❌ Console errors: {len(result.console_errors)}")
        click.echo(f"🌐 Network requests: {len(result.network_requests)}")
        click.echo(f"📸 Screenshots: {len(result.screenshots)}")
        click.echo(f"🔗 Final URL: {result.final_url}")
        click.echo(f"⏱️  Execution time: {result.execution_time_ms:.0f}ms")
        click.echo()

        if result.screenshots:
            click.echo("📸 Screenshots:")
            for screenshot in result.screenshots:
                click.echo(f"   • {screenshot}")
            click.echo()

        if result.console_errors:
            click.echo("❌ Console Errors (first 3):")
            for error in result.console_errors[:3]:
                click.echo(f"   [{error.type}] {error.text[:80]}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback

        traceback.print_exc()


# ============== Feedback / Self-Improvement ==============


@cli.group()
def feedback():
    """Self-improvement feedback commands — review and manage prompt patches."""
    pass


@feedback.command("rate-run")
@click.argument("run_id")
@click.argument("score", type=float)
@click.option("--notes", "-n", default="", help="Optional notes")
@click.pass_context
def feedback_rate_run(ctx, run_id, score, notes):
    """Rate a completed workflow run (0.0–1.0).

    Example:
        agenticom feedback rate-run abc123 0.9 --notes "Great output"
    """
    if not 0.0 <= score <= 1.0:
        click.echo("❌ Score must be between 0.0 and 1.0")
        return

    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        ok = loop.rate_run(run_id, score, notes)
        if ok:
            click.echo(f"✅ Run {run_id} rated {score:.2f}")
        else:
            click.echo(f"❌ Run {run_id} not found in self-improvement records")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("list-patches")
@click.option("--workflow", "-w", default=None, help="Filter by workflow ID")
@click.option(
    "--status", "-s", default=None, help="Filter by status (pending/applied/rejected)"
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def feedback_list_patches(ctx, workflow, status, as_json):
    """List prompt patches proposed by the self-improvement loop.

    Example:
        agenticom feedback list-patches --workflow feature-dev
    """
    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        patches = loop.list_patches(workflow_id=workflow, status=status)

        if as_json:
            click.echo(format_json({"patches": patches}))
            return

        if not patches:
            click.echo("No patches found.")
            return

        click.echo(f"📋 {len(patches)} patch(es):\n")
        for p in patches:
            icon = {"pending": "⏳", "applied": "✅", "rejected": "❌"}.get(
                p["status"], "🔹"
            )
            click.echo(
                f"{icon} [{p['id'][:8]}] {p['agent_id']} | "
                f"{p['status']} | conf={p['confidence']:.2f} | by={p['generated_by']}"
            )
            click.echo(f"   Gaps: {', '.join(p['gaps'][:3])}")
            click.echo(f"   {p['justification']}")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("approve-patch")
@click.argument("patch_id")
@click.option("--notes", "-n", default="", help="Optional approval notes")
@click.pass_context
def feedback_approve_patch(ctx, patch_id, notes):
    """Approve and immediately apply a pending prompt patch.

    Example:
        agenticom feedback approve-patch abc12345
    """
    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        result = loop.approve_patch(patch_id, notes=notes)
        if "error" in result:
            click.echo(f"❌ {result['error']}")
        else:
            click.echo(f"✅ Patch applied → version {result['version_number']}")
            click.echo(f"   New version ID: {result['new_version_id']}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("reject-patch")
@click.argument("patch_id")
@click.argument("reason")
@click.pass_context
def feedback_reject_patch(ctx, patch_id, reason):
    """Reject a pending prompt patch.

    Example:
        agenticom feedback reject-patch abc12345 "Adds too many constraints"
    """
    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        result = loop.reject_patch(patch_id, reason)
        if "error" in result:
            click.echo(f"❌ {result['error']}")
        else:
            click.echo(f"✅ Patch {patch_id} rejected")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("rollback")
@click.argument("workflow_id")
@click.argument("agent_id")
@click.pass_context
def feedback_rollback(ctx, workflow_id, agent_id):
    """Roll back an agent's persona to the previous version.

    Example:
        agenticom feedback rollback feature-dev planner
    """
    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        result = loop.rollback(workflow_id, agent_id)
        if "error" in result:
            click.echo(f"❌ {result['error']}")
        else:
            click.echo(
                f"✅ Rolled back {agent_id} to version {result['version_number']}"
            )
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("status")
@click.option("--workflow", "-w", default=None, help="Filter by workflow ID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def feedback_status(ctx, workflow, as_json):
    """Show self-improvement status: pending patches, applied patches.

    Example:
        agenticom feedback status --workflow feature-dev
    """
    try:
        from orchestration.self_improvement import get_improvement_loop

        loop = get_improvement_loop()
        result = loop.feedback_status(workflow_id=workflow)

        if as_json:
            click.echo(format_json(result))
            return

        click.echo("📊 Self-Improvement Status")
        click.echo("=" * 40)
        click.echo(f"⏳ Pending patches : {result['pending_patches']}")
        click.echo(f"✅ Applied patches : {result['applied_patches']}")

        if result["patches"]:
            click.echo("\n📋 Recent patches:")
            for p in result["patches"][:5]:
                icon = {"pending": "⏳", "applied": "✅", "rejected": "❌"}.get(
                    p["status"], "🔹"
                )
                click.echo(f"  {icon} {p['id'][:8]} | {p['agent_id']} | {p['status']}")
        else:
            click.echo("\nNo patches yet. Run a workflow to start learning.")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@feedback.command("report")
@click.argument("workflow_id")
@click.option(
    "--baseline-runs",
    "-b",
    default=5,
    show_default=True,
    help="Number of earliest runs to use as baseline",
)
@click.option(
    "--recent-runs",
    "-r",
    default=5,
    show_default=True,
    help="Number of latest runs to compare against",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def feedback_report(ctx, workflow_id, baseline_runs, recent_runs, as_json):
    """Before/after improvement report for a workflow.

    Compares agent SMARC scores between the earliest runs (baseline) and the
    most recent runs, lists every patch that has been applied, and shows the
    measured score delta so you can see the self-improvement loop working.

    Example:
        agenticom feedback report feature-dev
        agenticom feedback report due-diligence --baseline-runs 3 --recent-runs 3
    """
    import json
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".agenticom" / "self_improve.db"
    if not db_path.exists():
        click.echo(
            "❌ No self-improvement data yet. "
            'Run a workflow first: agenticom workflow run feature-dev "<task>"'
        )
        return

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row

            # ── Run records ──────────────────────────────────────────────
            rows = conn.execute(
                "SELECT id, overall_success, total_duration_ms, total_retries, "
                "       total_tokens, agent_scores, step_scores, created_at "
                "FROM si_run_records WHERE workflow_id = ? ORDER BY created_at ASC",
                (workflow_id,),
            ).fetchall()

            if not rows:
                click.echo(
                    f"❌ No runs recorded for workflow '{workflow_id}'.\n"
                    f"   Make sure self_improve is enabled and you have run the workflow."
                )
                return

            total_runs = len(rows)
            base_rows = rows[:baseline_runs]
            recent_rows = rows[-recent_runs:] if total_runs > baseline_runs else rows

            def avg_agent_scores(run_rows):
                sums: dict[str, float] = {}
                counts: dict[str, int] = {}
                for r in run_rows:
                    scores = json.loads(r["agent_scores"] or "{}")
                    for agent, score in scores.items():
                        sums[agent] = sums.get(agent, 0.0) + float(score)
                        counts[agent] = counts.get(agent, 0) + 1
                return {a: sums[a] / counts[a] for a in sums}

            baseline_scores = avg_agent_scores(base_rows)
            recent_scores = avg_agent_scores(recent_rows)
            all_agents = sorted(set(baseline_scores) | set(recent_scores))

            # ── Applied patches ───────────────────────────────────────────
            patches = conn.execute(
                "SELECT id, agent_id, agent_role, generated_by, confidence, "
                "       capability_gaps, justification, approved_at "
                "FROM si_prompt_patches "
                "WHERE workflow_id = ? AND status = 'applied' "
                "ORDER BY approved_at ASC",
                (workflow_id,),
            ).fetchall()

            # ── Summary stats ─────────────────────────────────────────────
            success_rate = (
                sum(1 for r in rows if r["overall_success"]) / total_runs * 100
            )
            avg_tokens = sum(r["total_tokens"] or 0 for r in rows) / total_runs
            avg_duration_s = (
                sum(r["total_duration_ms"] or 0 for r in rows) / total_runs / 1000
            )

        # ── JSON output ───────────────────────────────────────────────────
        if as_json:
            deltas = {
                a: {
                    "baseline": round(baseline_scores.get(a, 0.0), 3),
                    "recent": round(recent_scores.get(a, 0.0), 3),
                    "delta": round(
                        recent_scores.get(a, 0.0) - baseline_scores.get(a, 0.0), 3
                    ),
                }
                for a in all_agents
            }
            click.echo(
                format_json(
                    {
                        "workflow_id": workflow_id,
                        "total_runs": total_runs,
                        "baseline_runs": len(base_rows),
                        "recent_runs": len(recent_rows),
                        "success_rate_pct": round(success_rate, 1),
                        "avg_tokens_per_run": round(avg_tokens),
                        "avg_duration_s": round(avg_duration_s, 1),
                        "agent_scores": deltas,
                        "patches_applied": len(patches),
                    }
                )
            )
            return

        # ── Human-readable output ─────────────────────────────────────────
        click.echo()
        click.echo(f"  Self-Improvement Report — {workflow_id}")
        click.echo(f"  {'─' * 56}")
        click.echo(
            f"  Runs analysed : {total_runs}   "
            f"Success rate: {success_rate:.0f}%   "
            f"Patches applied: {len(patches)}"
        )
        click.echo(
            f"  Avg tokens    : {avg_tokens:,.0f} / run   "
            f"Avg duration: {avg_duration_s:.1f}s"
        )
        click.echo(
            f"  Baseline      : first {len(base_rows)} run(s)   "
            f"Current: last {len(recent_rows)} run(s)"
        )
        click.echo()

        # Agent score table
        col_w = max((len(a) for a in all_agents), default=8) + 2
        header = (
            f"  {'Agent':<{col_w}} {'Baseline':>10} {'Current':>10} {'Δ':>8}  Trend"
        )
        click.echo(header)
        click.echo(f"  {'─' * (col_w + 36)}")

        overall_deltas = []
        for agent in all_agents:
            b = baseline_scores.get(agent, 0.0)
            c = recent_scores.get(agent, 0.0)
            delta = c - b
            overall_deltas.append(delta)

            bar_len = int(c * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            trend = "▲" if delta > 0.02 else ("▼" if delta < -0.02 else "─")
            delta_str = f"{delta:+.3f}" if delta != 0 else "  n/a "
            click.echo(
                f"  {agent:<{col_w}} {b:>10.3f} {c:>10.3f} {delta_str:>8}  "
                f"{trend} {bar}"
            )

        click.echo()
        if overall_deltas:
            avg_delta = sum(overall_deltas) / len(overall_deltas)
            direction = "improved" if avg_delta > 0 else "declined"
            click.echo(
                f"  Overall score {direction} by {avg_delta:+.3f} "
                f"across {len(all_agents)} agent(s)"
            )

        # Applied patches
        if patches:
            click.echo()
            click.echo(f"  Applied patches ({len(patches)}):")
            click.echo(f"  {'─' * 56}")
            for p in patches:
                gaps = json.loads(p["capability_gaps"] or "[]")
                gap_str = ", ".join(g.replace("_", " ") for g in gaps[:3])
                ts = (p["approved_at"] or "")[:10]
                click.echo(
                    f"  [{p['id'][:8]}]  {p['agent_id']:<20} "
                    f"{'by ' + p['generated_by']:<12} {ts}"
                )
                click.echo(f"    gaps : {gap_str or 'none listed'}")
                click.echo(f"    why  : {p['justification'][:80]}")
                click.echo()
        else:
            click.echo()
            click.echo(
                "  No patches applied yet. "
                f"Run the workflow {5 - total_runs} more time(s) to trigger gap detection."
                if total_runs < 5
                else "  No patches applied yet. Use `agenticom feedback list-patches` "
                "to see pending proposals."
            )

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")
        import traceback

        traceback.print_exc()


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
