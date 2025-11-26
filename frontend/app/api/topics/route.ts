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
    // Auth optional for local development
    if (process.env.NODE_ENV === "production") {
      await requireAuth(request)
    }

    const { searchParams } = new URL(request.url)
    const limit = parseLimit(searchParams, 20, 100)
    const status = searchParams.get("status") || "pending"

    const { firestore } = getFirebaseAdmin()

    // Fetch topics filtered by status
    // Note: We don't orderBy here to avoid index requirement - we'll sort in memory
    const topicsRef = firestore.collection("topic_candidates")
    const query = topicsRef.where("status", "==", status).limit(limit * 2) // Fetch more to account for sorting

    const topicsSnapshot = await query.get()
    let topics = topicsSnapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }))

    if (topics.length === 0) {
      return successResponse([])
    }

    // Sort by created_at descending in memory
    topics.sort((a: any, b: any) => {
      const aTime = new Date(a.created_at || 0).getTime()
      const bTime = new Date(b.created_at || 0).getTime()
      return bTime - aTime
    })
    
    // Limit after sorting
    topics = topics.slice(0, limit)

    // Fetch latest scores for these topics - batch into groups of 10
    const topicIds = topics.map((t) => t.id)
    const scoreBatches = batchArray(topicIds, 10)

    const allScores: Array<{ topic_id: string; created_at: string; [key: string]: any }> = []
    for (const batch of scoreBatches) {
      // Don't use orderBy to avoid index requirement - we'll sort in memory
      const scoresSnapshot = await firestore
        .collection("topic_scores")
        .where("topic_id", "in", batch)
        .get()

      allScores.push(
        ...scoresSnapshot.docs.map((doc) => ({
          topic_id: doc.data().topic_id,
          created_at: toISOString(doc.data().created_at),
          ...doc.data(),
        }))
      )
    }

    // Group scores by topic_id, keeping only latest (sort by created_at descending)
    const scoresByTopic: Record<string, any> = {}
    // Sort all scores by created_at descending first
    allScores.sort((a, b) => {
      const aTime = new Date(a.created_at || 0).getTime()
      const bTime = new Date(b.created_at || 0).getTime()
      return bTime - aTime
    })
    
    // Take first score for each topic_id (which will be the latest due to sorting)
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
        reasoning: {},
        weights: {
          recency: 0.3,
          velocity: 0.4,
          audience_fit: 0.3,
        },
        metadata: {},
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
          // Ensure reasoning, weights, and metadata are included
          reasoning: score.reasoning || {},
          weights: score.weights || {
            recency: 0.3,
            velocity: 0.4,
            audience_fit: 0.3,
          },
          metadata: score.metadata || {},
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
  } catch (error: any) {
    console.error("Error fetching topics - full error:", JSON.stringify(error, null, 2))
    const errorMessage = error?.message || error?.toString() || String(error)
    const errorCode = error?.code
    
    // Check if it's an index error (Firestore returns code 9 for FAILED_PRECONDITION)
    const isIndexError = 
      errorCode === 9 ||
      errorCode === "FAILED_PRECONDITION" ||
      errorMessage?.includes("index") || 
      errorMessage?.includes("requires an index") || 
      errorMessage?.includes("FAILED_PRECONDITION")
    
    if (isIndexError) {
      console.log("Firestore index required. Using fallback query without ordering.")
      // Try without ordering as fallback
      try {
        const { searchParams } = new URL(request.url)
        const fallbackLimit = parseLimit(searchParams, 20, 100)
        const fallbackStatus = searchParams.get("status") || "pending"
        const { firestore } = getFirebaseAdmin()
        const topicsRef = firestore.collection("topic_candidates")
        const query = topicsRef.where("status", "==", fallbackStatus).limit(fallbackLimit)
        const topicsSnapshot = await query.get()
        const topics = topicsSnapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }))
        
        if (topics.length === 0) {
          return successResponse([])
        }
        
        // Sort in memory instead
        topics.sort((a: any, b: any) => {
          const aTime = new Date(a.created_at || 0).getTime()
          const bTime = new Date(b.created_at || 0).getTime()
          return bTime - aTime
        })
        
        // Fetch scores and join (same as before)
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
        
        const scoresByTopic: Record<string, any> = {}
        const seenTopics = new Set<string>()
        for (const scoreData of allScores) {
          const topicId = scoreData.topic_id
          if (topicId && !seenTopics.has(topicId)) {
            scoresByTopic[topicId] = scoreData
            seenTopics.add(topicId)
          }
        }
        
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
            reasoning: {},
            weights: {
              recency: 0.3,
              velocity: 0.4,
              audience_fit: 0.3,
            },
            metadata: {},
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
              // Ensure reasoning, weights, and metadata are included
              reasoning: score.reasoning || {},
              weights: score.weights || {
                recency: 0.3,
                velocity: 0.4,
                audience_fit: 0.3,
              },
              metadata: score.metadata || {},
            },
            status: (topic as any).status || "pending",
            rank: 0,
          }
        })
        
        result.sort((a, b) => (b.score.score || 0) - (a.score.score || 0))
        result.forEach((item, index) => {
          item.rank = index + 1
        })
        
        return successResponse(result)
      } catch (fallbackError) {
        console.error("Fallback query also failed:", fallbackError)
        return errorResponse(
          `Failed to fetch topics: ${errorMessage}`,
          ApiErrorCode.INTERNAL_ERROR,
          500,
        )
      }
    }
    return errorResponse(
      `Failed to fetch topics: ${errorMessage}`,
      ApiErrorCode.INTERNAL_ERROR,
      500,
    )
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

    // Fetch score data before transaction (can't query inside transaction)
    const scoreRef = firestore.collection("topic_scores")
      .where("topic_id", "==", data.topic_id)
      .orderBy("created_at", "desc")
      .limit(1)
    const scoreSnapshot = await scoreRef.get()
    const latestScore = scoreSnapshot.docs[0]?.data() || null

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

      // Validate defer only on pending topics
      if (data.action === "defer" && currentStatus !== "pending") {
        throw new Error("CAN_ONLY_DEFER_PENDING")
      }

      // Update topic status
      const newStatus =
        data.action === "approve" ? "approved" : data.action === "reject" ? "rejected" : "deferred"
      transaction.update(topicRef, { status: newStatus })

      // Create audit event with score data
      const auditRef = firestore.collection("audit_events").doc()
      const auditEvent = {
        id: auditRef.id,
        stage: "topic_selection",
        topic_id: data.topic_id,
        content_id: null,
        system_decision: {
          ranked_ids: [data.topic_id],
          scoring_components: latestScore
            ? {
                score: latestScore.score,
                recency: latestScore.components?.recency,
                velocity: latestScore.components?.velocity,
                audience_fit: latestScore.components?.audience_fit,
                integrity_penalty: latestScore.components?.integrity_penalty,
                reasoning: latestScore.reasoning || {},
                weights: latestScore.weights || {},
              }
            : {},
        },
        human_action: {
          selected_ids: data.action === "approve" ? [data.topic_id] : [],
          rejected_ids: data.action === "reject" ? [data.topic_id] : [],
          deferred_ids: data.action === "defer" ? [data.topic_id] : [],
          ...(data.reason !== undefined && { reason: data.reason }),
          ...(data.reason_code !== undefined && { reason_code: data.reason_code }),
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
    if (error.message === "CAN_ONLY_DEFER_PENDING") {
      return errorResponse(
        "Can only defer pending topics",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    return errorResponse("Failed to process topic decision", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

async function getTopicCounts(request: NextRequest) {
  try {
    const { firestore } = getFirebaseAdmin()

    // Fetch topics for each status (with reasonable limit for counting)
    // Note: For large datasets, consider using Firestore count queries if available
    const [pendingSnapshot, approvedSnapshot, rejectedSnapshot, deferredSnapshot] = await Promise.all([
      firestore.collection("topic_candidates").where("status", "==", "pending").limit(1000).get(),
      firestore.collection("topic_candidates").where("status", "==", "approved").limit(1000).get(),
      firestore.collection("topic_candidates").where("status", "==", "rejected").limit(1000).get(),
      firestore.collection("topic_candidates").where("status", "==", "deferred").limit(1000).get(),
    ])

    return successResponse({
      pending: pendingSnapshot.size,
      approved: approvedSnapshot.size,
      rejected: rejectedSnapshot.size,
      deferred: deferredSnapshot.size,
    })
  } catch (error: any) {
    console.error("Error fetching topic counts:", error)
    return errorResponse(
      "Failed to fetch topic counts",
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  
  // If counts_only query param is present, return counts
  if (searchParams.get("counts_only") === "true") {
    return getTopicCounts(request)
  }
  
  return getTopics(request)
}

export async function POST(request: NextRequest) {
  return postTopicDecision(request)
}

