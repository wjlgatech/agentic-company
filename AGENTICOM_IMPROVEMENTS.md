# Agenticom Framework Improvements

Based on meta-analysis of AI-human collaboration patterns, this document proposes concrete improvements to the Agenticom framework.

## Executive Summary

**Problem:** Current workflow execution provides limited visibility and verification, leading to high iteration counts when debugging issues.

**Solution:** Add built-in verification testing, enhanced observability, and interactive debugging capabilities.

**Impact:** Reduce bug fix iterations from 5-8 to 1-2, improve developer experience, enable self-healing workflows.

## Priority 1: Built-in Verification Testing

### Current State
- Workflows execute steps but don't verify outputs meet quality standards
- No automated testing of step outputs before proceeding
- Developers must manually test after workflow completion

### Proposed: WorkflowVerifier Module

**File:** `orchestration/testing/verifier.py`

```python
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class VerificationLevel(Enum):
    SYNTAX = "syntax"          # Basic syntax checking
    SEMANTIC = "semantic"      # Meaning/content validation
    FUNCTIONAL = "functional"  # Actual execution testing
    INTEGRATION = "integration" # End-to-end testing

@dataclass
class VerificationResult:
    passed: bool
    level: VerificationLevel
    message: str
    details: Optional[Dict] = None
    suggestions: List[str] = None

class WorkflowVerifier:
    """Automated verification testing for workflow steps"""

    def __init__(self):
        self.verifiers: Dict[str, List[Callable]] = {}

    def register_verifier(
        self,
        step_type: str,
        verifier: Callable,
        level: VerificationLevel
    ):
        """Register a verification function for a step type"""
        if step_type not in self.verifiers:
            self.verifiers[step_type] = []
        self.verifiers[step_type].append((verifier, level))

    async def verify_step_output(
        self,
        step_id: str,
        step_type: str,
        output: str,
        level: VerificationLevel = VerificationLevel.SEMANTIC
    ) -> VerificationResult:
        """
        Verify step output meets quality standards

        Example usage:
            result = await verifier.verify_step_output(
                step_id="implement",
                step_type="code_generation",
                output="def hello(): print('world')",
                level=VerificationLevel.SYNTAX
            )

            if not result.passed:
                # Auto-retry or loop back
                return result
        """
        # Get verifiers for this step type
        verifiers = self.verifiers.get(step_type, [])

        # Run applicable verifiers
        for verifier_func, verifier_level in verifiers:
            if verifier_level.value <= level.value:
                result = await verifier_func(step_id, output)
                if not result.passed:
                    return result

        return VerificationResult(
            passed=True,
            level=level,
            message=f"All {level.value} checks passed"
        )

# Built-in verifiers
async def verify_code_syntax(step_id: str, output: str) -> VerificationResult:
    """Verify generated code has valid syntax"""
    import ast

    try:
        # Try to parse as Python
        ast.parse(output)
        return VerificationResult(
            passed=True,
            level=VerificationLevel.SYNTAX,
            message="Code syntax is valid"
        )
    except SyntaxError as e:
        return VerificationResult(
            passed=False,
            level=VerificationLevel.SYNTAX,
            message=f"Syntax error: {e.msg}",
            details={"line": e.lineno, "offset": e.offset},
            suggestions=[
                "Check for unmatched brackets or quotes",
                "Verify indentation is consistent",
                "Review the error line and surrounding context"
            ]
        )

async def verify_api_response(step_id: str, output: str) -> VerificationResult:
    """Verify API endpoint is accessible"""
    import httpx
    import re

    # Extract URLs from output
    urls = re.findall(r'http[s]?://[^\s]+', output)

    if not urls:
        return VerificationResult(
            passed=True,
            level=VerificationLevel.FUNCTIONAL,
            message="No URLs to verify"
        )

    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code >= 400:
                    return VerificationResult(
                        passed=False,
                        level=VerificationLevel.FUNCTIONAL,
                        message=f"API endpoint {url} returned {response.status_code}",
                        suggestions=[
                            "Check if server is running",
                            "Verify endpoint exists",
                            "Review authentication requirements"
                        ]
                    )
            except Exception as e:
                return VerificationResult(
                    passed=False,
                    level=VerificationLevel.FUNCTIONAL,
                    message=f"Could not reach {url}: {e}",
                    suggestions=[
                        "Start the development server",
                        "Check firewall settings",
                        "Verify URL is correct"
                    ]
                )

    return VerificationResult(
        passed=True,
        level=VerificationLevel.FUNCTIONAL,
        message=f"All {len(urls)} API endpoints accessible"
    )
```

