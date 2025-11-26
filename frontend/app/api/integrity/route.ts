import { NextRequest } from "next/server"
import { IntegrityDecisionSchema } from "@/lib/validators"
import { ApiErrorCode } from "@/lib/api-errors"
import type { IntegrityDecisionRequest, IntegrityReviewItem } from "@/lib/api-types"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
    requireAuth,
    errorResponse,
    successResponse,
    parseLimit,
    batchArray,
    toISOString,
} from "@/lib/api-helpers"

const INTEGRITY_REVIEW_THRESHOLD = -0.15

async function getIntegrityItems(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url)
        const limit = parseLimit(searchParams, 20, 100)

        const { firestore } = getFirebaseAdmin()

        // Fetch topics that might need review - query each status separately
        const [pendingSnapshot, approvedSnapshot] = await Promise.all([
            firestore.collection("topic_candidates").where("status", "==", "pending").limit(limit * 2).get(),
            firestore.collection("topic_candidates").where("status", "==", "approved").limit(limit * 2).get(),
        ])

        const topics = [
            ...pendingSnapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })),
            ...approvedSnapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })),
        ]

        if (topics.length === 0) {
            return successResponse<IntegrityReviewItem[]>([])
        }

        const topicIds = topics.map((t) => t.id)

        // Fetch latest scores - batch into groups of 10
        const scoreBatches = batchArray(topicIds, 10)
        const allScores: Array<{ topic_id: string;[key: string]: any }> = []

        for (const batch of scoreBatches) {
            const scoresSnapshot = await firestore
                .collection("topic_scores")
                .where("topic_id", "in", batch)
                .orderBy("created_at", "desc")
                .get()

            allScores.push(...scoresSnapshot.docs.map((doc) => ({ topic_id: doc.data().topic_id, ...doc.data() })))
        }

        // Group scores by topic_id, keeping only latest
        const scoresByTopic: Record<string, any> = {}
        const seenTopics = new Set<string>()
        for (const scoreData of allScores) {
            const topicId = scoreData.topic_id
            if (topicId && !seenTopics.has(topicId)) {
                scoresByTopic[topicId] = scoreData
                seenTopics.add(topicId)
            }
        }

        // Filter by integrity threshold
        const result: IntegrityReviewItem[] = []
        for (const topic of topics) {
            const score = scoresByTopic[topic.id]
            if (!score) continue

            const integrityPenalty = score.components?.integrity_penalty || 0.0
            if (integrityPenalty >= INTEGRITY_REVIEW_THRESHOLD) {
                continue // Not flagged enough
            }

            // Determine risk level
            let riskLevel: "low" | "medium" | "high"
            if (integrityPenalty < -0.3) {
                riskLevel = "high"
            } else if (integrityPenalty < -0.2) {
                riskLevel = "medium"
            } else {
                riskLevel = "low"
            }

            result.push({
                topic_id: topic.id,
                topic: {
                    ...topic,
                    created_at: toISOString((topic as any).created_at),
                } as any,
                risk_level: riskLevel,
                reason: `Low integrity score: ${integrityPenalty.toFixed(2)}`,
                suggested_reframes: [], // Would come from LLM analysis
                integrity_score: integrityPenalty,
            })

            if (result.length >= limit) {
                break
            }
        }

        return successResponse(result)
    } catch (error) {
        console.error("Error fetching integrity items:", error)
        return errorResponse("Failed to fetch integrity items", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}

async function postIntegrityDecision(request: NextRequest) {
    try {
        // Verify authentication
        const user = await requireAuth(request)

        const body = await request.json()
        const validationResult = IntegrityDecisionSchema.safeParse(body)

        if (!validationResult.success) {
            return errorResponse(
                "Validation failed",
                ApiErrorCode.VALIDATION_ERROR,
                400,
                { errors: validationResult.error.errors }
            )
        }

        const data = validationResult.data as IntegrityDecisionRequest
        const { firestore } = getFirebaseAdmin()

        // Use transaction for atomic update
        const result = await firestore.runTransaction(async (transaction) => {
            // Verify topic exists
            const topicRef = firestore.collection("topic_candidates").doc(data.topic_id)
            const topicDoc = await transaction.get(topicRef)

            if (!topicDoc.exists) {
                throw new Error("TOPIC_NOT_FOUND")
            }

            // Create audit event
            const auditRef = firestore.collection("audit_events").doc()
            const auditEvent = {
                id: auditRef.id,
                stage: "ethics_review",
                topic_id: data.topic_id,
                content_id: null,
                system_decision: {
                    flagged: true,
                    recommendation: "review_required",
                },
                human_action: {
                    decision: data.decision,
                    notes: data.notes,
                    reframe_option: data.reframe_option,
                },
                actor: user.email || user.uid,
                created_at: new Date().toISOString(),
            }
            transaction.set(auditRef, auditEvent)

            // Handle decision
            if (data.decision === "skip") {
                // Mark topic as rejected
                transaction.update(topicRef, { status: "rejected" })
            } else if (data.decision === "reframe") {
                // Store reframe request in metadata instead of non-existent field
                // In production, this would trigger a job queue
                const currentData = topicDoc.data()
                const metadata = currentData?.metadata || {}
                transaction.update(topicRef, {
                    metadata: { ...metadata, needs_reframe: true, reframe_requested_at: new Date().toISOString() },
                })
            }
            // If "publish", topic stays as is

            return { audit_event_id: auditRef.id }
        })

        return successResponse(result)
    } catch (error: any) {
        console.error("Error processing integrity decision:", error)

        if (error.message === "UNAUTHORIZED") {
            return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
        }
        if (error.message === "TOPIC_NOT_FOUND") {
            return errorResponse("Topic not found", ApiErrorCode.TOPIC_NOT_FOUND, 404)
        }

        return errorResponse("Failed to process integrity decision", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}

export async function GET(request: NextRequest) {
    return getIntegrityItems(request)
}

export async function POST(request: NextRequest) {
    return postIntegrityDecision(request)
}

