"""
Prompt enhancement service for Content Engine.

Enhances prompts with stylistic context, with compression, validation, and safe fallback.
"""

from datetime import datetime, timezone

from ..core import get_logger, get_settings
from ..infra import FirestoreService
from .models import STYLE_PROFILES_COLLECTION, StyleProfile

logger = get_logger(__name__)

# In-memory cache for active profiles
_style_cache: dict[str, StyleProfile] = {}
_cache_updated_at: datetime | None = None
CACHE_TTL_SECONDS = 300  # 5 minutes


class PromptEnhancementService:
    """Enhance prompts with stylistic context."""

    def __init__(self, firestore: FirestoreService | None = None):
        """Initialize prompt enhancement service."""
        self.firestore = firestore or FirestoreService()
        self.settings = get_settings()

    async def enhance_prompt_safe(
        self,
        base_prompt: str,
        style_profile_id: str | None = None,
    ) -> str:
        """
        Enhance prompt with style, fallback to base if fails.

        Args:
            base_prompt: Base prompt to enhance
            style_profile_id: Optional style profile ID

        Returns:
            Enhanced prompt or base prompt if enhancement fails
        """
        # Feature flag check
        if not self.settings.enable_style_enhancement:
            return base_prompt

        # No style selected
        if not style_profile_id:
            return base_prompt

        try:
            # Fetch profile (with caching)
            profile = await self._get_profile_cached(style_profile_id)
            if not profile:
                logger.warning(f"Profile {style_profile_id} not found")
                return base_prompt

            # Check status
            if profile.status != "approved":
                logger.warning(f"Profile {style_profile_id} not approved (status: {profile.status})")
                return base_prompt

            # Validate style context
            if not self._validate_style_context(profile):
                logger.warning(f"Profile {style_profile_id} failed validation")
                return base_prompt

            # Build and compress style context
            style_context = self._build_and_compress_context(profile)

            # Enhance prompt
            enhanced = f"{base_prompt}\n\nSTYLISTIC CONTEXT:\n{style_context}\n\nWhen generating content, incorporate these stylistic elements naturally while maintaining the core message."

            return enhanced

        except Exception as e:
            # Always fallback - never fail
            logger.error(f"Style enhancement failed: {e}, using base prompt", exc_info=True)
            return base_prompt

    def _build_and_compress_context(self, profile: StyleProfile) -> str:
        """
        Build compressed style context (max tokens).

        Priority order:
        1. Tone (essential)
        2. Top 3 example phrases
        3. Literary devices (concise)
        4. Cultural markers (concise)
        """
        parts = []

        # 1. Tone (essential, ~20 tokens)
        if profile.tone:
            parts.append(f"Tone: {profile.tone}")

        # 2. Top 3 example phrases (~150 tokens)
        if profile.example_phrases:
            examples = profile.example_phrases[:3]
            examples_text = ', '.join(f'"{e[:100]}"' for e in examples)  # Truncate long phrases
            parts.append(f"Example phrases: {examples_text}")

        # 3. Literary devices (~50 tokens)
        if profile.literary_devices:
            devices = ', '.join(profile.literary_devices[:5])
            parts.append(f"Literary devices: {devices}")

        # 4. Cultural markers (~50 tokens)
        if profile.cultural_markers:
            markers = ', '.join(profile.cultural_markers[:5])
            parts.append(f"Cultural markers: {markers}")

        # Combine
        context = '\n'.join(parts)

        # Truncate to max tokens (rough estimate: 1 token ≈ 4 characters)
        max_chars = self.settings.max_style_context_tokens * 4
        if len(context) > max_chars:
            logger.warning(f"Style context truncated from {len(context)} to {max_chars} chars")
            context = context[:max_chars] + "..."

        return context

    def _validate_style_context(self, profile: StyleProfile) -> bool:
        """Validate style context is safe for injection."""
        # Check required fields
        if not profile.tone:
            return False

        # Check example phrases are reasonable
        if profile.example_phrases:
            for phrase in profile.example_phrases[:3]:
                if len(phrase) > 500:  # Too long
                    return False
                if not phrase.strip():  # Empty
                    return False

        return True

    async def _get_profile_cached(self, profile_id: str) -> StyleProfile | None:
        """Get profile with caching."""
        global _style_cache, _cache_updated_at

        # Refresh cache if stale
        if _cache_updated_at is None or (
            datetime.now(timezone.utc) - _cache_updated_at
        ).total_seconds() > CACHE_TTL_SECONDS:
            await self._refresh_cache()

        # Return from cache
        cached = _style_cache.get(profile_id)
        if cached:
            return cached

        # Not in cache, fetch from Firestore
        try:
            data = await self.firestore.get_document(STYLE_PROFILES_COLLECTION, profile_id)
            if data:
                profile = StyleProfile.from_firestore_dict(data, profile_id)
                # Add to cache
                _style_cache[profile_id] = profile
                return profile
        except Exception as e:
            logger.error(f"Failed to fetch profile {profile_id}: {e}")

        return None

    async def _refresh_cache(self) -> None:
        """Refresh cache with active approved profiles."""
        global _style_cache, _cache_updated_at

        try:
            # Fetch approved profiles
            profiles_data = await self.firestore.query_collection(
                STYLE_PROFILES_COLLECTION,
                filters=[("status", "==", "approved")],
                limit=100,  # Reasonable limit
            )

            _style_cache = {}
            for data in profiles_data:
                profile_id = data.get("id")
                if not profile_id:
                    logger.warning(f"Profile missing ID, skipping: {data.keys()}")
                    continue
                try:
                    profile = StyleProfile.from_firestore_dict(data, profile_id)
                    _style_cache[profile_id] = profile
                except Exception as e:
                    logger.error(f"Failed to parse profile {profile_id}: {e}")
                    continue

            _cache_updated_at = datetime.now(timezone.utc)
            logger.debug(f"Refreshed style cache with {len(_style_cache)} profiles")

        except Exception as e:
            logger.error(f"Failed to refresh style cache: {e}")

