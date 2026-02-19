#!/usr/bin/env python3
"""
Test script for stage tracking implementation.
Tests that stages are properly tracked as workflow steps execute.
"""

import json
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Setup test environment
test_db_dir = tempfile.mkdtemp()
test_db_path = Path(test_db_dir) / "test_state.db"

from agenticom.state import StateManager, WorkflowRun, StepResult, StepStatus, WorkflowStage
from agenticom.workflows import WorkflowDefinition, WorkflowRunner, AgentDefinition, StepDefinition


def test_stage_initialization():
    """Test that WorkflowRun initializes stages correctly."""
    print("=" * 60)
    print("TEST 1: Stage Initialization")
    print("=" * 60)

    run = WorkflowRun(
        id="test-123",
        workflow_id="test-workflow",
        task="Test task",
        status=StepStatus.PENDING,
        current_step=0,
        total_steps=5,
        context={"task": "Test"},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    # Check that stages are initialized
    assert run.stages is not None, "Stages should be initialized"
    assert len(run.stages) == 5, f"Should have 5 stages, got {len(run.stages)}"

    for stage in WorkflowStage:
        assert stage.value in run.stages, f"Stage {stage.value} should be initialized"
        stage_info = run.stages[stage.value]
        assert stage_info.started_at is None, f"Stage {stage.value} should not be started yet"
        assert stage_info.completed_at is None, f"Stage {stage.value} should not be completed yet"

    print("✅ Stages initialized correctly")
    print(f"   Initialized stages: {list(run.stages.keys())}")
    print()


def test_stage_transitions():
    """Test stage start and complete methods."""
    print("=" * 60)
    print("TEST 2: Stage Transitions")
    print("=" * 60)

    run = WorkflowRun(
        id="test-456",
        workflow_id="test-workflow",
        task="Test task",
        status=StepStatus.PENDING,
        current_step=0,
        total_steps=5,
        context={"task": "Test"},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    # Start plan stage
    run.start_stage(WorkflowStage.PLAN, "plan")
    assert run.current_stage == WorkflowStage.PLAN, "Current stage should be PLAN"
    assert run.stages["plan"].started_at is not None, "Plan stage should have started_at"
    assert run.stages["plan"].step_id == "plan", "Plan stage should have step_id"
    print("✅ Stage started correctly")
    print(f"   Current stage: {run.current_stage}")
    print(f"   Plan stage started at: {run.stages['plan'].started_at}")

    # Complete plan stage
    run.complete_stage(WorkflowStage.PLAN)
    assert run.stages["plan"].completed_at is not None, "Plan stage should have completed_at"
    print("✅ Stage completed correctly")
    print(f"   Plan stage completed at: {run.stages['plan'].completed_at}")

    # Add artifact
    run.add_artifact(WorkflowStage.PLAN, "/path/to/plan.md")
    assert len(run.stages["plan"].artifacts) == 1, "Should have 1 artifact"
    assert run.stages["plan"].artifacts[0] == "/path/to/plan.md", "Artifact path should match"
    print("✅ Artifact added correctly")
    print(f"   Plan stage artifacts: {run.stages['plan'].artifacts}")
    print()


def test_stage_persistence():
    """Test that stages are persisted to database."""
    print("=" * 60)
    print("TEST 3: Stage Persistence")
    print("=" * 60)

    state = StateManager(db_path=test_db_path)

    # Create and save run with stage data
    run = WorkflowRun(
        id="test-789",
        workflow_id="test-workflow",
        task="Test task",
        status=StepStatus.RUNNING,
        current_step=1,
        total_steps=5,
        context={"task": "Test"},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

    run.start_stage(WorkflowStage.PLAN, "plan")
    run.complete_stage(WorkflowStage.PLAN)
    run.add_artifact(WorkflowStage.PLAN, "/outputs/plan.md")

    run.start_stage(WorkflowStage.IMPLEMENT, "develop")
    run.add_artifact(WorkflowStage.IMPLEMENT, "/outputs/code.py")

    state.create_run(run)
    print("✅ Run created in database")

    # Retrieve and verify
    loaded_run = state.get_run("test-789")
    assert loaded_run is not None, "Run should be retrieved"
    assert loaded_run.stages is not None, "Stages should be loaded"
    assert loaded_run.current_stage == WorkflowStage.IMPLEMENT, "Current stage should be IMPLEMENT"

    plan_stage = loaded_run.stages["plan"]
    assert plan_stage.started_at is not None, "Plan stage should have started_at"
    assert plan_stage.completed_at is not None, "Plan stage should have completed_at"
    assert len(plan_stage.artifacts) == 1, "Plan stage should have 1 artifact"

    implement_stage = loaded_run.stages["implement"]
    assert implement_stage.started_at is not None, "Implement stage should have started_at"
    assert implement_stage.completed_at is None, "Implement stage should not be completed"
    assert len(implement_stage.artifacts) == 1, "Implement stage should have 1 artifact"

    print("✅ Stages persisted and loaded correctly")
    print(f"   Current stage: {loaded_run.current_stage}")
    print(f"   Plan stage: started={plan_stage.started_at}, completed={plan_stage.completed_at}")
    print(f"   Implement stage: started={implement_stage.started_at}, completed={implement_stage.completed_at}")
    print()


def test_workflow_integration():
    """Test stage tracking in workflow execution."""
    print("=" * 60)
    print("TEST 4: Workflow Integration")
    print("=" * 60)

    state = StateManager(db_path=test_db_path)

    # Define a simple workflow
    workflow = WorkflowDefinition(
        id="test-workflow",
        name="Test Workflow",
        description="Test workflow for stage tracking",
        agents=[
            AgentDefinition(
                id="planner",
                name="Planner",
                role="Planning Agent",
                prompt_template="You are a planner."
            ),
            AgentDefinition(
                id="developer",
                name="Developer",
                role="Development Agent",
                prompt_template="You are a developer."
            ),
        ],
        steps=[
            StepDefinition(
                id="plan",
                agent="planner",
                description="Create a plan",
                input_template="Task: {{task}}"
            ),
            StepDefinition(
                id="develop",
                agent="developer",
                description="Develop the solution",
                input_template="Implement: {{step_outputs.plan}}"
            ),
        ]
    )

    def mock_executor(agent_prompt: str, task_context: str) -> str:
        """Mock executor that returns simple output."""
        if "planner" in agent_prompt.lower():
            return "PLAN:\n1. Step one\n2. Step two\n\nSTATUS: done"
        else:
            return "```python\nprint('hello')\n```\n\nSTATUS: done"

    runner = WorkflowRunner(state_manager=state, executor=mock_executor)

    # Start workflow
    run = runner.start(workflow, "Build a simple app")
    print(f"✅ Workflow started: {run.id}")

    # Execute first step (plan)
    result1 = runner.execute_step(workflow, run, 0)
    run = state.get_run(run.id)  # Reload to get updated stages

    assert result1.status == StepStatus.COMPLETED, "Plan step should complete"
    assert run.stages is not None, "Stages should exist"
    assert run.stages["plan"].started_at is not None, "Plan stage should have started"
    print(f"✅ Plan stage tracked correctly")
    print(f"   Stage started: {run.stages['plan'].started_at}")
    print(f"   Stage completed: {run.stages['plan'].completed_at}")

    # Execute second step (implement)
    result2 = runner.execute_step(workflow, run, 1)
    run = state.get_run(run.id)  # Reload to get updated stages

    assert result2.status == StepStatus.COMPLETED, "Develop step should complete"
    assert run.stages["implement"].started_at is not None, "Implement stage should have started"
    print(f"✅ Implement stage tracked correctly")
    print(f"   Stage started: {run.stages['implement'].started_at}")
    print(f"   Stage completed: {run.stages['implement'].completed_at}")

    # Verify to_dict serialization includes stages
    run_dict = run.to_dict()
    assert "stages" in run_dict, "to_dict should include stages"
    assert "current_stage" in run_dict, "to_dict should include current_stage"
    assert run_dict["stages"]["plan"]["started_at"] is not None, "Serialized plan stage should have started_at"
    print(f"✅ Serialization includes stages")
    print(f"   Serialized stages: {list(run_dict['stages'].keys())}")
    print()


def test_stage_detection():
    """Test automatic stage detection from step IDs."""
    print("=" * 60)
    print("TEST 5: Stage Detection")
    print("=" * 60)

    from agenticom.workflows import WorkflowRunner

    test_cases = [
        ("plan", WorkflowStage.PLAN),
        ("planning", WorkflowStage.PLAN),
        ("analyze", WorkflowStage.PLAN),
        ("develop", WorkflowStage.IMPLEMENT),
        ("implement", WorkflowStage.IMPLEMENT),
        ("code", WorkflowStage.IMPLEMENT),
        ("build", WorkflowStage.IMPLEMENT),
        ("verify", WorkflowStage.VERIFY),
        ("check", WorkflowStage.VERIFY),
        ("validate", WorkflowStage.VERIFY),
        ("test", WorkflowStage.TEST),
        ("testing", WorkflowStage.TEST),
        ("qa", WorkflowStage.TEST),
        ("review", WorkflowStage.REVIEW),
        ("finalize", WorkflowStage.REVIEW),
        ("approve", WorkflowStage.REVIEW),
    ]

    for step_id, expected_stage in test_cases:
        detected = WorkflowRunner._detect_stage_from_step_id(step_id)
        assert detected == expected_stage, f"Step '{step_id}' should map to {expected_stage}, got {detected}"
        print(f"✅ '{step_id}' → {expected_stage.value}")

    print()


if __name__ == "__main__":
    try:
        print("\n🧪 Testing Stage Tracking Implementation\n")

        test_stage_initialization()
        test_stage_transitions()
        test_stage_persistence()
        test_workflow_integration()
        test_stage_detection()

        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✅ Stage initialization works")
        print("  ✅ Stage transitions (start/complete) work")
        print("  ✅ Artifact tracking works")
        print("  ✅ Database persistence works")
        print("  ✅ Workflow integration works")
        print("  ✅ Stage detection from step IDs works")
        print()
        print("Phase 1: Enhanced Ticket Tracking - COMPLETE")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        raise
    finally:
        # Cleanup
        import shutil
        if os.path.exists(test_db_dir):
            shutil.rmtree(test_db_dir)
