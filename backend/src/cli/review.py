"""
Interactive review CLI for Content Engine.
"""

import asyncio

import typer

from ..core import get_logger
from .reviewers.integrity_reviewer import IntegrityReviewer
from .reviewers.script_reviewer import ScriptReviewer
from .reviewers.style_reviewer import StyleReviewer
from .reviewers.topic_reviewer import TopicReviewer
from .review_utils import check_terminal_compatibility

logger = get_logger(__name__)

review_app = typer.Typer()


@review_app.command()
def topics(
    limit: int = typer.Option(50, "--limit", help="Maximum topics to review"),
    min_score: float | None = typer.Option(None, "--min-score", help="Minimum score threshold"),
    status: str = typer.Option("pending", "--status", help="Topic status filter"),
    resume: str | None = typer.Option(None, "--resume", help="Resume from session file"),
) -> None:
    """Interactive topic review workflow."""
    if not check_terminal_compatibility():
        raise typer.Exit(1)

    async def _review() -> None:
        reviewer = TopicReviewer(resume_file=resume)
        await reviewer.review_topics(limit=limit, min_score=min_score, status=status)

    asyncio.run(_review())


@review_app.command()
def scripts(
    limit: int = typer.Option(20, "--limit", help="Maximum topics to review"),
) -> None:
    """Interactive script/content review workflow."""
    if not check_terminal_compatibility():
        raise typer.Exit(1)

    async def _review() -> None:
        reviewer = ScriptReviewer()
        await reviewer.review_scripts(limit=limit)

    asyncio.run(_review())


@review_app.command()
def integrity(
    limit: int = typer.Option(20, "--limit", help="Maximum items to review"),
) -> None:
    """Interactive integrity/ethics review workflow."""
    if not check_terminal_compatibility():
        raise typer.Exit(1)

    async def _review() -> None:
        reviewer = IntegrityReviewer()
        await reviewer.review_integrity(limit=limit)

    asyncio.run(_review())


@review_app.command()
def styles(
    limit: int = typer.Option(20, "--limit", help="Maximum profiles to review"),
    status: str = typer.Option("pending", "--status", help="Profile status filter"),
) -> None:
    """Interactive style profile curation workflow."""
    if not check_terminal_compatibility():
        raise typer.Exit(1)

    async def _review() -> None:
        reviewer = StyleReviewer()
        await reviewer.review_styles(limit=limit, status=status)

    asyncio.run(_review())




@review_app.callback()
def main() -> None:
    """Interactive review workflows for Content Engine."""
    pass

