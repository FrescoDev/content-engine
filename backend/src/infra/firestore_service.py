"""
Firestore service for Content Engine using Application Default Credentials.
"""

import asyncio
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ..core import get_logger, get_settings

logger = get_logger(__name__)


class FirestoreService:
    """Service for Firestore operations using Application Default Credentials."""

    def __init__(self, database_id: str | None = None):
        """Initialize Firestore service."""
        settings = get_settings()
        self.database_id = database_id or settings.firestore_database_id
        self._client: firestore.Client | None = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Firestore client."""
        try:
            # Allow lazy initialization - don't fail if GCP_PROJECT_ID not set
            # This allows the service to be imported without full GCP setup
            settings = get_settings()
            project_id = settings.gcp_project_id

            if self.database_id:
                # Use project_id from settings if available, otherwise let ADC use default
                if project_id:
                    self._client = firestore.Client(project=project_id, database=self.database_id)
                    logger.info(
                        f"Firestore client initialized (project: {project_id}, database: {self.database_id})"
                    )
                else:
                    self._client = firestore.Client(database=self.database_id)
                    logger.info(
                        f"Firestore client initialized (database: {self.database_id}, using ADC default project)"
                    )
            else:
                logger.warning("Firestore database_id not configured - client will be None")
        except Exception as e:
            logger.warning(f"Firestore client initialization deferred: {e}")
            # Don't raise - allow lazy initialization
            self._client = None

    @property
    def client(self) -> firestore.Client:
        """Get Firestore client."""
        if not self._client:
            self._initialize_client()
        if not self._client:
            raise RuntimeError(
                "Firestore client not initialized. Check GCP credentials and database_id configuration."
            )
        return self._client

    async def get_document(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        """Get a single document by ID."""
        try:
            doc_ref = self.client.collection(collection).document(doc_id)
            doc = await asyncio.to_thread(doc_ref.get)
            if doc.exists:
                data = doc.to_dict()
                if data:
                    data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get document {collection}/{doc_id}: {e}")
            raise

    async def set_document(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        """Set/update a document."""
        try:
            doc_ref = self.client.collection(collection).document(doc_id)
            await asyncio.to_thread(doc_ref.set, data)
            logger.debug(f"Document set: {collection}/{doc_id}")
        except Exception as e:
            logger.error(f"Failed to set document {collection}/{doc_id}: {e}")
            raise

    async def add_document(self, collection: str, data: dict[str, Any]) -> str:
        """Add a new document and return its ID."""
        try:
            doc_ref = await asyncio.to_thread(self.client.collection(collection).add, data)
            doc_id = doc_ref[1].id
            logger.debug(f"Document added: {collection}/{doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document to {collection}: {e}")
            raise

    async def delete_document(self, collection: str, doc_id: str) -> None:
        """Delete a document."""
        try:
            doc_ref = self.client.collection(collection).document(doc_id)
            await asyncio.to_thread(doc_ref.delete)
            logger.debug(f"Document deleted: {collection}/{doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {collection}/{doc_id}: {e}")
            raise

    async def query_collection(
        self,
        collection: str,
        filters: list[tuple[str, str, Any]] | None = None,
        limit: int | None = None,
        order_by: str | None = None,
        order_direction: str = "ASCENDING",
    ) -> list[dict[str, Any]]:
        """
        Query a collection with optional filters.

        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            limit: Maximum number of results
            order_by: Field to order by
            order_direction: "ASCENDING" or "DESCENDING"

        Returns:
            List of document dictionaries
        """
        try:
            query = self.client.collection(collection)

            # Apply filters
            if filters:
                for field, operator, value in filters:
                    if operator == "==":
                        query = query.where(filter=FieldFilter(field, "==", value))
                    elif operator == ">":
                        query = query.where(filter=FieldFilter(field, ">", value))
                    elif operator == "<":
                        query = query.where(filter=FieldFilter(field, "<", value))
                    elif operator == ">=":
                        query = query.where(filter=FieldFilter(field, ">=", value))
                    elif operator == "<=":
                        query = query.where(filter=FieldFilter(field, "<=", value))
                    elif operator == "in":
                        # Firestore "in" operator
                        query = query.where(filter=FieldFilter(field, "in", value))
                    else:
                        logger.warning(f"Unsupported operator: {operator}")

            # Apply ordering
            if order_by:
                direction = (
                    firestore.Query.ASCENDING
                    if order_direction == "ASCENDING"
                    else firestore.Query.DESCENDING
                )
                query = query.order_by(order_by, direction=direction)

            # Apply limit
            if limit:
                query = query.limit(limit)

            docs = await asyncio.to_thread(query.stream)
            results = []
            for doc in docs:
                data = doc.to_dict()
                if data:
                    data["id"] = doc.id
                    results.append(data)

            logger.debug(f"Query returned {len(results)} documents from {collection}")
            return results
        except Exception as e:
            logger.error(f"Failed to query collection {collection}: {e}")
            raise
