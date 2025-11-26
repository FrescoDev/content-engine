"""Unit tests for Hacker News ingestion source."""

from unittest.mock import AsyncMock

import httpx
import pytest

from src.content.sources.hackernews import HackerNewsIngestionSource
from src.content.sources.base import RawTopicData


@pytest.mark.asyncio
async def test_hackernews_source_fetch_topics_success(mock_httpx_client, hackernews_api_response):
    """Test successful topic fetching from Hacker News."""
    top_stories, story_responses = hackernews_api_response

    # Mock topstories response
    top_stories_response = httpx.Response(
        200,
        json=top_stories,
        request=httpx.Request("GET", "https://hacker-news.firebaseio.com/v0/topstories.json"),
    )

    # Mock individual story responses
    story_mocks = [
        httpx.Response(
            200,
            json=story,
            request=httpx.Request(
                "GET", f"https://hacker-news.firebaseio.com/v0/item/{story['id']}.json"
            ),
        )
        for story in story_responses
    ]

    mock_httpx_client.get = AsyncMock(side_effect=[top_stories_response] + story_mocks)

    source = HackerNewsIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Verify results
    assert len(topics) == 2
    assert all(isinstance(topic, RawTopicData) for topic in topics)
    assert topics[0].title == "OpenAI Releases GPT-5"
    assert topics[0].source_platform == "hackernews"
    assert topics[0].engagement_score == 100
    assert topics[0].comment_count == 50


@pytest.mark.asyncio
async def test_hackernews_source_fetch_topics_error_handling(mock_httpx_client):
    """Test error handling when Hacker News API fails."""
    mock_httpx_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection error"))

    source = HackerNewsIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Should return empty list, not raise
    assert topics == []


@pytest.mark.asyncio
async def test_hackernews_source_fetch_topics_partial_failure(
    mock_httpx_client, hackernews_api_response
):
    """Test handling when some story fetches fail."""
    top_stories, story_responses = hackernews_api_response

    top_stories_response = httpx.Response(
        200,
        json=top_stories,
        request=httpx.Request("GET", "https://hacker-news.firebaseio.com/v0/topstories.json"),
    )

    # First story succeeds, second fails
    story_mocks = [
        httpx.Response(
            200,
            json=story_responses[0],
            request=httpx.Request("GET", "https://hacker-news.firebaseio.com/v0/item/123456.json"),
        ),
        httpx.HTTPError("Connection error"),
    ]

    mock_httpx_client.get = AsyncMock(side_effect=[top_stories_response] + story_mocks)

    source = HackerNewsIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Should return topics from successful fetches
    assert len(topics) == 1
    assert topics[0].title == "OpenAI Releases GPT-5"


@pytest.mark.asyncio
async def test_hackernews_source_fetch_topics_skips_non_stories(mock_httpx_client):
    """Test that non-story items are skipped."""
    top_stories = [123456]

    top_stories_response = httpx.Response(
        200,
        json=top_stories,
        request=httpx.Request("GET", "https://hacker-news.firebaseio.com/v0/topstories.json"),
    )

    # Return a comment instead of story
    comment_response = httpx.Response(
        200,
        json={"id": 123456, "type": "comment", "text": "This is a comment"},
        request=httpx.Request("GET", "https://hacker-news.firebaseio.com/v0/item/123456.json"),
    )

    mock_httpx_client.get = AsyncMock(side_effect=[top_stories_response, comment_response])

    source = HackerNewsIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Should skip comments
    assert len(topics) == 0


def test_hackernews_source_name():
    """Test source name property."""
    source = HackerNewsIngestionSource()
    assert source.source_name == "hackernews"
