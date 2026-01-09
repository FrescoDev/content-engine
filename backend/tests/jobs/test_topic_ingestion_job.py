"""Integration tests for topic ingestion job."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.content.models import TopicCandidate
from src.jobs.topic_ingestion_job import run_topic_ingestion


@pytest.mark.asyncio
async def test_run_topic_ingestion_success(mock_firestore_service):
    """Test successful job execution."""
    # Mock track_job_run to prevent real Firestore writes
    from contextlib import asynccontextmanager

    mock_job_run = MagicMock()
    mock_job_run.id = "test-run-id"
    mock_job_run.topics_ingested = 0
    mock_job_run.topics_saved = 0

    @asynccontextmanager
    async def mock_track_job_run(*args, **kwargs):
        yield mock_job_run

    # Mock ingestion service
    with patch("src.jobs.topic_ingestion_job.track_job_run", mock_track_job_run):
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
    # Mock track_job_run to prevent real Firestore writes
    from contextlib import asynccontextmanager

    mock_job_run = MagicMock()
    mock_job_run.id = "test-run-id"

    @asynccontextmanager
    async def mock_track_job_run(*args, **kwargs):
        yield mock_job_run

    with patch("src.jobs.topic_ingestion_job.track_job_run", mock_track_job_run):
        with patch("src.jobs.topic_ingestion_job.TopicIngestionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            mock_service.ingest_from_all_sources = AsyncMock(side_effect=Exception("Test error"))

            # Should raise exception
            with pytest.raises(Exception, match="Test error"):
                await run_topic_ingestion()
