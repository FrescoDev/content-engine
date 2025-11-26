"""Hacker News topic ingestion source."""

import asyncio
from datetime import datetime

import httpx

from ...core import get_logger
from .base import RawTopicData

logger = get_logger(__name__)


class HackerNewsIngestionSource:
    """Ingest topics from Hacker News."""

    SOURCE_NAME = "hackernews"
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, client: httpx.AsyncClient | None = None):
        """Initialize Hacker News source."""
        self.client = client or httpx.AsyncClient(timeout=10.0)

    @property
    def source_name(self) -> str:
        """Source identifier."""
        return self.SOURCE_NAME

    async def fetch_topics(self, limit: int = 25) -> list[RawTopicData]:
        """Fetch top stories from Hacker News."""
        try:
            # Step 1: Get top story IDs
            top_stories_url = f"{self.BASE_URL}/topstories.json"
            response = await self.client.get(top_stories_url)
            response.raise_for_status()
            story_ids = response.json()[:limit]

            # Step 2: Fetch each story detail (batch for efficiency)
            tasks = [
                self.client.get(f"{self.BASE_URL}/item/{story_id}.json") for story_id in story_ids
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            topics: list[RawTopicData] = []
            for response in responses:
                if isinstance(response, Exception):
                    logger.warning(f"Failed to fetch story: {response}")
                    continue

                try:
                    # Type guard: ensure response is httpx.Response
                    if not isinstance(response, httpx.Response):
                        continue
                    response.raise_for_status()
                    story_data = response.json()

                    # Skip if story is deleted or invalid
                    if not story_data or story_data.get("type") != "story":
                        continue

                    topic = RawTopicData(
                        title=story_data.get("title", ""),
                        source_url=story_data.get("url"),
                        source_platform="hackernews",
                        raw_payload=story_data,
                        engagement_score=story_data.get("score", 0),
                        comment_count=story_data.get("descendants", 0),
                        published_at=datetime.fromtimestamp(story_data.get("time", 0)),
                        author=story_data.get("by"),
                    )
                    topics.append(topic)

                except Exception as e:
                    logger.warning(f"Failed to parse story: {e}")
                    continue

            logger.info(f"Fetched {len(topics)} topics from Hacker News")
            return topics

        except Exception as e:
            logger.error(f"Failed to fetch from Hacker News: {e}")
            return []
