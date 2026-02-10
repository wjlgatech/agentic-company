"""
Celery task definitions for distributed workflow execution.

Provides async task processing with retries, rate limiting, and monitoring.
"""

import os
from datetime import datetime
from typing import Any, Optional

from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, task_failure

from orchestration.config import get_config
from orchestration.observability import get_observability

# Initialize Celery
config = get_config()
app = Celery(
    'agentic',
    broker=os.getenv('CELERY_BROKER_URL', config.celery.broker_url),
    backend=os.getenv('CELERY_RESULT_BACKEND', config.celery.result_backend),
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=config.celery.task_timeout,
    task_soft_time_limit=config.celery.task_timeout - 30,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
)

obs = get_observability()


class ObservedTask(Task):
    """Base task class with observability."""

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        obs.metrics.increment('celery_task_success', labels={'task': self.name})

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        obs.metrics.increment('celery_task_failure', labels={'task': self.name})
        obs.logger.error(
            'Task failed',
            task=self.name,
            task_id=task_id,
            error=str(exc),
        )

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        obs.metrics.increment('celery_task_retry', labels={'task': self.name})


# Signal handlers for metrics
@task_prerun.connect
def task_prerun_handler(task_id: str, task: Task, **kwargs: Any) -> None:
    """Record task start."""
    obs.metrics.increment('celery_task_started', labels={'task': task.name})


@task_postrun.connect
def task_postrun_handler(task_id: str, task: Task, retval: Any, state: str, **kwargs: Any) -> None:
    """Record task completion."""
    obs.metrics.increment('celery_task_completed', labels={'task': task.name, 'state': state})


# ============== Workflow Tasks ==============

@app.task(bind=True, base=ObservedTask, max_retries=3, default_retry_delay=60)
def run_workflow(
    self,
    workflow_name: str,
    input_data: str,
    config: Optional[dict] = None,
) -> dict[str, Any]:
    """Execute a workflow asynchronously."""
    from orchestration.pipeline import Pipeline, PipelineConfig, FunctionStep
    from orchestration.guardrails import create_default_pipeline

    try:
        with obs.observe('celery_workflow', {'workflow': workflow_name}):
            # Create simple pipeline
            pipeline = Pipeline(
                config=PipelineConfig(name=workflow_name),
                guardrails=create_default_pipeline(),
            )

            # Add processing step
            def process(data: str, ctx: dict) -> str:
                return f"Processed: {data}"

            pipeline.add_step(FunctionStep('process', process))

            # Run synchronously within task
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result, steps = loop.run_until_complete(pipeline.run(input_data))
            finally:
                loop.close()

            return {
                'workflow': workflow_name,
                'status': 'completed',
                'result': result,
                'steps': [s.to_dict() for s in steps],
                'completed_at': datetime.now().isoformat(),
            }

    except Exception as exc:
        obs.logger.error('Workflow task failed', workflow=workflow_name, error=str(exc))
        raise self.retry(exc=exc)


@app.task(bind=True, base=ObservedTask)
def evaluate_content(
    self,
    content: str,
    criteria: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Evaluate content asynchronously."""
    from orchestration.evaluator import RuleBasedEvaluator

    try:
        with obs.observe('celery_evaluate'):
            evaluator = RuleBasedEvaluator(
                min_length=50,
                required_elements=criteria or [],
            )
            result = evaluator.evaluate(content)

            return {
                'passed': result.passed,
                'score': result.score,
                'feedback': result.feedback,
                'suggestions': result.suggestions,
            }

    except Exception as exc:
        obs.logger.error('Evaluation task failed', error=str(exc))
        raise


@app.task(bind=True, base=ObservedTask)
def store_memory(
    self,
    content: str,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> dict[str, str]:
    """Store memory asynchronously."""
    from orchestration.memory import LocalMemoryStore

    try:
        with obs.observe('celery_memory_store'):
            memory = LocalMemoryStore()
            entry_id = memory.remember(content, metadata=metadata, tags=tags)

            return {
                'id': entry_id,
                'status': 'stored',
            }

    except Exception as exc:
        obs.logger.error('Memory store task failed', error=str(exc))
        raise


@app.task(bind=True, base=ObservedTask)
def search_memory(
    self,
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Search memory asynchronously."""
    from orchestration.memory import LocalMemoryStore

    try:
        with obs.observe('celery_memory_search'):
            memory = LocalMemoryStore()
            results = memory.search(query, limit=limit)

            return {
                'query': query,
                'results': [
                    {
                        'id': entry.id,
                        'content': entry.content,
                        'tags': entry.tags,
                    }
                    for entry in results
                ],
                'count': len(results),
            }

    except Exception as exc:
        obs.logger.error('Memory search task failed', error=str(exc))
        raise


# ============== Batch Tasks ==============

@app.task(bind=True, base=ObservedTask)
def batch_process(
    self,
    items: list[str],
    workflow_name: str = 'batch',
) -> dict[str, Any]:
    """Process multiple items in batch."""
    results = []
    errors = []

    for i, item in enumerate(items):
        try:
            # Process each item
            result = run_workflow.apply(
                args=[workflow_name, item],
            ).get(timeout=60)
            results.append({'index': i, 'result': result})
        except Exception as e:
            errors.append({'index': i, 'error': str(e)})

    return {
        'total': len(items),
        'successful': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors,
    }


# ============== Scheduled Tasks ==============

@app.task(bind=True, base=ObservedTask)
def cleanup_expired_memory(self) -> dict[str, int]:
    """Clean up expired memory entries."""
    # Placeholder - would implement actual cleanup
    return {'cleaned': 0}


@app.task(bind=True, base=ObservedTask)
def aggregate_metrics(self) -> dict[str, Any]:
    """Aggregate metrics for reporting."""
    metrics = obs.metrics.get_all_metrics()
    return {
        'timestamp': datetime.now().isoformat(),
        'counters': len(metrics.get('counters', {})),
        'gauges': len(metrics.get('gauges', {})),
        'histograms': len(metrics.get('histograms', {})),
    }


# Celery Beat schedule
app.conf.beat_schedule = {
    'cleanup-memory-hourly': {
        'task': 'orchestration.tasks.cleanup_expired_memory',
        'schedule': 3600.0,  # Every hour
    },
    'aggregate-metrics-minutely': {
        'task': 'orchestration.tasks.aggregate_metrics',
        'schedule': 60.0,  # Every minute
    },
}
