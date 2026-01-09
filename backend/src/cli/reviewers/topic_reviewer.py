"""
Topic review workflow for interactive CLI.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from rich.console import Console

from ...content.audit_service import AuditService
from ...content.models import (
    AUDIT_EVENTS_COLLECTION,
    TOPIC_CANDIDATES_COLLECTION,
    TOPIC_SCORES_COLLECTION,
)
from ...core import get_logger
from ...infra import FirestoreService
from ..review_utils import (
    check_terminal_compatibility,
    collect_notes,
    collect_reason_code,
    display_detail_panel,
    display_progress,
    display_topic_table,
    load_session_state,
    prompt_action,
    save_session_state,
    show_summary,
)

console = Console()
logger = get_logger(__name__)

REASON_CODES = ["too_generic", "not_on_brand", "speculative", "duplicate", "ethics"]


class TopicReviewer:
    """Interactive topic review workflow."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        audit_service: AuditService | None = None,
        resume_file: str | None = None,
    ):
        """Initialize topic reviewer."""
        self.firestore = firestore or FirestoreService()
        self.audit_service = audit_service or AuditService(firestore=self.firestore)
        self.resume_file = resume_file
        self.stats = {"approved": 0, "rejected": 0, "deferred": 0, "skipped": 0}
        self.processed_ids: set[str] = set()
        self.last_action: dict[str, Any] | None = None

    async def review_topics(
        self, limit: int = 50, min_score: float | None = None, status: str = "pending"
    ) -> None:
        """Run interactive topic review session."""
        if not check_terminal_compatibility():
            return

        # Load session state if resuming
        if self.resume_file:
            session_data = load_session_state(self.resume_file)
            if session_data:
                self.processed_ids = set(session_data.get("processed_ids", []))
                self.stats = session_data.get("stats", self.stats)
                console.print(f"[green]Resuming session from {self.resume_file}[/green]")

        try:
            # Fetch topics
            console.print("[bold cyan]Loading topics...[/bold cyan]")
            topics = await self._fetch_topics(limit=limit, status=status, min_score=min_score)

            if not topics:
                console.print("[yellow]No pending topics found.[/yellow]")
                console.print("Run `ingest-topics` and `score-topics` first.")
                return

            # Fetch scores
            scores = await self._fetch_scores([t["id"] for t in topics])

            # Filter out already processed
            topics = [t for t in topics if t["id"] not in self.processed_ids]

            # Filter by min_score if specified
            if min_score is not None:
                filtered_topics = []
                for topic in topics:
                    topic_id = topic["id"]
                    score_data = scores.get(topic_id)
                    if score_data:
                        topic_score = score_data.get("score", 0.0)
                        if topic_score >= min_score:
                            filtered_topics.append(topic)
                    elif min_score <= 0.0:
                        # Include topics without scores if min_score is 0 or negative
                        filtered_topics.append(topic)
                topics = filtered_topics

            if not topics:
                if min_score is not None:
                    console.print(f"[yellow]No topics found with score >= {min_score}.[/yellow]")
                else:
                    console.print("[yellow]All topics already processed.[/yellow]")
                return

            console.print(f"[green]Found {len(topics)} topics to review[/green]\n")

            # Review loop
            page = 1
            per_page = 10
            current_idx = 0

            while current_idx < len(topics):
                # Display current page
                display_topic_table(topics, scores, page=page, per_page=per_page)

                # Show progress
                display_progress(current_idx + 1, len(topics), self.stats)

                # Get user selection
                try:
                    choice = prompt_action(
                        "\nSelect topic [1-10] or [N]ext page / [Q]uit: ",
                        [str(i) for i in range(1, 11)] + ["n", "N", "q", "Q"],
                    )
                except (EOFError, KeyboardInterrupt):
                    await self._handle_interrupt()
                    return

                if choice.lower() == "q":
                    await self._handle_quit()
                    return

                if choice.lower() == "n":
                    page += 1
                    current_idx = min((page - 1) * per_page, len(topics))
                    continue

                # Parse selection
                try:
                    topic_num = int(choice)
                    topic_idx = (page - 1) * per_page + topic_num - 1
                    if topic_idx < 0 or topic_idx >= len(topics):
                        console.print("[red]Invalid selection[/red]")
                        continue
                except ValueError:
                    console.print("[red]Invalid selection[/red]")
                    continue

                topic = topics[topic_idx]
                topic_id = topic["id"]
                score = scores.get(topic_id)

                # Show detail and get decision
                await self._review_topic(topic, score)

                current_idx += 1
                if current_idx % 10 == 0:
                    # Auto-save every 10 items
                    await self._save_session()

            # Show summary
            show_summary(self.stats)
            console.print("\n[green]Review session complete![/green]")

        except Exception as e:
            logger.error(f"Topic review failed: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")
            await self._save_session()

    async def _fetch_topics(
        self, limit: int, status: str, min_score: float | None = None
    ) -> list[dict[str, Any]]:
        """Fetch topics from Firestore."""
        try:
            # Try with order_by first, fallback if index missing
            try:
                topics_data = await self.firestore.query_collection(
                    TOPIC_CANDIDATES_COLLECTION,
                    filters=[("status", "==", status)],
                    limit=limit * 2,  # Fetch more for filtering
                    order_by="created_at",
                    order_direction="DESCENDING",
                )
            except Exception as e:
                # Fallback: fetch without ordering, sort in memory
                logger.warning(f"Index error, using fallback: {e}")
                topics_data = await self.firestore.query_collection(
                    TOPIC_CANDIDATES_COLLECTION,
                    filters=[("status", "==", status)],
                    limit=limit * 2,
                )
                # Sort by created_at descending
                topics_data.sort(
                    key=lambda x: x.get("created_at", ""),
                    reverse=True,
                )

            # Filter out invalid topics
            valid_topics = []
            for topic in topics_data:
                if not topic.get("title"):
                    logger.warning(f"Skipping topic {topic.get('id')}: missing title")
                    continue
                valid_topics.append(topic)

            # Convert datetime strings
            for topic in valid_topics:
                if isinstance(topic.get("created_at"), str):
                    try:
                        topic["created_at"] = datetime.fromisoformat(topic["created_at"])
                    except Exception:
                        pass

            return valid_topics[:limit]
        except Exception as e:
            logger.error(f"Failed to fetch topics: {e}")
            raise

    async def _fetch_scores(self, topic_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch scores for topics."""
        scores_by_topic: dict[str, dict[str, Any]] = {}

        if not topic_ids:
            return scores_by_topic

        # Batch queries (Firestore "in" limit is 10)
        batch_size = 10
        for i in range(0, len(topic_ids), batch_size):
            batch = topic_ids[i : i + batch_size]
            try:
                # Try with order_by first
                try:
                    scores_data = await self.firestore.query_collection(
                        TOPIC_SCORES_COLLECTION,
                        filters=[("topic_id", "in", batch)],
                        order_by="created_at",
                        order_direction="DESCENDING",
                    )
                except Exception:
                    # Fallback: fetch without ordering, sort in memory
                    scores_data = await self.firestore.query_collection(
                        TOPIC_SCORES_COLLECTION,
                        filters=[("topic_id", "in", batch)],
                    )
                    scores_data.sort(
                        key=lambda x: x.get("created_at", ""),
                        reverse=True,
                    )

                # Group by topic_id, keeping latest
                seen = set()
                for score_data in scores_data:
                    topic_id = score_data.get("topic_id")
                    if topic_id and topic_id not in seen:
                        scores_by_topic[topic_id] = score_data
                        seen.add(topic_id)
            except Exception as e:
                logger.warning(f"Failed to fetch scores for batch: {e}")
                continue

        return scores_by_topic

    async def _review_topic(self, topic: dict[str, Any], score: dict[str, Any] | None) -> None:
        """Review a single topic."""
        topic_id = topic["id"]
        topic_title = topic.get("title", "Untitled")

        # Show detail panel
        console.print("\n")
        display_detail_panel(topic, score)

        # Get decision
        try:
            action = prompt_action(
                "\nAction: [A]pprove / [R]eject / [D]efer / [S]kip / [B]ack / [U]ndo: ",
                ["a", "A", "r", "R", "d", "D", "s", "S", "b", "B", "u", "U"],
            )
        except (EOFError, KeyboardInterrupt):
            raise

        action_lower = action.lower()

        if action_lower == "b":
            return  # Go back

        if action_lower == "u":
            await self._undo_last_action()
            return

        if action_lower == "s":
            self.stats["skipped"] += 1
            console.print(f"[dim]Skipped: {topic_title}[/dim]")
            return

        # Process decision
        reason_code = None
        notes = None

        if action_lower == "r":
            reason_code = collect_reason_code()
            notes = collect_notes()
        elif action_lower in ["a", "d"]:
            notes = collect_notes()

        # Update status
        new_status = {"a": "approved", "r": "rejected", "d": "deferred"}[action_lower]

        try:
            await self._update_topic_status(topic_id, new_status, reason_code, notes)
            self.stats[new_status] += 1
            self.processed_ids.add(topic_id)

            # Store for undo
            self.last_action = {
                "topic_id": topic_id,
                "old_status": topic.get("status"),
                "new_status": new_status,
                "action": action_lower,
            }

            console.print(f"[green]✓ {new_status.capitalize()}: {topic_title}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to update topic: {e}[/red]")
            logger.error(f"Failed to update topic {topic_id}: {e}")

    async def _update_topic_status(
        self, topic_id: str, status: str, reason_code: str | None, notes: str | None
    ) -> None:
        """Update topic status and create audit event."""
        # Retry logic for Firestore operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get current topic to check status
                topic_data = await self.firestore.get_document(
                    TOPIC_CANDIDATES_COLLECTION, topic_id
                )
                if not topic_data:
                    raise ValueError(f"Topic {topic_id} not found")

                current_status = topic_data.get("status")
                if current_status != "pending" and status != "deferred":
                    # Check if already processed
                    console.print(
                        f"[yellow]⚠ Topic already {current_status}. Override? [y/N][/yellow]"
                    )
                    override = prompt_action("", ["y", "Y", "n", "N"], default="n")
                    if override.lower() != "y":
                        return

                # Update topic status
                topic_data["status"] = status
                await self.firestore.set_document(TOPIC_CANDIDATES_COLLECTION, topic_id, topic_data)
                break  # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(
                        f"[yellow]⚠ Retrying update... (attempt {attempt + 1}/{max_retries})[/yellow]"
                    )
                    await asyncio.sleep(1.0 * (2**attempt))  # Exponential backoff
                else:
                    raise

        # Create audit event
        try:
            # Fetch score for audit
            scores_data = await self.firestore.query_collection(
                TOPIC_SCORES_COLLECTION,
                filters=[("topic_id", "==", topic_id)],
                order_by="created_at",
                order_direction="DESCENDING",
                limit=1,
            )
            latest_score = scores_data[0] if scores_data else None

            system_decision = {}
            if latest_score:
                system_decision = {
                    "score": latest_score.get("score", 0.0),
                    "recency": latest_score.get("components", {}).get("recency", 0.0),
                    "velocity": latest_score.get("components", {}).get("velocity", 0.0),
                    "audience_fit": latest_score.get("components", {}).get("audience_fit", 0.0),
                    "integrity_penalty": latest_score.get("components", {}).get(
                        "integrity_penalty", 0.0
                    ),
                    "reasoning": latest_score.get("reasoning", {}),
                    "weights": latest_score.get("weights", {}),
                }

            human_action: dict[str, Any] = {
                "selected_ids": [topic_id] if status == "approved" else [],
                "rejected_ids": [topic_id] if status == "rejected" else [],
                "deferred_ids": [topic_id] if status == "deferred" else [],
            }
            if reason_code:
                human_action["reason_code"] = reason_code
            if notes:
                human_action["notes"] = notes

            audit_event = {
                "id": f"audit_{topic_id}_{datetime.now(timezone.utc).isoformat()}",
                "stage": "topic_selection",
                "topic_id": topic_id,
                "content_id": None,
                "system_decision": system_decision,
                "human_action": human_action,
                "actor": "cli-user",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await self.firestore.add_document(AUDIT_EVENTS_COLLECTION, audit_event)
        except Exception as e:
            logger.warning(f"Failed to create audit event: {e}")

    async def _undo_last_action(self) -> None:
        """Undo last action."""
        if not self.last_action:
            console.print("[yellow]No action to undo[/yellow]")
            return

        action = self.last_action
        console.print(
            f"[yellow]Undo: Revert {action['new_status']} of topic {action['topic_id']}? [y/N][/yellow]"
        )
        confirm = prompt_action("", ["y", "Y", "n", "N"], default="n")
        if confirm.lower() != "y":
            return

        try:
            # Revert status
            topic_data = await self.firestore.get_document(
                TOPIC_CANDIDATES_COLLECTION, action["topic_id"]
            )
            if topic_data:
                topic_data["status"] = action["old_status"]
                await self.firestore.set_document(
                    TOPIC_CANDIDATES_COLLECTION, action["topic_id"], topic_data
                )

            # Update stats
            self.stats[action["new_status"]] -= 1
            self.processed_ids.discard(action["topic_id"])
            self.last_action = None

            console.print("[green]✓ Action undone[/green]")
        except Exception as e:
            console.print(f"[red]Failed to undo: {e}[/red]")

    async def _handle_interrupt(self) -> None:
        """Handle Ctrl+C interruption."""
        console.print("\n[yellow]Interrupted by user[/yellow]")
        await self._save_session()

    async def _handle_quit(self) -> None:
        """Handle quit action."""
        await self._save_session()
        console.print("\n[yellow]Session saved. Exiting...[/yellow]")

    async def _save_session(self) -> None:
        """Save session state."""
        session_data = {
            "workflow": "topics",
            "processed_ids": list(self.processed_ids),
            "stats": self.stats,
            "last_action": self.last_action,
        }
        save_session_state(session_data, ".review_session.json")
