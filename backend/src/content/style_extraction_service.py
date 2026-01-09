"""
Style extraction service for Content Engine.

Extracts stylistic patterns from content using LLMs with robust error handling,
cost tracking, and quality validation.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core import get_logger, get_settings
from ..infra import FirestoreService, OpenAIService
from .models import (
    STYLE_PROFILES_COLLECTION,
    STYLISTIC_CONTENT_COLLECTION,
    StyleProfile,
    StylisticContent,
)

logger = get_logger(__name__)

# Constants
MAX_CONTENT_LENGTH_WORDS = 2000
MIN_CONTENT_LENGTH_WORDS = 100
EXTRACTION_PROMPT_VERSION = "extraction_v1"


class StyleExtractionService:
    """Extract stylistic patterns from content using LLMs."""

    def __init__(
        self,
        firestore: FirestoreService | None = None,
        openai_service: OpenAIService | None = None,
    ):
        """Initialize style extraction service."""
        self.firestore = firestore or FirestoreService()
        self.openai_service = openai_service or OpenAIService()
        self.settings = get_settings()

    async def extract_style_profile(self, content: StylisticContent) -> StyleProfile | None:
        """
        Extract style profile from content with validation and error handling.

        Args:
            content: StylisticContent to extract from

        Returns:
            StyleProfile if successful, None if skipped/failed
        """
        # Validate content length
        word_count = len(content.raw_text.split())
        if word_count > MAX_CONTENT_LENGTH_WORDS:
            logger.warning(f"Content {content.id} too long ({word_count} words), skipping")
            content.status = "skipped"
            content.last_extraction_error = (
                f"Content too long ({word_count} > {MAX_CONTENT_LENGTH_WORDS} words)"
            )
            await self.firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
            )
            return None

        if word_count < MIN_CONTENT_LENGTH_WORDS:
            logger.warning(f"Content {content.id} too short ({word_count} words), skipping")
            content.status = "skipped"
            content.last_extraction_error = (
                f"Content too short ({word_count} < {MIN_CONTENT_LENGTH_WORDS} words)"
            )
            await self.firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
            )
            return None

        # Check daily cost limit
        daily_cost = await self._get_daily_extraction_cost()
        if daily_cost >= self.settings.max_daily_extraction_cost:
            logger.warning(f"Daily extraction cost limit reached (${daily_cost:.2f})")
            return None

        # Update status to processing
        content.status = "processing"
        content.extraction_attempts += 1
        await self.firestore.set_document(
            STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
        )

        try:
            # Extract with cost tracking
            profile, cost_info = await self._extract_with_cost_tracking(content)

            # Validate quality
            is_valid, issues = self._validate_profile_quality(profile)
            if not is_valid:
                profile.status = "needs_review"
                profile.quality_issues = issues
                logger.warning(f"Profile {profile.id} quality issues: {issues}")

            # Save profile
            await self.firestore.set_document(
                STYLE_PROFILES_COLLECTION, profile.id, profile.to_firestore_dict()
            )

            # Update content status
            content.status = "processed"
            content.profile_id = profile.id
            await self.firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
            )

            logger.info(
                f"Extracted style profile {profile.id} from content {content.id} (cost: ${cost_info['cost_usd']:.4f})"
            )
            return profile

        except Exception as e:
            # Handle failure gracefully
            logger.error(f"Extraction failed for content {content.id}: {e}", exc_info=True)
            content.status = "failed"
            content.last_extraction_error = str(e)
            await self.firestore.set_document(
                STYLISTIC_CONTENT_COLLECTION, content.id, content.to_firestore_dict()
            )

            # Create empty profile for manual review
            return await self._create_empty_profile(content, error=str(e))

    async def _extract_with_cost_tracking(
        self, content: StylisticContent
    ) -> tuple[StyleProfile, dict[str, Any]]:
        """Extract style profile with cost tracking."""
        # Build extraction prompt
        prompt = self._build_extraction_prompt(content)

        # Call LLM with structured output
        messages = [
            {
                "role": "system",
                "content": "You are a stylistic analyst. Analyze content and extract stylistic characteristics in detail. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ]

        response, cost_info = await self.openai_service.chat_with_cost_tracking(
            messages=messages,
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent extraction
        )

        # Parse response
        try:
            extracted_data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}\nResponse: {response[:200]}")
            raise ValueError(f"Invalid JSON response: {e}") from e

        # Create StyleProfile
        profile_id = self._generate_profile_id(content)
        profile = StyleProfile(
            id=profile_id,
            source_content_id=content.id,
            source_id=content.source_id,
            source_name=extracted_data.get("source_name", "unknown"),
            writing_style=extracted_data.get("writing_style", {}),
            speaking_style=extracted_data.get("speaking_style", {}),
            literary_devices=extracted_data.get("literary_devices", []),
            cultural_markers=extracted_data.get("cultural_markers", []),
            tone=extracted_data.get("tone", "casual"),
            voice_characteristics=extracted_data.get("voice_characteristics", {}),
            example_phrases=extracted_data.get("example_phrases", []),
            example_patterns=extracted_data.get("example_patterns", []),
            status="pending",
            curator_notes=None,
            curated_by=None,
            curated_at=None,
            quality_score=None,
            tags=extracted_data.get("tags", []),
            category=extracted_data.get("category"),
            extraction_model="gpt-4o-mini",
            extraction_prompt_version=EXTRACTION_PROMPT_VERSION,
            extraction_cost_usd=cost_info["cost_usd"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            archived_at=None,
        )

        return profile, cost_info

    def _build_extraction_prompt(self, content: StylisticContent) -> str:
        """Build extraction prompt."""
        # Actually truncate content to prevent token limit issues
        truncated_content = content.raw_text[:3000]
        if len(content.raw_text) > 3000:
            truncated_content += "... [truncated]"

        return f"""Analyze the following content and extract its stylistic characteristics in detail.

