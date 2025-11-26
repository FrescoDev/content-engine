"""RSS feed topic ingestion source."""

import asyncio
from datetime import datetime, timezone

import feedparser

from ...core import get_logger
from .base import RawTopicData

logger = get_logger(__name__)


class RSSIngestionSource:
    """Ingest topics from RSS feeds."""

    SOURCE_NAME = "rss"

    FEEDS = {
        "ai-infra": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
        ],
        "business-socioeconomic": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
        ],
        "culture-music": [
            "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        ],
    }

    def __init__(self):
        """Initialize RSS source."""
        pass

    @property
    def source_name(self) -> str:
        """Source identifier."""
        return self.SOURCE_NAME

    def _parse_date(self, date_str: str | None) -> datetime:
        """Parse RSS date string to datetime."""
        if not date_str:
            return datetime.now(timezone.utc)

        try:
            # feedparser handles various date formats
            parsed = feedparser._parse_date(date_str)
            if parsed:
                # feedparser returns (year, month, day, hour, minute, second, ...)
                # Create datetime and add UTC timezone
                dt = datetime(*parsed[:6])
                return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        return datetime.now(timezone.utc)

    async def fetch_topics(self, limit: int = 25) -> list[RawTopicData]:
        """Fetch topics from RSS feeds."""
        all_topics: list[RawTopicData] = []

        for _cluster, feed_urls in self.FEEDS.items():
            for feed_url in feed_urls:
                try:
                    # feedparser is synchronous, run in thread
                    feed = await asyncio.to_thread(feedparser.parse, feed_url)

                    if feed.bozo:
                        logger.warning(
                            f"RSS feed parse warning for {feed_url}: {feed.bozo_exception}"
                        )

                    for entry in feed.entries[:limit]:
                        topic = RawTopicData(
                            title=entry.get("title", ""),
                            source_url=entry.get("link"),
                            source_platform="rss",
                            raw_payload={"feed": feed_url, "entry": entry},
                            engagement_score=None,  # RSS has no engagement metrics
                            comment_count=None,
                            published_at=self._parse_date(entry.get("published")),
                            author=entry.get("author"),
                        )
                        all_topics.append(topic)

                except Exception as e:
                    logger.warning(f"Failed to fetch RSS {feed_url}: {e}")
                    continue

        logger.info(f"Fetched {len(all_topics)} topics from RSS feeds")
        return all_topics[:limit]
