"""Unit tests for script refinement service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.content.models import ContentOption
from src.content.script_refinement_service import ScriptRefinementService


@pytest.fixture
def sample_content_option():
    """Sample ContentOption for testing."""
    return ContentOption(
        id="test-script-1",
        topic_id="test-topic-1",
        option_type="short_script",
        content="This is a test script. It has multiple sentences. We can refine it.",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_firestore_service():
    """Mock FirestoreService for testing."""
    service = AsyncMock()
    service.get_document = AsyncMock()
    service.set_document = AsyncMock()
    return service


@pytest.fixture
def mock_openai_service():
    """Mock OpenAIService for testing."""
    service = AsyncMock()
    service.chat = AsyncMock(return_value="Refined script content")
    return service


@pytest.mark.asyncio
async def test_refine_script_tighten_success(
    mock_firestore_service, mock_openai_service, sample_content_option
):
    """Test successful script refinement with 'tighten' type."""
    # Setup mocks
    mock_firestore_service.get_document.return_value = sample_content_option.to_firestore_dict()
    mock_openai_service.chat.return_value = "Tightened script content"

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    result = await service.refine_script("test-script-1", "tighten", editor_id="user-123")

    # Verify OpenAI was called with correct prompt
    assert mock_openai_service.chat.called
    call_args = mock_openai_service.chat.call_args
    prompt_content = call_args[1]["messages"][1]["content"].lower()
    assert "concise" in prompt_content or "shorter" in prompt_content

    # Verify ContentOption was updated
    assert result.edited_content == "Tightened script content"
    assert result.edited_at is not None
    assert result.editor_id == "user-123"
    assert result.edit_history is not None
    assert len(result.edit_history) == 1
    assert result.edit_history[0]["change_type"] == "ai_refinement"
    assert result.edit_history[0]["refinement_type"] == "tighten"
    assert result.refinement_applied is not None
    assert "tighten" in result.refinement_applied

    # Verify Firestore was updated
    assert mock_firestore_service.set_document.called


@pytest.mark.asyncio
async def test_refine_script_casual_success(
    mock_firestore_service, mock_openai_service, sample_content_option
):
    """Test successful script refinement with 'casual' type."""
    mock_firestore_service.get_document.return_value = sample_content_option.to_firestore_dict()
    mock_openai_service.chat.return_value = "Casual script content"

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    result = await service.refine_script("test-script-1", "casual")

    # Verify prompt contains casual instructions
    call_args = mock_openai_service.chat.call_args
    assert "casual" in call_args[1]["messages"][1]["content"].lower()
    assert "conversational" in call_args[1]["messages"][1]["content"].lower()

    assert result.edited_content == "Casual script content"
    assert result.refinement_applied is not None
    assert "casual" in result.refinement_applied


@pytest.mark.asyncio
async def test_refine_script_regenerate_success(
    mock_firestore_service, mock_openai_service, sample_content_option
):
    """Test successful script refinement with 'regenerate' type."""
    mock_firestore_service.get_document.return_value = sample_content_option.to_firestore_dict()
    mock_openai_service.chat.return_value = "Regenerated script content"

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    result = await service.refine_script("test-script-1", "regenerate")

    # Verify prompt contains regenerate instructions
    call_args = mock_openai_service.chat.call_args
    assert "regenerate" in call_args[1]["messages"][1]["content"].lower()

    assert result.edited_content == "Regenerated script content"
    assert result.refinement_applied is not None
    assert "regenerate" in result.refinement_applied


@pytest.mark.asyncio
async def test_refine_script_uses_edited_content_if_exists(
    mock_firestore_service, mock_openai_service
):
    """Test that refinement uses edited_content if it exists."""
    option_with_edit = ContentOption(
        id="test-script-1",
        topic_id="test-topic-1",
        option_type="short_script",
        content="Original content",
        edited_content="Edited content",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )

    mock_firestore_service.get_document.return_value = option_with_edit.to_firestore_dict()
    mock_openai_service.chat.return_value = "Refined content"

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    await service.refine_script("test-script-1", "tighten")

    # Verify OpenAI was called with edited_content, not original content
    call_args = mock_openai_service.chat.call_args
    assert "Edited content" in call_args[1]["messages"][1]["content"]
    assert "Original content" not in call_args[1]["messages"][1]["content"]


@pytest.mark.asyncio
async def test_refine_script_option_not_found(mock_firestore_service, mock_openai_service):
    """Test refinement fails when ContentOption not found."""
    mock_firestore_service.get_document.return_value = None

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    with pytest.raises(ValueError, match="ContentOption.*not found"):
        await service.refine_script("non-existent", "tighten")


@pytest.mark.asyncio
async def test_refine_script_invalid_option_type(mock_firestore_service, mock_openai_service):
    """Test refinement fails for non-script ContentOption."""
    hook_option = ContentOption(
        id="test-hook-1",
        topic_id="test-topic-1",
        option_type="short_hook",
        content="Test hook",
        prompt_version="short_hook_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )

    mock_firestore_service.get_document.return_value = hook_option.to_firestore_dict()

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    with pytest.raises(ValueError, match="Can only refine scripts"):
        await service.refine_script("test-hook-1", "tighten")


@pytest.mark.asyncio
async def test_refine_script_openai_failure(mock_firestore_service, mock_openai_service, sample_content_option):
    """Test refinement handles OpenAI API failures."""
    mock_firestore_service.get_document.return_value = sample_content_option.to_firestore_dict()
    mock_openai_service.chat.side_effect = Exception("OpenAI API error")

    service = ScriptRefinementService(
        firestore=mock_firestore_service, openai_service=mock_openai_service
    )

    with pytest.raises(ValueError, match="AI refinement failed"):
        await service.refine_script("test-script-1", "tighten")


@pytest.mark.asyncio
async def test_update_script_content_success(
    mock_firestore_service, sample_content_option
):
    """Test successful manual script content update."""
    mock_firestore_service.get_document.return_value = sample_content_option.to_firestore_dict()

    service = ScriptRefinementService(firestore=mock_firestore_service)

    result = await service.update_script_content(
        "test-script-1", "Updated manual content", editor_id="user-456"
    )

    assert result.edited_content == "Updated manual content"
    assert result.edited_at is not None
    assert result.editor_id == "user-456"
    assert len(result.edit_history) == 1
    assert result.edit_history[0]["change_type"] == "manual_edit"
    assert "refinement_type" not in result.edit_history[0]

    assert mock_firestore_service.set_document.called


@pytest.mark.asyncio
async def test_update_script_content_appends_to_history(
    mock_firestore_service, sample_content_option
):
    """Test that manual updates append to existing edit history."""
    option_with_history = ContentOption(
        id="test-script-1",
        topic_id="test-topic-1",
        option_type="short_script",
        content="Original",
        prompt_version="short_script_v1",
        model="gpt-4o-mini",
        metadata={},
        created_at=datetime.now(timezone.utc),
        edit_history=[
            {
                "timestamp": datetime.now(timezone.utc),
                "editor_id": "user-1",
                "change_type": "ai_refinement",
                "refinement_type": "tighten",
            }
        ],
    )

    mock_firestore_service.get_document.return_value = option_with_history.to_firestore_dict()

    service = ScriptRefinementService(firestore=mock_firestore_service)

    result = await service.update_script_content("test-script-1", "New content")

    assert result.edit_history is not None
    assert len(result.edit_history) == 2
    assert result.edit_history[1]["change_type"] == "manual_edit"


@pytest.mark.asyncio
async def test_build_refinement_prompt_invalid_type(mock_firestore_service, sample_content_option):
    """Test that invalid refinement type raises error."""
    service = ScriptRefinementService(firestore=mock_firestore_service)

    with pytest.raises(ValueError, match="Unknown refinement_type"):
        service._build_refinement_prompt("content", "invalid_type", sample_content_option)

