"""Topic ingestion service orchestrator."""

import hashlib
from typing import Literal

from ..core import get_logger
from ..infra import FirestoreService
from .models import TOPIC_CANDIDATES_COLLECTION, TopicCandidate
from .processing.clustering import TopicClusterer
from .processing.deduplication import TopicDeduplicator
from .processing.entity_extraction import EntityExtractor
from .sources.base import RawTopicData
from .sources.hackernews import HackerNewsIngestionSource
from .sources.reddit import RedditIngestionSource
from .sources.rss import RSSIngestionSource

logger = get_logger(__name__)


class TopicIngestionService:
    """Orchestrates topic ingestion from all sources."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        reddit_source: RedditIngestionSource | None = None,
        hn_source: HackerNewsIngestionSource | None = None,
        rss_source: RSSIngestionSource | None = None,
    ):
        """Initialize ingestion service."""
        self.firestore = firestore or FirestoreService()
        self.reddit = reddit_source or RedditIngestionSource()
        self.hackernews = hn_source or HackerNewsIngestionSource()
        self.rss = rss_source or RSSIngestionSource()
        self.deduplicator = TopicDeduplicator(self.firestore)
        self.entity_extractor = EntityExtractor()
        self.clusterer = TopicClusterer()

    async def ingest_from_all_sources(self, limit_per_source: int = 25) -> list[TopicCandidate]:
        """
        Ingest topics from all sources.

        Args:
            limit_per_source: Maximum topics to fetch per source

        Returns:
            List of TopicCandidate objects
        """
        all_raw_topics: list[RawTopicData] = []

        # Fetch from all sources (continue on error)
        sources = [
            ("reddit", self.reddit),
            ("hackernews", self.hackernews),
            ("rss", self.rss),
        ]

        for source_name, source in sources:
            try:
                topics = await source.fetch_topics(limit=limit_per_source)
                all_raw_topics.extend(topics)
                logger.info(f"Fetched {len(topics)} topics from {source_name}")
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}", exc_info=True)
                continue

        if not all_raw_topics:
            logger.warning("No topics fetched from any source")
            return []

        # Deduplicate
        unique_topics = await self.deduplicator.filter_duplicates(all_raw_topics)
        logger.info(f"After deduplication: {len(unique_topics)} unique topics")

        # Process and convert to TopicCandidate
        candidates: list[TopicCandidate] = []
        for raw_topic in unique_topics:
            try:
                # Extract entities
                entities = self.entity_extractor.extract_entities(raw_topic.title)

                # Determine cluster
                cluster = self.clusterer.cluster_topic(raw_topic.title, entities)

                # Generate ID
                topic_id = self._generate_topic_id(raw_topic)

                # Create TopicCandidate
                # Type cast source_platform to satisfy Literal type
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
                    detected_language=None,  # Future: add language detection
                    status="pending",
                    created_at=raw_topic.published_at,
                )
                candidates.append(candidate)

            except Exception as e:
                logger.error(f"Failed to process topic '{raw_topic.title}': {e}")
                continue

        logger.info(f"Processed {len(candidates)} topic candidates")
        return candidates

    def _generate_topic_id(self, raw_topic: RawTopicData) -> str:
        """
        Generate unique topic ID.

        Args:
            raw_topic: Raw topic data

        Returns:
            Unique topic identifier
        """
        timestamp = int(raw_topic.published_at.timestamp())
        content = f"{raw_topic.source_platform}-{raw_topic.title}-{timestamp}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{raw_topic.source_platform}-{timestamp}-{hash_suffix}"

    async def save_topics(self, topics: list[TopicCandidate]) -> int:
        """
        Save topics to Firestore (skip duplicates by ID).

        Args:
            topics: List of TopicCandidate objects

        Returns:
            Number of topics saved
        """
        saved_count = 0

        for topic in topics:
            try:
                # Check if already exists
                existing = await self.firestore.get_document(TOPIC_CANDIDATES_COLLECTION, topic.id)

                if existing:
                    logger.debug(f"Topic {topic.id} already exists, skipping")
                    continue

                # Save new topic
                await self.firestore.set_document(
                    TOPIC_CANDIDATES_COLLECTION, topic.id, topic.to_firestore_dict()
                )
                saved_count += 1

            except Exception as e:
                logger.error(f"Failed to save topic {topic.id}: {e}")
                continue

        logger.info(f"Saved {saved_count} new topics to Firestore")
        return saved_count
