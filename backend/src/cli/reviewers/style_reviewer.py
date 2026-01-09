"""
Style profile curation workflow for interactive CLI.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel

from ...content.models import STYLE_PROFILES_COLLECTION
from ...content.style_curation_service import StyleCurationService
from ...core import get_logger
from ...infra import FirestoreService
from ..review_utils import (
    check_terminal_compatibility,
    display_progress,
    prompt_action,
    show_summary,
)

console = Console()
logger = get_logger(__name__)


class StyleReviewer:
    """Interactive style profile curation workflow."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize style reviewer."""
        self.firestore = firestore or FirestoreService()
        self.curation_service = StyleCurationService()
        self.stats = {"approved": 0, "rejected": 0, "skipped": 0}

    async def review_styles(self, limit: int = 20, status: str = "pending") -> None:
        """Run interactive style profile review session."""
        if not check_terminal_compatibility():
            return

        try:
            # Fetch style profiles
            console.print("[bold cyan]Loading style profiles...[/bold cyan]")
            profiles = await self._fetch_profiles(limit=limit, status=status)

            if not profiles:
                console.print(f"[yellow]No {status} style profiles found.[/yellow]")
                return

            console.print(f"[green]Found {len(profiles)} style profiles[/green]\n")

            # Review loop
            for idx, profile in enumerate(profiles, 1):
                display_progress(idx, len(profiles), self.stats)
                await self._review_profile(profile)

            # Show summary
            show_summary(self.stats)
            console.print("\n[green]Style review complete![/green]")

        except Exception as e:
            logger.error(f"Style review failed: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")

    async def _fetch_profiles(self, limit: int, status: str) -> list[dict[str, Any]]:
        """Fetch style profiles."""
        try:
            filters = []
            if status != "all":
                filters.append(("status", "==", status))

            # Try with order_by first, fallback if index missing
            try:
                profiles_data = await self.firestore.query_collection(
                    STYLE_PROFILES_COLLECTION,
                    filters=filters if filters else None,
                    limit=limit,
                    order_by="created_at",
                    order_direction="DESCENDING",
                )
            except Exception as e:
                # Fallback: fetch without ordering, sort in memory
                logger.warning(f"Index error, using fallback: {e}")
                profiles_data = await self.firestore.query_collection(
                    STYLE_PROFILES_COLLECTION,
                    filters=filters if filters else None,
                    limit=limit,
                )
                # Sort by created_at descending
                profiles_data.sort(
                    key=lambda x: x.get("created_at", ""),
                    reverse=True,
                )

            return profiles_data
        except Exception as e:
            logger.error(f"Failed to fetch profiles: {e}")
            raise

    async def _review_profile(self, profile: dict[str, Any]) -> None:
        """Review a style profile."""
        profile_id = profile.get("id", "unknown")
        source_name = profile.get("source_name", "unknown")
        tone = profile.get("tone", "unknown")
        example_phrases = profile.get("example_phrases", [])
        literary_devices = profile.get("literary_devices", [])
        cultural_markers = profile.get("cultural_markers", [])

        # Display profile
        panel_content = [
            f"[bold]Source:[/bold] {source_name}",
            f"[bold]Tone:[/bold] {tone}",
        ]

        if literary_devices:
            panel_content.append(
                f"[bold]Literary Devices:[/bold] {', '.join(literary_devices[:5])}"
            )

        if cultural_markers:
            panel_content.append(
                f"[bold]Cultural Markers:[/bold] {', '.join(cultural_markers[:5])}"
            )

        if example_phrases:
            panel_content.append("\n[bold]Example Phrases:[/bold]")
            for phrase in example_phrases[:3]:
                panel_content.append(f"  • {phrase[:80]}...")

        console.print("\n")
        console.print(Panel("\n".join(panel_content), title="Style Profile", border_style="blue"))

        # Get action
        try:
            action = prompt_action(
                "\nAction: [A]pprove / [R]eject / [T]est / [S]kip: ",
                ["a", "A", "r", "R", "t", "T", "s", "S"],
            )
        except (EOFError, KeyboardInterrupt):
            raise

        action_lower = action.lower()

        if action_lower == "s":
            self.stats["skipped"] += 1
            return

        # Process action
        try:
            if action_lower == "a":
                await self.curation_service.approve_profile(profile_id, "cli-user", None)
                self.stats["approved"] += 1
                console.print(f"[green]✓ Approved profile: {source_name}[/green]")
            elif action_lower == "r":
                reason = console.input("Rejection reason: ").strip()
                if not reason:
                    reason = "Not specified"
                await self.curation_service.reject_profile(profile_id, "cli-user", reason)
                self.stats["rejected"] += 1
                console.print(f"[green]✓ Rejected profile: {source_name}[/green]")
            elif action_lower == "t":
                console.print("[yellow]Test generation not yet implemented[/yellow]")
                # TODO: Implement test generation
        except Exception as e:
            console.print(f"[red]✗ Failed to process: {e}[/red]")
            logger.error(f"Failed to process style profile: {e}")
