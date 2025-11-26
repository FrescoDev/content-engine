"""Unit tests for RSS ingestion source."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.content.sources.rss import RSSIngestionSource
from src.content.sources.base import RawTopicData


@pytest.mark.asyncio
async def test_rss_source_fetch_topics_success(mocker, rss_feed_data):
    """Test successful topic fetching from RSS feeds."""
    # Mock asyncio.to_thread to return the mocked feed data
    # RSS source iterates through multiple feeds, so mock returns same data for each
    mocker.patch("asyncio.to_thread", return_value=rss_feed_data)

    source = RSSIngestionSource()
    topics = await source.fetch_topics(limit=25)

    # Verify results - RSS source fetches from multiple feeds, so we get more than 2
    assert len(topics) > 0
    assert len(topics) <= 25  # Respects limit
    assert all(isinstance(topic, RawTopicData) for topic in topics)
    assert topics[0].title == "Tech News Article"
    assert topics[0].source_platform == "rss"
    assert topics[0].engagement_score is None  # RSS has no engagement metrics
    assert topics[0].source_url == "https://example.com/article1"


@pytest.mark.asyncio
async def test_rss_source_fetch_topics_error_handling(mocker):
    """Test error handling when RSS feed fails."""
    mocker.patch("asyncio.to_thread", side_effect=Exception("Parse error"))

    source = RSSIngestionSource()
    topics = await source.fetch_topics(limit=25)

    # Should return empty list, not raise
    assert topics == []


@pytest.mark.asyncio
async def test_rss_source_fetch_topics_multiple_feeds(mocker, rss_feed_data):
    """Test fetching from multiple RSS feeds."""
    mocker.patch("asyncio.to_thread", return_value=rss_feed_data)

    source = RSSIngestionSource()
    topics = await source.fetch_topics(limit=25)

    # Should fetch from multiple feeds
    assert len(topics) > 0


@pytest.mark.asyncio
async def test_rss_source_date_parsing(mocker):
    """Test RSS date parsing."""
    feed_data = Mock()
    feed_data.bozo = False
    feed_data.entries = [
        {
            "title": "Test Article",
            "link": "https://example.com/test",
            "published": "Mon, 01 Jan 2024 12:00:00 GMT",
            "author": "Test Author",
        }
    ]

    mocker.patch("asyncio.to_thread", return_value=feed_data)

    source = RSSIngestionSource()
    topics = await source.fetch_topics(limit=25)

    assert len(topics) >= 1  # May have multiple feeds
    assert isinstance(topics[0].published_at, datetime)
    # Check that date was parsed (has timezone info)
    assert topics[0].published_at.tzinfo is not None


@pytest.mark.asyncio
async def test_rss_source_missing_date(mocker):
    """Test handling of missing publication date."""
    feed_data = Mock()
    feed_data.bozo = False
    feed_data.entries = [
        {
            "title": "Test Article",
            "link": "https://example.com/test",
            "published": None,
            "author": "Test Author",
        }
    ]

    mocker.patch("asyncio.to_thread", return_value=feed_data)

    source = RSSIngestionSource()
    topics = await source.fetch_topics(limit=25)

    # Should use current time as fallback
    assert len(topics) >= 1  # May have multiple feeds
    assert isinstance(topics[0].published_at, datetime)
    # Check that date was parsed (has timezone info)
    assert topics[0].published_at.tzinfo is not None


def test_rss_source_name():
    """Test source name property."""
    source = RSSIngestionSource()
    assert source.source_name == "rss"