**Integration into AgentTeam:**

```python
# orchestration/agents/team.py

class AgentTeam:
    def __init__(self, ...):
        self.verifier = WorkflowVerifier()
        self._register_default_verifiers()

    def _register_default_verifiers(self):
        """Register built-in verifiers"""
        self.verifier.register_verifier(
            "code_generation",
            verify_code_syntax,
            VerificationLevel.SYNTAX
        )
        self.verifier.register_verifier(
            "api_implementation",
            verify_api_response,
            VerificationLevel.FUNCTIONAL
        )

    async def execute_step(self, step: WorkflowStep) -> StepResult:
        # ... existing code ...

        # Execute step
        output = await agent.execute(final_input)

        # NEW: Verify output before proceeding
        verification = await self.verifier.verify_step_output(
            step_id=step.id,
            step_type=step.metadata.get("type", "general"),
            output=output,
            level=VerificationLevel.SEMANTIC
        )

        if not verification.passed:
            result.status = StepStatus.FAILED
            result.error = verification.message
            result.metadata["verification_failed"] = True
            result.metadata["suggestions"] = verification.suggestions
            return result

        # Continue with existing quality gate and expectations...
        # ...
```

**YAML Configuration:**

```yaml
steps:
  - id: implement
    agent: developer
    input: "{{task}}"
    metadata:
      type: code_generation
      verification: syntax  # Enable syntax verification

  - id: deploy
    agent: deployer
    input: "Deploy {{step_outputs.implement}}"
    metadata:
      type: api_implementation
      verification: functional  # Enable functional testing
```

### Benefits
- ✅ Catches errors before they propagate
- ✅ Reduces manual testing burden
- ✅ Provides actionable suggestions for fixes
- ✅ Configurable verification levels per step
- ✅ Extensible: developers can add custom verifiers

## Priority 2: Interactive Debugging Mode

### Current State
- Limited visibility into workflow state
- No way to inspect step inputs/outputs after failure
- Can't manually re-execute failed steps

### Proposed: agenticom workflow debug Command

```bash
# Start interactive debugging session
agenticom workflow debug <run-id>

# Opens IPython-like shell with workflow context
```

**File:** `orchestration/debugging/inspector.py`

```python
import code
from typing import Optional
from ..workflows.models import WorkflowRun
from ..database import Database

class WorkflowInspector:
    """Interactive debugging for workflows"""

    def __init__(self, run_id: str):
        self.run = Database().get_run(run_id)
        self.context = {
            'run': self.run,
            'steps': self.run.steps,
            'outputs': self.get_step_outputs(),
            'errors': self.get_step_errors(),
        }

    def start(self):
        """Start interactive debugging session"""
        banner = f"""
╔══════════════════════════════════════════════════════╗
║  Agenticom Workflow Debugger                         ║
║  Run ID: {self.run.id[:8]}...                           ║
║  Status: {self.run.status}                               ║
╚══════════════════════════════════════════════════════╝

Available commands:
  run.steps              # List all steps
  show_step('plan')      # Show step details
  show_output('plan')    # Show step output
  show_error('plan')     # Show step error
  retry_step('plan')     # Re-execute step
  export_logs()          # Export full logs
  help()                 # Show this message

Starting interactive shell...
        """

        # Add helper functions to context
        self.context.update({
            'show_step': self.show_step,
            'show_output': self.show_output,
            'show_error': self.show_error,
            'retry_step': self.retry_step,
            'export_logs': self.export_logs,
            'help': lambda: print(banner),
        })

        # Start IPython or fall back to standard console
        try:
            from IPython import embed
            embed(user_ns=self.context, banner1=banner)
        except ImportError:
            code.interact(banner=banner, local=self.context)

    def show_step(self, step_id: str):
        """Show detailed information about a step"""
        step = next((s for s in self.run.steps if s.id == step_id), None)
        if not step:
            print(f"❌ Step '{step_id}' not found")
            return

        print(f"📋 Step: {step.id}")
        print(f"   Agent: {step.agent}")
        print(f"   Status: {step.status}")
        print(f"   Started: {step.started_at}")
        print(f"   Completed: {step.completed_at}")
        if step.error:
            print(f"   ❌ Error: {step.error}")
        print(f"\n📥 Input ({len(step.input)} chars):")
        print(f"   {step.input[:200]}...")
        print(f"\n📤 Output ({len(step.output)} chars):")
        print(f"   {step.output[:200]}...")

    def show_output(self, step_id: str):
        """Show full output of a step"""
        output = self.context['outputs'].get(step_id)
        if not output:
            print(f"❌ No output for step '{step_id}'")
            return
        print(output)

    def show_error(self, step_id: str):
        """Show error details for a step"""
        error = self.context['errors'].get(step_id)
        if not error:
            print(f"✅ No errors for step '{step_id}'")
            return
        print(f"❌ Error in step '{step_id}':")
        print(error)

    async def retry_step(self, step_id: str):
        """Re-execute a failed step"""
        print(f"🔄 Retrying step '{step_id}'...")
        # Re-execute step with same input
        # Show live output
        # Update run state
        pass

    def export_logs(self, filename: Optional[str] = None):
        """Export full workflow logs"""
        if not filename:
            filename = f"workflow_{self.run.id}_logs.txt"

        with open(filename, 'w') as f:
            f.write(f"Workflow Run: {self.run.id}\n")
            f.write(f"Status: {self.run.status}\n")
            f.write("=" * 80 + "\n\n")

            for step in self.run.steps:
                f.write(f"\n{'='*80}\n")
                f.write(f"STEP: {step.id}\n")
                f.write(f"{'='*80}\n")
                f.write(f"Status: {step.status}\n")
                if step.error:
                    f.write(f"Error: {step.error}\n")
                f.write(f"\nInput:\n{step.input}\n")
                f.write(f"\nOutput:\n{step.output}\n")

        print(f"✅ Logs exported to {filename}")
```

