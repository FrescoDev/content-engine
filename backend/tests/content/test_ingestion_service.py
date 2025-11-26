"""Unit tests for ingestion service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.content.ingestion_service import TopicIngestionService
from src.content.models import TopicCandidate
from src.content.sources.base import RawTopicData
from src.content.sources.hackernews import HackerNewsIngestionSource
from src.content.sources.reddit import RedditIngestionSource
from src.content.sources.rss import RSSIngestionSource


@pytest.mark.asyncio
async def test_ingest_from_all_sources_success(mock_firestore_service):
    """Test successful ingestion from all sources."""
    # Mock sources
    mock_reddit = MagicMock(spec=RedditIngestionSource)
    mock_reddit.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="Reddit Topic",
                source_url="https://reddit.com/test",
                source_platform="reddit",
                raw_payload={},
                published_at=datetime.now(timezone.utc),
            )
        ]
    )

    mock_hn = MagicMock(spec=HackerNewsIngestionSource)
    mock_hn.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="HN Topic",
                source_url="https://news.ycombinator.com/test",
                source_platform="hackernews",
                raw_payload={},
                published_at=datetime.now(timezone.utc),
            )
        ]
    )

    mock_rss = MagicMock(spec=RSSIngestionSource)
    mock_rss.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="RSS Topic",
                source_url="https://example.com/test",
                source_platform="rss",
                raw_payload={},
                published_at=datetime.now(timezone.utc),
            )
        ]
    )

    service = TopicIngestionService(
        firestore=mock_firestore_service,
        reddit_source=mock_reddit,
        hn_source=mock_hn,
        rss_source=mock_rss,
    )

    candidates = await service.ingest_from_all_sources(limit_per_source=25)

    assert len(candidates) == 3
    assert all(isinstance(c, TopicCandidate) for c in candidates)
    assert candidates[0].source_platform == "reddit"
    assert candidates[1].source_platform == "hackernews"
    assert candidates[2].source_platform == "rss"


@pytest.mark.asyncio
async def test_ingest_from_all_sources_partial_failure(mock_firestore_service):
    """Test ingestion continues when one source fails."""
    mock_reddit = MagicMock(spec=RedditIngestionSource)
    mock_reddit.fetch_topics = AsyncMock(side_effect=Exception("Reddit failed"))

    mock_hn = MagicMock(spec=HackerNewsIngestionSource)
    mock_hn.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="HN Topic",
                source_url="https://news.ycombinator.com/test",
                source_platform="hackernews",
                raw_payload={},
                published_at=datetime.now(timezone.utc),
            )
        ]
    )

    mock_rss = MagicMock(spec=RSSIngestionSource)
    mock_rss.fetch_topics = AsyncMock(return_value=[])

    service = TopicIngestionService(
        firestore=mock_firestore_service,
        reddit_source=mock_reddit,
        hn_source=mock_hn,
        rss_source=mock_rss,
    )

    candidates = await service.ingest_from_all_sources(limit_per_source=25)

    # Should still get topics from working sources
    assert len(candidates) == 1
    assert candidates[0].source_platform == "hackernews"


@pytest.mark.asyncio
async def test_ingest_from_all_sources_deduplication(mock_firestore_service, existing_topics_data):
    """Test that deduplication is applied."""
    existing_topics_data[0]["source_url"] = "https://reddit.com/test"
    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics_data)

    # Mock all sources to avoid real API calls
    mock_reddit = MagicMock(spec=RedditIngestionSource)
    mock_reddit.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="Duplicate Topic",
                source_url="https://reddit.com/test",  # Duplicate URL
                source_platform="reddit",
                raw_payload={},
                published_at=datetime.now(timezone.utc),
            )
        ]
    )

    mock_hn = MagicMock(spec=HackerNewsIngestionSource)
    mock_hn.fetch_topics = AsyncMock(return_value=[])

    mock_rss = MagicMock(spec=RSSIngestionSource)
    mock_rss.fetch_topics = AsyncMock(return_value=[])

    service = TopicIngestionService(
        firestore=mock_firestore_service,
        reddit_source=mock_reddit,
        hn_source=mock_hn,
        rss_source=mock_rss,
    )

    candidates = await service.ingest_from_all_sources(limit_per_source=25)

    # Duplicate should be filtered out
    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_save_topics_new_topics(mock_firestore_service, sample_topic_candidate):
    """Test saving new topics."""
    mock_firestore_service.get_document = AsyncMock(return_value=None)  # Not exists

    service = TopicIngestionService(firestore=mock_firestore_service)
    saved_count = await service.save_topics([sample_topic_candidate])

    assert saved_count == 1
    mock_firestore_service.set_document.assert_called_once()


@pytest.mark.asyncio
async def test_save_topics_duplicate_skipped(mock_firestore_service, sample_topic_candidate):
    """Test that duplicate topics are skipped."""
    mock_firestore_service.get_document = AsyncMock(
        return_value={"id": sample_topic_candidate.id}
    )  # Exists

    service = TopicIngestionService(firestore=mock_firestore_service)
    saved_count = await service.save_topics([sample_topic_candidate])

    assert saved_count == 0
    mock_firestore_service.set_document.assert_not_called()


@pytest.mark.asyncio
async def test_save_topics_error_handling(mock_firestore_service, sample_topic_candidate):
    """Test error handling when saving fails."""
    mock_firestore_service.get_document = AsyncMock(return_value=None)
    mock_firestore_service.set_document = AsyncMock(side_effect=Exception("Firestore error"))

    service = TopicIngestionService(firestore=mock_firestore_service)
    saved_count = await service.save_topics([sample_topic_candidate])

    # Should continue and return count of successful saves
    assert saved_count == 0


def test_generate_topic_id(sample_raw_topic_data):
    """Test topic ID generation."""
    service = TopicIngestionService()
    topic_id = service._generate_topic_id(sample_raw_topic_data)

    assert topic_id.startswith("reddit-")
    assert len(topic_id) > 20  # Should have timestamp and hash


def test_generate_topic_id_deterministic(sample_raw_topic_data):
    """Test that same topic generates same ID."""
    service = TopicIngestionService()
    id1 = service._generate_topic_id(sample_raw_topic_data)
    id2 = service._generate_topic_id(sample_raw_topic_data)

    assert id1 == id2  # Should be deterministic
