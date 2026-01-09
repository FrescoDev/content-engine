"""Unit tests for entity extraction service."""

import pytest

from src.content.processing.entity_extraction import EntityExtractor


def test_extract_entities_tech_company():
    """Test extraction of tech company entities."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("Google Announces New AI Model")

    assert "Google" in entities


def test_extract_entities_ai_model():
    """Test extraction of AI model entities."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("OpenAI Releases GPT-4 with New Features")

    assert "GPT-4" in entities
    assert "OpenAI" in entities


def test_extract_entities_multiple():
    """Test extraction of multiple entities."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("Microsoft and OpenAI Partner on GPT-4 Integration")

    assert "Microsoft" in entities
    assert "OpenAI" in entities
    assert "GPT-4" in entities


def test_extract_entities_case_insensitive():
    """Test that extraction is case-insensitive."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("google announces new features")

    assert "Google" in entities


def test_extract_entities_no_matches():
    """Test extraction when no entities found."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("Random News Article About Weather")

    assert entities == []


def test_extract_entities_deduplication():
    """Test that duplicate entities are deduplicated."""
    extractor = EntityExtractor()

    entities = extractor.extract_entities("OpenAI OpenAI GPT-4 GPT-4")

    assert entities.count("OpenAI") == 1
    assert entities.count("GPT-4") == 1