**CLI Integration:**

```python
# agenticom/cli.py

@click.command()
@click.argument("run_id")
def debug(run_id):
    """Start interactive debugging session for a workflow run"""
    from orchestration.debugging.inspector import WorkflowInspector

    inspector = WorkflowInspector(run_id)
    inspector.start()
```

### Benefits
- ✅ Inspect workflow state without writing code
- ✅ Manually retry failed steps
- ✅ Export logs for bug reports
- ✅ Faster debugging cycles

## Priority 3: Enhanced Error Reporting

### Current State
- Errors are simple strings
- No context about what went wrong
- No suggestions for fixes

### Proposed: Structured Error System

```python
# orchestration/errors.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class ErrorSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    QUALITY_GATE = "quality_gate"
    TIMEOUT = "timeout"
    RESOURCE = "resource"

@dataclass
class WorkflowError:
    """Structured error with context and suggestions"""

    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    step_id: Optional[str] = None
    details: Optional[Dict] = None
    suggestions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "step_id": self.step_id,
            "details": self.details,
            "suggestions": self.suggestions,
            "related_errors": self.related_errors,
            "timestamp": self.timestamp,
        }

    def to_user_message(self) -> str:
        """Format error for user display"""
        icon = "⚠️" if self.severity == ErrorSeverity.WARNING else "❌"

        msg = f"{icon} {self.message}\n"

        if self.step_id:
            msg += f"   Step: {self.step_id}\n"

        if self.details:
            msg += f"   Details: {self.details}\n"

        if self.suggestions:
            msg += f"\n💡 Suggestions:\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                msg += f"   {i}. {suggestion}\n"

        return msg

# Example usage in workflows.py
def _check_quality_gate(self, step_id: str, output: str) -> tuple[bool, Optional[WorkflowError]]:
    """Check quality gate with structured errors"""

    if not any(keyword in step_id.lower() for keyword in ['review', 'verify', 'validate']):
        return True, None

    found_negative = [ind for ind in negative_indicators if ind in output.lower()]

    if found_negative:
        error = WorkflowError(
            message="Quality gate failed: Review rejected the work",
            category=ErrorCategory.QUALITY_GATE,
            severity=ErrorSeverity.ERROR,
            step_id=step_id,
            details={
                "rejection_indicators": found_negative[:3],
                "review_excerpt": output[:200],
            },
            suggestions=[
                "Review the feedback from the previous step",
                "Address all identified issues before retrying",
                "Check if implementation meets acceptance criteria",
                f"This is attempt {loop_count} of {max_loops}",
            ],
            timestamp=datetime.now().isoformat(),
        )
        return False, error

    return True, None
```

