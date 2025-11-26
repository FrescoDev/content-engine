"""
Topic scoring job.

Calculates engagement scores for topics and saves them to Firestore.
"""

import uuid
from datetime import datetime, timedelta, timezone

from ..content.models import (
    TOPIC_CANDIDATES_COLLECTION,
    TOPIC_SCORES_COLLECTION,
    TopicCandidate,
    TopicScore,
)
from ..content.scoring_service import ScoringService
from ..core import get_logger
from ..infra import FirestoreService
from .job_tracker import track_job_run

logger = get_logger(__name__)


class TopicScoringJob:
    """Job for scoring topics."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        scoring_service: ScoringService | None = None,
    ):
        """
        Initialize scoring job.

        Args:
            firestore: Firestore service instance
            scoring_service: Scoring service instance
        """
        self.firestore = firestore or FirestoreService()
        self.scoring_service = scoring_service or ScoringService()
        logger.debug("TopicScoringJob initialized")

    async def fetch_topics_to_score(
        self,
        limit: int = 100,
        min_age_hours: int | None = None,
        status: str = "pending",
    ) -> list[TopicCandidate]:
        """
        Fetch topics that need scoring.

        Args:
            limit: Maximum number of topics to fetch
            min_age_hours: Minimum age in hours (to avoid scoring topics immediately after ingestion)
            status: Topic status filter (default: "pending")

        Returns:
            List of TopicCandidate objects
        """
        try:
            # Fetch topics filtered by status
            filters = [("status", "==", status)]

            # If min_age_hours specified, filter by created_at
            # Note: Firestore comparison works with ISO strings, but for safety we'll
            # filter in memory if the query doesn't work as expected
            if min_age_hours:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=min_age_hours)
                # Use ISO string - Firestore should handle this correctly
                filters.append(("created_at", "<=", cutoff_time.isoformat()))

            topics_data = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=filters,
                limit=limit * 2,  # Fetch more to account for filtering
                order_by="created_at",
                order_direction="DESCENDING",
            )

            # Convert to TopicCandidate objects
            topics = [
                TopicCandidate.from_firestore_dict(topic_data, topic_data.get("id"))
                for topic_data in topics_data
            ]

            # For MVP, score all fetched topics (can optimize later to check for existing scores)
            # This avoids Firestore index requirements and ensures all topics get scored
            topics_to_score = topics[:limit]

            logger.info(
                f"Found {len(topics_to_score)} topics to score (from {len(topics)} fetched)"
            )
            return topics_to_score

        except Exception as e:
            logger.error(f"Failed to fetch topics to score: {e}", exc_info=True)
            raise

    async def score_topics(self, topics: list[TopicCandidate]) -> list[TopicScore]:
        """
        Calculate scores for a list of topics.

        Args:
            topics: List of TopicCandidate objects

        Returns:
            List of TopicScore objects
        """
        if not topics:
            return []

        run_id = str(uuid.uuid4())
        logger.info(f"Scoring {len(topics)} topics (run_id: {run_id})")

        # Score all topics (pass all_topics for percentile calculation)
        scores = []
        failures = []
        total_cost = 0.0

        # Check if LLM scoring is enabled
        from ..core import get_settings

        settings = get_settings()
        use_llm = settings.enable_llm_scoring

        for topic in topics:
            try:
                # Calculate score (use async version if LLM enabled)
                if use_llm:
                    # Estimate cost before scoring (rough estimate: 2 LLM calls per topic)
                    # Average cost per topic: ~$0.001-0.002 (very rough estimate)
                    estimated_cost_per_topic = 0.002
                    estimated_total = total_cost + (
                        estimated_cost_per_topic * (len(topics) - len(scores))
                    )

                    # Check cost limit BEFORE scoring (fail fast)
                    if estimated_total > settings.max_llm_cost_per_run:
                        logger.warning(
                            f"Estimated cost ${estimated_total:.4f} exceeds limit ${settings.max_llm_cost_per_run:.2f}. "
                            f"Stopping scoring early to prevent runaway costs. "
                            f"Scored {len(scores)}/{len(topics)} topics so far."
                        )
                        break  # Stop scoring, but save what we have

                    score_result = await self.scoring_service.score_topic_async(
                        topic, all_topics=topics, use_llm=True
                    )
                    # Track costs
                    cost_info = score_result.get("cost_info", {})
                    topic_cost = cost_info.get("total_cost_usd", 0.0)
                    total_cost += topic_cost

                    # Double-check cost limit after actual cost (safety check)
                    if total_cost > settings.max_llm_cost_per_run:
                        logger.error(
                            f"Cost limit exceeded: ${total_cost:.4f} > ${settings.max_llm_cost_per_run:.2f}. "
                            f"Stopping scoring to prevent runaway costs. "
                            f"Scored {len(scores)}/{len(topics)} topics so far."
                        )
                        break  # Stop scoring, but save what we have
                else:
                    score_result = self.scoring_service.score_topic(topic, all_topics=topics)

                # Validate score_result structure
                if not isinstance(score_result, dict):
                    raise ValueError(f"Invalid score_result type: {type(score_result)}")
                if "score" not in score_result or "components" not in score_result:
                    raise ValueError("Invalid score_result structure: missing required fields")

                # Validate components
                components = score_result.get("components", {})
                required_components = ["recency", "velocity", "audience_fit", "integrity_penalty"]
                for comp in required_components:
                    if comp not in components:
                        logger.warning(
                            f"Missing component {comp} in score_result, defaulting to 0.0"
                        )
                        components[comp] = 0.0

                # Validate score is numeric and in valid range
                score_value = score_result.get("score", 0.0)
                if not isinstance(score_value, (int, float)):
                    raise ValueError(f"Invalid score type: {type(score_value)}")
                if not (0.0 <= score_value <= 1.0):
                    logger.warning(f"Score {score_value} out of range [0,1], clamping")
                    score_value = max(0.0, min(1.0, score_value))

                # Create TopicScore object
                topic_score = TopicScore(
                    topic_id=topic.id,
                    score=float(score_value),
                    components={k: float(v) for k, v in components.items()},
                    reasoning=score_result.get("reasoning", {}),
                    weights=score_result.get("weights", {}),
                    run_id=run_id,
                    metadata={
                        "scored_at": datetime.now(timezone.utc).isoformat(),
                        "topic_title": (
                            topic.title[:100] if topic.title else ""
                        ),  # Store title for debugging
                        "llm_used": use_llm,
                        "cost_usd": (
                            score_result.get("cost_info", {}).get("total_cost_usd", 0.0)
                            if use_llm
                            else 0.0
                        ),
                    },
                )

                scores.append(topic_score)
                logger.debug(f"Scored topic {topic.id}: {topic_score.score:.3f}")

            except Exception as e:
                logger.error(f"Failed to score topic {topic.id}: {e}", exc_info=True)
                failures.append({"topic_id": topic.id, "error": str(e)})
                continue

        logger.info(
            f"Successfully scored {len(scores)}/{len(topics)} topics " f"({len(failures)} failures)"
        )
        if use_llm:
            logger.info(f"Total LLM cost for this batch: ${total_cost:.4f}")
        if failures:
            logger.warning(f"Failed topics: {[f['topic_id'] for f in failures]}")
        return scores

    async def save_scores(self, scores: list[TopicScore]) -> int:
        """
        Save scores to Firestore.

        Args:
            scores: List of TopicScore objects

        Returns:
            Number of scores saved
        """
        saved_count = 0

        for score in scores:
            try:
                # Use topic_id as document ID (one score per topic, latest overwrites)
                # Actually, we want to keep history, so use UUID as doc ID
                score_id = str(uuid.uuid4())

                await self.firestore.set_document(
                    TOPIC_SCORES_COLLECTION,
                    score_id,
                    score.to_firestore_dict(),
                )
                saved_count += 1

            except Exception as e:
                logger.error(f"Failed to save score for topic {score.topic_id}: {e}")
                continue

        logger.info(f"Saved {saved_count}/{len(scores)} scores to Firestore")
        return saved_count

    async def run(
        self,
        limit: int = 100,
        min_age_hours: int = 0,
        status: str = "pending",
    ) -> dict[str, int]:
        """
        Run the scoring job.

        Args:
            limit: Maximum number of topics to score
            min_age_hours: Minimum age in hours before scoring (default: 0 = score immediately)
            status: Topic status filter (default: "pending")

        Returns:
            Dictionary with metrics (topics_scored, scores_saved)
        """
        # Fetch topics to score
        topics = await self.fetch_topics_to_score(
            limit=limit,
            min_age_hours=min_age_hours,
            status=status,
        )

        if not topics:
            logger.info("No topics to score")
            return {"topics_scored": 0, "scores_saved": 0}

        # Score topics
        scores = await self.score_topics(topics)

        # Save scores
        saved_count = await self.save_scores(scores)

        # Calculate metrics
        failed_count = len(topics) - len(scores)

        # Calculate total cost from saved scores
        total_cost = sum(
            s.metadata.get("cost_usd", 0.0) for s in scores if s.metadata.get("llm_used", False)
        )

        return {
            "topics_scored": len(scores),
            "scores_saved": saved_count,
            "topics_failed": failed_count,
            "topics_total": len(topics),
            "total_cost_usd": total_cost,
        }


async def run_topic_scoring(
    limit: int = 100,
    min_age_hours: int = 0,
    status: str = "pending",
) -> None:
    """
    Run topic scoring job with tracking.

    Args:
        limit: Maximum number of topics to score
        min_age_hours: Minimum age in hours before scoring
        status: Topic status filter
    """
    async with track_job_run(
        "topic_scoring", metadata={"limit": limit, "topic_status_filter": status}
    ) as job_run:
        job = TopicScoringJob()

        metrics = await job.run(
            limit=limit,
            min_age_hours=min_age_hours,
            status=status,
        )

        # Update job run metrics
        # Note: JobRun has specific fields, but we'll store in metadata for now
        # Future: Add topics_scored, scores_saved fields to JobRun model
        job_run.metadata.update(metrics)

        logger.info(
            f"Topic scoring job completed: "
            f"scored {metrics['topics_scored']} topics, "
            f"saved {metrics['scores_saved']} scores"
        )
