"""
Test fixtures for topic scoring system.

These fixtures represent topics with known characteristics to enable
rapid, cost-free testing of scoring algorithms.
"""

from datetime import datetime, timedelta, timezone

from src.content.models import TopicCandidate


def create_test_topics() -> list[TopicCandidate]:
    """
    Create test topics with known characteristics.
    
    Returns:
        List of TopicCandidate objects with predictable scores
    """
    now = datetime.now(timezone.utc)
    
    topics = [
        # Test 1: Recent, high engagement, perfect audience fit
        TopicCandidate(
            id="test-recent-high-engagement-ai",
            source_platform="reddit",
            source_url="https://reddit.com/r/MachineLearning/test1",
            title="OpenAI Releases GPT-5 with Revolutionary Multimodal Capabilities",
            raw_payload={
                "score": 500,
                "num_comments": 200,
                "created_utc": (now - timedelta(hours=2)).timestamp(),
            },
            entities=["OpenAI", "GPT-5", "AI", "multimodal"],
            topic_cluster="ai-infra",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(hours=2),
        ),
        # Test 2: Recent, medium engagement, good audience fit
        TopicCandidate(
            id="test-recent-medium-engagement-business",
            source_platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=123",
            title="Tech Startup Raises $50M Series B to Expand AI Platform",
            raw_payload={
                "score": 150,
                "descendants": 45,
                "time": int((now - timedelta(hours=5)).timestamp()),
            },
            entities=["startup", "funding", "AI"],
            topic_cluster="business-socioeconomic",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(hours=5),
        ),
        # Test 3: Old topic, no engagement metrics (RSS)
        TopicCandidate(
            id="test-old-rss-no-engagement",
            source_platform="rss",
            source_url="https://example.com/old-news",
            title="Tech Industry Trends from Last Month",
            raw_payload={
                "feed": "https://example.com/feed",
                "entry": {"published": (now - timedelta(days=30)).isoformat()},
            },
            entities=[],
            topic_cluster="business-socioeconomic",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(days=30),
        ),
        # Test 4: Very recent, low engagement (new post)
        TopicCandidate(
            id="test-recent-low-engagement",
            source_platform="reddit",
            source_url="https://reddit.com/r/technology/test2",
            title="New JavaScript Framework Released",
            raw_payload={
                "score": 5,
                "num_comments": 2,
                "created_utc": (now - timedelta(minutes=30)).timestamp(),
            },
            entities=["JavaScript", "framework"],
            topic_cluster="ai-infra",  # Might be miscategorized
            detected_language="en",
            status="pending",
            created_at=now - timedelta(minutes=30),
        ),
        # Test 5: Medium recency, high engagement, good fit
        TopicCandidate(
            id="test-medium-recent-high-engagement",
            source_platform="hackernews",
            source_url="https://news.ycombinator.com/item?id=456",
            title="Major Cloud Provider Announces New AI Infrastructure",
            raw_payload={
                "score": 300,
                "descendants": 120,
                "time": int((now - timedelta(hours=12)).timestamp()),
            },
            entities=["cloud", "AI", "infrastructure"],
            topic_cluster="ai-infra",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(hours=12),
        ),
        # Test 6: Edge case - future timestamp (should use created_at)
        TopicCandidate(
            id="test-future-timestamp",
            source_platform="manual",
            source_url=None,
            title="Manually Added Topic for Testing",
            raw_payload={"notes": "Test topic"},
            entities=["test"],
            topic_cluster="business-socioeconomic",
            detected_language="en",
            status="pending",
            created_at=now,  # Use current time, not future
        ),
        # Test 7: Edge case - negative engagement (downvotes)
        TopicCandidate(
            id="test-negative-engagement",
            source_platform="reddit",
            source_url="https://reddit.com/r/test/test3",
            title="Controversial Topic with Downvotes",
            raw_payload={
                "score": -10,  # Negative score
                "num_comments": 50,
                "created_utc": (now - timedelta(hours=1)).timestamp(),
            },
            entities=["controversial"],
            topic_cluster="business-socioeconomic",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(hours=1),
        ),
        # Test 8: Edge case - zero engagement
        TopicCandidate(
            id="test-zero-engagement",
            source_platform="reddit",
            source_url="https://reddit.com/r/test/test4",
            title="New Post with No Engagement Yet",
            raw_payload={
                "score": 1,  # Just posted
                "num_comments": 0,
                "created_utc": (now - timedelta(minutes=5)).timestamp(),
            },
            entities=[],
            topic_cluster="ai-infra",
            detected_language="en",
            status="pending",
            created_at=now - timedelta(minutes=5),
        ),
    ]
    
    return topics

