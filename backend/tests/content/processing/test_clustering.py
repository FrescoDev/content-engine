"""Unit tests for clustering service."""

import pytest

from src.content.processing.clustering import TopicClusterer


def test_cluster_topic_ai_infra():
    """Test clustering to ai-infra."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("OpenAI Releases GPT-4", ["OpenAI", "GPT-4"])

    assert cluster == "ai-infra"


def test_cluster_topic_business_socioeconomic():
    """Test clustering to business-socioeconomic."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("Tech Startup Raises $100M Series A", [])

    assert cluster == "business-socioeconomic"


def test_cluster_topic_culture_music():
    """Test clustering to culture-music."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("New Album Release Wins Grammy Award", [])

    assert cluster == "culture-music"


def test_cluster_topic_applied_industry():
    """Test clustering to applied-industry."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("New Insurance Policy Changes", [])

    assert cluster == "applied-industry"


def test_cluster_topic_meta_content_intel():
    """Test clustering to meta-content-intel."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("Social Media Algorithm Changes", [])

    assert cluster == "meta-content-intel"


def test_cluster_topic_default_fallback():
    """Test default fallback when no keywords match."""
    clusterer = TopicClusterer()

    cluster = clusterer.cluster_topic("Random Unrelated Topic", [])

    assert cluster == "business-socioeconomic"  # Default fallback


def test_cluster_topic_entity_influence():
    """Test that entities influence clustering."""
    clusterer = TopicClusterer()

    # Title alone might not match, but entities help
    cluster = clusterer.cluster_topic("New Release", ["GPT-4", "OpenAI"])

    assert cluster == "ai-infra"


def test_cluster_topic_highest_score():
    """Test that highest scoring cluster wins."""
    clusterer = TopicClusterer()

    # Title has both AI and business keywords
    cluster = clusterer.cluster_topic("AI Startup Raises Funding for Machine Learning Platform", [])

    # Should pick cluster with most matches
    assert cluster in ["ai-infra", "business-socioeconomic"]
