#!/usr/bin/env python3
"""
Create test data for scripts functionality testing.

Creates:
- 1 approved topic
- 2-3 hooks (ContentOption with option_type="short_hook")
- 1-2 scripts (ContentOption with option_type="short_script")
"""

import asyncio
import hashlib
from datetime import datetime, timezone

from src.content.models import (
    CONTENT_OPTIONS_COLLECTION,
    TOPIC_CANDIDATES_COLLECTION,
    ContentOption,
    TopicCandidate,
)
from src.core.logging import get_logger
from src.infra import FirestoreService

logger = get_logger(__name__)


async def create_test_data():
    """Create test topic and content options."""
    firestore = FirestoreService()

    # Create test topic
    topic_title = "Anthropic Releases Claude 3.5 with Extended Context"
    topic_id = f"manual-{int(datetime.now(timezone.utc).timestamp())}-{hashlib.md5(topic_title.encode()).hexdigest()[:8]}"

    topic = TopicCandidate(
        id=topic_id,
        source_platform="manual",
        source_url="https://example.com/test",
        title=topic_title,
        raw_payload={},
        entities=["Anthropic", "Claude", "AI"],
        topic_cluster="ai-infra",
        detected_language="en",
        status="approved",
        created_at=datetime.now(timezone.utc),
    )

    await firestore.set_document(TOPIC_CANDIDATES_COLLECTION, topic_id, topic.to_firestore_dict())
    logger.info(f"✓ Created test topic: {topic_id}")

    # Create test hooks
    hooks = [
        "Claude 3.5 just dropped with 200K context—here's why that matters",
        "Anthropic's latest release could change how we build AI apps",
        "The context window wars just got more interesting",
    ]

    hook_ids = []
    for i, hook_content in enumerate(hooks):
        hook_id = f"{topic_id}-hook-{i+1}"
        hook = ContentOption(
            id=hook_id,
            topic_id=topic_id,
            option_type="short_hook",
            content=hook_content,
            prompt_version="short_hook_v1",
            model="gpt-4o-mini",
            metadata={},
            created_at=datetime.now(timezone.utc),
            edited_content=None,
            edited_at=None,
            editor_id=None,
            edit_history=None,
            refinement_applied=None,
        )
        await firestore.set_document(CONTENT_OPTIONS_COLLECTION, hook_id, hook.to_firestore_dict())
        hook_ids.append(hook_id)
        logger.info(f"✓ Created hook {i+1}: {hook_id}")

    # Create test script
    script_content = """Here's what makes Claude 3.5's 200K context window a big deal:

1. You can now feed it entire codebases
2. Long-form content analysis becomes practical
3. Multi-document reasoning improves dramatically

This isn't just a number bump—it's unlocking new use cases. Companies building AI assistants and research tools are about to have a field day.

The race for longer context continues, but quality matters more than length. Anthropic's known for reliable outputs even at scale."""

    script_id = f"{topic_id}-script-1"
    script = ContentOption(
        id=script_id,
        topic_id=topic_id,
        option_type="short_script",
        content=script_content,
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
        edited_content=None,
        edited_at=None,
        editor_id=None,
        edit_history=None,
        refinement_applied=None,
    )
    await firestore.set_document(CONTENT_OPTIONS_COLLECTION, script_id, script.to_firestore_dict())
    logger.info(f"✓ Created script: {script_id}")

    logger.info("\n✓ Test data created successfully!")
    logger.info(f"  Topic ID: {topic_id}")
    logger.info(f"  Hooks: {len(hook_ids)}")
    logger.info("  Scripts: 1")
    logger.info(
        f"\nYou can now test the scripts view at: http://localhost:3000/scripts?topic={topic_id}"
    )


if __name__ == "__main__":
    asyncio.run(create_test_data())
