"""Manual topic entry."""

from datetime import datetime, timezone

from .base import RawTopicData


def create_manual_topic(
    title: str,
    topic_cluster: str,
    source_url: str | None = None,
    notes: str | None = None,
) -> RawTopicData:
    """Create a manual topic entry."""
    return RawTopicData(
        title=title,
        source_url=source_url,
        source_platform="manual",
        raw_payload={"notes": notes} if notes else {},
        engagement_score=None,
        comment_count=None,
        published_at=datetime.now(timezone.utc),
        author=None,
    )
