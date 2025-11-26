"""
Job execution tracker for auditing and monitoring.
"""

import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from ..content.models import JOB_RUNS_COLLECTION, JobRun
from ..core import get_logger
from ..infra import FirestoreService

logger = get_logger(__name__)


@asynccontextmanager
async def track_job_run(
    job_type: str,
    metadata: dict[str, Any] | None = None,
):
    """
    Context manager to track job execution.

    Usage:
        async with track_job_run("topic_ingestion", {"limit_per_source": 25}) as job_run:
            # Job execution code
            job_run.topics_ingested = 75
            job_run.topics_saved = 75
    """
    import uuid

    run_id = str(uuid.uuid4())
    firestore = FirestoreService()
    started_at = datetime.now(timezone.utc)

    job_run = JobRun(
        id=run_id,
        job_type=job_type,
        status="running",
        started_at=started_at,
        metadata=metadata or {},
    )

    # Save initial job run record
    try:
        await firestore.set_document(JOB_RUNS_COLLECTION, run_id, job_run.to_firestore_dict())
        logger.info(f"Job run started: {run_id} ({job_type})")
    except Exception as e:
        logger.error(f"Failed to save initial job run record: {e}")

    try:
        yield job_run
        # Job completed successfully
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        job_run.status = "completed"
        job_run.completed_at = completed_at
        job_run.duration_seconds = duration

        await firestore.set_document(JOB_RUNS_COLLECTION, run_id, job_run.to_firestore_dict())
        logger.info(f"Job run completed: {run_id} (duration: {duration:.2f}s)")

    except Exception as e:
        # Job failed
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()
        error_tb = traceback.format_exc()

        job_run.status = "failed"
        job_run.completed_at = completed_at
        job_run.duration_seconds = duration
        job_run.error_message = str(e)
        job_run.error_traceback = error_tb

        try:
            await firestore.set_document(JOB_RUNS_COLLECTION, run_id, job_run.to_firestore_dict())
            logger.error(f"Job run failed: {run_id} (duration: {duration:.2f}s)")
        except Exception as save_error:
            logger.error(f"Failed to save failed job run record: {save_error}")

        raise