CONTENT:
{truncated_content}

Extract the following stylistic elements:

1. WRITING STYLE:
   - Sentence structure: Are sentences short/punchy or long/complex? Fragments used?
   - Vocabulary level: Formal, casual, technical, slang-heavy?
   - Formality: Very formal, casual, conversational, intimate?
   - Punctuation patterns: Heavy use of exclamation, ellipses, em dashes?
   - Paragraph organization: How are ideas structured?

2. SPEAKING STYLE (if applicable):
   - Natural speech patterns: Filler words, pauses, interruptions?
   - Conversational flow: How does the speaker transition between ideas?
   - Tone and inflection cues: What emotions/attitudes are conveyed?
   - Pace: Fast-paced, measured, dramatic pauses?

3. LITERARY DEVICES:
   - Humor type: Dry, witty, absurd, self-deprecating, dark, observational?
   - Wordplay: Puns, double entendres, clever phrasing?
   - Alliteration/rhythm: Use of sound patterns?
   - Metaphors/analogies: How are comparisons made?
   - Comedic timing: Where are jokes/punchlines placed?

4. CULTURAL MARKERS:
   - References: Pop culture, memes, current events, historical?
   - Trends: What's trendy/cool in this content?
   - Slang: Specific terms, phrases, expressions?
   - Generational language: Boomer, Gen X, Millennial, Gen Z markers?
   - Platform conventions: Reddit-speak, podcast banter, etc.?

5. TONE AND VOICE:
   - Overall tone: Casual, serious, comedic, educational, inspirational?
   - Voice characteristics: Authoritative, humble, confident, self-aware?
   - Audience relationship: Peer-to-peer, teacher-student, friend-to-friend?

6. EXAMPLE PHRASES:
   Extract 5-10 representative phrases that exemplify the style. Include:
   - Opening/closing phrases
   - Transition phrases
   - Characteristic expressions
   - Memorable turns of phrase

7. STYLISTIC PATTERNS:
   Identify recurring patterns:
   - How are questions used?
   - How are lists structured?
   - How are examples given?
   - How are conclusions drawn?

Return your analysis as a JSON object matching this structure:
{{
  "source_name": "source name",
  "writing_style": {{
    "sentence_structure": "...",
    "vocabulary_level": "...",
    "formality": "...",
    "punctuation_patterns": "...",
    "paragraph_organization": "..."
  }},
  "speaking_style": {{
    "natural_speech_patterns": "...",
    "conversational_flow": "...",
    "tone_inflection": "...",
    "pace": "..."
  }},
  "literary_devices": ["humor: dry", "wordplay", "alliteration"],
  "cultural_markers": ["meme references", "slang terms", "trends"],
  "tone": "casual-witty",
  "voice_characteristics": {{
    "overall": "...",
    "authority_level": "...",
    "audience_relationship": "..."
  }},
  "example_phrases": ["...", "..."],
  "example_patterns": ["...", "..."],
  "tags": ["tag1", "tag2"],
  "category": "category-name"
}}"""

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
            if all(any(g in p.lower() for g in generic) for p in profile.example_phrases[:3]):
                issues.append("Example phrases too generic")

        return len(issues) == 0, issues

    async def _create_empty_profile(self, content: StylisticContent, error: str) -> StyleProfile:
        """Create empty profile for manual review after failure."""
        profile_id = self._generate_profile_id(content)
        profile = StyleProfile(
            id=profile_id,
            source_content_id=content.id,
            source_id=content.source_id,
            source_name="unknown",
            tone="unknown",
            status="needs_review",
            curator_notes=None,
            curated_by=None,
            curated_at=None,
            quality_score=None,
            quality_issues=[f"Extraction failed: {error}"],
            category=None,
            extraction_model="gpt-4o-mini",
            extraction_prompt_version=EXTRACTION_PROMPT_VERSION,
            extraction_cost_usd=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            archived_at=None,
        )

        await self.firestore.set_document(
            STYLE_PROFILES_COLLECTION, profile.id, profile.to_firestore_dict()
        )

        return profile

    def _generate_profile_id(self, content: StylisticContent) -> str:
        """Generate unique profile ID using UUID."""
        # Use UUID for guaranteed uniqueness (avoids collisions)
        return f"style-{uuid.uuid4().hex[:16]}"

    async def _get_daily_extraction_cost(self) -> float:
        """Get total extraction cost for today."""
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Query profiles created today
        profiles = await self.firestore.query_collection(
            STYLE_PROFILES_COLLECTION,
            filters=[
                ("created_at", ">=", start_of_day.isoformat()),
            ],
        )

        total_cost = sum(p.get("extraction_cost_usd", 0.0) for p in profiles)
        return total_cost
