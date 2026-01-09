import { NextRequest, NextResponse } from "next/server"
import { ApiErrorCode } from "@/lib/api-errors"
import type { ApiResponse, PerformanceData } from "@/lib/api-types"
import { getFirestore } from "firebase-admin/firestore"
import { getFirebaseAdmin } from "@/lib/firebase-admin"

export async function GET(request: NextRequest) {
    try {
        const { firestore } = getFirebaseAdmin()

        // Fetch latest scoring weights from config
        const configSnapshot = await firestore
            .collection("scoring_config")
            .orderBy("updated_at", "desc")
            .limit(1)
            .get()

        let weights = {
            recency: 0.4,
            velocity: 0.3,
            audience_fit: 0.3,
            integrity_penalty: -0.2,
            last_updated: new Date().toISOString(),
        }

        if (!configSnapshot.empty) {
            const configData = configSnapshot.docs[0].data()
            weights = {
                recency: configData.recency || 0.4,
                velocity: configData.velocity || 0.3,
                audience_fit: configData.audience_fit || 0.3,
                integrity_penalty: configData.integrity_penalty || -0.2,
                last_updated: configData.updated_at?.toDate?.()?.toISOString() || configData.updated_at || new Date().toISOString(),
            }
        }

        // Aggregate metrics from content_metrics
        const metricsSnapshot = await firestore
            .collection("content_metrics")
            .orderBy("collected_at", "desc")
            .limit(100) // Last 100 metrics
            .get()

        const metrics = metricsSnapshot.docs.map((doc) => doc.data())

        // Calculate averages
        let totalDuration = 0
        let totalViews = 0
        let totalImpressions = 0
        let count = 0

        metrics.forEach((m) => {
            if (m.avg_view_duration_seconds) {
                totalDuration += m.avg_view_duration_seconds
            }
            totalViews += m.views || 0
            totalImpressions += m.impressions || 0
            count++
        })

        const avgViewDuration = count > 0 ? totalDuration / count : 0
        const engagementRate = totalImpressions > 0 ? (totalViews / totalImpressions) * 100 : 0

        // Count published content
        const publishedSnapshot = await firestore
            .collection("published_content")
            .where("status", "==", "published")
            .get()

        const result: PerformanceData = {
            metrics: {
                avg_view_duration_seconds: avgViewDuration,
                engagement_rate: engagementRate,
                content_published_count: publishedSnapshot.size,
                period: "last_7_days", // Would calculate from date range
            },
            weights,
            suggestions: [], // Would come from learning service
        }

        return NextResponse.json({
            success: true,
            data: result,
        } satisfies ApiResponse<PerformanceData>)
    } catch (error) {
        console.error("Error fetching performance data:", error)
        return NextResponse.json(
            {
                success: false,
                error: {
                    error: "Failed to fetch performance data",
                    code: ApiErrorCode.INTERNAL_ERROR,
                },
            } satisfies ApiResponse<never>,
            { status: 500 }
        )
    }
}





