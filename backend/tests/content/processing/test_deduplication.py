"""Unit tests for deduplication service."""

from unittest.mock import AsyncMock

import pytest

from src.content.processing.deduplication import TopicDeduplicator
from src.content.sources.base import RawTopicData


@pytest.mark.asyncio
async def test_filter_duplicates_by_url(
    mock_firestore_service, sample_raw_topic_data, existing_topics_data
):
    """Test deduplication by URL."""
    existing_topics_data[0]["source_url"] = "https://example.com/news"
    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics_data)

    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    # Create topic with same URL
    duplicate_topic = RawTopicData(
        title="Different Title",
        source_url="https://example.com/news",  # Same URL
        source_platform="reddit",
        raw_payload={},
        published_at=sample_raw_topic_data.published_at,
    )

    filtered = await deduplicator.filter_duplicates([duplicate_topic])

    assert len(filtered) == 0  # Should be filtered out


@pytest.mark.asyncio
async def test_filter_duplicates_by_title(
    mock_firestore_service, sample_raw_topic_data, existing_topics_data
):
    """Test deduplication by title."""
    existing_topics_data[0]["title"] = "Existing Topic"
    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics_data)

    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    # Create topic with same title (case-insensitive)
    duplicate_topic = RawTopicData(
        title="existing topic",  # Same title, different case
        source_url="https://example.com/different",
        source_platform="reddit",
        raw_payload={},
        published_at=sample_raw_topic_data.published_at,
    )

    filtered = await deduplicator.filter_duplicates([duplicate_topic])

    assert len(filtered) == 0  # Should be filtered out


@pytest.mark.asyncio
async def test_filter_duplicates_unique_topics(
    mock_firestore_service, sample_raw_topic_data, existing_topics_data
):
    """Test that unique topics pass through."""
    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics_data)

    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    unique_topic = RawTopicData(
        title="Completely New Topic",
        source_url="https://example.com/new",
        source_platform="reddit",
        raw_payload={},
        published_at=sample_raw_topic_data.published_at,
    )

    filtered = await deduplicator.filter_duplicates([unique_topic])

    assert len(filtered) == 1
    assert filtered[0].title == "Completely New Topic"


@pytest.mark.asyncio
async def test_filter_duplicates_empty_existing(mock_firestore_service, sample_raw_topic_data):
    """Test deduplication when no existing topics."""
    mock_firestore_service.query_collection = AsyncMock(return_value=[])

    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    filtered = await deduplicator.filter_duplicates([sample_raw_topic_data])

    assert len(filtered) == 1  # Should pass through


@pytest.mark.asyncio
async def test_filter_duplicates_prefetched_existing(
    mock_firestore_service, sample_raw_topic_data, existing_topics_data
):
    """Test deduplication with pre-fetched existing topics."""
    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    # Pass existing topics directly
    filtered = await deduplicator.filter_duplicates(
        [sample_raw_topic_data], existing_topics=existing_topics_data
    )

    # Should not call Firestore again
    mock_firestore_service.query_collection.assert_not_called()
    assert len(filtered) == 1  # sample_raw_topic_data is unique


@pytest.mark.asyncio
async def test_filter_duplicates_multiple_topics(mock_firestore_service, sample_raw_topic_data):
    """Test deduplication with multiple topics."""
    # Set up existing topics with specific titles/URLs
    existing_topics = [
        {
            "id": "existing-1",
            "title": "Existing Topic",
            "source_url": "https://example.com/existing",
        },
        {
            "id": "existing-2",
            "title": "Another Existing",
            "source_url": "https://example.com/another-existing",
        },
    ]
    mock_firestore_service.query_collection = AsyncMock(return_value=existing_topics)

    deduplicator = TopicDeduplicator(firestore=mock_firestore_service)

    topics = [
        sample_raw_topic_data,  # Unique (different title and URL)
        RawTopicData(
            title="Existing Topic",  # Duplicate by title
            source_url="https://example.com/different",
            source_platform="reddit",
            raw_payload={},
            published_at=sample_raw_topic_data.published_at,
        ),
        RawTopicData(
            title="Another Unique Topic",
            source_url="https://example.com/another",
            source_platform="reddit",
            raw_payload={},
            published_at=sample_raw_topic_data.published_at,
        ),
    ]

    filtered = await deduplicator.filter_duplicates(topics)

    assert len(filtered) == 2  # One duplicate filtered out (the "Existing Topic")
