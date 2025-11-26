"""
Script to run topic ingestion locally and verify the data.
"""

import asyncio
import json
from datetime import datetime

from src.content.ingestion_service import TopicIngestionService
from src.content.models import TOPIC_CANDIDATES_COLLECTION
from src.core import get_logger
from src.infra import FirestoreService

logger = get_logger(__name__)


async def run_ingestion() -> int:
    """Run topic ingestion and return count of saved topics."""
    logger.info("=" * 60)
    logger.info("Starting topic ingestion...")
    logger.info("=" * 60)

    service = TopicIngestionService()

    # Ingest from all sources
    topics = await service.ingest_from_all_sources(limit_per_source=10)
    logger.info(f"\n✓ Ingested {len(topics)} topics from all sources")

    # Save to Firestore
    saved_count = await service.save_topics(topics)
    logger.info(f"✓ Saved {saved_count} topics to Firestore\n")

    return saved_count


async def verify_data() -> None:
    """Query and display saved topics."""
    logger.info("=" * 60)
    logger.info("Verifying saved data...")
    logger.info("=" * 60)

    firestore = FirestoreService()

    # Query all topics
    topics = await firestore.query_collection(
        TOPIC_CANDIDATES_COLLECTION,
        limit=20,
        order_by="created_at",
        order_direction="DESCENDING",
    )

    logger.info(f"\nFound {len(topics)} topics in Firestore\n")

    if not topics:
        logger.warning("No topics found in Firestore")
        return

    # Display topics
    for i, topic in enumerate(topics, 1):
        logger.info(f"\n{'─' * 60}")
        logger.info(f"Topic #{i}")
        logger.info(f"{'─' * 60}")
        logger.info(f"ID: {topic.get('id', 'N/A')}")
        logger.info(f"Title: {topic.get('title', 'N/A')}")
        logger.info(f"Source: {topic.get('source_platform', 'N/A')}")
        logger.info(f"URL: {topic.get('source_url', 'N/A')}")
        logger.info(f"Status: {topic.get('status', 'N/A')}")
        logger.info(f"Cluster: {topic.get('topic_cluster', 'N/A')}")
        logger.info(f"Created: {topic.get('created_at', 'N/A')}")

        # Entities
        entities = topic.get("entities", [])
        if entities:
            logger.info(f"Entities: {', '.join(entities[:5])}")

        # Raw payload snippet
        raw_payload = topic.get("raw_payload", {})
        if raw_payload:
            payload_str = json.dumps(raw_payload, indent=2)[:200]
            logger.info(f"Raw Payload: {payload_str}...")

    # Summary statistics
    logger.info(f"\n{'=' * 60}")
    logger.info("Summary Statistics")
    logger.info(f"{'=' * 60}")

    sources = {}
    clusters = {}
    statuses = {}

    for topic in topics:
        source = topic.get("source_platform", "unknown")
        sources[source] = sources.get(source, 0) + 1

        cluster = topic.get("topic_cluster", "unknown")
        clusters[cluster] = clusters.get(cluster, 0) + 1

        status = topic.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1

    logger.info(f"\nBy Source Platform:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        logger.info(f"  {source}: {count}")

    logger.info(f"\nBy Topic Cluster:")
    for cluster, count in sorted(clusters.items(), key=lambda x: -x[1]):
        logger.info(f"  {cluster}: {count}")

    logger.info(f"\nBy Status:")
    for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
        logger.info(f"  {status}: {count}")


async def main() -> None:
    """Main entry point."""
    try:
        # Run ingestion
        saved_count = await run_ingestion()

        if saved_count == 0:
            logger.warning("No topics were saved. Check logs for errors.")
            return

        # Wait a moment for Firestore to be consistent
        await asyncio.sleep(1)

        # Verify data
        await verify_data()

        logger.info(f"\n{'=' * 60}")
        logger.info("✓ Verification complete!")
        logger.info(f"{'=' * 60}\n")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
