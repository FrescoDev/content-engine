"""End-to-end integration tests."""

from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.content.ingestion_service import TopicIngestionService
from src.content.models import TopicCandidate
from src.content.sources.base import RawTopicData
from src.content.sources.hackernews import HackerNewsIngestionSource
from src.content.sources.reddit import RedditIngestionSource
from src.content.sources.rss import RSSIngestionSource


@pytest.mark.asyncio
async def test_end_to_end_ingestion_flow(mock_firestore_service):
    """Test complete ingestion flow from sources to Firestore."""

    # Setup mock sources with realistic data
    mock_reddit = MagicMock(spec=RedditIngestionSource)
    mock_reddit.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="OpenAI Releases GPT-5",
                source_url="https://reddit.com/r/MachineLearning/comments/abc123",
                source_platform="reddit",
                raw_payload={"score": 1000, "num_comments": 50},
                engagement_score=1000,
                comment_count=50,
                published_at=datetime.now(timezone.utc),
                author="test_user",
            )
        ]
    )

    mock_hn = MagicMock(spec=HackerNewsIngestionSource)
    mock_hn.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="New AI Breakthrough",
                source_url="https://example.com/news",
                source_platform="hackernews",
                raw_payload={"score": 100, "descendants": 50},
                engagement_score=100,
                comment_count=50,
                published_at=datetime.now(timezone.utc),
                author="hn_user",
            )
        ]
    )

    mock_rss = MagicMock(spec=RSSIngestionSource)
    mock_rss.fetch_topics = AsyncMock(return_value=[])

    # Setup Firestore mocks
    mock_firestore_service.query_collection = AsyncMock(return_value=[])  # No existing topics
    mock_firestore_service.get_document = AsyncMock(return_value=None)  # Topics don't exist
    mock_firestore_service.set_document = AsyncMock()

    # Run ingestion
    service = TopicIngestionService(
        firestore=mock_firestore_service,
        reddit_source=mock_reddit,
        hn_source=mock_hn,
        rss_source=mock_rss,
    )

    candidates = await service.ingest_from_all_sources(limit_per_source=25)

    # Verify processing
    assert len(candidates) == 2
    assert all(isinstance(c, TopicCandidate) for c in candidates)

    # Verify entities extracted
    assert any("OpenAI" in c.entities for c in candidates)

    # Verify clustering
    assert any(c.topic_cluster == "ai-infra" for c in candidates)

    # Save topics
    saved_count = await service.save_topics(candidates)

    # Verify saving
    assert saved_count == 2
    assert mock_firestore_service.set_document.call_count == 2


@pytest.mark.asyncio
async def test_end_to_end_deduplication(mock_firestore_service):
    """Test that deduplication works end-to-end."""
    # Existing topic in Firestore
    existing_topics = [
        {
            "id": "reddit-1234567890-existing",
            "title": "OpenAI Releases GPT-5",
            "source_url": "https://reddit.com/r/MachineLearning/comments/abc123",
        }
    ]

    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics)

    # Mock all sources to avoid real API calls
    mock_reddit = MagicMock(spec=RedditIngestionSource)
    mock_reddit.fetch_topics = AsyncMock(
        return_value=[
            RawTopicData(
                title="OpenAI Releases GPT-5",  # Same title
                source_url="https://reddit.com/r/MachineLearning/comments/abc123",  # Same URL
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
