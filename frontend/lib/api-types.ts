/**
 * TypeScript type definitions for API requests and responses.
 * These match the backend Python models.
 */

// Topic Decision Request
export interface TopicDecisionRequest {
  topic_id: string
  action: "approve" | "reject" | "defer"
  reason?: string // Required if reject
  reason_code?: "too_generic" | "not_on_brand" | "speculative" | "duplicate" | "ethics"
}

// Option Selection Request
export interface OptionSelectionRequest {
  topic_id: string
  selected_option_id: string
  edited_content?: string // If user edited
  mark_ready: boolean
  needs_ethics_review?: boolean
  reason_code?: string
  notes?: string
  platform?: "youtube_short" | "youtube_long" | "tiktok"
}

// Integrity Decision Request
export interface IntegrityDecisionRequest {
  topic_id: string
  decision: "publish" | "reframe" | "skip"
  reframe_option?: number // If reframe, which suggested option
  notes?: string
}

// Scoring Weights Update
export interface ScoringWeightsUpdate {
  recency?: number
  velocity?: number
  audience_fit?: number
  integrity_penalty?: number
}

// Topic Candidate (matches backend model)
export interface TopicCandidate {
  id: string
  source_platform: "youtube" | "tiktok" | "x" | "news" | "manual"
  source_url: string | null
  title: string
  raw_payload: Record<string, any>
  entities: string[]
  topic_cluster: string
  detected_language: string | null
  status: "pending" | "approved" | "rejected" | "deferred"
  created_at: string
}

// Topic Score (matches backend model)
export interface TopicScore {
  topic_id: string
  score: number
  components: {
    recency: number
    velocity: number
    audience_fit: number
    integrity_penalty: number
  }
  reasoning?: {
    recency?: string
    velocity?: string
    audience_fit?: string
    integrity_penalty?: string
  }
  weights?: {
    recency?: number
    velocity?: number
    audience_fit?: number
  }
  metadata?: {
    llm_used?: boolean
    cost_usd?: number
    [key: string]: any
  }
  run_id: string
  created_at: string
}

// Content Option (matches backend model)
export interface ContentOption {
  id: string
  topic_id: string
  option_type: "short_hook" | "short_script" | "long_outline"
  content: string
  prompt_version: string
  model: string
  metadata: Record<string, any>
  created_at: string
  // Enhanced fields for script editing (MVP)
  edited_content?: string | null
  edited_at?: string | null
  editor_id?: string | null
  edit_history?: Array<{
    timestamp: string
    editor_id: string
    change_type: "manual_edit" | "ai_refinement"
    refinement_type?: "tighten" | "casual" | "regenerate"
  }> | null
  refinement_applied?: string[] | null
}

// Topic Review Item Response
export interface TopicReviewItem {
  topic: TopicCandidate
  score: TopicScore
  status: "pending" | "approved" | "rejected" | "deferred"
  rank: number
}

// Topic with Options Response
export interface TopicWithOptions {
  topic: TopicCandidate
  hooks: ContentOption[] // option_type: "short_hook"
  scripts: ContentOption[] // option_type: "short_script"
  status: "options-ready" | "ready" | "needs-ethics"
}

// Integrity Review Item Response
export interface IntegrityReviewItem {
  topic_id: string
  topic: TopicCandidate
  risk_level: "low" | "medium" | "high"
  reason: string
  suggested_reframes: string[]
  integrity_score: number
}

// Audit Event Response
export interface AuditEventResponse {
  id: string
  stage: "topic_selection" | "option_selection" | "ethics_review"
  topic_id?: string
  topic_title?: string
  actor: string
  created_at: string
  system_decision: Record<string, any>
  human_action: Record<string, any> | null
}

// Performance Data Response
export interface PerformanceData {
  metrics: {
    avg_view_duration_seconds: number
    engagement_rate: number
    content_published_count: number
    period: string
  }
  weights: {
    recency: number
    velocity: number
    audience_fit: number
    integrity_penalty: number
    last_updated: string
  }
  suggestions: string[]
}

// Error Response
export interface ApiError {
  error: string
  code: string
  details?: Record<string, any>
}

// Job Run (matches backend model)
export interface JobRun {
  id: string
  job_type: "topic_ingestion" | "topic_scoring" | "option_generation" | "weekly_learning" | "metrics_collection"
  status: "running" | "completed" | "failed" | "cancelled"
  started_at: string
  completed_at?: string
  duration_seconds?: number
  topics_ingested?: number
  topics_saved?: number
  topics_processed?: number
  error_message?: string
  error_traceback?: string
  metadata?: Record<string, any>
}

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: ApiError
}

