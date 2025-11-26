import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { OptionSelectionSchema } from "@/lib/validators"
import { ApiErrorCode } from "@/lib/api-errors"
import type { OptionSelectionRequest, TopicWithOptions } from "@/lib/api-types"
import type firestore from "firebase-admin/firestore"
import {
    requireAuth,
    errorResponse,
    successResponse,
    batchArray,
    toISOString,
} from "@/lib/api-helpers"

async function getOptions(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url)
        const topicId = searchParams.get("topic_id")
        const status = searchParams.get("status") // options-ready|ready|needs-ethics

        const { firestore } = getFirebaseAdmin()

        // Build topic query
        let topicQuery = firestore.collection("topic_candidates").where("status", "==", "approved")

        if (topicId) {
            topicQuery = firestore.collection("topic_candidates").where("__name__", "==", topicId)
        }

        const topicsSnapshot = await topicQuery.limit(50).get()
        const topics = topicsSnapshot.docs.map((doc: firestore.QueryDocumentSnapshot) => ({
            id: doc.id,
            ...doc.data(),
        }))

        if (topics.length === 0) {
            return successResponse<TopicWithOptions[]>([])
        }

        const topicIds = topics.map((t: { id: string }) => t.id)

        if (topicIds.length === 0) {
            return successResponse<TopicWithOptions[]>([])
        }

        // Fetch content options for these topics - batch into groups of 10
        const optionBatches = batchArray(topicIds, 10)
        const allOptions: Array<{ id: string; topic_id: string;[key: string]: any }> = []

        for (const batch of optionBatches) {
            const optionsSnapshot = await firestore
                .collection("content_options")
                .where("topic_id", "in", batch)
                .get()

            allOptions.push(
                ...optionsSnapshot.docs.map((doc: firestore.QueryDocumentSnapshot) => {
                    const data = doc.data()
                    return {
                        id: doc.id,
                        topic_id: data.topic_id,
                        option_type: data.option_type,
                        content: data.content,
                        created_at: data.created_at,
                        ...data,
                    }
                })
            )
        }

        // Group options by topic_id and type
        const optionsByTopic: Record<string, { hooks: any[]; scripts: any[] }> = {}
        for (const optionData of allOptions) {
            const tid = optionData.topic_id
            if (!tid) continue

            if (!optionsByTopic[tid]) {
                optionsByTopic[tid] = { hooks: [], scripts: [] }
            }

            const option = {
                ...optionData,
                id: optionData.id, // Ensure id is set correctly
                created_at: toISOString(optionData.created_at),
            }

            if (optionData.option_type === "short_hook") {
                optionsByTopic[tid].hooks.push(option)
            } else if (optionData.option_type === "short_script") {
                optionsByTopic[tid].scripts.push(option)
            }
        }

        // Build result - filter out topics without options
        const result: TopicWithOptions[] = []
        for (const topic of topics) {
            const topicOptions = optionsByTopic[topic.id] || { hooks: [], scripts: [] }
            const hasOptions = topicOptions.hooks.length > 0 || topicOptions.scripts.length > 0

            if (!hasOptions) {
                continue // Skip topics without options
            }

            result.push({
                topic: {
                    ...topic,
                    created_at: toISOString((topic as any).created_at),
                } as any,
                hooks: topicOptions.hooks,
                scripts: topicOptions.scripts,
                status: "options-ready",
            })
        }

        return successResponse(result)
    } catch (error) {
        console.error("Error fetching options:", error)
        return errorResponse("Failed to fetch options", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}

async function postOptionSelection(request: NextRequest) {
    try {
        // Verify authentication
        const user = await requireAuth(request)

        const body = await request.json()
        const validationResult = OptionSelectionSchema.safeParse(body)

        if (!validationResult.success) {
            return errorResponse(
                "Validation failed",
                ApiErrorCode.VALIDATION_ERROR,
                400,
                { errors: validationResult.error.errors }
            )
        }

        const data = validationResult.data as OptionSelectionRequest
        const { firestore } = getFirebaseAdmin()

        // Use transaction for atomic updates with validation
        const result = await firestore.runTransaction(async (transaction) => {
            // Verify topic and option exist
            const topicRef = firestore.collection("topic_candidates").doc(data.topic_id)
            const optionRef = firestore.collection("content_options").doc(data.selected_option_id)

            const [topicDoc, optionDoc] = await Promise.all([
                transaction.get(topicRef),
                transaction.get(optionRef),
            ])

            if (!topicDoc.exists) {
                throw new Error("TOPIC_NOT_FOUND")
            }

            if (!optionDoc.exists) {
                throw new Error("OPTION_NOT_FOUND")
            }

            const optionData = optionDoc.data()
            if (optionData?.topic_id !== data.topic_id) {
                throw new Error("OPTION_MISMATCH")
            }

            // Compute diff if content was edited
            let diff = null
            if (data.edited_content && data.edited_content !== optionData.content) {
                // Simple diff - in production would use diff-match-patch library
                diff = {
                    original_length: optionData.content?.length || 0,
                    edited_length: data.edited_content.length,
                    changed: true,
                }
            }

            // Create audit event
            const auditRef = firestore.collection("audit_events").doc()
            const auditEvent = {
                id: auditRef.id,
                stage: "option_selection",
                topic_id: data.topic_id,
                content_id: null,
                system_decision: {
                    option_ids: [], // Would include all options for topic
                    recommended_option_id: data.selected_option_id,
                },
                human_action: {
                    selected_option_id: data.selected_option_id,
                    rejected_option_ids: [],
                    reason_code: data.reason_code,
                    notes: data.notes,
                    edited: !!data.edited_content,
                    diff: diff,
                },
                actor: user.email || user.uid,
                created_at: new Date().toISOString(),
            }
            transaction.set(auditRef, auditEvent)

            // Create PublishedContent draft if marking ready
            let publishedContentId: string | undefined
            if (data.mark_ready) {
                const publishedRef = firestore.collection("published_content").doc()
                publishedContentId = publishedRef.id

                const publishedContent = {
                    id: publishedRef.id,
                    topic_id: data.topic_id,
                    selected_option_id: data.selected_option_id,
                    platform: data.platform || "youtube_short", // Use platform from request
                    status: "draft",
                    needs_ethics_review: data.needs_ethics_review || false,
                    scheduled_at: null,
                    published_at: null,
                    external_id: null,
                }
                transaction.set(publishedRef, publishedContent)
            }

            return { audit_event_id: auditRef.id, published_content_id: publishedContentId }
        })

        return successResponse(result)
    } catch (error: any) {
        console.error("Error processing option selection:", error)

        if (error.message === "UNAUTHORIZED") {
            return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
        }
        if (error.message === "TOPIC_NOT_FOUND") {
            return errorResponse("Topic not found", ApiErrorCode.TOPIC_NOT_FOUND, 404)
        }
        if (error.message === "OPTION_NOT_FOUND") {
            return errorResponse("Option not found", ApiErrorCode.OPTION_NOT_FOUND, 404)
        }
        if (error.message === "OPTION_MISMATCH") {
            return errorResponse("Option does not belong to topic", ApiErrorCode.VALIDATION_ERROR, 400)
        }

        return errorResponse("Failed to process option selection", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}

export async function GET(request: NextRequest) {
    return getOptions(request)
}

export async function POST(request: NextRequest) {
    return postOptionSelection(request)
}

