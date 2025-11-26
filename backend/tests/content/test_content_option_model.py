"""Unit tests for ContentOption model enhancements."""

from datetime import datetime, timezone

import pytest

from src.content.models import ContentOption


def test_content_option_with_edited_content():
    """Test ContentOption with edited_content field."""
    option = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Original content",
        edited_content="Edited content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
        edited_at=datetime.now(timezone.utc),
        editor_id="user-123",
    )

    assert option.edited_content == "Edited content"
    assert option.edited_at is not None
    assert option.editor_id == "user-123"


def test_content_option_with_edit_history():
    """Test ContentOption with edit_history field."""
    edit_history = [
        {
            "timestamp": datetime.now(timezone.utc),
            "editor_id": "user-1",
            "change_type": "manual_edit",
        },
        {
            "timestamp": datetime.now(timezone.utc),
            "editor_id": "user-2",
            "change_type": "ai_refinement",
            "refinement_type": "tighten",
        },
    ]

    option = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
        edit_history=edit_history,
    )

    assert option.edit_history is not None
    assert len(option.edit_history) == 2
    assert option.edit_history[0]["change_type"] == "manual_edit"
    assert option.edit_history[1]["refinement_type"] == "tighten"


def test_content_option_with_refinement_applied():
    """Test ContentOption with refinement_applied field."""
    option = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
        refinement_applied=["tighten", "casual"],
    )

    assert option.refinement_applied is not None
    assert "tighten" in option.refinement_applied
    assert "casual" in option.refinement_applied
    assert len(option.refinement_applied) == 2


def test_content_option_to_firestore_dict_with_datetimes():
    """Test ContentOption serialization handles datetime fields correctly."""
    now = datetime.now(timezone.utc)
    option = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=now,
        edited_at=now,
        edit_history=[
            {
                "timestamp": now,
                "editor_id": "user-1",
                "change_type": "manual_edit",
            }
        ],
    )

    firestore_dict = option.to_firestore_dict()

    # Verify datetime fields are converted to ISO strings
    assert isinstance(firestore_dict["created_at"], str)
    assert isinstance(firestore_dict["edited_at"], str)
    assert isinstance(firestore_dict["edit_history"][0]["timestamp"], str)


def test_content_option_from_firestore_dict_with_datetimes():
    """Test ContentOption deserialization handles ISO string datetime fields."""
    now = datetime.now(timezone.utc)
    firestore_data = {
        "id": "test-1",
        "topic_id": "topic-1",
        "option_type": "short_script",
        "content": "Content",
        "prompt_version": "short_script_v1",
        "model": "gpt-4o-mini",
        "metadata": {},
        "created_at": now.isoformat(),
        "edited_at": now.isoformat(),
        "edit_history": [
            {
                "timestamp": now.isoformat(),
                "editor_id": "user-1",
                "change_type": "manual_edit",
            }
        ],
    }

    option = ContentOption.from_firestore_dict(firestore_data, "test-1")

    assert isinstance(option.created_at, datetime)
    assert isinstance(option.edited_at, datetime)
    assert isinstance(option.edit_history[0]["timestamp"], datetime)


def test_content_option_optional_fields_default_to_none():
    """Test that optional fields default to None when not provided."""
    option = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )

    assert option.edited_content is None
    assert option.edited_at is None
    assert option.editor_id is None
    assert option.edit_history is None
    assert option.refinement_applied is None


def test_content_option_round_trip_serialization():
    """Test that serialization and deserialization preserves all fields."""
    now = datetime.now(timezone.utc)
    original = ContentOption(
        id="test-1",
        topic_id="topic-1",
        option_type="short_script",
        content="Original content",
        edited_content="Edited content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={"key": "value"},
        created_at=now,
        edited_at=now,
        editor_id="user-123",
        edit_history=[
            {
                "timestamp": now,
                "editor_id": "user-1",
                "change_type": "ai_refinement",
                "refinement_type": "tighten",
            }
        ],
        refinement_applied=["tighten"],
    )

    # Serialize to Firestore dict
    firestore_dict = original.to_firestore_dict()

    # Deserialize from Firestore dict
    restored = ContentOption.from_firestore_dict(firestore_dict, "test-1")

    # Verify all fields match
    assert restored.id == original.id
    assert restored.topic_id == original.topic_id
    assert restored.option_type == original.option_type
    assert restored.content == original.content
    assert restored.edited_content == original.edited_content
    assert restored.editor_id == original.editor_id
    assert restored.edit_history is not None
    assert original.edit_history is not None
    assert len(restored.edit_history) == len(original.edit_history)
    assert restored.refinement_applied == original.refinement_applied

