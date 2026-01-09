import { NextRequest, NextResponse } from "next/server"
import { verifyAuthToken } from "@/lib/firebase-admin"
import { ScoringWeightsSchema } from "@/lib/validators"
import { ApiErrorCode } from "@/lib/api-errors"
import type { ScoringWeightsUpdate, ApiResponse } from "@/lib/api-types"
import { getFirestore } from "firebase-admin/firestore"
import { getFirebaseAdmin } from "@/lib/firebase-admin"

export async function POST(request: NextRequest) {
    try {
        // Verify authentication
        const authHeader = request.headers.get("authorization")
        const token = authHeader?.replace("Bearer ", "") || null
        const user = await verifyAuthToken(token)

        if (!user) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "Unauthorized",
                        code: ApiErrorCode.UNAUTHORIZED,
                    },
                } satisfies ApiResponse<never>,
                { status: 401 }
            )
        }

        const body = await request.json()
        const validationResult = ScoringWeightsSchema.safeParse(body)

        if (!validationResult.success) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "Validation failed",
                        code: ApiErrorCode.INVALID_WEIGHTS,
                        details: validationResult.error.errors,
                    },
                } satisfies ApiResponse<never>,
                { status: 400 }
            )
        }

        const data = validationResult.data as ScoringWeightsUpdate
        const { firestore } = getFirebaseAdmin()

        // Fetch current weights to merge
        const configSnapshot = await firestore
            .collection("scoring_config")
            .orderBy("updated_at", "desc")
            .limit(1)
            .get()

        let currentWeights = {
            recency: 0.4,
            velocity: 0.3,
            audience_fit: 0.3,
            integrity_penalty: -0.2,
        }

        if (!configSnapshot.empty) {
            const configData = configSnapshot.docs[0].data()
            currentWeights = {
                recency: configData.recency || 0.4,
                velocity: configData.velocity || 0.3,
                audience_fit: configData.audience_fit || 0.3,
                integrity_penalty: configData.integrity_penalty || -0.2,
            }
        }

        // Merge with updates
        const updatedWeights = {
            recency: data.recency ?? currentWeights.recency,
            velocity: data.velocity ?? currentWeights.velocity,
            audience_fit: data.audience_fit ?? currentWeights.audience_fit,
            integrity_penalty: data.integrity_penalty ?? currentWeights.integrity_penalty,
        }

        // Validate final weights sum
        const positiveSum = updatedWeights.recency + updatedWeights.velocity + updatedWeights.audience_fit
        if (positiveSum < 0.95 || positiveSum > 1.05) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "Weights must sum to approximately 1.0",
                        code: ApiErrorCode.INVALID_WEIGHTS,
                        details: { current_sum: positiveSum },
                    },
                } satisfies ApiResponse<never>,
                { status: 400 }
            )
        }

        // Validate integrity_penalty is negative
        if (updatedWeights.integrity_penalty > 0) {
            return NextResponse.json(
                {
                    success: false,
                    error: {
                        error: "integrity_penalty must be negative or zero",
                        code: ApiErrorCode.INVALID_WEIGHTS,
                    },
                } satisfies ApiResponse<never>,
                { status: 400 }
            )
        }

        // Store updated weights
        const configRef = firestore.collection("scoring_config").doc()
        await configRef.set({
            ...updatedWeights,
            updated_at: new Date().toISOString(),
            updated_by: user.email || user.uid,
            is_manual_override: true,
        })

        return NextResponse.json({
            success: true,
            data: {},
        } satisfies ApiResponse<Record<string, never>>)
    } catch (error) {
        console.error("Error updating weights:", error)
        return NextResponse.json(
            {
                success: false,
                error: {
                    error: "Failed to update weights",
                    code: ApiErrorCode.INTERNAL_ERROR,
                },
            } satisfies ApiResponse<never>,
            { status: 500 }
        )
    }
}





