/**
 * Zod validation schemas for API requests.
 */

import { z } from "zod"

export const TopicDecisionSchema = z
  .object({
    topic_id: z.string().min(1),
    action: z.enum(["approve", "reject", "defer"]),
    reason: z.string().optional(),
    reason_code: z.enum(["too_generic", "not_on_brand", "speculative", "duplicate", "ethics"]).optional(),
  })
  .refine((data) => {
    // If rejecting, require reason or reason_code
    if (data.action === "reject" && !data.reason && !data.reason_code) {
      return false
    }
    return true
  }, "Reason or reason_code required when rejecting")

export const OptionSelectionSchema = z.object({
  topic_id: z.string().min(1),
  selected_option_id: z.string().min(1),
  edited_content: z.string().optional(),
  mark_ready: z.boolean(),
  needs_ethics_review: z.boolean().optional(),
  reason_code: z.string().optional(),
  notes: z.string().optional(),
  platform: z.enum(["youtube_short", "youtube_long", "tiktok"]).optional().default("youtube_short"),
})

export const IntegrityDecisionSchema = z.object({
  topic_id: z.string().min(1),
  decision: z.enum(["publish", "reframe", "skip"]),
  reframe_option: z.number().int().positive().optional(),
  notes: z.string().optional(),
})

export const ScoringWeightsSchema = z
  .object({
    recency: z.number().min(0).max(1).optional(),
    velocity: z.number().min(0).max(1).optional(),
    audience_fit: z.number().min(0).max(1).optional(),
    integrity_penalty: z.number().max(0).optional(), // Must be negative or zero
  })
  .refine(
    (data) => {
      // Calculate sum of positive weights
      const positiveSum =
        (data.recency ?? 0) + (data.velocity ?? 0) + (data.audience_fit ?? 0)
      // Allow small floating point errors
      return positiveSum >= 0.95 && positiveSum <= 1.05
    },
    "Weights must sum to approximately 1.0"
  )

