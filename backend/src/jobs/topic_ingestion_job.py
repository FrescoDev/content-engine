"""Topic ingestion job entrypoint."""

from ..content.ingestion_service import TopicIngestionService
from ..core import get_logger
from .job_tracker import track_job_run

logger = get_logger(__name__)


async def run_topic_ingestion(limit_per_source: int = 25) -> None:
    """Run topic ingestion job."""
    async with track_job_run("topic_ingestion", {"limit_per_source": limit_per_source}) as job_run:
        service = TopicIngestionService()

        # Ingest from all sources
        topics = await service.ingest_from_all_sources(limit_per_source=limit_per_source)
        logger.info(f"Ingested {len(topics)} topics from all sources")

        # Save to Firestore
        saved_count = await service.save_topics(topics)
        logger.info(f"Saved {saved_count} topics to Firestore")
        
        # Update job run metrics
        job_run.metrics = {
            "topics_ingested": len(topics),
            "topics_saved": saved_count,
        }

        logger.info(
            f"Topic ingestion job completed (run_id: {job_run.id}, saved: {saved_count})"
        )
