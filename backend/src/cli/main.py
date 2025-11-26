"""
CLI entry point for Content Engine backend.
"""

import asyncio

import typer

from ..content.ingestion_service import TopicIngestionService
from ..content.models import TopicCandidate
from ..content.sources.manual import create_manual_topic
from ..core import get_logger
from ..infra import FirestoreService, GCSService
from ..jobs.topic_ingestion_job import run_topic_ingestion

app = typer.Typer()
logger = get_logger(__name__)


@app.command()
def check_infra() -> None:
    """Check infrastructure connectivity (Firestore, GCS)."""
    logger.info("Checking infrastructure...")

    async def _check() -> None:
        try:
            # Check Firestore
            try:
                firestore_svc = FirestoreService()
                if firestore_svc._client:
                    logger.info("✓ Firestore service initialized")
                else:
                    logger.warning("⚠ Firestore client not initialized (missing config)")
            except Exception as e:
                logger.warning(f"⚠ Firestore check skipped: {e}")

            # Check GCS
            try:
                _gcs = GCSService()
                logger.info("✓ GCS service initialized")
            except Exception as e:
                logger.warning(f"⚠ GCS check skipped: {e}")

            logger.info("Infrastructure check complete")
        except Exception as e:
            logger.error(f"Infrastructure check failed: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_check())


@app.command()
def ingest_topics() -> None:
    """Run topic ingestion locally."""
    logger.info("Running topic ingestion...")
    asyncio.run(run_topic_ingestion())


@app.command()
def add_topic(
    title: str = typer.Argument(..., help="Topic title"),
    cluster: str = typer.Option(..., "--cluster", "-c", help="Topic cluster"),
    url: str | None = typer.Option(None, "--url", "-u", help="Source URL"),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notes"),
) -> None:
    """Add a manual topic."""

    async def _add() -> None:
        try:
            raw_topic = create_manual_topic(title, cluster, url, notes)
            service = TopicIngestionService()

            # Process manually created topic
            entities = service.entity_extractor.extract_entities(raw_topic.title)
            cluster_result = service.clusterer.cluster_topic(raw_topic.title, entities)

            topic_id = service._generate_topic_id(raw_topic)
            candidate = TopicCandidate(
                id=topic_id,
                source_platform="manual",
                source_url=url,
                title=title,
                raw_payload={"notes": notes} if notes else {},
                entities=entities,
                topic_cluster=cluster_result,
                detected_language=None,
                status="pending",
                created_at=raw_topic.published_at,
            )

            saved = await service.save_topics([candidate])
            if saved > 0:
                logger.info(f"✓ Saved manual topic: {topic_id}")
            else:
                logger.warning(f"Topic {topic_id} already exists or failed to save")
        except Exception as e:
            logger.error(f"Failed to add manual topic: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_add())


if __name__ == "__main__":
    app()
