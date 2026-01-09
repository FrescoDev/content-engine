"""Topic deduplication service."""

from ...core import get_logger
from ...infra import FirestoreService
from ..models import TOPIC_CANDIDATES_COLLECTION
from ..sources.base import RawTopicData

logger = get_logger(__name__)


class TopicDeduplicator:
    """Prevent duplicate topics."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize deduplicator."""
        self.firestore = firestore or FirestoreService()

    async def filter_duplicates(
        self,
        topics: list[RawTopicData],
        existing_topics: list[dict] | None = None,
    ) -> list[RawTopicData]:
        """
        Filter out duplicates from list.

        Args:
            topics: List of raw topics to check
            existing_topics: Optional pre-fetched existing topics (for efficiency)

        Returns:
            Filtered list of unique topics
        """
        if existing_topics is None:
            # Fetch recent existing topics
            existing_topics = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                limit=1000,  # Reasonable limit for deduplication
                order_by="created_at",
                order_direction="DESCENDING",
            )

        # Build sets for fast lookup
        existing_urls: set[str] = set()
        existing_titles: set[str] = set()

        if existing_topics:
            existing_urls = {
                str(t.get("source_url")) for t in existing_topics if t.get("source_url") is not None
            }
            existing_titles = {
                str(t.get("title", "")).lower().strip()
                for t in existing_topics
                if t.get("title") is not None
            }

        filtered: list[RawTopicData] = []
        duplicates_count = 0

        for topic in topics:
            # Check URL match (exact)
            if topic.source_url and topic.source_url in existing_urls:
                duplicates_count += 1
                logger.debug(f"Duplicate by URL: {topic.source_url}")
                continue

            # Check title match (exact, case-insensitive)
            title_normalized = topic.title.lower().strip()
            if title_normalized in existing_titles:
                duplicates_count += 1
                logger.debug(f"Duplicate by title: {topic.title}")
                continue

            filtered.append(topic)

        if duplicates_count > 0:
            logger.info(
                f"Filtered {duplicates_count} duplicates, {len(filtered)} unique topics remaining"
            )

        return filtered
