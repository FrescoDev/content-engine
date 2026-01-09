"""Unit tests for manual topic entry."""

from datetime import datetime

import pytest

from src.content.sources.manual import create_manual_topic
from src.content.sources.base import RawTopicData


def test_create_manual_topic():
    """Test manual topic creation."""
    topic = create_manual_topic(
        title="Breaking News",
        topic_cluster="ai-infra",
        source_url="https://example.com/news",
        notes="Important update",
    )

    assert isinstance(topic, RawTopicData)
    assert topic.title == "Breaking News"
    assert topic.source_platform == "manual"
    assert topic.source_url == "https://example.com/news"
    assert topic.raw_payload == {"notes": "Important update"}
    assert topic.engagement_score is None
    assert topic.comment_count is None
    assert isinstance(topic.published_at, datetime)


def test_create_manual_topic_minimal():
    """Test manual topic creation with minimal fields."""
    topic = create_manual_topic(
        title="Simple Topic",
        topic_cluster="business-socioeconomic",
    )

    assert topic.title == "Simple Topic"
    assert topic.source_url is None
    assert topic.raw_payload == {}
    assert topic.author is None




