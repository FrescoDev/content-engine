"""
Domain models for Content Engine.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

# Collection name constants
TOPIC_CANDIDATES_COLLECTION = "topic_candidates"
TOPIC_SCORES_COLLECTION = "topic_scores"
CONTENT_OPTIONS_COLLECTION = "content_options"
PUBLISHED_CONTENT_COLLECTION = "published_content"
AUDIT_EVENTS_COLLECTION = "audit_events"
CONTENT_METRICS_COLLECTION = "content_metrics"
PROMPTS_COLLECTION = "prompt_definitions"
JOB_RUNS_COLLECTION = "job_runs"


class TopicCandidate(BaseModel):
    """Topic candidate discovered from external sources."""

    id: str = Field(..., description="Unique identifier (e.g., platform-timestamp-hash)")
    source_platform: Literal[
        "youtube", "tiktok", "x", "news", "manual", "reddit", "hackernews", "rss"
    ] = Field(..., description="Source platform")
    source_url: str | None = Field(None, description="Source URL")
    title: str = Field(..., description="Topic title")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Original API data")
    entities: list[str] = Field(default_factory=list, description="Detected entities")
    topic_cluster: str = Field(
        ...,
        description="Topic cluster (e.g., ai-infra, music-industry, business-socioeconomic)",
    )
    detected_language: str | None = Field(None, description="Detected language")
    status: Literal["pending", "approved", "rejected", "deferred"] = Field(
        default="pending", description="Review status"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        # Convert datetime to ISO string for Firestore
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_firestore_dict(
        cls, data: dict[str, Any], doc_id: str | None = None
    ) -> "TopicCandidate":
        """Create from Firestore dictionary."""
        if doc_id:
            data["id"] = doc_id
        # Convert ISO string back to datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class TopicScore(BaseModel):
    """Score for a topic candidate."""

    topic_id: str = Field(..., description="Topic candidate ID")
    score: float = Field(..., description="Composite score")
    components: dict[str, float] = Field(
        ...,
        description="Score components (recency, velocity, audience_fit, integrity_penalty)",
    )
    reasoning: dict[str, str] = Field(
        default_factory=dict,
        description="Human-readable explanation for each score component",
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "recency": 0.3,
            "velocity": 0.4,
            "audience_fit": 0.3,
        },
        description="Weights used for composite score calculation",
    )
    run_id: str = Field(..., description="Scoring run ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (LLM costs, processing time, etc.)",
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "TopicScore":
        """Create from Firestore dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class ContentOption(BaseModel):
    """Generated content option (hook or script)."""

    id: str = Field(..., description="Unique identifier")
    topic_id: str = Field(..., description="Topic candidate ID")
    option_type: Literal["short_hook", "short_script", "long_outline"] = Field(
        ..., description="Content option type"
    )
    content: str = Field(..., description="Generated content")
    prompt_version: str = Field(..., description="Prompt version used (e.g., short_hook_v3)")
    model: str = Field(..., description="Model used (e.g., gpt-4o-mini)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    # Enhanced fields for script editing (MVP)
    edited_content: str | None = Field(
        None, description="Edited content (null = original, set = edited)"
    )
    edited_at: datetime | None = Field(None, description="Timestamp of last edit")
    editor_id: str | None = Field(None, description="User ID who edited")
    edit_history: list[dict[str, Any]] | None = Field(
        None,
        description="Simple edit history: [{timestamp, editor_id, change_type, refinement_type?}]",
    )
    refinement_applied: list[str] | None = Field(
        None, description="List of refinement types applied: ['tighten', 'casual', 'regenerate']"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        for field in ["created_at", "edited_at"]:
            if isinstance(data.get(field), datetime):
                data[field] = data[field].isoformat()
        # Handle edit_history timestamps
        if data.get("edit_history"):
            for entry in data["edit_history"]:
                if isinstance(entry.get("timestamp"), datetime):
                    entry["timestamp"] = entry["timestamp"].isoformat()
        return data

    @classmethod
    def from_firestore_dict(
        cls, data: dict[str, Any], doc_id: str | None = None
    ) -> "ContentOption":
        """Create from Firestore dictionary."""
        if doc_id:
            data["id"] = doc_id
        for field in ["created_at", "edited_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        # Handle edit_history timestamps
        if data.get("edit_history"):
            for entry in data["edit_history"]:
                if isinstance(entry.get("timestamp"), str):
                    entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
        return cls(**data)


class PublishedContent(BaseModel):
    """Published content item."""

    id: str = Field(..., description="Unique identifier")
    topic_id: str = Field(..., description="Topic candidate ID")
    selected_option_id: str = Field(..., description="Selected content option ID")
    platform: Literal["youtube_short", "youtube_long", "tiktok"] = Field(
        ..., description="Publishing platform"
    )
    status: Literal["draft", "scheduled", "published"] = Field(
        ..., description="Publication status"
    )
    needs_ethics_review: bool = Field(default=False, description="Flagged for ethics review")
    scheduled_at: datetime | None = Field(None, description="Scheduled publication time")
    published_at: datetime | None = Field(None, description="Actual publication time")
    external_id: str | None = Field(None, description="Platform video ID")

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        for field in ["scheduled_at", "published_at"]:
            if isinstance(data.get(field), datetime):
                data[field] = data[field].isoformat()
        return data

    @classmethod
    def from_firestore_dict(
        cls, data: dict[str, Any], doc_id: str | None = None
    ) -> "PublishedContent":
        """Create from Firestore dictionary."""
        if doc_id:
            data["id"] = doc_id
        for field in ["scheduled_at", "published_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class AuditEvent(BaseModel):
    """Audit event for decision tracking."""

    id: str = Field(..., description="Unique identifier")
    stage: Literal["topic_selection", "option_selection", "ethics_review"] = Field(
        ..., description="Decision stage"
    )
    topic_id: str | None = Field(None, description="Topic ID (if applicable)")
    content_id: str | None = Field(None, description="Content ID (if applicable)")
    system_decision: dict[str, Any] = Field(
        ..., description="System decision (ranked list, scores, etc.)"
    )
    human_action: dict[str, Any] | None = Field(
        None, description="Human action (approved, rejected_ids, reason_codes, notes)"
    )
    actor: str = Field(..., description="Actor (e.g., 'kojo' or 'system')")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "AuditEvent":
        """Create from Firestore dictionary."""
        if doc_id:
            data["id"] = doc_id
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class ContentMetrics(BaseModel):
    """Content performance metrics."""

    content_id: str = Field(..., description="Published content ID")
    platform: str = Field(..., description="Platform name")
    impressions: int = Field(default=0, description="Impressions count")
    views: int = Field(default=0, description="Views count")
    click_through_rate: float | None = Field(None, description="CTR")
    avg_view_duration_seconds: float | None = Field(None, description="Average view duration")
    likes: int = Field(default=0, description="Likes count")
    comments: int = Field(default=0, description="Comments count")
    shares: int = Field(default=0, description="Shares count")
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Collection timestamp"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        if isinstance(data.get("collected_at"), datetime):
            data["collected_at"] = data["collected_at"].isoformat()
        return data

    @classmethod
    def from_firestore_dict(
        cls, data: dict[str, Any], doc_id: str | None = None
    ) -> "ContentMetrics":
        """Create from Firestore dictionary."""
        if isinstance(data.get("collected_at"), str):
            data["collected_at"] = datetime.fromisoformat(data["collected_at"])
        return cls(**data)


class PromptDefinition(BaseModel):
    """Prompt template definition."""

    name: str = Field(..., description="Prompt name (e.g., 'short_hook_v3')")
    description: str = Field(..., description="Prompt description")
    template: str = Field(..., description="Prompt template string")
    active: bool = Field(default=True, description="Whether prompt is active")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        for field in ["created_at", "updated_at"]:
            if isinstance(data.get(field), datetime):
                data[field] = data[field].isoformat()
        return data

    @classmethod
    def from_firestore_dict(
        cls, data: dict[str, Any], doc_id: str | None = None
    ) -> "PromptDefinition":
        """Create from Firestore dictionary."""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class JobRun(BaseModel):
    """Job execution record for auditing and monitoring."""

    id: str = Field(..., description="Unique job run identifier (UUID)")
    job_type: Literal[
        "topic_ingestion",
        "topic_scoring",
        "option_generation",
        "weekly_learning",
        "metrics_collection",
    ] = Field(..., description="Type of job")
    status: Literal["running", "completed", "failed", "cancelled"] = Field(
        ..., description="Job execution status"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Job start timestamp"
    )
    completed_at: datetime | None = Field(None, description="Job completion timestamp")
    duration_seconds: float | None = Field(None, description="Job duration in seconds")
    topics_ingested: int = Field(default=0, description="Number of topics ingested")
    topics_saved: int = Field(default=0, description="Number of topics saved to Firestore")
    topics_processed: int = Field(default=0, description="Number of topics processed")
    error_message: str | None = Field(None, description="Error message if failed")
    error_traceback: str | None = Field(None, description="Error traceback if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional job metadata (sources, limits, etc.)"
    )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        data = self.model_dump()
        for field in ["started_at", "completed_at"]:
            if isinstance(data.get(field), datetime):
                data[field] = data[field].isoformat()
        return data

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "JobRun":
        """Create from Firestore dictionary."""
        if doc_id:
            data["id"] = doc_id
        for field in ["started_at", "completed_at"]:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)
