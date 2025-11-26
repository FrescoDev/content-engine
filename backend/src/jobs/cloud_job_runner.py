"""
Cloud Run Job runner entry point.
"""

import asyncio
import os

from ..core import get_logger
from .topic_ingestion_job import run_topic_ingestion

logger = get_logger(__name__)


async def run_from_env() -> None:
    """Run job based on JOB_TYPE environment variable."""
    job_type = os.getenv("JOB_TYPE", "unknown")
    logger.info(f"Starting job: {job_type}")

    if job_type == "topic_ingestion":
        await run_topic_ingestion()
    elif job_type == "topic_scoring":
        logger.info("JOB_TYPE=topic_scoring not implemented yet")
    elif job_type == "option_generation":
        logger.info("JOB_TYPE=option_generation not implemented yet")
    elif job_type == "weekly_learning":
        logger.info("JOB_TYPE=weekly_learning not implemented yet")
    else:
        logger.warning(f"JOB_TYPE={job_type} not implemented yet")

    logger.info(f"Job {job_type} completed")


if __name__ == "__main__":
    asyncio.run(run_from_env())
