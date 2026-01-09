"""
CLI entry point for Content Engine backend.
"""

import asyncio

import typer

from ..content.ingestion_service import TopicIngestionService
from ..content.models import (
    STYLE_PROFILES_COLLECTION,
    STYLISTIC_CONTENT_COLLECTION,
    StylisticContent,
    TopicCandidate,
)
from ..content.sources.manual import create_manual_topic
from ..content.style_curation_service import StyleCurationService
from ..content.style_extraction_service import StyleExtractionService
from ..core import get_logger
from ..infra import FirestoreService, GCSService
from ..jobs.topic_ingestion_job import run_topic_ingestion
from ..jobs.topic_scoring_job import run_topic_scoring
from .review import review_app

app = typer.Typer()
logger = get_logger(__name__)

# Add review subcommands
app.add_typer(review_app, name="review")


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


@app.command()
def test_scoring() -> None:
    """Test scoring system with fixtures (no external dependencies)."""
    # Note: test_scoring.py script not yet implemented
    # Use pytest instead: poetry run pytest tests/ -v
    logger.error("test_scoring command not yet implemented")
    logger.info("Use: poetry run pytest tests/ -v")
    raise typer.Exit(1)


@app.command()
def score_topics(
    limit: int = typer.Option(100, help="Maximum topics to score"),
    min_age_hours: int = typer.Option(0, help="Minimum age in hours before scoring"),
    status: str = typer.Option("pending", help="Topic status filter"),
) -> None:
    """Run topic scoring job."""
    logger.info(
        f"Running topic scoring (limit: {limit}, min_age: {min_age_hours}h, status: {status})..."
    )
    asyncio.run(run_topic_scoring(limit=limit, min_age_hours=min_age_hours, status=status))


