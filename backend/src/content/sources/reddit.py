"""Reddit topic ingestion source."""

import asyncio
from datetime import datetime

import httpx

from ...core import get_logger
from .base import RawTopicData

logger = get_logger(__name__)


class RedditIngestionSource:
    """Ingest topics from Reddit."""

    SOURCE_NAME = "reddit"
    BASE_URL = "https://www.reddit.com"
    USER_AGENT = "ContentEngine/1.0"

    # Subreddits per cluster
    SUBREDDITS = {
        "ai-infra": ["MachineLearning", "artificial", "singularity"],
        "business-socioeconomic": ["technology", "business", "startups"],
        "culture-music": ["entertainment", "music", "television"],
        "applied-industry": ["insurance", "realestate"],
        "meta-content-intel": ["content_marketing", "socialmedia"],
    }

    def __init__(self, client: httpx.AsyncClient | None = None):
        """Initialize Reddit source."""
        self.client = client or httpx.AsyncClient(
            timeout=10.0, headers={"User-Agent": self.USER_AGENT}
        )

    @property
    def source_name(self) -> str:
        """Source identifier."""
        return self.SOURCE_NAME

    async def fetch_topics(self, limit: int = 25) -> list[RawTopicData]:
        """Fetch hot posts from configured subreddits."""
        all_topics: list[RawTopicData] = []

        for _cluster, subreddits in self.SUBREDDITS.items():
            for subreddit in subreddits:
                try:
                    url = f"{self.BASE_URL}/r/{subreddit}/hot.json"
                    params = {"limit": min(limit, 25)}  # Reddit max 25 per request
                    response = await self.client.get(url, params=params)
                    response.raise_for_status()

                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        post_data = post.get("data", {})
                        topic = RawTopicData(
                            title=post_data.get("title", ""),
                            source_url=f"{self.BASE_URL}{post_data.get('permalink', '')}",
                            source_platform="reddit",
                            raw_payload=post_data,
                            engagement_score=post_data.get("score", 0),
                            comment_count=post_data.get("num_comments", 0),
                            published_at=datetime.fromtimestamp(post_data.get("created_utc", 0)),
                            author=post_data.get("author"),
                        )
                        all_topics.append(topic)

                    # Rate limiting: Reddit allows ~60 req/min, add delay
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"Failed to fetch from r/{subreddit}: {e}")
                    continue

        # Return top N topics
        return all_topics[:limit]
