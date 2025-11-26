"""
Script refinement service for Content Engine.

Provides AI-driven script refinement capabilities:
- Tighten: Make script more concise
- Casual: Adjust tone to be more conversational
- Regenerate: Full regeneration with same context
"""

from datetime import datetime, timezone
from typing import Literal

from ..core import get_logger
from ..infra import FirestoreService, OpenAIService
from .models import CONTENT_OPTIONS_COLLECTION, ContentOption

logger = get_logger(__name__)


class ScriptRefinementService:
    """Service for refining scripts using AI."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        openai_service: OpenAIService | None = None,
    ):
        """Initialize script refinement service."""
        self.firestore = firestore or FirestoreService()
        self.openai_service = openai_service or OpenAIService()

    async def refine_script(
        self,
        option_id: str,
        refinement_type: Literal["tighten", "casual", "regenerate"],
        editor_id: str | None = None,
    ) -> ContentOption:
        """
        Refine a script using AI.

        Args:
            option_id: ContentOption ID to refine
            refinement_type: Type of refinement to apply
            editor_id: User ID performing the refinement

        Returns:
            Updated ContentOption with edited_content set

        Raises:
            ValueError: If option not found or invalid refinement_type
        """
        # Fetch ContentOption
        option_data = await self.firestore.get_document(CONTENT_OPTIONS_COLLECTION, option_id)
        if not option_data:
            raise ValueError(f"ContentOption {option_id} not found")

        option = ContentOption.from_firestore_dict(option_data, option_id)

        # Ensure it's a script, not a hook
        if option.option_type != "short_script":
            raise ValueError(f"Can only refine scripts, not {option.option_type}")

        # Get base content (use edited_content if exists, otherwise content)
        base_content = option.edited_content or option.content

        # Build refinement prompt
        prompt = self._build_refinement_prompt(base_content, refinement_type, option)

        # Call LLM
        try:
            refined_content = await self.openai_service.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional script editor helping create engaging short-form video content. Maintain the core message while applying the requested refinement.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="gpt-4o-mini",
            )
        except Exception as e:
            logger.error(f"Failed to refine script {option_id}: {e}", exc_info=True)
            raise ValueError(f"AI refinement failed: {e}") from e

        # Update ContentOption
        now = datetime.now(timezone.utc)
        option.edited_content = refined_content.strip()
        option.edited_at = now
        if editor_id:
            option.editor_id = editor_id

        # Update edit_history
        if option.edit_history is None:
            option.edit_history = []
        option.edit_history.append(
            {
                "timestamp": now,
                "editor_id": editor_id or "system",
                "change_type": "ai_refinement",
                "refinement_type": refinement_type,
            }
        )

        # Update refinement_applied
        if option.refinement_applied is None:
            option.refinement_applied = []
        if refinement_type not in option.refinement_applied:
            option.refinement_applied.append(refinement_type)

        # Save to Firestore
        await self.firestore.set_document(
            CONTENT_OPTIONS_COLLECTION, option_id, option.to_firestore_dict()
        )

        logger.info(f"Refined script {option_id} with {refinement_type}")
        return option

    def _build_refinement_prompt(
        self, content: str, refinement_type: str, option: ContentOption
    ) -> str:
        """Build prompt for refinement."""
        base_instruction = f"Refine the following script for a short-form video:\n\n{content}\n\n"

        if refinement_type == "tighten":
            return (
                base_instruction
                + "Make this script more concise and punchy. Remove filler words and unnecessary phrases. "
                "Keep the core message and key points, but make every word count. Aim for 20-30% shorter."
            )
        elif refinement_type == "casual":
            return (
                base_instruction
                + "Adjust the tone to be more conversational and casual. Make it sound like you're talking to a friend, "
                "not reading from a script. Keep it engaging and natural while maintaining the core message."
            )
        elif refinement_type == "regenerate":
            return (
                base_instruction
                + "Regenerate this script with fresh wording while keeping the same core message and structure. "
                "Make it feel new and engaging while preserving all key points."
            )
        else:
            raise ValueError(f"Unknown refinement_type: {refinement_type}")

    async def update_script_content(
        self, option_id: str, content: str, editor_id: str | None = None
    ) -> ContentOption:
        """
        Update script content manually (non-AI edit).

        Args:
            option_id: ContentOption ID to update
            content: New content
            editor_id: User ID performing the edit

        Returns:
            Updated ContentOption

        Raises:
            ValueError: If option not found
        """
        # Fetch ContentOption
        option_data = await self.firestore.get_document(CONTENT_OPTIONS_COLLECTION, option_id)
        if not option_data:
            raise ValueError(f"ContentOption {option_id} not found")

        option = ContentOption.from_firestore_dict(option_data, option_id)

        # Ensure it's a script
        if option.option_type != "short_script":
            raise ValueError(f"Can only edit scripts, not {option.option_type}")

        # Update ContentOption
        now = datetime.now(timezone.utc)
        option.edited_content = content
        option.edited_at = now
        if editor_id:
            option.editor_id = editor_id

        # Update edit_history
        if option.edit_history is None:
            option.edit_history = []
        option.edit_history.append(
            {
                "timestamp": now,
                "editor_id": editor_id or "system",
                "change_type": "manual_edit",
            }
        )

        # Save to Firestore
        await self.firestore.set_document(
            CONTENT_OPTIONS_COLLECTION, option_id, option.to_firestore_dict()
        )

        logger.info(f"Updated script {option_id} manually")
        return option

