"""Base types for topic ingestion sources."""

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class RawTopicData(BaseModel):
    """Standardized raw topic data from any source."""

    title: str = Field(..., description="Topic title")
    source_url: str | None = Field(None, description="Source URL")
    source_platform: str = Field(..., description="Source platform identifier")
    raw_payload: dict[str, Any] = Field(
        default_factory=dict, description="Original API response data"
    )
    engagement_score: int | None = Field(
        None, description="Engagement metric (upvotes, views, etc.)"
    )
    comment_count: int | None = Field(None, description="Comment count")
    published_at: datetime = Field(..., description="Publication timestamp")
    author: str | None = Field(None, description="Author identifier")


class IngestionSource(Protocol):
    """Protocol for topic ingestion sources."""

    @property
    def source_name(self) -> str:
        """Source identifier."""
        ...

    async def fetch_topics(self, limit: int = 25) -> list[RawTopicData]:
        """Fetch topics from source."""
        ...
