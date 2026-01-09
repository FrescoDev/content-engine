"""
Google Cloud Storage service for Content Engine.
"""

import asyncio

from google.cloud import storage
from google.cloud.exceptions import NotFound

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class GCSService:
    """Service for Google Cloud Storage operations."""

    def __init__(self, bucket_name: str | None = None):
        """Initialize GCS service."""
        settings = get_settings()
        self.bucket_name = bucket_name or settings.gcs_bucket_name
        self._client: storage.Client | None = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize GCS client."""
        try:
            self._client = storage.Client()
            logger.info(f"GCS client initialized (bucket: {self.bucket_name})")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    @property
    def client(self) -> storage.Client:
        """Get GCS client."""
        if not self._client:
            self._initialize_client()
        if not self._client:
            raise RuntimeError("GCS client not initialized. Check GCP credentials configuration.")
        return self._client

    async def upload_bytes(
        self,
        bucket: str,
        blob_name: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload bytes to GCS.

        Returns:
            Public URL of the uploaded blob
        """
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(blob_name)

            if metadata:
                blob.metadata = metadata

            await asyncio.to_thread(blob.upload_from_string, data)
            logger.info(f"Uploaded {blob_name} to {bucket}")
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload {blob_name}: {e}")
            raise

    async def download_bytes(self, bucket: str, blob_name: str) -> bytes:
        """Download bytes from GCS."""
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(blob_name)

            if not await asyncio.to_thread(blob.exists):
                raise NotFound(f"Blob not found: {blob_name}")

            data = await asyncio.to_thread(blob.download_as_bytes)
            logger.debug(f"Downloaded {blob_name} from {bucket}")
            return data
        except Exception as e:
            logger.error(f"Failed to download {blob_name}: {e}")
            raise

    async def delete_blob(self, bucket: str, blob_name: str) -> None:
        """Delete a blob from GCS."""
        try:
            bucket_obj = self.client.bucket(bucket)
            blob = bucket_obj.blob(blob_name)
            await asyncio.to_thread(blob.delete)
            logger.debug(f"Deleted {blob_name} from {bucket}")
        except Exception as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            raise
