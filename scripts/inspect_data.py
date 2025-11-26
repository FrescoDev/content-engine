#!/usr/bin/env python3
"""
Inspect data in Firestore to verify functionality.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.content.models import TOPIC_CANDIDATES_COLLECTION
from src.core import get_logger
from src.infra import FirestoreService

logger = get_logger(__name__)


async def inspect_topics():
    """Inspect topic candidates in Firestore."""
    firestore = FirestoreService()

    # Get all topics
    topics = await firestore.query_collection(
        TOPIC_CANDIDATES_COLLECTION,
        limit=100,
        order_by="created_at",
        order_direction="DESCENDING",
    )

    print(f"\n{'='*60}")
    print(f"TOPIC CANDIDATES INSPECTION")
    print(f"{'='*60}")
    print(f"\nTotal topics found: {len(topics)}\n")

    if not topics:
        print("No topics found in Firestore.")
        return

    # Statistics
    by_platform = {}
    by_status = {}
    by_cluster = {}

    for topic in topics:
        platform = topic.get("source_platform", "unknown")
        status = topic.get("status", "unknown")
        cluster = topic.get("topic_cluster", "unknown")

        by_platform[platform] = by_platform.get(platform, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        by_cluster[cluster] = by_cluster.get(cluster, 0) + 1

    print("STATISTICS:")
    print(f"\nBy Platform:")
    for platform, count in sorted(by_platform.items(), key=lambda x: -x[1]):
        print(f"  {platform:15} {count:3} topics")

    print(f"\nBy Status:")
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {status:15} {count:3} topics")

    print(f"\nBy Cluster (top 10):")
    for cluster, count in sorted(by_cluster.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cluster:30} {count:3} topics")

    # Sample topics
    print(f"\n{'='*60}")
    print("SAMPLE TOPICS (first 10):")
    print(f"{'='*60}\n")

    for i, topic in enumerate(topics[:10], 1):
        print(
            f"{i}. [{topic.get('source_platform', 'unknown').upper()}] {topic.get('title', 'No title')}"
        )
        print(f"   ID: {topic.get('id', 'N/A')}")
        print(f"   Status: {topic.get('status', 'N/A')}")
        print(f"   Cluster: {topic.get('topic_cluster', 'N/A')}")
        print(f"   Created: {topic.get('created_at', 'N/A')}")
        if topic.get("source_url"):
            print(f"   URL: {topic.get('source_url')}")
        if topic.get("entities"):
            print(f"   Entities: {', '.join(topic.get('entities', [])[:5])}")
        print()

    # Detailed view of one topic
    if topics:
        print(f"{'='*60}")
        print("DETAILED VIEW (first topic):")
        print(f"{'='*60}\n")
        sample = topics[0]
        print(json.dumps(sample, indent=2, default=str))
        print()


async def main():
    """Run inspection."""
    try:
        await inspect_topics()
    except Exception as e:
        logger.error(f"Inspection failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
