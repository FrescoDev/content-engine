"""Integration tests for topic ingestion job."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.jobs.topic_ingestion_job import run_topic_ingestion
from src.content.models import TopicCandidate
from src.content.sources.base import RawTopicData


@pytest.mark.asyncio
async def test_run_topic_ingestion_success(mock_firestore_service):
    """Test successful job execution."""
    # Mock ingestion service
    with patch("src.jobs.topic_ingestion_job.TopicIngestionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_service.ingest_from_all_sources = AsyncMock(
            return_value=[
                TopicCandidate(
                    id="test-1",
                    source_platform="reddit",
                    title="Test Topic",
                    topic_cluster="ai-infra",
                    status="pending",
                )
            ]
        )
        mock_service.save_topics = AsyncMock(return_value=1)

        await run_topic_ingestion()

        # Verify service was called
        mock_service.ingest_from_all_sources.assert_called_once()
        mock_service.save_topics.assert_called_once()


@pytest.mark.asyncio
async def test_run_topic_ingestion_error_handling():
    """Test error handling in job."""
    with patch("src.jobs.topic_ingestion_job.TopicIngestionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_service.ingest_from_all_sources = AsyncMock(side_effect=Exception("Test error"))

        # Should raise exception
        with pytest.raises(Exception):
            await run_topic_ingestion()
