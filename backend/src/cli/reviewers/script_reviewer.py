"""
Script/content review workflow for interactive CLI.
"""

import asyncio
from typing import Any

from rich.console import Console
from rich.panel import Panel

from ...content.models import (
    CONTENT_OPTIONS_COLLECTION,
    PUBLISHED_CONTENT_COLLECTION,
    TOPIC_CANDIDATES_COLLECTION,
)
from ...core import get_logger
from ...infra import FirestoreService, OpenAIService
from ..review_utils import (
    check_terminal_compatibility,
    collect_notes,
    display_progress,
    prompt_action,
    save_session_state,
    show_summary,
)

console = Console()
logger = get_logger(__name__)


class ScriptReviewer:
    """Interactive script review workflow."""

    def __init__(
        self, firestore: FirestoreService | None = None, openai_service: OpenAIService | None = None
    ):
        """Initialize script reviewer."""
        self.firestore = firestore or FirestoreService()
        self.openai_service = openai_service or OpenAIService()
        self.stats = {"reviewed": 0, "marked_ready": 0, "flagged_ethics": 0, "skipped": 0}

    async def review_scripts(self, limit: int = 20) -> None:
        """Run interactive script review session."""
        if not check_terminal_compatibility():
            return

        try:
            # Fetch approved topics with content options
            console.print("[bold cyan]Loading scripts...[/bold cyan]")
            topics_with_options = await self._fetch_topics_with_options(limit=limit)

            if not topics_with_options:
                console.print("[yellow]No topics with content options found.[/yellow]")
                console.print("Run content generation first.")
                return

            console.print(f"[green]Found {len(topics_with_options)} topics with scripts[/green]\n")

            # Review loop
            for idx, item in enumerate(topics_with_options, 1):
                topic = item["topic"]
                hooks = item["hooks"]
                scripts = item["scripts"]

                display_progress(idx, len(topics_with_options), self.stats)

                await self._review_script_set(topic, hooks, scripts)

            # Show summary
            show_summary(self.stats)
            console.print("\n[green]Script review complete![/green]")

        except Exception as e:
            logger.error(f"Script review failed: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")

    async def _fetch_topics_with_options(self, limit: int) -> list[dict[str, Any]]:
        """Fetch approved topics with their content options."""
        try:
            # Fetch approved topics
            topics_data = await self.firestore.query_collection(
                TOPIC_CANDIDATES_COLLECTION,
                filters=[("status", "==", "approved")],
                limit=limit,
            )

            if not topics_data:
                return []

            topic_ids = [t["id"] for t in topics_data]

            # Fetch content options in batches
            options_by_topic: dict[str, dict[str, list[dict[str, Any]]]] = {}
            batch_size = 10
            for i in range(0, len(topic_ids), batch_size):
                batch = topic_ids[i : i + batch_size]
                try:
                    options_data = await self.firestore.query_collection(
                        CONTENT_OPTIONS_COLLECTION,
                        filters=[("topic_id", "in", batch)],
                    )

                    for opt in options_data:
                        topic_id = opt.get("topic_id")
                        if not topic_id:
                            continue

                        if topic_id not in options_by_topic:
                            options_by_topic[topic_id] = {"hooks": [], "scripts": []}

                        opt_type = opt.get("option_type")
                        if opt_type == "short_hook":
                            options_by_topic[topic_id]["hooks"].append(opt)
                        elif opt_type == "short_script":
                            options_by_topic[topic_id]["scripts"].append(opt)
                except Exception as e:
                    logger.warning(f"Failed to fetch options for batch: {e}")
                    continue

            # Build result
            result = []
            for topic in topics_data:
                topic_id = topic["id"]
                options = options_by_topic.get(topic_id, {"hooks": [], "scripts": []})
                if options["hooks"] or options["scripts"]:
                    result.append(
                        {
                            "topic": topic,
                            "hooks": options["hooks"],
                            "scripts": options["scripts"],
                        }
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to fetch topics with options: {e}")
            raise

    async def _review_script_set(
        self, topic: dict[str, Any], hooks: list[dict[str, Any]], scripts: list[dict[str, Any]]
    ) -> None:
        """Review hooks and scripts for a topic."""
        topic_id = topic["id"]
        topic_title = topic.get("title", "Untitled")

        # Display topic info
        console.print("\n")
        panel_content = [
            f"[bold]Topic:[/bold] {topic_title}",
            f"[bold]Topic ID:[/bold] {topic_id}",
        ]
        console.print(Panel("\n".join(panel_content), title="Script Review", border_style="blue"))

        # Display hooks
        if hooks:
            console.print("\n[bold]Hooks:[/bold]")
            for i, hook in enumerate(hooks, 1):
                content = hook.get("content", "")
                console.print(f"  [{i}] {content[:100]}...")

        # Display scripts
        if scripts:
            console.print("\n[bold]Scripts:[/bold]")
            for i, script in enumerate(scripts, 1):
                content = script.get("content", "")
                console.print(f"\n[{i}] {content[:200]}...")

        # Get user action
        try:
            action = prompt_action(
                "\nAction: Select hook [1-3] / [E]dit / [R]efine / [M]ark ready / [F]lag ethics / [S]kip: ",
                [str(i) for i in range(1, 4)] + ["e", "E", "r", "R", "m", "M", "f", "F", "s", "S"],
            )
        except (EOFError, KeyboardInterrupt):
            raise

        action_lower = action.lower()

        if action_lower == "s":
            self.stats["skipped"] += 1
            return

        # Process action
        selected_hook_id = None
        selected_script_id = scripts[0]["id"] if scripts else None

        if action_lower.isdigit():
            hook_idx = int(action_lower) - 1
            if 0 <= hook_idx < len(hooks):
                selected_hook_id = hooks[hook_idx]["id"]
            else:
                console.print("[red]Invalid hook selection[/red]")
                return
        elif action_lower == "e":
            if not scripts:
                console.print("[red]No scripts to edit[/red]")
                return
            # Edit script (simplified - just collect notes)
            notes = console.input("Edit notes: ").strip()
            if notes:
                console.print(
                    f"[yellow]Note: Full editing not implemented. Notes: {notes}[/yellow]"
                )
        elif action_lower == "r":
            if not scripts:
                console.print("[red]No scripts to refine[/red]")
                return
            await self._refine_script(scripts[0])
        elif action_lower == "m":
            if not selected_script_id:
                console.print("[red]No script selected[/red]")
                return
            await self._mark_ready(topic_id, selected_hook_id, selected_script_id)
            self.stats["marked_ready"] += 1
        elif action_lower == "f":
            await self._flag_ethics(topic_id)
            self.stats["flagged_ethics"] += 1

        self.stats["reviewed"] += 1

    async def _refine_script(self, script: dict[str, Any] | None) -> None:
        """Refine script using AI."""
        if not script:
            console.print("[red]No script to refine[/red]")
            return

        console.print("\n[bold]Refinement type:[/bold]")
        refinement_type = prompt_action(
            "  [T]ighten / [C]asual / [R]egenerate: ", ["t", "T", "c", "C", "r", "R"]
        )

        type_map = {"t": "tighten", "c": "casual", "r": "regenerate"}
        refine_type = type_map[refinement_type.lower()]

        console.print(f"\n[yellow]Refining script ({refine_type})...[/yellow]")

        try:
            # Use OpenAI service for refinement
            base_content = script.get("content", "")
            prompt = self._build_refinement_prompt(base_content, refine_type)

            refined_content = await self.openai_service.chat(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional script editor."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            refined_content = refined_content.strip()
            if refined_content:
                console.print("[green]✓ Refinement complete[/green]")
                console.print(f"\n[bold]Refined script:[/bold]\n{refined_content[:300]}...")
            else:
                console.print("[red]✗ Refinement failed: Empty response[/red]")
        except Exception as e:
            console.print(f"[red]✗ Refinement failed: {e}[/red]")
            logger.error(f"Script refinement failed: {e}")

    def _build_refinement_prompt(self, content: str, refine_type: str) -> str:
        """Build refinement prompt."""
        base = f"Refine the following script for a short-form video:\n\n{content}\n\n"
        if refine_type == "tighten":
            return (
                base
                + "Make this script more concise and punchy. Remove filler words. Aim for 20-30% shorter."
            )
        elif refine_type == "casual":
            return (
                base
                + "Adjust the tone to be more conversational and casual. Make it sound natural."
            )
        else:  # regenerate
            return (
                base
                + "Regenerate with fresh wording while keeping the same core message and structure."
            )

    async def _mark_ready(self, topic_id: str, hook_id: str | None, script_id: str | None) -> None:
        """Mark content as ready for publication."""
        if not script_id:
            console.print("[red]No script selected[/red]")
            return

        platform = prompt_action(
            "Platform: [Y]outube Short / [T]ikTok: ", ["y", "Y", "t", "T"], default="y"
        )
        platform_map = {"y": "youtube_short", "t": "tiktok"}
        platform_name = platform_map[platform.lower()]

        try:
            published_content = {
                "id": f"pub_{topic_id}_{script_id}",
                "topic_id": topic_id,
                "selected_option_id": script_id,
                "platform": platform_name,
                "status": "draft",
                "needs_ethics_review": False,
                "scheduled_at": None,
                "published_at": None,
                "external_id": None,
            }

            await self.firestore.set_document(
                PUBLISHED_CONTENT_COLLECTION, published_content["id"], published_content
            )
            console.print(f"[green]✓ Marked ready for {platform_name}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to mark ready: {e}[/red]")
            logger.error(f"Failed to mark ready: {e}")

    async def _flag_ethics(self, topic_id: str) -> None:
        """Flag content for ethics review."""
        try:
            # Find published content for this topic
            published_data = await self.firestore.query_collection(
                PUBLISHED_CONTENT_COLLECTION,
                filters=[("topic_id", "==", topic_id)],
                limit=1,
            )

            if published_data:
                pub_id = published_data[0]["id"]
                published_data[0]["needs_ethics_review"] = True
                await self.firestore.set_document(
                    PUBLISHED_CONTENT_COLLECTION, pub_id, published_data[0]
                )
                console.print("[green]✓ Flagged for ethics review[/green]")
            else:
                console.print("[yellow]No published content found. Creating draft...[/yellow]")
                # Create draft with flag
                draft = {
                    "id": f"pub_{topic_id}_draft",
                    "topic_id": topic_id,
                    "selected_option_id": None,
                    "platform": "youtube_short",
                    "status": "draft",
                    "needs_ethics_review": True,
                }
                await self.firestore.set_document(PUBLISHED_CONTENT_COLLECTION, draft["id"], draft)
        except Exception as e:
            console.print(f"[red]✗ Failed to flag: {e}[/red]")
            logger.error(f"Failed to flag ethics: {e}")
