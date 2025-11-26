"""
Script to verify topic ingestion data locally without requiring Firestore.
"""

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING

from src.content.models import TopicCandidate
from src.content.processing.clustering import TopicClusterer
from src.content.processing.entity_extraction import EntityExtractor
from src.content.sources.base import RawTopicData
from src.content.sources.hackernews import HackerNewsIngestionSource
from src.content.sources.reddit import RedditIngestionSource
from src.content.sources.rss import RSSIngestionSource
from src.core import get_logger

if TYPE_CHECKING:
    from src.infra import FirestoreService

logger = get_logger(__name__)


def format_topic(topic) -> str:
    """Format a topic for display."""
    lines = []
    lines.append(f"  ID: {topic.id}")
    lines.append(f"  Title: {topic.title}")
    lines.append(f"  Source: {topic.source_platform}")
    lines.append(f"  URL: {topic.source_url or 'N/A'}")
    lines.append(f"  Status: {topic.status}")
    lines.append(f"  Cluster: {topic.topic_cluster}")
    lines.append(f"  Created: {topic.created_at}")
    
    if topic.entities:
        lines.append(f"  Entities: {', '.join(topic.entities[:5])}")
    
    if topic.raw_payload:
        payload_str = json.dumps(topic.raw_payload, indent=2)[:200]
        lines.append(f"  Raw Payload: {payload_str}...")
    
    return "\n".join(lines)


def simple_deduplicate(raw_topics: list[RawTopicData]) -> list[RawTopicData]:
    """Simple in-memory deduplication by URL and title."""
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    for topic in raw_topics:
        url_key = topic.source_url.lower().strip() if topic.source_url else None
        title_key = topic.title.lower().strip() if topic.title else None
        
        if url_key and url_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        
        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)
        
        unique.append(topic)
    
    return unique


