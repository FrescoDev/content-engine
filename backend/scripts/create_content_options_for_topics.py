#!/usr/bin/env python3
"""
Create ContentOption records (hooks and scripts) for approved topics.

This script:
1. Fetches approved topics from Firestore
2. Generates hooks and scripts using OpenAI
3. Saves ContentOption records to Firestore

Usage:
    poetry run python scripts/create_content_options_for_topics.py [--topic-id TOPIC_ID] [--limit N]
"""

import argparse
import asyncio
from datetime import datetime, timezone

from src.content.models import (
    CONTENT_OPTIONS_COLLECTION,
    TOPIC_CANDIDATES_COLLECTION,
    ContentOption,
)
from src.core.logging import get_logger
from src.infra import FirestoreService, OpenAIService

logger = get_logger(__name__)


async def generate_hook(topic_title: str, openai_service: OpenAIService) -> str:
    """Generate a hook for a topic."""
    prompt = f"""Generate a short, engaging hook (1-2 sentences) for a short-form video about:

{topic_title}

The hook should:
- Be attention-grabbing and conversational
- Make viewers want to watch more
- Be under 100 characters if possible
- Sound natural and not clickbait-y

Hook:"""

    try:
        hook = await openai_service.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional content creator writing hooks for short-form videos. Keep it concise and engaging.",
                },
                {"role": "user", "content": prompt},
            ],
            model="gpt-4o-mini",
        )
        return hook.strip()
    except Exception as e:
        logger.error(f"Failed to generate hook: {e}")
        return f"Check out this: {topic_title[:50]}..."


async def generate_script(topic_title: str, openai_service: OpenAIService) -> str:
    """Generate a script for a topic."""
    prompt = f"""Write a short-form video script (30-60 seconds) about:

{topic_title}

The script should:
- Be engaging and conversational
- Have a clear structure (hook, main points, conclusion)
- Be suitable for YouTube Shorts or TikTok
- Be around 100-150 words
- Use natural, casual language

Script:"""

    try:
        script = await openai_service.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional script writer for short-form video content. Write engaging, conversational scripts.",
                },
                {"role": "user", "content": prompt},
            ],
            model="gpt-4o-mini",
        )
        return script.strip()
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        return (
            f"Let's talk about {topic_title}. This is an interesting topic that deserves attention."
        )


async def create_options_for_topic(
    topic_id: str, topic_title: str, firestore: FirestoreService, openai_service: OpenAIService
):
    """Create hooks and scripts for a topic."""
    logger.info(f"Creating options for topic: {topic_title}")

    # Check if options already exist
    existing_options = await firestore.query_collection(
        CONTENT_OPTIONS_COLLECTION,
        filters=[("topic_id", "==", topic_id)],
    )
    if existing_options:
        logger.info(f"  Options already exist for {topic_id}, skipping")
        return

    # Generate hooks (3 hooks)
    hooks = []
    for i in range(3):
        hook_content = await generate_hook(topic_title, openai_service)
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
        hooks.append(hook_id)
        logger.info(f"  ✓ Created hook {i+1}: {hook_content[:60]}...")

    # Generate script (1 script)
    script_content = await generate_script(topic_title, openai_service)
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
    logger.info(f"  ✓ Created script: {script_content[:60]}...")

    logger.info(f"✓ Created {len(hooks)} hooks and 1 script for {topic_id}")


async def main():
    parser = argparse.ArgumentParser(description="Create ContentOptions for topics")
    parser.add_argument("--topic-id", help="Specific topic ID to process")
    parser.add_argument("--limit", type=int, default=5, help="Maximum topics to process")
    args = parser.parse_args()

    firestore = FirestoreService()
    openai_service = OpenAIService()

    if args.topic_id:
        # Process specific topic
        topic_doc = await firestore.get_document(TOPIC_CANDIDATES_COLLECTION, args.topic_id)
        if not topic_doc:
            logger.error(f"Topic {args.topic_id} not found")
            return
        topic_title = topic_doc.get("title", "Untitled")
        await create_options_for_topic(args.topic_id, topic_title, firestore, openai_service)
    else:
        # Process approved topics
        topics = await firestore.query_collection(
            TOPIC_CANDIDATES_COLLECTION,
            filters=[("status", "==", "approved")],
            limit=args.limit,
        )

        if not topics:
            logger.info("No approved topics found")
            return

        logger.info(f"Found {len(topics)} approved topics, creating options...")

        for topic in topics:
            topic_id = topic.get("id") or topic.get("__id__")
            topic_title = topic.get("title", "Untitled")
            if topic_id:
                await create_options_for_topic(topic_id, topic_title, firestore, openai_service)
                # Small delay to avoid rate limits
                await asyncio.sleep(1)

    logger.info("✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
