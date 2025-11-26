"""Pytest configuration and shared fixtures."""

import asyncio
import asyncio
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import Response

from src.content.models import TopicCandidate
from src.content.sources.base import RawTopicData


# Remove event_loop fixture - pytest-asyncio handles this automatically


@pytest.fixture
def mock_httpx_client(mocker):
    """Mock httpx.AsyncClient."""
    client = AsyncMock()
    mocker.patch("httpx.AsyncClient", return_value=client)
    return client


@pytest.fixture
def mock_firestore_service(mocker):
    """Mock FirestoreService."""
    service = AsyncMock()
    service.query_collection = AsyncMock(return_value=[])
    service.get_document = AsyncMock(return_value=None)
    service.set_document = AsyncMock()
    service.add_document = AsyncMock(return_value="test-doc-id")
    service.client = MagicMock()
    return service


@pytest.fixture
def sample_raw_topic_data():
    """Sample RawTopicData for testing."""
    return RawTopicData(
        title="OpenAI Releases GPT-5",
        source_url="https://example.com/news",
        source_platform="reddit",
        raw_payload={"score": 1000, "num_comments": 50},
        engagement_score=1000,
        comment_count=50,
        published_at=datetime.now(timezone.utc),
        author="test_user",
    )


@pytest.fixture
def sample_topic_candidate():
    """Sample TopicCandidate for testing."""
    return TopicCandidate(
        id="reddit-1234567890-abc12345",
        source_platform="reddit",
        source_url="https://example.com/news",
        title="OpenAI Releases GPT-5",
        raw_payload={"score": 1000},
        entities=["OpenAI", "GPT-5"],
        topic_cluster="ai-infra",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def reddit_api_response():
    """Sample Reddit API response."""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "OpenAI Releases GPT-5",
                        "score": 1000,
                        "num_comments": 50,
                        "created_utc": 1704067200,
                        "permalink": "/r/MachineLearning/comments/abc123/test/",
                        "author": "test_user",
                    }
                },
                {
                    "data": {
                        "title": "New AI Breakthrough",
                        "score": 500,
                        "num_comments": 25,
                        "created_utc": 1704063600,
                        "permalink": "/r/MachineLearning/comments/def456/test/",
                        "author": "another_user",
                    }
                },
            ]
        }
    }


@pytest.fixture
def hackernews_api_response():
    """Sample Hacker News API responses."""
    top_stories = [123456, 123457, 123458]

    story_responses = [
        {
            "id": 123456,
            "title": "OpenAI Releases GPT-5",
            "score": 100,
            "descendants": 50,
            "time": 1704067200,
            "url": "https://example.com/news",
            "by": "test_user",
            "type": "story",
        },
        {
            "id": 123457,
            "title": "New AI Breakthrough",
            "score": 50,
            "descendants": 25,
            "time": 1704063600,
            "url": "https://example.com/news2",
            "by": "another_user",
            "type": "story",
        },
    ]

    return top_stories, story_responses


@pytest.fixture
def rss_feed_data():
    """Sample RSS feed data."""

    class MockFeed:
        def __init__(self):
            self.bozo = False
            self.entries = [
                {
                    "title": "Tech News Article",
                    "link": "https://example.com/article1",
                    "published": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "author": "Tech Writer",
                },
                {
                    "title": "Another Tech Story",
                    "link": "https://example.com/article2",
                    "published": "Mon, 01 Jan 2024 11:00:00 GMT",
                    "author": "Another Writer",
                },
            ]

    return MockFeed()


@pytest.fixture
def existing_topics_data():
    """Sample existing topics data for deduplication tests."""
    return [
        {
            "id": "reddit-1234567890-existing",
            "title": "Existing Topic",
            "source_url": "https://example.com/existing",
        },
        {
            "id": "hackernews-1234567890-existing",
            "title": "Another Existing Topic",
            "source_url": "https://example.com/another",
        },
    ]
