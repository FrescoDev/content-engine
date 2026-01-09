"""
Integrity/ethics review workflow for interactive CLI.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel

from ...content.audit_service import AuditService
from ...content.models import TOPIC_CANDIDATES_COLLECTION, TOPIC_SCORES_COLLECTION
from ...core import get_logger
from ...infra import FirestoreService
from ..review_utils import (
    check_terminal_compatibility,
    collect_notes,
    display_progress,
    prompt_action,
    show_summary,
)

console = Console()
logger = get_logger(__name__)

INTEGRITY_REVIEW_THRESHOLD = -0.15


class IntegrityReviewer:
    """Interactive integrity review workflow."""

    def __init__(
        self, firestore: FirestoreService | None = None, audit_service: AuditService | None = None
    ):
        """Initialize integrity reviewer."""
        self.firestore = firestore or FirestoreService()
        self.audit_service = audit_service or AuditService(firestore=self.firestore)
        self.stats = {"published": 0, "reframed": 0, "skipped": 0}

    async def review_integrity(self, limit: int = 20) -> None:
        """Run interactive integrity review session."""
        if not check_terminal_compatibility():
            return

        try:
            # Fetch flagged topics
            console.print("[bold cyan]Loading flagged topics...[/bold cyan]")
            flagged_items = await self._fetch_flagged_items(limit=limit)

            if not flagged_items:
                console.print("[green]No topics flagged for integrity review.[/green]")
                return

            console.print(f"[yellow]Found {len(flagged_items)} flagged topics[/yellow]\n")

            # Review loop
            for idx, item in enumerate(flagged_items, 1):
                display_progress(idx, len(flagged_items), self.stats)
                await self._review_item(item)

            # Show summary
            show_summary(self.stats)
            console.print("\n[green]Integrity review complete![/green]")

        except Exception as e:
            logger.error(f"Integrity review failed: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")

    async def _fetch_flagged_items(self, limit: int) -> list[dict[str, Any]]:
        """Fetch topics flagged for integrity review."""
        try:
            # Fetch pending and approved topics
            topics_data = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=[("status", "in", ["pending", "approved"])],
                limit=limit * 2,
            )

            if not topics_data:
                return []

            topic_ids = [t["id"] for t in topics_data]

            # Fetch scores in batches
            scores_by_topic: dict[str, dict[str, Any]] = {}
            batch_size = 10
            for i in range(0, len(topic_ids), batch_size):
                batch = topic_ids[i : i + batch_size]
                try:
                    scores_data = await self.firestore.query_collection(
                        TOPIC_SCORES_COLLECTION,
                        filters=[("topic_id", "in", batch)],
                        order_by="created_at",
                        order_direction="DESCENDING",
                    )

                    seen = set()
                    for score_data in scores_data:
                        topic_id = score_data.get("topic_id")
                        if topic_id and topic_id not in seen:
                            scores_by_topic[topic_id] = score_data
                            seen.add(topic_id)
                except Exception as e:
                    logger.warning(f"Failed to fetch scores for batch: {e}")
                    continue

            # Filter by integrity threshold
            flagged = []
            for topic in topics_data:
                topic_id = topic["id"]
                score = scores_by_topic.get(topic_id)
                if score:
                    integrity_penalty = score.get("components", {}).get("integrity_penalty", 0.0)
                    if integrity_penalty < INTEGRITY_REVIEW_THRESHOLD:
                        # Determine risk level
                        if integrity_penalty < -0.3:
                            risk_level = "high"
                        elif integrity_penalty < -0.2:
                            risk_level = "medium"
                        else:
                            risk_level = "low"

                        flagged.append(
                            {
                                "topic": topic,
                                "score": score,
                                "integrity_penalty": integrity_penalty,
                                "risk_level": risk_level,
                            }
                        )

                        if len(flagged) >= limit:
                            break

            return flagged
        except Exception as e:
            logger.error(f"Failed to fetch flagged items: {e}")
            raise

    async def _review_item(self, item: dict[str, Any]) -> None:
        """Review a flagged item."""
        topic = item["topic"]
        topic_id = topic["id"]
        topic_title = topic.get("title", "Untitled")
        risk_level = item["risk_level"]
        integrity_penalty = item["integrity_penalty"]

        # Display item
        risk_colors = {"high": "red", "medium": "yellow", "low": "green"}
        risk_color = risk_colors.get(risk_level, "white")
        risk_symbols = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        risk_symbol = risk_symbols.get(risk_level, "⚪")

        panel_content = [
            f"{risk_symbol} [bold]Risk Level:[/bold] [{risk_color}]{risk_level.upper()}[/{risk_color}]",
            f"[bold]Topic:[/bold] {topic_title}",
            f"[bold]Integrity Penalty:[/bold] {integrity_penalty:.2f}",
            f"[bold]Reason:[/bold] Low integrity confidence score",
            "",
            "[bold]Suggested reframes:[/bold]",
            "  • What this tells us about industry trends",
            "  • How platforms shape narratives",
        ]

        console.print("\n")
        console.print(
            Panel("\n".join(panel_content), title="Integrity Review", border_style=risk_color)
        )

        # Get decision
        try:
            action = prompt_action(
                "\nAction: [P]ublish as-is / [R]eframe / [S]kip: ",
                ["p", "P", "r", "R", "s", "S"],
            )
        except (EOFError, KeyboardInterrupt):
            raise

        action_lower = action.lower()

        if action_lower == "s":
            self.stats["skipped"] += 1
            return

        notes = collect_notes()

        # Process decision
        try:
            if action_lower == "p":
                # Publish as-is (no change to topic status)
                await self.audit_service.log_ethics_review(
                    topic_id=topic_id, decision="publish", notes=notes, actor="cli-user"
                )
                self.stats["published"] += 1
                console.print(f"[green]✓ Published as-is: {topic_title}[/green]")
            elif action_lower == "r":
                # Reframe - store in metadata
                topic_data = await self.firestore.get_document(
                    TOPIC_CANDIDATES_COLLECTION, topic_id
                )
                if topic_data:
                    metadata = topic_data.get("metadata", {})
                    if not isinstance(metadata, dict):
                        metadata = {}
                    metadata["needs_reframe"] = True
                    metadata["reframe_requested_at"] = str(topic_data.get("created_at", ""))
                    topic_data["metadata"] = metadata
                    await self.firestore.set_document(
                        TOPIC_CANDIDATES_COLLECTION, topic_id, topic_data
                    )

                await self.audit_service.log_ethics_review(
                    topic_id=topic_id, decision="reframe", notes=notes, actor="cli-user"
                )
                self.stats["reframed"] += 1
                console.print(f"[green]✓ Reframe requested: {topic_title}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to process decision: {e}[/red]")
            logger.error(f"Failed to process integrity decision: {e}")
