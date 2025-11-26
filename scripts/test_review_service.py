#!/usr/bin/env python3
"""
Test the review service functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.content.review_service import ReviewService
from src.core import get_logger

logger = get_logger(__name__)


async def test_review_service():
    """Test review service fetching."""
    service = ReviewService()

    print(f"\n{'='*60}")
    print("REVIEW SERVICE TEST")
    print(f"{'='*60}\n")

    # Test fetching topic review batch
    print("Fetching topic review batch (limit=10, status=pending)...")
    topics = await service.fetch_topic_review_batch(limit=10, status="pending")

    print(f"\n✓ Fetched {len(topics)} topics\n")

    if topics:
        print("Sample topics with scores:")
        for i, item in enumerate(topics[:5], 1):
            topic = item.get("topic", {})
            score = item.get("score")
            print(f"\n{i}. {topic.get('title', 'No title')}")
            print(f"   Platform: {topic.get('source_platform', 'N/A')}")
            print(f"   Status: {topic.get('status', 'N/A')}")
            if score:
                print(f"   Score: {score.get('total_score', 'N/A')}")
                print(
                    f"   Components: recency={score.get('recency_score', 'N/A')}, "
                    f"velocity={score.get('velocity_score', 'N/A')}, "
                    f"audience_fit={score.get('audience_fit_score', 'N/A')}"
                )
            else:
                print(f"   Score: No score available yet")
    else:
        print("No topics found.")


async def main():
    """Run test."""
    try:
        await test_review_service()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