# Style management commands
@app.command()
def add_style_source(
    source_url: str = typer.Option(..., "--url", "-u", help="Source URL (auto-detects type)"),
    source_name: str | None = typer.Option(None, "--name", "-n", help="Optional custom name"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Optional description"
    ),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags"),
    auto: bool = typer.Option(
        True, "--auto/--no-auto", help="Automatically fetch content and extract styles"
    ),
) -> None:
    """
    Add a stylistic source from URL - fully automated.

    Examples:
        # Reddit subreddit
        add-style-source --url "https://www.reddit.com/r/hiphopheads/"

        # Podcast episode
        add-style-source --url "https://podscripts.co/podcasts/the-joe-budden-podcast/episode-872-purple-eye"

        # With custom name and tags
        add-style-source --url "https://www.reddit.com/r/hiphopheads/" --name "Hip-Hop Heads" --tags "hip-hop,culture"
    """
    from ..content.stylistic_source_ingestion_service import StylisticSourceIngestionService

    async def _add() -> None:
        try:
            async with StylisticSourceIngestionService() as service:
                tags_list = tags.split(",") if tags else None

                logger.info(f"Ingesting source from URL: {source_url}")
                result = await service.ingest_from_url(
                    url=source_url,
                    source_name=source_name,
                    description=description,
                    tags=tags_list,
                    auto_extract=auto,
                )

                if result["status"] == "success":
                    logger.info(f"✓ Successfully ingested source: {result['source_id']}")
                    logger.info(f"  Content items: {result['content_count']}")
                    logger.info(f"  Style profiles: {result['profiles_created']}")
                elif result["status"] == "partial":
                    logger.warning(f"⚠ Partially ingested source: {result['source_id']}")
                    logger.warning(f"  Content items: {result['content_count']}")
                    logger.warning(f"  Style profiles: {result['profiles_created']}")
                    if result["errors"]:
                        logger.warning(f"  Errors: {', '.join(result['errors'])}")
                else:
                    logger.error("✗ Failed to ingest source")
                    if result["errors"]:
                        logger.error(f"  Errors: {', '.join(result['errors'])}")
                    raise typer.Exit(1)

        except Exception as e:
            logger.error(f"Failed to ingest source: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_add())


@app.command()
def list_style_profiles(
    status: str = typer.Option(
        "pending", "--status", "-s", help="Filter by status: pending, approved, rejected, all"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum profiles to show"),
) -> None:
    """List style profiles."""

    async def _list() -> None:
        try:
            firestore = FirestoreService()

            filters = []
            if status != "all":
                filters.append(("status", "==", status))

            profiles_data = await firestore.query_collection(
                STYLE_PROFILES_COLLECTION,
                filters=filters,
                limit=limit,
                order_by="created_at",
                order_direction="DESCENDING",
            )

            if not profiles_data:
                logger.info("No profiles found")
                return

            logger.info(f"\nFound {len(profiles_data)} profiles:\n")
            for data in profiles_data:
                profile_id = data.get("id", "unknown")
                source_name = data.get("source_name", "unknown")
                tone = data.get("tone", "unknown")
                profile_status = data.get("status", "unknown")
                logger.info(f"  {profile_id[:20]}... | {source_name} | {tone} | {profile_status}")

        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_list())


@app.command()
def approve_style_profile(
    profile_id: str = typer.Argument(..., help="Profile ID to approve"),
    curator_id: str = typer.Option("cli-user", "--curator", "-c", help="Curator user ID"),
    notes: str | None = typer.Option(None, "--notes", "-n", help="Optional notes"),
) -> None:
    """Approve a style profile."""

    async def _approve() -> None:
        try:
            curation_service = StyleCurationService()
            await curation_service.approve_profile(profile_id, curator_id, notes)
            logger.info(f"✓ Approved profile: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to approve profile: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_approve())


@app.command()
def reject_style_profile(
    profile_id: str = typer.Argument(..., help="Profile ID to reject"),
    curator_id: str = typer.Option("cli-user", "--curator", "-c", help="Curator user ID"),
    reason: str = typer.Option(..., "--reason", "-r", help="Rejection reason"),
) -> None:
    """Reject a style profile."""

    async def _reject() -> None:
        try:
            curation_service = StyleCurationService()
            await curation_service.reject_profile(profile_id, curator_id, reason)
            logger.info(f"✓ Rejected profile: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to reject profile: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_reject())


@app.command()
def extract_styles(
    content_id: str | None = typer.Option(
        None, "--content-id", "-c", help="Extract from specific content ID"
    ),
    source_id: str | None = typer.Option(
        None, "--source-id", "-s", help="Extract from all pending content in source"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum items to process"),
) -> None:
    """Extract styles from content."""

    async def _extract() -> None:
        try:
            firestore = FirestoreService()
            extraction_service = StyleExtractionService()

            if content_id:
                # Extract from specific content
                content_data = await firestore.get_document(
                    STYLISTIC_CONTENT_COLLECTION, content_id
                )
                if not content_data:
                    logger.error(f"Content {content_id} not found")
                    raise typer.Exit(1)

                content = StylisticContent.from_firestore_dict(content_data, content_id)
                profile = await extraction_service.extract_style_profile(content)
                if profile:
                    logger.info(f"✓ Extracted profile: {profile.id}")
                else:
                    logger.warning(f"Failed to extract profile from {content_id}")

            elif source_id:
                # Extract from all pending content in source
                contents_data = await firestore.query_collection(
                    STYLISTIC_CONTENT_COLLECTION,
                    filters=[
                        ("source_id", "==", source_id),
                        ("status", "==", "pending"),
                    ],
                    limit=limit,
                )

                if not contents_data:
                    logger.info("No pending content found")
                    return

                logger.info(f"Processing {len(contents_data)} content items...")
                extracted = 0
                for data in contents_data:
                    content_id_item = data.get("id")
                    if content_id_item:
                        content = StylisticContent.from_firestore_dict(data, content_id_item)
                        profile = await extraction_service.extract_style_profile(content)
                        if profile:
                            extracted += 1

                logger.info(f"✓ Extracted {extracted}/{len(contents_data)} profiles")
            else:
                logger.error("Must provide either --content-id or --source-id")
                raise typer.Exit(1)

        except Exception as e:
            logger.error(f"Failed to extract styles: {e}")
            raise typer.Exit(1) from e

    asyncio.run(_extract())


if __name__ == "__main__":
    app()
