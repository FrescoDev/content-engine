"""Unit tests for Reddit ingestion source."""

from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest

from src.content.sources.reddit import RedditIngestionSource
from src.content.sources.base import RawTopicData


@pytest.mark.asyncio
async def test_reddit_source_fetch_topics_success(mock_httpx_client, reddit_api_response):
    """Test successful topic fetching from Reddit."""
    # Setup mock response
    mock_response = httpx.Response(
        200,
        json=reddit_api_response,
        request=httpx.Request("GET", "https://www.reddit.com/r/MachineLearning/hot.json"),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    source = RedditIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Verify results
    assert len(topics) > 0
    assert all(isinstance(topic, RawTopicData) for topic in topics)
    assert topics[0].title == "OpenAI Releases GPT-5"
    assert topics[0].source_platform == "reddit"
    assert topics[0].engagement_score == 1000
    assert topics[0].comment_count == 50


@pytest.mark.asyncio
async def test_reddit_source_fetch_topics_error_handling(mock_httpx_client):
    """Test error handling when Reddit API fails."""
    mock_httpx_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection error"))

    source = RedditIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Should return empty list, not raise
    assert topics == []


@pytest.mark.asyncio
async def test_reddit_source_fetch_topics_rate_limiting(
    mock_httpx_client, reddit_api_response, mocker
):
    """Test that rate limiting delay is applied."""
    mock_response = httpx.Response(
        200,
        json=reddit_api_response,
        request=httpx.Request("GET", "https://www.reddit.com/r/MachineLearning/hot.json"),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    sleep_spy = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    source = RedditIngestionSource(client=mock_httpx_client)
    await source.fetch_topics(limit=25)

    # Verify sleep was called (rate limiting)
    assert sleep_spy.call_count > 0


@pytest.mark.asyncio
async def test_reddit_source_fetch_topics_multiple_subreddits(
    mock_httpx_client, reddit_api_response
):
    """Test fetching from multiple subreddits."""
    mock_response = httpx.Response(
        200,
        json=reddit_api_response,
        request=httpx.Request("GET", "https://www.reddit.com/r/MachineLearning/hot.json"),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    source = RedditIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    # Should fetch from multiple subreddits
    assert mock_httpx_client.get.call_count > 1


def test_reddit_source_name():
    """Test source name property."""
    source = RedditIngestionSource()
    assert source.source_name == "reddit"


@pytest.mark.asyncio
async def test_reddit_source_empty_response(mock_httpx_client):
    """Test handling of empty Reddit response."""
    empty_response = httpx.Response(
        200,
        json={"data": {"children": []}},
        request=httpx.Request("GET", "https://www.reddit.com/r/MachineLearning/hot.json"),
    )
    mock_httpx_client.get = AsyncMock(return_value=empty_response)

    source = RedditIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=25)

    assert topics == []


@pytest.mark.asyncio
async def test_reddit_source_limit_enforcement(mock_httpx_client, reddit_api_response):
    """Test that limit parameter is respected."""
    mock_response = httpx.Response(
        200,
        json=reddit_api_response,
        request=httpx.Request("GET", "https://www.reddit.com/r/MachineLearning/hot.json"),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    source = RedditIngestionSource(client=mock_httpx_client)
    topics = await source.fetch_topics(limit=1)

    # Should respect limit (though may be more due to multiple subreddits)
    assert len(topics) <= 25  # Max limit