### Benefits
- ✅ Clear error categorization
- ✅ Actionable suggestions for users
- ✅ Structured data for error analytics
- ✅ Better debugging experience

## Priority 4: Workflow Visualization

### Current State
- Text-based workflow status
- Hard to see overall progress
- No visual representation of dependencies

### Proposed: agenticom workflow visualize Command

```bash
agenticom workflow visualize feature-dev --output workflow.png
```

Generates a flowchart showing:
- All workflow steps
- Current execution status
- Dependencies between steps
- Loop-back paths
- Error locations

**Implementation:** Use Graphviz or Mermaid to generate diagrams from YAML

### Benefits
- ✅ Quickly understand workflow structure
- ✅ Identify bottlenecks
- ✅ Debug complex workflows visually

## Priority 5: Performance Profiling

### Current State
- No visibility into step execution time
- Can't identify slow steps
- No performance optimization guidance

### Proposed: Built-in Profiling

```python
# orchestration/profiling/profiler.py

from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class StepProfile:
    step_id: str
    duration_ms: float
    llm_tokens_in: int
    llm_tokens_out: int
    llm_cost_usd: float
    retries: int

class WorkflowProfiler:
    """Profile workflow execution for optimization"""

    def __init__(self):
        self.profiles: List[StepProfile] = []

    def profile_step(self, step_id: str, func):
        """Decorator to profile step execution"""
        start = time.time()
        result = func()
        duration = (time.time() - start) * 1000

        # Track metrics
        profile = StepProfile(
            step_id=step_id,
            duration_ms=duration,
            llm_tokens_in=result.get('tokens_in', 0),
            llm_tokens_out=result.get('tokens_out', 0),
            llm_cost_usd=result.get('cost', 0.0),
            retries=result.get('retries', 0),
        )
        self.profiles.append(profile)

        return result

    def report(self) -> Dict:
        """Generate performance report"""
        total_duration = sum(p.duration_ms for p in self.profiles)
        total_cost = sum(p.llm_cost_usd for p in self.profiles)

        return {
            "total_duration_ms": total_duration,
            "total_cost_usd": total_cost,
            "steps": [
                {
                    "step": p.step_id,
                    "duration_ms": p.duration_ms,
                    "duration_pct": (p.duration_ms / total_duration) * 100,
                    "cost_usd": p.llm_cost_usd,
                    "tokens": p.llm_tokens_in + p.llm_tokens_out,
                    "retries": p.retries,
                }
                for p in self.profiles
            ],
            "slowest_steps": sorted(
                self.profiles,
                key=lambda p: p.duration_ms,
                reverse=True
            )[:5],
        }
```

### Benefits
- ✅ Identify performance bottlenecks
- ✅ Optimize workflow execution
- ✅ Track LLM costs per step

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [x] Quality gate validation (DONE)
- [ ] Structured error system
- [ ] Basic verification testing

### Phase 2: Developer Experience (Week 3-4)
- [ ] Interactive debugging mode
- [ ] Enhanced error reporting with suggestions
- [ ] Workflow visualization

### Phase 3: Optimization (Week 5-6)
- [ ] Performance profiling
- [ ] Cost tracking and optimization
- [ ] Advanced verification testing

### Phase 4: Production Readiness (Week 7-8)
- [ ] Comprehensive test coverage
- [ ] Documentation and tutorials
- [ ] Performance benchmarks

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Bug fix iterations | 5-8 | 1-2 | Track iterations per bug report |
| Time to resolution | 2 days | 2 hours | Average time from bug report to fix |
| False "Fixed!" claims | 80% | <10% | Track verification test pass rate |
| Developer satisfaction | N/A | 8/10 | User surveys |
| Workflow success rate | 60% | 90% | Completed vs failed workflows |

## Conclusion

These improvements will transform Agenticom from a workflow orchestration tool into a self-verifying, self-healing system that dramatically reduces debugging cycles and improves developer experience.

The key insight: **Automate verification, not just execution.**

By building verification testing, interactive debugging, and enhanced error reporting into the framework, we enable AI-human collaboration patterns that leverage the strengths of both: AI's speed and consistency in testing, human's judgment and strategic thinking.
