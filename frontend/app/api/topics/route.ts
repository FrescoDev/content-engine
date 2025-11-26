import { NextRequest } from "next/server"
import { TopicDecisionSchema } from "@/lib/validators"
import { ApiErrorCode } from "@/lib/api-errors"
import type { TopicDecisionRequest } from "@/lib/api-types"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
  parseLimit,
  batchArray,
  toISOString,
} from "@/lib/api-helpers"

async function getTopics(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseLimit(searchParams, 20, 100)
    const status = searchParams.get("status") || "pending"

    const { firestore } = getFirebaseAdmin()

    // Fetch topics filtered by status
    const topicsRef = firestore.collection("topic_candidates")
    let query = topicsRef.where("status", "==", status).limit(limit)

    // Order by created_at descending
    query = query.orderBy("created_at", "desc")

    const topicsSnapshot = await query.get()
    const topics = topicsSnapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }))

    if (topics.length === 0) {
      return successResponse([])
    }

    // Fetch latest scores for these topics - batch into groups of 10
    const topicIds = topics.map((t) => t.id)
    const scoreBatches = batchArray(topicIds, 10)

    const allScores: Array<{ topic_id: string; [key: string]: any }> = []
    for (const batch of scoreBatches) {
      const scoresSnapshot = await firestore
        .collection("topic_scores")
        .where("topic_id", "in", batch)
        .orderBy("created_at", "desc")
        .get()

      allScores.push(
        ...scoresSnapshot.docs.map((doc) => ({
          topic_id: doc.data().topic_id,
          ...doc.data(),
        }))
      )
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

    // Join topics with scores
    const result = topics.map((topic: { id: string; [key: string]: any }) => {
      const score = scoresByTopic[topic.id] || {
        topic_id: topic.id,
        score: 0.0,
        components: {
          recency: 0.0,
          velocity: 0.0,
          audience_fit: 0.0,
          integrity_penalty: 0.0,
        },
        run_id: "default",
        created_at: new Date().toISOString(),
      }

      return {
        topic: {
          ...topic,
          created_at: toISOString((topic as any).created_at),
        },
        score: {
          ...score,
          created_at: toISOString(score.created_at),
        },
        status: (topic as any).status || "pending",
        rank: 0, // Will be set after sorting
      }
    })

    // Sort by score descending
    result.sort((a, b) => (b.score.score || 0) - (a.score.score || 0))
    result.forEach((item, index) => {
      item.rank = index + 1
    })

    return successResponse(result)
  } catch (error) {
    console.error("Error fetching topics:", error)
    return errorResponse("Failed to fetch topics", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

async function postTopicDecision(request: NextRequest) {
  try {
    // Verify authentication
    const user = await requireAuth(request)

    const body = await request.json()
    const validationResult = TopicDecisionSchema.safeParse(body)

    if (!validationResult.success) {
      return errorResponse(
        "Validation failed",
        ApiErrorCode.VALIDATION_ERROR,
        400,
        { errors: validationResult.error.errors }
      )
    }

    const data = validationResult.data as TopicDecisionRequest
    const { firestore } = getFirebaseAdmin()

    // Use transaction for atomic update with race condition protection
    const result = await firestore.runTransaction(async (transaction) => {
      const topicRef = firestore.collection("topic_candidates").doc(data.topic_id)
      const topicDoc = await transaction.get(topicRef)

      if (!topicDoc.exists) {
        throw new Error("TOPIC_NOT_FOUND")
      }

      const topicData = topicDoc.data()
      const currentStatus = topicData?.status || "pending"

      // Check if already processed (atomic check)
      if (currentStatus !== "pending" && data.action !== "defer") {
        throw new Error("TOPIC_ALREADY_PROCESSED")
      }

      // Update topic status
      const newStatus =
        data.action === "approve" ? "approved" : data.action === "reject" ? "rejected" : "deferred"
      transaction.update(topicRef, { status: newStatus })

      // Create audit event
      const auditRef = firestore.collection("audit_events").doc()
      const auditEvent = {
        id: auditRef.id,
        stage: "topic_selection",
        topic_id: data.topic_id,
        content_id: null,
        system_decision: {
          ranked_ids: [data.topic_id], // Simplified - would come from scoring service
          scoring_components: {}, // Would include actual scores
        },
        human_action: {
          selected_ids: data.action === "approve" ? [data.topic_id] : [],
          rejected_ids: data.action === "reject" ? [data.topic_id] : [],
          reason: data.reason,
          reason_code: data.reason_code,
        },
        actor: user.email || user.uid,
        created_at: new Date().toISOString(),
      }
      transaction.set(auditRef, auditEvent)

      return { audit_event_id: auditRef.id }
    })

    return successResponse(result)
  } catch (error: any) {
    console.error("Error processing topic decision:", error)

    if (error.message === "UNAUTHORIZED") {
      return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
    }
    if (error.message === "TOPIC_NOT_FOUND") {
      return errorResponse("Topic not found", ApiErrorCode.TOPIC_NOT_FOUND, 404)
    }
    if (error.message === "TOPIC_ALREADY_PROCESSED") {
      return errorResponse("Topic already processed", ApiErrorCode.TOPIC_ALREADY_PROCESSED, 409)
    }

    return errorResponse("Failed to process topic decision", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

export async function GET(request: NextRequest) {
  return getTopics(request)
}

export async function POST(request: NextRequest) {
  return postTopicDecision(request)
}

