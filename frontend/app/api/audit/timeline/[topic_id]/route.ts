import { NextRequest, NextResponse } from "next/server"
import { ApiErrorCode } from "@/lib/api-errors"
import type { ApiResponse } from "@/lib/api-types"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import type firestore from "firebase-admin/firestore"

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ topic_id: string }> }
) {
    try {
        const { topic_id: topicId } = await params

        if (!topicId) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "Topic ID required",
                        code: ApiErrorCode.VALIDATION_ERROR,
                    },
                } satisfies ApiResponse<never>,
                { status: 400 }
            )
        }

        const { firestore } = getFirebaseAdmin()

        // Fetch topic
        const topicDoc = await firestore.collection("topic_candidates").doc(topicId).get()
        if (!topicDoc.exists) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "Topic not found",
                        code: ApiErrorCode.TOPIC_NOT_FOUND,
                    },
                } satisfies ApiResponse<never>,
                { status: 404 }
            )
        }

        // Fetch all events for this topic
        const auditEventsSnapshot = await firestore
            .collection("audit_events")
            .where("topic_id", "==", topicId)
            .orderBy("created_at", "asc")
            .get()

        // Fetch scores
        const scoresSnapshot = await firestore
            .collection("topic_scores")
            .where("topic_id", "==", topicId)
            .orderBy("created_at", "asc")
            .get()

        // Fetch content options
        const optionsSnapshot = await firestore
            .collection("content_options")
            .where("topic_id", "==", topicId)
            .orderBy("created_at", "asc")
            .get()

        // Fetch published content
        const publishedSnapshot = await firestore
            .collection("published_content")
            .where("topic_id", "==", topicId)
            .get()

        // Fetch metrics
        const publishedIds = publishedSnapshot.docs.map((d: firestore.QueryDocumentSnapshot) => d.id)
        const metricsSnapshot =
            publishedIds.length > 0
                ? await firestore
                    .collection("content_metrics")
                    .where("content_id", "in", publishedIds)
                    .get()
                : { docs: [] }

        // Build timeline
        const timeline = []

        // Topic ingestion
        timeline.push({
            stage: "ingestion",
            timestamp: topicDoc.data()?.created_at?.toDate?.()?.toISOString() || topicDoc.data()?.created_at,
            data: {
                source: topicDoc.data()?.source_platform,
                title: topicDoc.data()?.title,
            },
        })

        // Scoring events
        scoresSnapshot.docs.forEach((doc: firestore.QueryDocumentSnapshot) => {
            const scoreData = doc.data()
            timeline.push({
                stage: "scoring",
                timestamp: scoreData.created_at?.toDate?.()?.toISOString() || scoreData.created_at,
                data: {
                    score: scoreData.score,
                    components: scoreData.components,
                    run_id: scoreData.run_id,
                },
            })
        })

        // Audit events (reviews, selections)
        auditEventsSnapshot.docs.forEach((doc: firestore.QueryDocumentSnapshot) => {
            const eventData = doc.data()
            timeline.push({
                stage: eventData.stage,
                timestamp: eventData.created_at?.toDate?.()?.toISOString() || eventData.created_at,
                data: {
                    actor: eventData.actor,
                    system_decision: eventData.system_decision,
                    human_action: eventData.human_action,
                },
            })
        })

        // Option generation
        if (optionsSnapshot.docs.length > 0) {
            timeline.push({
                stage: "option_generation",
                timestamp: optionsSnapshot.docs[0].data()?.created_at?.toDate?.()?.toISOString() || optionsSnapshot.docs[0].data()?.created_at,
                data: {
                    options_count: optionsSnapshot.docs.length,
                },
            })
        }

        // Publishing
        publishedSnapshot.docs.forEach((doc: firestore.QueryDocumentSnapshot) => {
            const pubData = doc.data()
            timeline.push({
                stage: "published",
                timestamp: pubData.published_at?.toDate?.()?.toISOString() || pubData.scheduled_at?.toDate?.()?.toISOString() || pubData.created_at,
                data: {
                    platform: pubData.platform,
                    status: pubData.status,
                    external_id: pubData.external_id,
                },
            })
        })

        // Metrics
        metricsSnapshot.docs.forEach((doc: firestore.QueryDocumentSnapshot) => {
            const metricsData = doc.data()
            timeline.push({
                stage: "metrics",
                timestamp: metricsData.collected_at?.toDate?.()?.toISOString() || metricsData.collected_at,
                data: {
                    views: metricsData.views,
                    avg_view_duration: metricsData.avg_view_duration_seconds,
                    engagement_rate: metricsData.click_through_rate,
                },
            })
        })

        // Sort by timestamp
        timeline.sort((a, b) => {
            const timeA = new Date(a.timestamp).getTime()
            const timeB = new Date(b.timestamp).getTime()
            return timeA - timeB
        })

        return NextResponse.json({
            success: true,
            data: {
                topic_id: topicId,
                topic_title: topicDoc.data()?.title,
                timeline,
            },
        } satisfies ApiResponse<{ topic_id: string; topic_title: string; timeline: any[] }>)
    } catch (error) {
        console.error("Error fetching timeline:", error)
        return NextResponse.json(
            {
                success: false,
                error: {
                    error: "Failed to fetch timeline",
                    code: ApiErrorCode.INTERNAL_ERROR,
                },
            } satisfies ApiResponse<never>,
            { status: 500 }
        )
    }
}

