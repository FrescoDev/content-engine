"""
Topic scoring service.

Calculates engagement potential scores for topics using multiple components:
- Recency: Time decay (exponential)
- Velocity: Normalized engagement metrics
- Audience Fit: Keyword/cluster matching (MVP), LLM-enhanced (future)
- Integrity Penalty: LLM-based detection (future)

All components are designed to be:
- Fast (no external API calls in MVP)
- Testable (deterministic outputs)
- Explainable (reasoning stored)
- Robust (handle edge cases gracefully)
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any

from ..core import get_logger, get_settings
from ..infra import OpenAIService
from .models import TopicCandidate

logger = get_logger(__name__)

# Default weights for composite score
DEFAULT_WEIGHTS = {
    "recency": 0.3,
    "velocity": 0.4,
    "audience_fit": 0.3,
}

# Platform-specific max engagement values (for normalization)
# These can be updated based on observed data
PLATFORM_MAX_ENGAGEMENT = {
    "reddit": 1000,  # Typical max score for hot posts
    "hackernews": 500,  # Typical max score for top stories
    "rss": 0,  # No engagement metrics
    "manual": 0,  # No engagement metrics
}

# Cluster-based audience fit scores (MVP keyword-based)
CLUSTER_AUDIENCE_SCORES = {
    "ai-infra": 0.9,  # High fit - tech-savvy audience loves AI
    "business-socioeconomic": 0.85,  # High fit - business/econ interest
    "culture-music": 0.7,  # Medium fit - trendy but less tech-focused
    "applied-industry": 0.6,  # Lower fit - niche industries
}

# Trendy keywords that boost audience fit
TRENDY_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "startup",
    "tech",
    "innovation",
    "trend",
    "breakthrough",
    "revolutionary",
    "disrupt",
    "unicorn",
    "funding",
    "series",
    "raise",
    "ipo",
]


class ScoringService:
    """Service for calculating topic engagement scores."""

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        platform_max_engagement: dict[str, int] | None = None,
        openai_service: OpenAIService | None = None,
    ):
        """
        Initialize scoring service.

        Args:
            weights: Custom weights for composite score (defaults to DEFAULT_WEIGHTS)
            platform_max_engagement: Platform-specific max engagement values
            openai_service: OpenAI service instance (created if not provided)
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.platform_max = platform_max_engagement or PLATFORM_MAX_ENGAGEMENT.copy()
        self.openai_service = openai_service
        self.settings = get_settings()
        logger.debug(f"ScoringService initialized with weights: {self.weights}")

    def _get_openai_service(self) -> OpenAIService | None:
        """Get OpenAI service instance, checking if LLM is enabled."""
        if not self.settings.enable_llm_scoring:
            return None
        if self.openai_service is None:
            try:
                self.openai_service = OpenAIService()
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI service: {e}")
                return None
        return self.openai_service

    def _get_cache_key(self, topic: TopicCandidate, cache_type: str) -> str:
        """
        Generate cache key for LLM results.

        Args:
            topic: Topic candidate
            cache_type: Type of cache ("audience_fit" or "integrity")

        Returns:
            Cache key string
        """
        # Use topic ID + cache type + title hash for cache key
        title_hash = hashlib.md5((topic.title or "").encode()).hexdigest()[:8]
        return f"{cache_type}:{topic.id}:{title_hash}"

    def _get_cached_result(self, topic: TopicCandidate, cache_type: str) -> dict[str, Any] | None:
        """
        Get cached LLM result from topic metadata.

        Args:
            topic: Topic candidate
            cache_type: Type of cache ("audience_fit" or "integrity")

        Returns:
            Cached result dict or None
        """
        cache_key = self._get_cache_key(topic, cache_type)
        metadata = topic.raw_payload.get("_scoring_cache", {})
        cached = metadata.get(cache_key)
        if cached:
            # Check if cache is still valid (24 hours)
            cache_time = datetime.fromisoformat(cached.get("cached_at", ""))
            hours_old = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
            if hours_old < 24:
                logger.debug(f"Using cached {cache_type} result for topic {topic.id}")
                return cached.get("result")
        return None

    def calculate_recency(self, topic: TopicCandidate) -> tuple[float, str]:
        """
        Calculate recency score using exponential decay.

        Formula: e^(-decay_rate * hours_old)
        Half-life: 24 hours (score drops to 0.5 after 24 hours)

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (score, reasoning)
        """
        try:
            # Use created_at as timestamp (handles all cases)
            timestamp = topic.created_at

            # Validate timestamp
            if timestamp is None:
                logger.warning(f"Topic {topic.id} has no timestamp, using current time")
                timestamp = datetime.now(timezone.utc)

            # Ensure timestamp is timezone-aware (convert naive to UTC)
            if timestamp.tzinfo is None:
                # Assume naive datetime is UTC
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Handle future timestamps (shouldn't happen, but be safe)
            now = datetime.now(timezone.utc)
            if timestamp > now:
                logger.warning(f"Topic {topic.id} has future timestamp, using current time")
                timestamp = now

            # Calculate hours old
            hours_old = (now - timestamp).total_seconds() / 3600

            # Handle very old topics (cap at 0.0)
            if hours_old < 0:
                hours_old = 0

            # Exponential decay with 24-hour half-life
            half_life_hours = 24.0
            decay_rate = math.log(2) / half_life_hours
            recency = math.exp(-decay_rate * hours_old)

            # Clamp to 0-1 range
            recency = max(0.0, min(1.0, recency))

            # Generate reasoning
            if hours_old < 0.017:  # Less than 1 minute
                seconds_old = int(hours_old * 3600)
                reasoning = f"Published {seconds_old} seconds ago (very recent)"
            elif hours_old < 1:
                minutes_old = int(hours_old * 60)
                reasoning = f"Published {minutes_old} minutes ago (very recent)"
            elif hours_old < 24:
                reasoning = f"Published {hours_old:.1f} hours ago"
            else:
                days_old = hours_old / 24
                reasoning = f"Published {days_old:.1f} days ago (recency: {recency:.2f})"

            return recency, reasoning

        except Exception as e:
            logger.error(f"Failed to calculate recency for topic {topic.id}: {e}")
            return 0.0, f"Error calculating recency: {e}"

    def extract_engagement(self, topic: TopicCandidate) -> int:
        """
        Extract engagement metric from topic's raw_payload.

        Handles different platform formats.

        Args:
            topic: Topic candidate

        Returns:
            Engagement score (0 if not available)
        """
        try:
            platform = topic.source_platform
            payload = topic.raw_payload or {}

            if platform == "reddit":
                score = payload.get("score", 0) or 0
                comments = payload.get("num_comments", 0) or 0
                # Weight comments less than score
                engagement = score + int(comments * 0.1)
                return max(0, engagement)  # Handle negative scores

            elif platform == "hackernews":
                score = payload.get("score", 0) or 0
                comments = payload.get("descendants", 0) or 0
                engagement = score + int(comments * 0.1)
                return max(0, engagement)

            else:
                # RSS, manual, or unknown platforms
                return 0

        except Exception as e:
            logger.warning(f"Failed to extract engagement for topic {topic.id}: {e}")
            return 0

    def calculate_velocity(
        self, topic: TopicCandidate, all_topics: list[TopicCandidate] | None = None
    ) -> tuple[float, str]:
        """
        Calculate velocity score using normalized engagement.

        Uses log scaling to normalize engagement across platforms.
        If all_topics provided, calculates percentile within platform.
        Otherwise, uses platform max values for normalization.

        Args:
            topic: Topic candidate
            all_topics: Optional list of all topics (for percentile calculation)

        Returns:
            Tuple of (score, reasoning)
        """
        try:
            platform = topic.source_platform
            engagement = self.extract_engagement(topic)

            # Handle zero or negative engagement
            if engagement <= 0:
                return 0.0, "No engagement metrics available"

            # If we have all topics, calculate percentile within platform
            if all_topics:
                platform_topics = [t for t in all_topics if t.source_platform == platform]
                if len(platform_topics) == 1:
                    # Single topic from platform - use log normalization instead
                    max_engagement = self.platform_max.get(platform, 100)
                    if max_engagement > 0:
                        normalized = math.log10(engagement + 1) / math.log10(max_engagement + 1)
                        velocity = min(1.0, normalized)
                        reasoning = f"Single topic from {platform}, normalized: {engagement}/{max_engagement} = {velocity:.2f}"
                        return velocity, reasoning
                    else:
                        return 0.0, f"{platform} platform has no engagement metrics"
                elif len(platform_topics) > 1:
                    platform_engagements = [self.extract_engagement(t) for t in platform_topics]
                    platform_engagements.sort()

                    # Calculate percentile rank (0-100)
                    # Percentile = (number of values below) / (total - 1) * 100
                    rank = sum(1 for e in platform_engagements if e < engagement)
                    percentile = (rank / (len(platform_engagements) - 1)) * 100

                    velocity = percentile / 100.0
                    reasoning = f"Ranked in {percentile:.1f}th percentile for {platform} engagement ({engagement} points)"
                    return velocity, reasoning

            # Otherwise, use log normalization with platform max
            max_engagement = self.platform_max.get(platform, 100)

            if max_engagement <= 0:
                # Platform has no engagement metrics
                return 0.0, f"{platform} platform has no engagement metrics"

            # Log normalization: log10(engagement + 1) / log10(max + 1)
            normalized = math.log10(engagement + 1) / math.log10(max_engagement + 1)
            velocity = min(1.0, normalized)

            reasoning = f"Normalized engagement: {engagement}/{max_engagement} = {velocity:.2f}"
            return velocity, reasoning

        except Exception as e:
            logger.error(f"Failed to calculate velocity for topic {topic.id}: {e}")
            return 0.0, f"Error calculating velocity: {e}"

    def _calculate_audience_fit_keyword(self, topic: TopicCandidate) -> tuple[float, str]:
        """
        Calculate audience fit score using keyword-based method (fallback).

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (score, reasoning)
        """
        # Base score from cluster
        cluster = topic.topic_cluster
        base_score = CLUSTER_AUDIENCE_SCORES.get(cluster, 0.5)

        # Boost for trendy keywords in title
        title_lower = (topic.title or "").lower()
        keyword_matches = [kw for kw in TRENDY_KEYWORDS if kw.lower() in title_lower]
        keyword_boost = min(0.15, len(keyword_matches) * 0.03)  # Max 0.15 boost

        # Boost for entities (indicates topic richness)
        entity_boost = min(0.1, len(topic.entities or []) * 0.02)  # Max 0.1 boost

        # Calculate final score
        score = base_score + keyword_boost + entity_boost
        score = min(1.0, score)  # Cap at 1.0

        # Generate reasoning
        reasons = [f"Cluster: {cluster} (base: {base_score:.2f})"]
        if keyword_matches:
            reasons.append(f"Trendy keywords: {', '.join(keyword_matches[:3])}")
        if topic.entities:
            reasons.append(f"Entities detected: {len(topic.entities)}")

        reasoning = " | ".join(reasons)
        return score, reasoning

    async def _calculate_audience_fit_llm(
        self, topic: TopicCandidate
    ) -> tuple[float | None, str | None, dict[str, Any] | None]:
        """
        Calculate audience fit score using LLM.

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (score, reasoning, cost_info) or (None, None, None) if LLM unavailable
        """
        openai_service = self._get_openai_service()
        if not openai_service:
            return None, None, None

        prompt = f"""Score this topic (0-1) for audience fit:

Audience Profile:
- Age: 20-40 years old
- Demographics: Predominantly male (but not overly), ethnically diverse
- Political: Left-leaning or centrist
- Interests: Tech-savvy, business/economics, culturally trendy/hip/cool
- Content preferences: Engaging, slightly sensational but not excessive

Topic Information:
- Title: {topic.title}
- Cluster: {topic.topic_cluster}
- Entities: {', '.join(topic.entities[:10]) if topic.entities else 'None'}
- Source: {topic.source_platform}

Respond with JSON:
{{
    "score": 0.0-1.0,
    "reasoning": "Brief explanation of why this score fits the audience"
}}"""

        try:
            # Use chat_with_cost_tracking to get both JSON and cost info
            content, cost_info = await openai_service.chat_with_cost_tracking(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                max_retries=2,  # Fewer retries for scoring (fast fallback)
            )
            result = json.loads(content)

            # Validate response
            score = result.get("score")
            reasoning = result.get("reasoning", "LLM analysis")

            if not isinstance(score, (int, float)):
                raise ValueError(f"Invalid score type: {type(score)}")
            if not (0.0 <= score <= 1.0):
                logger.warning(f"LLM score {score} out of range [0,1], clamping")
                score = max(0.0, min(1.0, float(score)))
            else:
                score = float(score)

            return score, reasoning, cost_info

        except Exception as e:
            logger.warning(f"LLM audience fit calculation failed for topic {topic.id}: {e}")
            return None, None, None

    def calculate_audience_fit(self, topic: TopicCandidate) -> tuple[float, str]:
        """
        Calculate audience fit score (synchronous wrapper, keyword-based).

        Phase 1: Uses cluster matching + trendy keywords
        Phase 2: LLM available via async method

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (score, reasoning)
        """
        try:
            return self._calculate_audience_fit_keyword(topic)
        except Exception as e:
            logger.error(f"Failed to calculate audience fit for topic {topic.id}: {e}")
            return 0.5, f"Error calculating audience fit: {e}"

    async def calculate_audience_fit_async(
        self, topic: TopicCandidate, use_cache: bool = True
    ) -> tuple[float, str, dict[str, Any] | None]:
        """
        Calculate audience fit score asynchronously (supports LLM).

        Args:
            topic: Topic candidate
            use_cache: Whether to use cached results

        Returns:
            Tuple of (score, reasoning, cost_info)
        """
        try:
            # Check cache first
            if use_cache:
                cached = self._get_cached_result(topic, "audience_fit")
                if cached:
                    return cached.get("score", 0.5), cached.get("reasoning", "Cached result"), None

            # Try LLM first
            llm_score, llm_reasoning, cost_info = await self._calculate_audience_fit_llm(topic)

            if llm_score is not None:
                # Cache LLM result (would need to update topic metadata, but for now just return)
                return llm_score, f"LLM: {llm_reasoning}", cost_info

            # Fallback to keyword-based
            keyword_score, keyword_reasoning = self._calculate_audience_fit_keyword(topic)
            return keyword_score, f"Keyword-based: {keyword_reasoning}", None

        except Exception as e:
            logger.error(f"Failed to calculate audience fit for topic {topic.id}: {e}")
            # Fallback to keyword-based on error
            keyword_score, keyword_reasoning = self._calculate_audience_fit_keyword(topic)
            return keyword_score, f"Error fallback: {keyword_reasoning}", None

    async def _calculate_integrity_penalty_llm(
        self, topic: TopicCandidate
    ) -> tuple[float | None, str | None, dict[str, Any] | None]:
        """
        Calculate integrity penalty using LLM.

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (penalty, reasoning, cost_info) or (None, None, None) if LLM unavailable
            Penalty is negative or zero: 0.0 = no issues, -0.5 = major violation
        """
        openai_service = self._get_openai_service()
        if not openai_service:
            return None, None, None

        prompt = f"""Analyze this topic for content integrity issues:

Topic:
- Title: {topic.title}
- URL: {topic.source_url or 'N/A'}
- Source: {topic.source_platform}

Check for:
- Obscene or sexual content
- Immoral or unethical content
- Excessive sensationalism
- Misinformation risk
- Content that could damage brand reputation

Respond with JSON:
{{
    "penalty": 0.0 to -0.5 (0.0 = no issues, -0.1 to -0.3 = minor concerns, -0.5 = major violation),
    "reasoning": "Brief explanation",
    "flags": ["flag1", "flag2"] (optional list of specific issues)
}}"""

        try:
            # Use chat_with_cost_tracking to get both JSON and cost info
            content, cost_info = await openai_service.chat_with_cost_tracking(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                max_retries=2,
            )
            result = json.loads(content)

            # Validate response
            penalty = result.get("penalty", 0.0)
            reasoning = result.get("reasoning", "LLM analysis")
            flags = result.get("flags", [])

            if not isinstance(penalty, (int, float)):
                raise ValueError(f"Invalid penalty type: {type(penalty)}")
            if not (-0.5 <= penalty <= 0.0):
                logger.warning(f"LLM penalty {penalty} out of range [-0.5,0], clamping")
                penalty = max(-0.5, min(0.0, float(penalty)))
            else:
                penalty = float(penalty)

            # Build reasoning with flags
            if flags:
                reasoning = f"{reasoning} (Flags: {', '.join(flags)})"

            return penalty, reasoning, cost_info

        except Exception as e:
            logger.warning(f"LLM integrity calculation failed for topic {topic.id}: {e}")
            return None, None, None

    def calculate_integrity_penalty(self, topic: TopicCandidate) -> tuple[float, str]:
        """
        Calculate integrity penalty (synchronous wrapper, returns 0.0 for MVP).

        Phase 2: LLM-based detection available via async method.

        Args:
            topic: Topic candidate

        Returns:
            Tuple of (penalty, reasoning)
        """
        # Synchronous version returns 0.0 (LLM will be used in async version)
        return 0.0, "Integrity checking via LLM (use async method)"

    async def calculate_integrity_penalty_async(
        self, topic: TopicCandidate, use_cache: bool = True
    ) -> tuple[float, str, dict[str, Any] | None]:
        """
        Calculate integrity penalty asynchronously (supports LLM).

        Args:
            topic: Topic candidate
            use_cache: Whether to use cached results

        Returns:
            Tuple of (penalty, reasoning, cost_info)
        """
        try:
            # Check cache first
            if use_cache:
                cached = self._get_cached_result(topic, "integrity")
                if cached:
                    return (
                        cached.get("penalty", 0.0),
                        cached.get("reasoning", "Cached result"),
                        None,
                    )

            # Try LLM
            llm_penalty, llm_reasoning, cost_info = await self._calculate_integrity_penalty_llm(
                topic
            )

            if llm_penalty is not None:
                return llm_penalty, f"LLM: {llm_reasoning}", cost_info

            # Fallback to 0.0 (no penalty)
            return 0.0, "No integrity issues detected (LLM unavailable)", None

        except Exception as e:
            logger.error(f"Failed to calculate integrity penalty for topic {topic.id}: {e}")
            return 0.0, f"Error fallback: {e}", None

    def calculate_composite_score(
        self,
        recency: float,
        velocity: float,
        audience_fit: float,
        integrity_penalty: float,
    ) -> float:
        """
        Calculate weighted composite score.

        Formula: (w1*recency + w2*velocity + w3*audience_fit) + integrity_penalty

        Args:
            recency: Recency component score
            velocity: Velocity component score
            audience_fit: Audience fit component score
            integrity_penalty: Integrity penalty (negative or zero)

        Returns:
            Composite score (0.0 to 1.0)
        """
        # Validate weights sum to ~1.0 (use local copy to avoid mutating instance)
        weight_sum = sum(self.weights.get(k, 0.0) for k in ["recency", "velocity", "audience_fit"])

        # Use normalized weights locally if needed (don't mutate instance)
        normalized_weights = self.weights.copy()
        if abs(weight_sum - 1.0) > 0.01:
            logger.warning(
                f"Weights don't sum to 1.0: {weight_sum}, normalizing for this calculation"
            )
            # Normalize weights locally
            for key in ["recency", "velocity", "audience_fit"]:
                normalized_weights[key] = normalized_weights.get(key, 0.0) / weight_sum

        # Calculate weighted sum using normalized weights
        weighted_sum = (
            normalized_weights["recency"] * recency
            + normalized_weights["velocity"] * velocity
            + normalized_weights["audience_fit"] * audience_fit
        )

        # Apply integrity penalty (always subtractive)
        final_score = weighted_sum + integrity_penalty

        # Clamp to 0-1 range
        return max(0.0, min(1.0, final_score))

    def score_topic(
        self, topic: TopicCandidate, all_topics: list[TopicCandidate] | None = None
    ) -> dict[str, Any]:
        """
        Calculate all score components for a topic.

        Args:
            topic: Topic candidate
            all_topics: Optional list of all topics (for percentile calculation)

        Returns:
            Dictionary with score components, reasoning, and composite score
        """
        # Calculate each component
        recency, recency_reasoning = self.calculate_recency(topic)
        velocity, velocity_reasoning = self.calculate_velocity(topic, all_topics)
        audience_fit, audience_reasoning = self.calculate_audience_fit(topic)
        integrity_penalty, integrity_reasoning = self.calculate_integrity_penalty(topic)

        # Calculate composite score
        composite_score = self.calculate_composite_score(
            recency, velocity, audience_fit, integrity_penalty
        )

        return {
            "components": {
                "recency": recency,
                "velocity": velocity,
                "audience_fit": audience_fit,
                "integrity_penalty": integrity_penalty,
            },
            "reasoning": {
                "recency": recency_reasoning,
                "velocity": velocity_reasoning,
                "audience_fit": audience_reasoning,
                "integrity_penalty": integrity_reasoning,
            },
            "score": composite_score,
            "weights": self.weights.copy(),
        }

    async def score_topic_async(
        self,
        topic: TopicCandidate,
        all_topics: list[TopicCandidate] | None = None,
        use_llm: bool = True,
    ) -> dict[str, Any]:
        """
        Calculate all score components for a topic asynchronously (supports LLM).

        Args:
            topic: Topic candidate
            all_topics: Optional list of all topics (for percentile calculation)
            use_llm: Whether to use LLM for audience_fit and integrity (if enabled)

        Returns:
            Dictionary with score components, reasoning, composite score, and cost_info
        """
        total_cost = 0.0
        cost_details: list[dict[str, Any]] = []

        # Calculate synchronous components
        recency, recency_reasoning = self.calculate_recency(topic)
        velocity, velocity_reasoning = self.calculate_velocity(topic, all_topics)

        # Calculate LLM-enhanced components if enabled
        if use_llm and self.settings.enable_llm_scoring:
            audience_fit, audience_reasoning, audience_cost = (
                await self.calculate_audience_fit_async(topic)
            )
            if audience_cost:
                total_cost += audience_cost.get("cost_usd", 0.0)
                cost_details.append({"type": "audience_fit", **audience_cost})

            integrity_penalty, integrity_reasoning, integrity_cost = (
                await self.calculate_integrity_penalty_async(topic)
            )
            if integrity_cost:
                total_cost += integrity_cost.get("cost_usd", 0.0)
                cost_details.append({"type": "integrity", **integrity_cost})
        else:
            # Use synchronous methods
            audience_fit, audience_reasoning = self.calculate_audience_fit(topic)
            integrity_penalty, integrity_reasoning = self.calculate_integrity_penalty(topic)

        # Calculate composite score
        composite_score = self.calculate_composite_score(
            recency, velocity, audience_fit, integrity_penalty
        )

        result = {
            "components": {
                "recency": recency,
                "velocity": velocity,
                "audience_fit": audience_fit,
                "integrity_penalty": integrity_penalty,
            },
            "reasoning": {
                "recency": recency_reasoning,
                "velocity": velocity_reasoning,
                "audience_fit": audience_reasoning,
                "integrity_penalty": integrity_reasoning,
            },
            "score": composite_score,
            "weights": self.weights.copy(),
        }

        # Add cost info if LLM was used
        if cost_details:
            result["cost_info"] = {
                "total_cost_usd": total_cost,
                "details": cost_details,
            }

        return result
