"""
Review service for fetching and joining data for reviewer UX.
"""

from typing import Any

from ..core import get_logger
from ..infra import FirestoreService
from .models import (
    CONTENT_OPTIONS_COLLECTION,
    TOPIC_CANDIDATES_COLLECTION,
    TOPIC_SCORES_COLLECTION,
    ContentOption,
    TopicCandidate,
    TopicScore,
)

logger = get_logger(__name__)


class ReviewService:
    """Service for fetching reviewable data with joins."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize review service."""
        self.firestore = firestore or FirestoreService()
        logger.info("ReviewService initialized")

    async def fetch_topic_review_batch(
        self, limit: int = 20, status: str = "pending"
    ) -> list[dict[str, Any]]:
        """
        Fetch topics with their latest scores for review.

        Returns enriched topic data with scores.
        """
        try:
            # Fetch topics filtered by status
            topics = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=[("status", "==", status)] if status else None,
                limit=limit,
                order_by="created_at",
                order_direction="DESCENDING",
            )

            if not topics:
                return []

            # Fetch latest scores for these topics
            topic_ids = [t["id"] for t in topics]
            scores = await self._fetch_latest_scores(topic_ids)

            # Join topics with scores
            result = []
            for topic_data in topics:
                topic = TopicCandidate.from_firestore_dict(topic_data, topic_data["id"])
                topic_score = scores.get(topic.id)

                # If no score, create default
                if not topic_score:
                    topic_score = TopicScore(
                        topic_id=topic.id,
                        score=0.0,
                        components={
                            "recency": 0.0,
                            "velocity": 0.0,
                            "audience_fit": 0.0,
                            "integrity_penalty": 0.0,
                        },
                        run_id="default",
                    )

                result.append(
                    {
                        "topic": topic.model_dump(),
                        "score": topic_score.model_dump(),
                        "status": topic.status,
                    }
                )

            # Sort by score descending
            result.sort(key=lambda x: float(x["score"].get("score", 0.0)), reverse=True)

            # Add rank
            for i, item in enumerate(result, 1):
                item["rank"] = i

            logger.info(f"Fetched {len(result)} topics for review (status: {status})")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch topic review batch: {e}")
            raise

    async def _fetch_latest_scores(self, topic_ids: list[str]) -> dict[str, TopicScore]:
        """Fetch latest score for each topic."""
        try:
            scores_dict: dict[str, TopicScore] = {}

            # Fetch all scores for these topics
            # Note: Firestore "in" queries are limited to 10 items, so we batch if needed
            all_scores = []
            if topic_ids:
                # Batch into groups of 10 for "in" query
                for i in range(0, len(topic_ids), 10):
                    batch_ids = topic_ids[i : i + 10]
                    batch_scores = await self.firestore.query_collection(
                        TOPIC_SCORES_COLLECTION,
                        filters=[("topic_id", "in", batch_ids)],
                        order_by="created_at",
                        order_direction="DESCENDING",
                    )
                    all_scores.extend(batch_scores)

            # Group by topic_id and keep only latest
            seen_topics: set[str] = set()
            for score_data in all_scores:
                topic_id = score_data.get("topic_id")
                if topic_id and topic_id not in seen_topics:
                    score = TopicScore.from_firestore_dict(score_data)
                    scores_dict[topic_id] = score
                    seen_topics.add(topic_id)

            return scores_dict
        except Exception as e:
            logger.error(f"Failed to fetch latest scores: {e}")
            return {}

    async def fetch_topics_with_options(
        self, topic_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch approved topics with their content options.

        Groups options by type (hooks vs scripts).
        """
        try:
            # Build filters
            filters = []
            if topic_id:
                filters.append(("id", "==", topic_id))
            if status:
                # For options, we check if topic has options ready
                # This is a simplified version - in practice might need different logic
                filters.append(("status", "==", "approved"))

            # Fetch approved topics
            topics = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=filters if filters else None,
                limit=50,
            )

            if not topics:
                return []

            topic_ids = [t["id"] for t in topics]

            # Fetch all content options for these topics
            # Batch into groups of 10 for "in" query
            options = []
            if topic_ids:
                for i in range(0, len(topic_ids), 10):
                    batch_ids = topic_ids[i : i + 10]
                    batch_options = await self.firestore.query_collection(
                        CONTENT_OPTIONS_COLLECTION,
                        filters=[("topic_id", "in", batch_ids)],
                    )
                    options.extend(batch_options)

            # Group options by topic_id and type
            options_by_topic: dict[str, dict[str, list[ContentOption]]] = {}
            for option_data in options:
                option = ContentOption.from_firestore_dict(option_data, option_data.get("id"))
                if option.topic_id not in options_by_topic:
                    options_by_topic[option.topic_id] = {"hooks": [], "scripts": []}

                if option.option_type == "short_hook":
                    options_by_topic[option.topic_id]["hooks"].append(option)
                elif option.option_type == "short_script":
                    options_by_topic[option.topic_id]["scripts"].append(option)

            # Build result
            result = []
            for topic_data in topics:
                topic = TopicCandidate.from_firestore_dict(topic_data, topic_data["id"])
                topic_options = options_by_topic.get(topic.id, {"hooks": [], "scripts": []})

                # Determine status
                has_options = len(topic_options["hooks"]) > 0 or len(topic_options["scripts"]) > 0
                topic_status = "options-ready" if has_options else "pending"

                result.append(
                    {
                        "topic": topic.model_dump(),
                        "hooks": [opt.model_dump() for opt in topic_options["hooks"]],
                        "scripts": [opt.model_dump() for opt in topic_options["scripts"]],
                        "status": topic_status,
                    }
                )

            logger.info(f"Fetched {len(result)} topics with options")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch topics with options: {e}")
            raise

    async def fetch_flagged_items(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Fetch items flagged for integrity review.

        Items with low integrity scores or explicit needs_review flag.
        """
        try:
            # Fetch topics with low integrity scores
            # Fetch pending topics first, then approved
            pending_topics = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=[("status", "==", "pending")],
                limit=limit * 2,
            )
            approved_topics = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=[("status", "==", "approved")],
                limit=limit * 2,
            )
            topics = pending_topics + approved_topics

            if not topics:
                return []

            topic_ids = [t["id"] for t in topics]
            scores = await self._fetch_latest_scores(topic_ids)

            result = []
            for topic_data in topics:
                topic = TopicCandidate.from_firestore_dict(topic_data, topic_data["id"])
                score = scores.get(topic.id)

                if not score:
                    continue

                # Check integrity penalty threshold
                integrity_penalty = score.components.get("integrity_penalty", 0.0)
                if integrity_penalty >= -0.15:  # Not flagged enough
                    continue

                # Determine risk level
                if integrity_penalty < -0.3:
                    risk_level = "high"
                elif integrity_penalty < -0.2:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                result.append(
                    {
                        "topic_id": topic.id,
                        "topic": topic.model_dump(),
                        "risk_level": risk_level,
                        "reason": f"Low integrity score: {integrity_penalty:.2f}",
                        "suggested_reframes": [],  # Would come from LLM analysis
                        "integrity_score": integrity_penalty,
                    }
                )

            logger.info(f"Fetched {len(result)} flagged items")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch flagged items: {e}")
            raise

    async def update_topic_status(
        self, topic_id: str, new_status: str, transaction: Any | None = None
    ) -> None:
        """
        Update topic status.

        If transaction provided, uses it for atomic update.
        """
        try:
            topic_ref = self.firestore.client.collection(TOPIC_CANDIDATES_COLLECTION).document(
                topic_id
            )
            update_data = {"status": new_status}

            if transaction:
                transaction.update(topic_ref, update_data)
            else:
                await self.firestore.set_document(
                    TOPIC_CANDIDATES_COLLECTION, topic_id, update_data
                )

            logger.info(f"Updated topic {topic_id} status to {new_status}")
        except Exception as e:
            logger.error(f"Failed to update topic status: {e}")
            raise
