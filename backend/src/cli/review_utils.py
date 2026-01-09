"""
Shared utilities for interactive CLI review workflows.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def is_interactive() -> bool:
    """Check if running in interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def check_terminal_compatibility() -> bool:
    """Check terminal compatibility and return True if compatible."""
    if not is_interactive():
        console.print("[red]Error: Non-interactive terminal detected.[/red]")
        console.print("This command requires an interactive terminal.")
        return False
    return True


def truncate_text(text: str, max_length: int = 77) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def display_topic_table(
    topics: list[dict[str, Any]], scores: dict[str, dict[str, Any]], page: int = 1, per_page: int = 10
) -> None:
    """Display topics in a rich table format."""
    table = Table(title=f"Topics (Page {page})", show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Score", style="yellow", width=8)
    table.add_column("Platform", style="blue", width=10)
    table.add_column("Cluster", style="green", width=15)
    table.add_column("Title", style="white", width=50)

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_topics = topics[start_idx:end_idx]

    for idx, topic in enumerate(page_topics, start=start_idx + 1):
        topic_id = topic.get("id", "")
        score_data = scores.get(topic_id, {})
        score = score_data.get("score", 0.0)

        # Color code by score
        if score >= 0.8:
            score_style = "green"
        elif score >= 0.6:
            score_style = "yellow"
        else:
            score_style = "red"

        score_text = Text(f"{score:.2f}", style=score_style)
        platform = topic.get("source_platform", "unknown")
        cluster = topic.get("topic_cluster", "unknown")
        title = truncate_text(topic.get("title", "Untitled"))

        table.add_row(str(idx), score_text, platform, cluster, title)

    console.print(table)


def display_detail_panel(topic: dict[str, Any], score: dict[str, Any] | None = None) -> None:
    """Display topic details in an expandable panel."""
    title = topic.get("title", "Untitled")
    platform = topic.get("source_platform", "unknown")
    cluster = topic.get("topic_cluster", "unknown")
    entities = topic.get("entities", [])
    source_url = topic.get("source_url", "N/A")
    created_at = topic.get("created_at", "")

    content_lines = [
        f"[bold]Title:[/bold] {title}",
        f"[bold]Platform:[/bold] {platform}",
        f"[bold]Cluster:[/bold] {cluster}",
        "",
    ]

    if score:
        score_val = score.get("score", 0.0)
        components = score.get("components", {})
        recency = components.get("recency", 0.0)
        velocity = components.get("velocity", 0.0)
        audience_fit = components.get("audience_fit", 0.0)
        integrity_penalty = components.get("integrity_penalty", 0.0)

        content_lines.extend(
            [
                f"[bold]Score:[/bold] {score_val:.2f}",
                f"  Recency: {recency:.2f} | Velocity: {velocity:.2f} | Audience: {audience_fit:.2f}",
                f"  Integrity Penalty: {integrity_penalty:.2f}",
                "",
            ]
        )
    else:
        content_lines.append("[yellow]Score: N/A[/yellow]\n")

    if entities:
        content_lines.append(f"[bold]Entities:[/bold] {', '.join(entities[:5])}")
        if len(entities) > 5:
            content_lines.append(f"  ... and {len(entities) - 5} more")

    content_lines.extend(
        [
            "",
            f"[bold]Source:[/bold] {source_url}",
            f"[bold]Created:[/bold] {created_at}",
        ]
    )

    panel = Panel("\n".join(content_lines), title="Topic Details", border_style="blue")
    console.print(panel)


def prompt_action(
    prompt: str, valid_keys: list[str], default: str | None = None, case_sensitive: bool = False
) -> str:
    """Prompt user for action with validation."""
    if not case_sensitive:
        valid_keys_lower = [k.lower() for k in valid_keys]
    else:
        valid_keys_lower = valid_keys

    while True:
        try:
            response = console.input(f"{prompt} ").strip()
            if not response and default:
                return default

            if not case_sensitive:
                response = response.lower()
                if response in valid_keys_lower:
                    idx = valid_keys_lower.index(response)
                    return valid_keys[idx]
            else:
                if response in valid_keys:
                    return response

            console.print(
                f"[red]Invalid input. Valid options: {', '.join(valid_keys)}[/red]"
            )
        except (EOFError, KeyboardInterrupt):
            raise


def collect_reason_code() -> str | None:
    """Collect rejection reason code from user."""
    reasons = {
        "1": "too_generic",
        "2": "not_on_brand",
        "3": "speculative",
        "4": "duplicate",
        "5": "ethics",
    }

    console.print("\n[bold]Select reason code:[/bold]")
    console.print("  1. Too generic")
    console.print("  2. Not on brand")
    console.print("  3. Speculative")
    console.print("  4. Duplicate")
    console.print("  5. Ethics")
    console.print("  0. Skip (no reason)")

    choice = prompt_action("Choice [0-5]: ", ["0", "1", "2", "3", "4", "5"], default="0")
    if choice == "0":
        return None
    return reasons.get(choice)


def collect_notes() -> str | None:
    """Collect optional notes from user."""
    console.print("\n[dim]Optional notes (press Enter to skip):[/dim]")
    try:
        notes = console.input("Notes: ").strip()
        return notes if notes else None
    except (EOFError, KeyboardInterrupt):
        return None


def show_summary(stats: dict[str, int]) -> None:
    """Display session summary statistics."""
    approved = stats.get("approved", 0)
    rejected = stats.get("rejected", 0)
    deferred = stats.get("deferred", 0)
    skipped = stats.get("skipped", 0)
    total = approved + rejected + deferred + skipped

    summary_lines = [
        f"[green]✓ Approved:[/green] {approved}",
        f"[red]✗ Rejected:[/red] {rejected}",
        f"[yellow]⏸ Deferred:[/yellow] {deferred}",
        f"[dim]⊘ Skipped:[/dim] {skipped}",
        "",
        f"[bold]Total reviewed:[/bold] {total}",
    ]

    panel = Panel("\n".join(summary_lines), title="Session Summary", border_style="green")
    console.print("\n")
    console.print(panel)


def save_session_state(session_data: dict[str, Any], filepath: str = ".review_session.json") -> None:
    """Save session state to file."""
    try:
        session_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        with open(filepath, "w") as f:
            json.dump(session_data, f, indent=2)
        console.print(f"[green]Session state saved to {filepath}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save session state: {e}[/red]")


def load_session_state(filepath: str = ".review_session.json") -> dict[str, Any] | None:
    """Load session state from file."""
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Failed to load session state: {e}[/red]")
        return None


def display_progress(current: int, total: int, stats: dict[str, int]) -> None:
    """Display progress indicator."""
    approved = stats.get("approved", 0)
    rejected = stats.get("rejected", 0)
    deferred = stats.get("deferred", 0)
    remaining = total - current

    progress_text = (
        f"[green]✓ {approved}[/green] | "
        f"[red]✗ {rejected}[/red] | "
        f"[yellow]⏸ {deferred}[/yellow] | "
        f"[dim]Remaining: {remaining}[/dim]"
    )

    console.print(f"\n[bold]Progress:[/bold] {progress_text}")
    console.print(f"Reviewing item {current} of {total}\n")


async def retry_with_backoff(
    func, max_retries: int = 3, initial_delay: float = 1.0, *args, **kwargs
) -> Any:
    """Retry a function with exponential backoff."""
    import asyncio

    last_error = None
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = initial_delay * (2**attempt)
                console.print(f"[yellow]⚠ Retrying... (attempt {attempt + 1}/{max_retries})[/yellow]")
                await asyncio.sleep(delay)
            else:
                console.print(f"[red]✗ Failed after {max_retries} attempts[/red]")
                raise last_error
    raise last_error or ValueError("Retry failed")