async def verify_data_local() -> None:
    """Run ingestion and verify data without saving to Firestore."""
    logger.info("=" * 70)
    logger.info("Local Topic Ingestion Verification (No Firestore Required)")
    logger.info("=" * 70)

    # Initialize sources
    reddit = RedditIngestionSource()
    hackernews = HackerNewsIngestionSource()
    rss = RSSIngestionSource()
    
    entity_extractor = EntityExtractor()
    clusterer = TopicClusterer()

    # Fetch from all sources
    logger.info("\n📥 Fetching topics from all sources...")
    all_raw_topics: list[RawTopicData] = []
    
    sources = [
        ("reddit", reddit),
        ("hackernews", hackernews),
        ("rss", rss),
    ]
    
    for source_name, source in sources:
        try:
            topics = await source.fetch_topics(limit=10)
            all_raw_topics.extend(topics)
            logger.info(f"✓ Fetched {len(topics)} topics from {source_name}")
        except Exception as e:
            logger.error(f"✗ Failed to fetch from {source_name}: {e}")
            continue

    if not all_raw_topics:
        logger.warning("No topics were fetched from any source.")
        return

    logger.info(f"\n📊 Total fetched: {len(all_raw_topics)} topics")

    # Simple deduplication (in-memory, no Firestore)
    logger.info("\n🔄 Deduplicating topics...")
    unique_topics = simple_deduplicate(all_raw_topics)
    logger.info(f"✓ After deduplication: {len(unique_topics)} unique topics")

    # Process and convert to TopicCandidate
    logger.info("\n⚙️  Processing topics (entity extraction, clustering)...")
    topics: list[TopicCandidate] = []
    
    for raw_topic in unique_topics:
        try:
            # Extract entities
            entities = entity_extractor.extract_entities(raw_topic.title)
            
            # Determine cluster
            cluster = clusterer.cluster_topic(raw_topic.title, entities)
            
            # Generate ID (simple hash-based)
            import hashlib
            id_str = f"{raw_topic.source_platform}:{raw_topic.title}"
            topic_id = hashlib.md5(id_str.encode()).hexdigest()[:16]
            
            # Create TopicCandidate
            from typing import Literal
            platform: Literal[
                "youtube", "tiktok", "x", "news", "manual", "reddit", "hackernews", "rss"
            ] = raw_topic.source_platform  # type: ignore[assignment]
            
            candidate = TopicCandidate(
                id=topic_id,
                source_platform=platform,
                source_url=raw_topic.source_url,
                title=raw_topic.title,
                raw_payload=raw_topic.raw_payload,
                entities=entities,
                topic_cluster=cluster,
                detected_language=None,
                status="pending",
                created_at=raw_topic.published_at,
            )
            topics.append(candidate)
        except Exception as e:
            logger.error(f"Failed to process topic '{raw_topic.title}': {e}")
            continue

    logger.info(f"✓ Processed {len(topics)} topic candidates\n")

    if not topics:
        logger.warning("No topics were ingested. Check source configurations.")
        return

    # Display topics
    logger.info("=" * 70)
    logger.info("INGESTED TOPICS")
    logger.info("=" * 70)

    for i, topic in enumerate(topics, 1):
        logger.info(f"\n{'─' * 70}")
        logger.info(f"Topic #{i}")
        logger.info(f"{'─' * 70}")
        logger.info(format_topic(topic))

    # Summary statistics
    logger.info(f"\n{'=' * 70}")
    logger.info("SUMMARY STATISTICS")
    logger.info(f"{'=' * 70}")

    sources = {}
    clusters = {}
    statuses = {}
    entities_count = {}
    has_urls = 0

    for topic in topics:
        # By source
        source = topic.source_platform
        sources[source] = sources.get(source, 0) + 1

        # By cluster
        cluster = topic.topic_cluster
        clusters[cluster] = clusters.get(cluster, 0) + 1

        # By status
        status = topic.status
        statuses[status] = statuses.get(status, 0) + 1

        # Entity statistics
        if topic.entities:
            for entity in topic.entities:
                entities_count[entity] = entities_count.get(entity, 0) + 1

        # URLs
        if topic.source_url:
            has_urls += 1

    logger.info(f"\n📊 By Source Platform:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        logger.info(f"  {source:20s}: {count:3d} topics")

    logger.info(f"\n📊 By Topic Cluster:")
    for cluster, count in sorted(clusters.items(), key=lambda x: -x[1]):
        logger.info(f"  {cluster:30s}: {count:3d} topics")

    logger.info(f"\n📊 By Status:")
    for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
        logger.info(f"  {status:20s}: {count:3d} topics")

    logger.info(f"\n📊 Data Quality:")
    logger.info(f"  Topics with URLs: {has_urls}/{len(topics)} ({100*has_urls/len(topics):.1f}%)")
    logger.info(f"  Topics with entities: {sum(1 for t in topics if t.entities)}/{len(topics)}")
    logger.info(f"  Total unique entities: {len(entities_count)}")

    if entities_count:
        logger.info(f"\n📊 Top 10 Entities:")
        top_entities = sorted(entities_count.items(), key=lambda x: -x[1])[:10]
        for entity, count in top_entities:
            logger.info(f"  {entity:30s}: {count:3d} occurrences")

    # Sample topic data structure
    logger.info(f"\n{'=' * 70}")
    logger.info("SAMPLE TOPIC DATA STRUCTURE")
    logger.info(f"{'=' * 70}")
    if topics:
        sample = topics[0]
        logger.info("\nSample topic (first one):")
        logger.info(format_topic(sample))

        # Show Firestore-ready dict structure
        logger.info(f"\n{'─' * 70}")
        logger.info("Firestore-ready dictionary (what would be saved):")
        logger.info(f"{'─' * 70}")
        firestore_dict = sample.to_firestore_dict()
        logger.info(json.dumps(firestore_dict, indent=2, default=str))

    # Validation checks
    logger.info(f"\n{'=' * 70}")
    logger.info("DATA VALIDATION")
    logger.info(f"{'=' * 70}")

    issues = []
    for i, topic in enumerate(topics, 1):
        if not topic.title or len(topic.title.strip()) == 0:
            issues.append(f"Topic #{i}: Missing title")
        if not topic.id:
            issues.append(f"Topic #{i}: Missing ID")
        if not topic.source_platform:
            issues.append(f"Topic #{i}: Missing source_platform")
        if not topic.topic_cluster:
            issues.append(f"Topic #{i}: Missing topic_cluster")
        if not topic.status:
            issues.append(f"Topic #{i}: Missing status")

    if issues:
        logger.warning(f"\n⚠ Found {len(issues)} validation issues:")
        for issue in issues[:10]:  # Show first 10
            logger.warning(f"  - {issue}")
        if len(issues) > 10:
            logger.warning(f"  ... and {len(issues) - 10} more")
    else:
        logger.info("\n✓ All topics passed validation checks")

    logger.info(f"\n{'=' * 70}")
    logger.info("✓ Verification complete!")
    logger.info(f"{'=' * 70}\n")


async def main() -> None:
    """Main entry point."""
    try:
        await verify_data_local()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

