"""
Automated stylistic source ingestion service.

Takes a URL and automatically:
1. Detects source type
2. Creates source record
3. Fetches content
4. Extracts style profiles
5. Returns results

All in one automated flow.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from ..core import get_logger
from ..infra import FirestoreService
from .models import (
    STYLISTIC_CONTENT_COLLECTION,
    STYLISTIC_SOURCES_COLLECTION,
    StylisticContent,
    StylisticSource,
)
from .style_extraction_service import StyleExtractionService

logger = get_logger(__name__)

# Constants
MAX_CONTENT_LENGTH_WORDS = 2000
CHUNK_SIZE_WORDS = 1800


class StylisticSourceIngestionService:
    """Automated ingestion service for stylistic sources."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        extraction_service: StyleExtractionService | None = None,
    ):
        """Initialize ingestion service."""
        self.firestore = firestore or FirestoreService()
        self.extraction_service = extraction_service or StyleExtractionService()
        self.client = httpx.AsyncClient(timeout=30.0, headers={"User-Agent": "ContentEngine/1.0"})

    def detect_source_type(
        self, url: str
    ) -> Literal["reddit", "podcast", "rss", "youtube", "manual"]:
        """
        Auto-detect source type from URL.

        Args:
            url: Source URL

        Returns:
            Detected source type
        """
        url_lower = url.lower()

        if "reddit.com/r/" in url_lower:
            return "reddit"
        elif "podscripts.co" in url_lower:
            return "podcast"
        elif "podcasts.musixmatch.com" in url_lower or "podcasts.happyscribe.com" in url_lower:
            return "podcast"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif url_lower.endswith(".rss") or url_lower.endswith(".xml") or "/feed" in url_lower:
            return "rss"
        else:
            return "manual"

    def generate_source_name(self, url: str, source_type: str) -> str:
        """Generate a human-readable source name from URL."""
        if source_type == "reddit":
            # Extract subreddit name
            match = re.search(r"reddit\.com/r/([^/]+)", url)
            if match:
                return f"r/{match.group(1)}"
        elif source_type == "podcast":
            # Extract podcast/episode name
            if "podscripts.co" in url:
                match = re.search(r"podscripts\.co/podcasts/([^/]+)", url)
                if match:
                    podcast_name = match.group(1).replace("-", " ").title()
                    # Check for episode
                    episode_match = re.search(r"episode-(\d+)", url)
                    if episode_match:
                        return f"{podcast_name} - Episode {episode_match.group(1)}"
                    return podcast_name
            elif "musixmatch.com" in url:
                return "Podcast (Musixmatch)"
            elif "happyscribe.com" in url:
                return "Podcast (HappyScribe)"
        elif source_type == "youtube":
            return "YouTube Channel/Video"
        elif source_type == "rss":
            return "RSS Feed"

        # Fallback: use domain name
        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if match:
            domain = match.group(1)
            return domain.split(".")[0].title()

        return "Unknown Source"

    async def ingest_from_url(
        self,
        url: str,
        source_name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        auto_extract: bool = True,
    ) -> dict[str, Any]:
        """
        Ingest stylistic source from URL - fully automated.

        Args:
            url: Source URL
            source_name: Optional custom name (auto-generated if not provided)
            description: Optional description
            tags: Optional tags list
            auto_extract: Whether to automatically extract styles (default: True)

        Returns:
            Dict with ingestion results:
            {
                "source_id": str,
                "source": StylisticSource,
                "content_count": int,
                "profiles_created": int,
                "status": "success" | "partial" | "failed",
                "errors": list[str]
            }
        """
        errors = []
        content_count = 0
        profiles_created = 0

        try:
            # Step 1: Detect source type
            source_type = self.detect_source_type(url)
            logger.info(f"Detected source type: {source_type} for URL: {url}")

            # Step 2: Generate source name if not provided
            if not source_name:
                source_name = self.generate_source_name(url, source_type)

            # Step 3: Check for existing source (prevent duplicates)
            existing_sources = await self.firestore.query_collection(
                STYLISTIC_SOURCES_COLLECTION,
                filters=[("source_url", "==", url)],
                limit=1,
            )

            if existing_sources:
                source_id = existing_sources[0]["id"]
                logger.info(f"Source already exists: {source_id}, reusing")
                # Update timestamp
                existing_sources[0]["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.firestore.set_document(
                    STYLISTIC_SOURCES_COLLECTION, source_id, existing_sources[0]
                )
                source = StylisticSource.from_firestore_dict(existing_sources[0], source_id)
            else:
                # Create new source record
                source_id = f"source-{uuid.uuid4().hex[:8]}"
                source = StylisticSource(
                    id=source_id,
                    source_type=source_type,
                    source_url=url,
                    source_name=source_name,
                    description=description,
                    tags=tags or [],
                    status="active",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                await self.firestore.set_document(
                    STYLISTIC_SOURCES_COLLECTION, source_id, source.to_firestore_dict()
                )
                logger.info(f"✓ Created source: {source_id} ({source_name})")

            # Step 4: Fetch content based on source type
            if source_type == "reddit":
                content_count = await self._fetch_reddit_content(source_id, url)
            elif source_type == "podcast":
                content_count = await self._fetch_podcast_content(source_id, url, source_name)
            else:
                logger.warning(f"Content fetching not yet implemented for {source_type}")
                errors.append(f"Content fetching not implemented for {source_type}")

            # Step 4.5: Handle orphaned source (content fetch failed)
            if content_count == 0 and not errors:
                logger.warning(f"No content fetched for source {source_id}, marking as paused")
                source.status = "paused"  # Use 'paused' status to indicate temporary failure
                source.updated_at = datetime.now(timezone.utc)
                # Store failure reason in metadata
                source.metadata = source.metadata or {}
                source.metadata["last_failure_reason"] = "No content fetched"
                await self.firestore.set_document(
                    STYLISTIC_SOURCES_COLLECTION, source_id, source.to_firestore_dict()
                )

            # Step 5: Extract styles if requested
            if auto_extract and content_count > 0:
                profiles_created = await self._extract_styles_from_source(source_id)

            # Determine status
            if content_count > 0 and (not auto_extract or profiles_created > 0):
                status = "success"
            elif content_count > 0:
                status = "partial"  # Content fetched but extraction failed
            else:
                status = "failed"

            return {
                "source_id": source_id,
                "source": source,
                "content_count": content_count,
                "profiles_created": profiles_created,
                "status": status,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Failed to ingest source from URL {url}: {e}", exc_info=True)
            errors.append(str(e))
            return {
                "source_id": source_id if "source_id" in locals() else None,
                "source": source if "source" in locals() else None,
                "content_count": content_count,
                "profiles_created": profiles_created,
                "status": "failed",
                "errors": errors,
            }

    async def _fetch_reddit_content(self, source_id: str, url: str, limit: int = 10) -> int:
        """Fetch Reddit content."""
        try:
            # Extract subreddit name
            match = re.search(r"reddit\.com/r/([^/]+)", url)
            if not match:
                logger.error(f"Could not extract subreddit from URL: {url}")
                return 0

            subreddit = match.group(1)
            logger.info(f"Fetching from r/{subreddit}...")

            # Fetch hot posts
            reddit_url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            params = {"limit": min(limit, 25)}  # type: ignore
            response = await self.client.get(reddit_url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            content_count = 0
            for post in posts[:limit]:
                post_data = post.get("data", {})
                post_title = post_data.get("title", "")
                post_text = post_data.get("selftext", "")
                post_url = f"https://www.reddit.com{post_data.get('permalink', '')}"

                if not post_text and not post_title:
                    continue

                content_text = f"{post_title}\n\n{post_text}".strip()
                if len(content_text.split()) < 50:
                    continue

                # Fetch top comments
                comments_url = f"https://www.reddit.com{post_data.get('permalink', '')}.json"
                try:
                    comments_response = await self.client.get(comments_url)
                    comments_response.raise_for_status()
                    comments_data = comments_response.json()
                    if len(comments_data) > 1:
                        comments = comments_data[1].get("data", {}).get("children", [])[:5]
                        for comment in comments:
                            comment_data = comment.get("data", {})
                            comment_body = comment_data.get("body", "")
                            if comment_body and len(comment_body.split()) >= 20:
                                # Remove problematic nested fields
                                if "replies" in comment_data:
                                    del comment_data["replies"]
                                # Check for existing content (prevent duplicates)
                                comment_id = comment_data.get("id", "unknown")
                                post_id = post_data.get("id", "unknown")
                                content_id = f"reddit-{post_id}-{comment_id}"

                                existing = await self.firestore.get_document(
                                    STYLISTIC_CONTENT_COLLECTION, content_id
                                )
                                if existing:
                                    logger.debug(f"Content {content_id} already exists, skipping")
                                    continue

                                content = StylisticContent(
                                    id=content_id,
                                    source_id=source_id,
                                    content_type="comment",
                                    raw_text=comment_body,
                                    source_url=f"https://www.reddit.com{comment_data.get('permalink', '')}",
                                    published_at=datetime.fromtimestamp(
                                        comment_data.get("created_utc", 0), tz=timezone.utc
                                    ),
                                    author=comment_data.get("author"),
                                    engagement_score=comment_data.get("score", 0),
                                    raw_payload=comment_data,
                                    status="pending",
                                    last_extraction_error=None,
                                    profile_id=None,
                                    created_at=datetime.now(timezone.utc),
                                )
                                await self.firestore.set_document(
                                    STYLISTIC_CONTENT_COLLECTION,
                                    content_id,
                                    content.to_firestore_dict(),
                                )
                                content_count += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch comments: {e}")
                    continue

                # Create content for post
                post_id = post_data.get("id", "unknown")
                content_id = f"reddit-{post_id}"

                # Check for existing content (prevent duplicates)
                existing = await self.firestore.get_document(
                    STYLISTIC_CONTENT_COLLECTION, content_id
                )
                if existing:
                    logger.debug(f"Content {content_id} already exists, skipping")
                    continue

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

                await self.firestore.set_document(
                    STYLISTIC_CONTENT_COLLECTION, content_id, content.to_firestore_dict()
                )
                content_count += 1

            logger.info(f"✓ Fetched {content_count} content items from r/{subreddit}")
            return content_count

        except Exception as e:
            logger.error(f"Failed to fetch Reddit content: {e}", exc_info=True)
            return 0

    async def _fetch_podcast_content(self, source_id: str, url: str, source_name: str) -> int:
        """Fetch podcast transcript content."""
        try:
            logger.info(f"Fetching podcast transcript from {url}...")

            if "podscripts.co" in url:
                # Fetch PodScripts transcript
                response = await self.client.get(url)
                response.raise_for_status()

                html = response.text

                # Extract transcript text (simple HTML parsing)
                import re

                # Remove script and style tags
                html = re.sub(
                    r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
                )
                html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

                # Extract text from HTML
                text = re.sub(r"<[^>]+>", "\n", html)
                lines = [line.strip() for line in text.split("\n") if line.strip()]

                # Filter and find transcript section
                transcript_lines = []
                in_transcript = False
                skip_keywords = [
                    "home",
                    "pricing",
                    "podcasts",
                    "categories",
                    "about",
                    "contact",
                    "sign in",
                    "privacy policy",
                    "podscripts.co",
                    "©",
                    "discussion",
                    "comments",
                ]

                for line in lines:
                    line_lower = line.lower()
                    if "starting point" in line_lower or "transcript" in line_lower:
                        in_transcript = True

                    if in_transcript:
                        if any(keyword in line_lower for keyword in skip_keywords):
                            continue
                        if len(line) > 15:
                            transcript_lines.append(line)
                            if len(transcript_lines) > 1000:
                                break

                transcript_text = "\n".join(transcript_lines)

                if len(transcript_text) < 1000:
                    logger.warning("Transcript too short, skipping")
                    return 0

                # Extract episode date if available
                date_match = re.search(r"Episode Date: ([^<]+)", html)
                published_at = datetime.now(timezone.utc)
                if date_match:
                    try:
                        from dateutil import parser  # type: ignore

                        published_at = parser.parse(date_match.group(1).strip()).replace(
                            tzinfo=timezone.utc
                        )
                    except Exception:
                        pass

                # Create content (check for duplicates by source_url)
                existing_content = await self.firestore.query_collection(
                    STYLISTIC_CONTENT_COLLECTION,
                    filters=[("source_id", "==", source_id), ("source_url", "==", url)],
                    limit=1,
                )

                if existing_content:
                    logger.info(f"Content already exists for {url}, skipping")
                    return 0

                # Use UUID for uniqueness
                content_id = f"podcast-{source_id[:8]}-{uuid.uuid4().hex[:8]}"
                content = StylisticContent(
                    id=content_id,
                    source_id=source_id,
                    content_type="transcript",
                    raw_text=transcript_text[:50000],  # Limit to 50k chars
                    source_url=url,
                    published_at=published_at,
                    author=None,
                    engagement_score=None,
                    raw_payload={
                        "scraped_from": "podscripts.co",
                        "method": "html_extraction",
                    },
                    status="pending",
                    last_extraction_error=None,
                    profile_id=None,
                    created_at=datetime.now(timezone.utc),
                )

                await self.firestore.set_document(
                    STYLISTIC_CONTENT_COLLECTION, content_id, content.to_firestore_dict()
                )

                logger.info(
                    f"✓ Created transcript content: {content_id} ({len(transcript_text)} chars)"
                )
                return 1

            else:
                # Other podcast sources - create placeholder
                logger.warning(f"Podcast transcript fetching not yet implemented for {url}")
                content_id = f"podcast-placeholder-{source_id}"
                content = StylisticContent(
                    id=content_id,
                    source_id=source_id,
                    content_type="transcript",
                    raw_text="[Transcript placeholder - add transcript manually]",
                    source_url=url,
                    published_at=datetime.now(timezone.utc),
                    author=None,
                    engagement_score=None,
                    raw_payload={"note": "Manual transcript entry required"},
                    status="pending",
                    last_extraction_error=None,
                    profile_id=None,
                    created_at=datetime.now(timezone.utc),
                )

                await self.firestore.set_document(
                    STYLISTIC_CONTENT_COLLECTION, content_id, content.to_firestore_dict()
                )
                return 1

        except Exception as e:
            logger.error(f"Failed to fetch podcast content: {e}", exc_info=True)
            return 0

    async def _extract_styles_from_source(self, source_id: str) -> int:
        """Extract style profiles from all pending content in a source."""
        try:
            # Get all pending content for this source
            contents_data = await self.firestore.query_collection(
                STYLISTIC_CONTENT_COLLECTION,
                filters=[("source_id", "==", source_id), ("status", "==", "pending")],
                limit=100,
            )

            if not contents_data:
                logger.info("No pending content found for style extraction")
                return 0

            logger.info(f"Extracting styles from {len(contents_data)} content items...")
            profiles_created = 0

            for data in contents_data:
                content_id = data.get("id")
                if not content_id:
                    continue

                try:
                    content = StylisticContent.from_firestore_dict(data, content_id)
                    word_count = len(content.raw_text.split())

                    # Handle long content by chunking
                    if word_count > MAX_CONTENT_LENGTH_WORDS:
                        profiles_created += await self._extract_from_long_content(content)
                    else:
                        profile = await self.extraction_service.extract_style_profile(content)
                        if profile:
                            profiles_created += 1

                except Exception as e:
                    logger.error(f"Failed to extract style from {content_id}: {e}")
                    continue

            logger.info(f"✓ Created {profiles_created} style profiles")
            return profiles_created

        except Exception as e:
            logger.error(f"Failed to extract styles from source {source_id}: {e}", exc_info=True)
            return 0

    async def _extract_from_long_content(self, content: StylisticContent) -> int:
        """Extract styles from long content by chunking."""
        text = content.raw_text
        words = text.split()
        total_words = len(words)
        num_chunks = (total_words // CHUNK_SIZE_WORDS) + 1

        # Sample chunks: beginning, middle sections, and end
        sample_indices = [0]
        if num_chunks > 2:
            middle_start = num_chunks // 3
            middle_end = (2 * num_chunks) // 3
            sample_indices.extend(
                range(middle_start, middle_end, max(1, (middle_end - middle_start) // 2))
            )
        if num_chunks > 1:
            sample_indices.append(num_chunks - 1)

        sample_indices = sorted(set(sample_indices))
        profiles_created = 0

        for idx in sample_indices:
            start_word = idx * CHUNK_SIZE_WORDS
            end_word = min(start_word + CHUNK_SIZE_WORDS, total_words)
            chunk_words = words[start_word:end_word]
            chunk_text = " ".join(chunk_words)

            if len(chunk_text.split()) < 100:
                continue

            # Create chunk content
            chunk_id = f"{content.id}-chunk-{idx}"
            chunk_content = StylisticContent(
                id=chunk_id,
                source_id=content.source_id,
                content_type=content.content_type,
                raw_text=chunk_text,
                source_url=content.source_url,
                published_at=content.published_at,
                author=content.author,
                engagement_score=content.engagement_score,
                raw_payload={
                    **content.raw_payload,
                    "chunk_index": idx,
                    "total_chunks": num_chunks,
                },
                status="pending",
                last_extraction_error=None,
                profile_id=None,
                created_at=datetime.now(timezone.utc),
            )

            # Save chunk content before extraction (allows retry on failure)
            await self.firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, chunk_id, chunk_content.to_firestore_dict()
            )

            try:
                profile = await self.extraction_service.extract_style_profile(chunk_content)
                if profile:
                    profiles_created += 1
            except Exception as e:
                logger.warning(f"Failed to extract from chunk {idx}: {e}")
                continue

        # Mark original content as processed
        content.status = "processed"
        await self.firestore.set_document(
            STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
        )

        return profiles_created

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
