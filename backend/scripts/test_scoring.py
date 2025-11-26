#!/usr/bin/env python3
"""
Test scoring system with fixtures.

This script allows rapid, cost-free testing of the scoring algorithm
by using test fixtures instead of real topics or LLM calls.
"""

import sys
from pathlib import Path
from typing import Any

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.content.scoring_service import ScoringService
from src.core import get_logger
from tests.fixtures.scoring_test_topics import create_test_topics

logger = get_logger(__name__)


def format_score_breakdown(result: dict[str, Any], topic_title: str) -> str:
    """Format score breakdown for display."""
    components = result["components"]
    reasoning = result["reasoning"]
    score = result["score"]
    weights = result["weights"]
    
    lines = [
        f"\n{'='*70}",
        f"Topic: {topic_title[:60]}",
        f"{'='*70}",
        f"Composite Score: {score:.3f}",
        "",
        "Components:",
        f"  Recency:        {components['recency']:.3f} (weight: {weights['recency']:.2f})",
        f"    → {reasoning['recency']}",
        f"  Velocity:       {components['velocity']:.3f} (weight: {weights['velocity']:.2f})",
        f"    → {reasoning['velocity']}",
        f"  Audience Fit:   {components['audience_fit']:.3f} (weight: {weights['audience_fit']:.2f})",
        f"    → {reasoning['audience_fit']}",
        f"  Integrity:      {components['integrity_penalty']:.3f}",
        f"    → {reasoning['integrity_penalty']}",
        "",
        f"Calculation:",
        f"  ({weights['recency']:.2f} × {components['recency']:.3f}) + "
        f"({weights['velocity']:.2f} × {components['velocity']:.3f}) + "
        f"({weights['audience_fit']:.2f} × {components['audience_fit']:.3f}) + "
        f"{components['integrity_penalty']:.3f} = {score:.3f}",
    ]
    
    return "\n".join(lines)


def main():
    """Run scoring tests on fixtures."""
    logger.info("=" * 70)
    logger.info("TOPIC SCORING TEST HARNESS")
    logger.info("=" * 70)
    
    # Create test topics
    test_topics = create_test_topics()
    logger.info(f"\nCreated {len(test_topics)} test topics")
    
    # Initialize scoring service
    scoring_service = ScoringService()
    
    # Score all topics
    results = []
    for topic in test_topics:
        try:
            result = scoring_service.score_topic(topic, all_topics=test_topics)
            results.append((topic, result))
            logger.info(format_score_breakdown(result, topic.title))
        except Exception as e:
            logger.error(f"Failed to score topic {topic.id}: {e}", exc_info=True)
            results.append((topic, None))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    successful = [r for r in results if r[1] is not None]
    failed = [r for r in results if r[1] is None]
    
    logger.info(f"✅ Successfully scored: {len(successful)}/{len(results)}")
    if failed:
        logger.warning(f"❌ Failed to score: {len(failed)} topics")
        for topic, _ in failed:
            logger.warning(f"  - {topic.id}: {topic.title}")
    
    # Rank by score
    if successful:
        ranked = sorted(successful, key=lambda x: x[1]["score"], reverse=True)
        logger.info("\nRanked Topics (by composite score):")
        for i, (topic, result) in enumerate(ranked, 1):
            logger.info(
                f"  #{i}: {result['score']:.3f} - {topic.title[:50]} "
                f"({topic.source_platform}, {topic.topic_cluster})"
            )
    
    logger.info("\n" + "=" * 70)
    logger.info("Test complete!")
    logger.info("=" * 70)
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

