"""
Style curation service for Content Engine.

Manages human curation of style profiles with soft delete and validation.
"""

from datetime import datetime, timezone
from typing import Any

from ..core import get_logger
from ..infra import FirestoreService
from .models import STYLE_PROFILES_COLLECTION, StyleProfile

logger = get_logger(__name__)


class StyleCurationService:
    """Manage human curation of style profiles."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize style curation service."""
        self.firestore = firestore or FirestoreService()

    async def approve_profile(
        self, profile_id: str, curator_id: str, notes: str | None = None
    ) -> StyleProfile:
        """
        Approve a style profile.

        Args:
            profile_id: Profile ID to approve
            curator_id: User ID performing the curation
            notes: Optional curator notes

        Returns:
            Updated StyleProfile

        Raises:
            ValueError: If profile not found
        """
        profile_data = await self.firestore.get_document(STYLE_PROFILES_COLLECTION, profile_id)
        if not profile_data:
            raise ValueError(f"StyleProfile {profile_id} not found")

        profile = StyleProfile.from_firestore_dict(profile_data, profile_id)

        # Validate quality before approval (warn but allow)
        is_valid, issues = self._validate_profile_quality(profile)
        if not is_valid:
            logger.warning(f"Approving profile {profile_id} with quality issues: {issues}")

        # Update profile
        profile.status = "approved"
        profile.curated_by = curator_id
        profile.curated_at = datetime.now(timezone.utc)
        profile.curator_notes = notes
        profile.updated_at = datetime.now(timezone.utc)

        await self.firestore.set_document(
            STYLE_PROFILES_COLLECTION, profile_id, profile.to_firestore_dict()
        )

        logger.info(f"Approved style profile {profile_id} by {curator_id}")
        return profile

    async def reject_profile(
        self, profile_id: str, curator_id: str, reason: str
    ) -> StyleProfile:
        """
        Reject a style profile.

        Args:
            profile_id: Profile ID to reject
            curator_id: User ID performing the curation
            reason: Rejection reason

        Returns:
            Updated StyleProfile

        Raises:
            ValueError: If profile not found
        """
        profile_data = await self.firestore.get_document(STYLE_PROFILES_COLLECTION, profile_id)
        if not profile_data:
            raise ValueError(f"StyleProfile {profile_id} not found")

        profile = StyleProfile.from_firestore_dict(profile_data, profile_id)

        # Update profile
        profile.status = "rejected"
        profile.curated_by = curator_id
        profile.curated_at = datetime.now(timezone.utc)
        profile.curator_notes = reason
        profile.updated_at = datetime.now(timezone.utc)

        await self.firestore.set_document(
            STYLE_PROFILES_COLLECTION, profile_id, profile.to_firestore_dict()
        )

        logger.info(f"Rejected style profile {profile_id} by {curator_id}")
        return profile

    async def archive_profile(self, profile_id: str, curator_id: str) -> StyleProfile:
        """
        Archive profile (soft delete) with validation.

        Args:
            profile_id: Profile ID to archive
            curator_id: User ID performing the archive

        Returns:
            Updated StyleProfile

        Raises:
            ValueError: If profile not found or used in content
        """
        profile_data = await self.firestore.get_document(STYLE_PROFILES_COLLECTION, profile_id)
        if not profile_data:
            raise ValueError(f"StyleProfile {profile_id} not found")

        profile = StyleProfile.from_firestore_dict(profile_data, profile_id)

        # Check if used in content generation (check ContentOption metadata)
        # For MVP, we'll do a simple check - can enhance later
        usage_count = await self._count_profile_usage(profile_id)
        if usage_count > 0:
            raise ValueError(
                f"Cannot archive: profile used in {usage_count} content generations. "
                "Consider marking as 'rejected' instead."
            )

        # Archive
        profile.status = "archived"
        profile.archived_at = datetime.now(timezone.utc)
        profile.curated_by = curator_id
        profile.curated_at = datetime.now(timezone.utc)
        profile.updated_at = datetime.now(timezone.utc)

        await self.firestore.set_document(
            STYLE_PROFILES_COLLECTION, profile_id, profile.to_firestore_dict()
        )

        logger.info(f"Archived style profile {profile_id} by {curator_id}")
        return profile

    async def edit_profile(
        self, profile_id: str, curator_id: str, edits: dict[str, Any]
    ) -> StyleProfile:
        """
        Manually edit a style profile.

        Args:
            profile_id: Profile ID to edit
            curator_id: User ID performing the edit
            edits: Dictionary of fields to update

        Returns:
            Updated StyleProfile

        Raises:
            ValueError: If profile not found
        """
        profile_data = await self.firestore.get_document(STYLE_PROFILES_COLLECTION, profile_id)
        if not profile_data:
            raise ValueError(f"StyleProfile {profile_id} not found")

        profile = StyleProfile.from_firestore_dict(profile_data, profile_id)

        # Apply edits
        for key, value in edits.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        # Auto-approve if edited
        if profile.status == "pending":
            profile.status = "approved"

        profile.curated_by = curator_id
        profile.curated_at = datetime.now(timezone.utc)
        profile.updated_at = datetime.now(timezone.utc)

        await self.firestore.set_document(
            STYLE_PROFILES_COLLECTION, profile_id, profile.to_firestore_dict()
        )

        logger.info(f"Edited style profile {profile_id} by {curator_id}")
        return profile

    def _validate_profile_quality(self, profile: StyleProfile) -> tuple[bool, list[str]]:
        """Validate profile quality."""
        issues = []

        # Required fields
        if not profile.tone:
            issues.append("Missing tone")

        if len(profile.example_phrases) < 3:
            issues.append(f"Too few example phrases ({len(profile.example_phrases)} < 3)")

        if len(profile.literary_devices) == 0:
            issues.append("No literary devices identified")

        # Quality checks
        if profile.example_phrases:
            generic = ["check this out", "let's talk", "this is"]
            if all(
                any(g in p.lower() for g in generic) for p in profile.example_phrases[:3]
            ):
                issues.append("Example phrases too generic")

        return len(issues) == 0, issues

    async def _count_profile_usage(self, profile_id: str) -> int:
        """
        Count how many times profile is used in content generation.

        For MVP, we'll check ContentOption metadata for style_profile_id.
        """
        from .models import CONTENT_OPTIONS_COLLECTION

        try:
            # Query ContentOptions with this style_profile_id in metadata
            options = await self.firestore.query_collection(
                CONTENT_OPTIONS_COLLECTION,
                filters=[("metadata.style_profile_id", "==", profile_id)],
            )
            return len(options)
        except Exception as e:
            logger.warning(f"Failed to count profile usage: {e}")
            return 0  # Assume not used if we can't check

