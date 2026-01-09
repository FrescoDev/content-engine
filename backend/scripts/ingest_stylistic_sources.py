#!/usr/bin/env python3
"""
Ingest stylistic content from Reddit and podcast sources.

This script:
1. Adds stylistic sources to the database
2. Fetches content from Reddit (posts + top comments)
3. Fetches content from podcast sources (if transcripts available)
4. Saves as StylisticContent
5. Optionally extracts style profiles
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Add backend to path (required for standalone script execution)
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# ruff: noqa: E402
from src.content.models import (
    STYLISTIC_CONTENT_COLLECTION,
    STYLISTIC_SOURCES_COLLECTION,
    StylisticContent,
    StylisticSource,
)
from src.content.style_extraction_service import StyleExtractionService
from src.core import get_logger
from src.infra import FirestoreService

logger = get_logger(__name__)

# Sources to ingest
SOURCES = [
    {
        "source_type": "reddit",
        "source_url": "https://www.reddit.com/r/hiphopheads/",
        "source_name": "r/hiphopheads",
        "description": "Hip-hop culture subreddit",
        "tags": ["hip-hop", "culture", "music", "rap"],
    },
    {
        "source_type": "reddit",
        "source_url": "https://www.reddit.com/r/theJoeBuddenPodcast/",
        "source_name": "r/theJoeBuddenPodcast",
        "description": "Joe Budden Podcast discussion subreddit",
        "tags": ["podcast", "hip-hop", "culture", "discussion"],
    },
    {
        "source_type": "podcast",
        "source_url": "https://podcasts.musixmatch.com/podcast/the-joe-budden-podcast-01gv03qx00bhdgccn8k448zhy3",
        "source_name": "The Joe Budden Podcast (Musixmatch)",
        "description": "Joe Budden Podcast transcripts",
        "tags": ["podcast", "hip-hop", "transcript"],
    },
    {
        "source_type": "podcast",
        "source_url": "https://podcasts.happyscribe.com/the-joe-rogan-experience",
        "source_name": "The Joe Rogan Experience (HappyScribe)",
        "description": "Joe Rogan Experience podcast transcripts",
        "tags": ["podcast", "transcript", "conversation"],
    },
]


async def add_stylistic_source(firestore: FirestoreService, source_config: dict) -> str:
    """Add a stylistic source to the database."""
    import uuid

    source_id = f"source-{uuid.uuid4().hex[:8]}"

    source = StylisticSource(
        id=source_id,
        source_type=source_config["source_type"],  # type: ignore
        source_url=source_config["source_url"],
        source_name=source_config["source_name"],
        description=source_config.get("description"),
        tags=source_config.get("tags", []),
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await firestore.set_document(
        STYLISTIC_SOURCES_COLLECTION, source_id, source.to_firestore_dict()
    )

    logger.info(f"✓ Added source: {source_id} ({source_config['source_name']})")
    return source_id


async def fetch_reddit_content(
    firestore: FirestoreService, source_id: str, subreddit: str, limit: int = 10
) -> int:
    """Fetch Reddit posts and top comments as stylistic content."""
    client = httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "ContentEngine/1.0"})

    try:
        # Fetch hot posts
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": min(limit, 25)}
        response = await client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        posts = data.get("data", {}).get("children", [])

        content_count = 0

        for post in posts[:limit]:
            post_data = post.get("data", {})
            post_title = post_data.get("title", "")
            post_text = post_data.get("selftext", "")
            post_url = f"https://www.reddit.com{post_data.get('permalink', '')}"

            # Skip if no text content (link-only posts)
            if not post_text and not post_title:
                continue

            # Combine title + text for content
            content_text = f"{post_title}\n\n{post_text}".strip()

            # Skip if too short
            if len(content_text.split()) < 50:
                continue

            # Create StylisticContent for post
            content_id = f"reddit-{post_data.get('id', 'unknown')}"
            content = StylisticContent(
                id=content_id,
                source_id=source_id,
                content_type="post",
                raw_text=content_text,
                source_url=post_url,
                published_at=datetime.fromtimestamp(
                    post_data.get("created_utc", 0), tz=timezone.utc
                ),
                author=post_data.get("author"),
                engagement_score=post_data.get("score", 0),
                raw_payload=post_data,
                status="pending",
                last_extraction_error=None,
                profile_id=None,
                created_at=datetime.now(timezone.utc),
            )

            await firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, content_id, content.to_firestore_dict()
            )
            content_count += 1

            # Fetch top comments for this post
            post_id = post_data.get("id")
            if post_id:
                comments_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
                try:
                    comments_response = await client.get(comments_url)
                    comments_response.raise_for_status()
                    comments_data = comments_response.json()

                    # Parse comments (nested structure)
                    if len(comments_data) > 1:
                        comments_list = comments_data[1].get("data", {}).get("children", [])
                        for comment_item in comments_list[:5]:  # Top 5 comments
                            comment_data = comment_item.get("data", {})
                            comment_body = comment_data.get("body", "")
                            comment_author = comment_data.get("author")

                            if len(comment_body.split()) >= 30:  # Minimum length
                                comment_id = f"reddit-comment-{comment_data.get('id', 'unknown')}"
                                # Clean payload - remove nested entities that Firestore can't handle
                                clean_payload = {
                                    "id": comment_data.get("id"),
                                    "score": comment_data.get("score"),
                                    "author": comment_data.get("author"),
                                    "created_utc": comment_data.get("created_utc"),
                                    "permalink": comment_data.get("permalink"),
                                }

                                comment_content = StylisticContent(
                                    id=comment_id,
                                    source_id=source_id,
                                    content_type="comment",
                                    raw_text=comment_body,
                                    source_url=f"{post_url}#{comment_id}",
                                    published_at=datetime.fromtimestamp(
                                        comment_data.get("created_utc", 0), tz=timezone.utc
                                    ),
                                    author=comment_author,
                                    engagement_score=comment_data.get("score", 0),
                                    raw_payload=clean_payload,
                                    status="pending",
                                    last_extraction_error=None,
                                    profile_id=None,
                                    created_at=datetime.now(timezone.utc),
                                )

                                await firestore.set_document(
                                    STYLISTIC_CONTENT_COLLECTION,
                                    comment_id,
                                    comment_content.to_firestore_dict(),
                                )
                                content_count += 1

                except Exception as e:
                    logger.warning(f"Failed to fetch comments for post {post_id}: {e}")
                    continue

            # Rate limiting
            await asyncio.sleep(1)

        return content_count

    finally:
        await client.aclose()


async def fetch_podcast_content(
    firestore: FirestoreService, source_id: str, source_url: str, source_name: str
) -> int:
    """Fetch podcast transcripts (placeholder - requires API access)."""
    # Note: Podcast transcript APIs require authentication/API keys
    # For MVP, we'll create placeholder content entries that can be manually filled
    # or integrated with transcript APIs later

    logger.warning(
        f"Podcast transcript fetching not yet implemented for {source_name}. "
        "Please add transcripts manually or integrate with transcript API."
    )

    # Create a placeholder entry for manual transcript addition
    content_id = f"podcast-placeholder-{source_id}"
    content = StylisticContent(
        id=content_id,
        source_id=source_id,
        content_type="transcript",
        raw_text="[Transcript placeholder - add transcript manually]",
        source_url=source_url,
        published_at=datetime.now(timezone.utc),
        author=None,
        engagement_score=None,
        raw_payload={"note": "Manual transcript entry required"},
        status="pending",
        last_extraction_error=None,
        profile_id=None,
        created_at=datetime.now(timezone.utc),
    )

    await firestore.set_document(
        STYLISTIC_CONTENT_COLLECTION, content_id, content.to_firestore_dict()
    )

    return 1


async def main():
    """Main ingestion workflow."""
    logger.info("=" * 70)
    logger.info("Stylistic Content Ingestion")
    logger.info("=" * 70)
    logger.info("Usage: python ingest_stylistic_sources.py [--extract|-e]")
    logger.info("")

    try:
        firestore = FirestoreService()
        # Test connection
        await firestore.get_document("_test", "connection_test")
    except Exception as e:
        logger.error(f"Firestore connection failed: {e}")
        logger.error("Please ensure Firestore is configured correctly.")
        logger.error("You may need to set up the database or configure credentials.")
        return

    extraction_service = StyleExtractionService()

    # Step 1: Add sources
    logger.info("\n📝 Step 1: Adding stylistic sources...")
    source_ids = {}
    for source_config in SOURCES:
        try:
            source_id = await add_stylistic_source(firestore, source_config)
            source_ids[source_config["source_url"]] = source_id
        except Exception as e:
            logger.error(f"Failed to add source {source_config['source_name']}: {e}")
            continue

    logger.info(f"✓ Added {len(source_ids)} sources")

    # Step 2: Fetch content
    logger.info("\n📥 Step 2: Fetching content from sources...")
    total_content = 0

    for source_config in SOURCES:
        source_id = source_ids.get(source_config["source_url"])
        if not source_id:
            continue

        try:
            if source_config["source_type"] == "reddit":
                # Extract subreddit name from URL
                subreddit = source_config["source_url"].split("/r/")[-1].rstrip("/")
                logger.info(f"Fetching from r/{subreddit}...")
                count = await fetch_reddit_content(firestore, source_id, subreddit, limit=10)
                total_content += count
                logger.info(f"✓ Fetched {count} content items from r/{subreddit}")

            elif source_config["source_type"] == "podcast":
                logger.info(f"Fetching from {source_config['source_name']}...")
                count = await fetch_podcast_content(
                    firestore, source_id, source_config["source_url"], source_config["source_name"]
                )
                total_content += count
                logger.info(f"✓ Created placeholder for {source_config['source_name']}")

        except Exception as e:
            logger.error(f"Failed to fetch from {source_config['source_name']}: {e}", exc_info=True)
            continue

    logger.info(f"\n✓ Total content items created: {total_content}")

    # Step 3: Extract styles (optional)
    # Check command line argument for extraction
    extract = "--extract" in sys.argv or "-e" in sys.argv
    if extract:
        logger.info("\n🎨 Step 3: Extracting style profiles...")
        extraction_count = 0

        # Fetch pending content
        pending_content = await firestore.query_collection(
            STYLISTIC_CONTENT_COLLECTION,
            filters=[("status", "==", "pending")],
            limit=50,
        )

        for content_data in pending_content:
            try:
                content_id = content_data.get("id")
                if not content_id:
                    continue

                content = StylisticContent.from_firestore_dict(content_data, content_id)
                profile = await extraction_service.extract_style_profile(content)

                if profile:
                    extraction_count += 1
                    logger.info(f"✓ Extracted profile: {profile.id} (tone: {profile.tone})")

            except Exception as e:
                logger.error(f"Failed to extract from content {content_id}: {e}")
                continue

        logger.info(f"\n✓ Extracted {extraction_count} style profiles")

    logger.info("\n✅ Ingestion complete!")
    logger.info("\nNext steps:")
    logger.info("1. Review profiles in /styles page")
    logger.info("2. Approve/reject profiles as needed")
    logger.info("3. Use approved profiles in content generation")


if __name__ == "__main__":
    asyncio.run(main())
