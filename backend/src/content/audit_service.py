"""
Audit log service for tracking decisions and creating observable audit trail.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from ..core import get_logger
from ..infra import FirestoreService
from .models import AUDIT_EVENTS_COLLECTION, AuditEvent

logger = get_logger(__name__)


class AuditService:
    """Service for logging audit events and decisions."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize audit service."""
        self.firestore = firestore or FirestoreService()
        logger.info("AuditService initialized")

    async def log_topic_selection_decision(
        self,
        *,
        candidate_ids: list[str],
        ranked_ids: list[str],
        selected_ids: list[str],
        rejected_ids: list[str],
        scoring_components: dict[str, dict[str, float]],
        actor: str | None = None,
        reason: str | None = None,
    ) -> str:
        """
        Log a topic selection decision.

        Args:
            candidate_ids: All candidate IDs considered
            ranked_ids: System-ranked order
            selected_ids: IDs approved by human
            rejected_ids: IDs rejected by human
            scoring_components: Score breakdown per topic
            actor: Human actor (defaults to "system")
            reason: Optional reason for rejection

        Returns:
            Audit event ID
        """
        try:
            event_id = str(uuid.uuid4())
            actor_name = actor or "system"

            system_decision = {
                "ranked_ids": ranked_ids,
                "scoring_components": scoring_components,
            }

            human_action = {
                "selected_ids": selected_ids,
                "rejected_ids": rejected_ids,
                "reason": reason,
            }

            audit_event = AuditEvent(
                id=event_id,
                stage="topic_selection",
                topic_id=None,  # Multiple topics in this event
                content_id=None,
                system_decision=system_decision,
                human_action=human_action,
                actor=actor_name,
                created_at=datetime.now(timezone.utc),
            )

            await self.firestore.set_document(
                AUDIT_EVENTS_COLLECTION, event_id, audit_event.to_firestore_dict()
            )

            logger.info(
                f"Logged topic selection decision: {len(selected_ids)} approved, {len(rejected_ids)} rejected"
            )
            return event_id
        except Exception as e:
            logger.error(f"Failed to log topic selection decision: {e}")
            raise

    async def log_option_selection_decision(
        self,
        *,
        topic_id: str,
        option_ids: list[str],
        selected_option_id: str,
        rejected_option_ids: list[str],
        reason_code: str | None,
        notes: str | None,
        actor: str | None = None,
    ) -> str:
        """
        Log an option selection decision.

        Args:
            topic_id: Topic ID
            option_ids: All option IDs considered
            selected_option_id: Selected option ID
            rejected_option_ids: Rejected option IDs
            reason_code: Reason code if edited
            notes: Optional notes
            actor: Human actor

        Returns:
            Audit event ID
        """
        try:
            event_id = str(uuid.uuid4())
            actor_name = actor or "system"

            system_decision = {
                "option_ids": option_ids,
                "recommended_option_id": option_ids[0] if option_ids else None,
            }

            human_action = {
                "selected_option_id": selected_option_id,
                "rejected_option_ids": rejected_option_ids,
                "reason_code": reason_code,
                "notes": notes,
            }

            audit_event = AuditEvent(
                id=event_id,
                stage="option_selection",
                topic_id=topic_id,
                content_id=None,
                system_decision=system_decision,
                human_action=human_action,
                actor=actor_name,
                created_at=datetime.now(timezone.utc),
            )

            await self.firestore.set_document(
                AUDIT_EVENTS_COLLECTION, event_id, audit_event.to_firestore_dict()
            )

            logger.info(f"Logged option selection decision for topic {topic_id}")
            return event_id
        except Exception as e:
            logger.error(f"Failed to log option selection decision: {e}")
            raise

    async def log_ethics_review(
        self,
        *,
        topic_id: str,
        decision: Literal["publish", "reframe", "skip"],
        notes: str | None,
        actor: str | None = None,
    ) -> str:
        """
        Log an ethics review decision.

        Args:
            topic_id: Topic ID
            decision: Decision made (publish, reframe, skip)
            notes: Optional notes
            actor: Human actor

        Returns:
            Audit event ID
        """
        try:
            event_id = str(uuid.uuid4())
            actor_name = actor or "system"

            system_decision = {
                "flagged": True,
                "recommendation": "review_required",
            }

            human_action = {
                "decision": decision,
                "notes": notes,
            }

            audit_event = AuditEvent(
                id=event_id,
                stage="ethics_review",
                topic_id=topic_id,
                content_id=None,
                system_decision=system_decision,
                human_action=human_action,
                actor=actor_name,
                created_at=datetime.now(timezone.utc),
            )

            await self.firestore.set_document(
                AUDIT_EVENTS_COLLECTION, event_id, audit_event.to_firestore_dict()
            )

            logger.info(f"Logged ethics review decision for topic {topic_id}: {decision}")
            return event_id
        except Exception as e:
            logger.error(f"Failed to log ethics review: {e}")
            raise

    async def list_recent_events(
        self,
        limit: int = 50,
        stage: str | None = None,
        topic_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AuditEvent]:
        """
        List recent audit events with optional filters.

        Args:
            limit: Maximum number of events
            stage: Filter by stage
            topic_id: Filter by topic ID
            date_from: Start date filter
            date_to: End date filter

        Returns:
            List of audit events
        """
        try:
            filters = []
            if stage:
                filters.append(("stage", "==", stage))
            if topic_id:
                filters.append(("topic_id", "==", topic_id))
            if date_from:
                filters.append(("created_at", ">=", date_from.isoformat()))
            if date_to:
                filters.append(("created_at", "<=", date_to.isoformat()))

            events_data = await self.firestore.query_collection(
                AUDIT_EVENTS_COLLECTION,
                filters=filters if filters else None,
                limit=limit,
                order_by="created_at",
                order_direction="DESCENDING",
            )

            events = []
            for event_data in events_data:
                try:
                    event = AuditEvent.from_firestore_dict(event_data, event_data.get("id"))
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse audit event {event_data.get('id')}: {e}")
                    continue

            logger.info(f"Fetched {len(events)} audit events")
            return events
        except Exception as e:
            logger.error(f"Failed to list recent events: {e}")
            raise
