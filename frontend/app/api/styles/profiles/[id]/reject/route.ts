import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * POST /api/styles/profiles/[id]/reject
 * Reject a style profile
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const body = await request.json()
    const { reason } = body
    const { id: profileId } = await params

    if (!reason) {
      return errorResponse(
        "reason is required",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    const { firestore } = getFirebaseAdmin()

    const profileRef = firestore.collection("style_profiles").doc(profileId)
    const profileDoc = await profileRef.get()

    if (!profileDoc.exists) {
      return errorResponse("Profile not found", ApiErrorCode.NOT_FOUND, 404)
    }

    const now = new Date().toISOString()
    await profileRef.update({
      status: "rejected",
      curated_by: user.email || user.uid,
      curated_at: now,
      curator_notes: reason,
      updated_at: now,
    })

    return successResponse({
      message: "Profile rejected",
      profile_id: profileId,
    })
  } catch (error: any) {
    console.error("Error rejecting profile:", error)
    return errorResponse(
      `Failed to reject profile: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

