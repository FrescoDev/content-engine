import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * POST /api/styles/profiles/[id]/test/feedback
 * Submit feedback on a test script (approve/reject with notes)
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const body = await request.json()
    const { id: profileId } = await params
    const { script_id, approved, notes } = body as {
      script_id: string
      approved: boolean
      notes?: string
    }

    if (!script_id || typeof approved !== "boolean") {
      return errorResponse(
        "script_id and approved are required",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    const { firestore } = getFirebaseAdmin()

    // Verify script exists and belongs to this profile
    const scriptDoc = await firestore.collection("style_test_scripts").doc(script_id).get()
    if (!scriptDoc.exists) {
      return errorResponse("Test script not found", ApiErrorCode.NOT_FOUND, 404)
    }

    const scriptData = scriptDoc.data()
    if (scriptData?.profile_id !== profileId) {
      return errorResponse(
        "Script does not belong to this profile",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    // Check if feedback already submitted
    if (scriptData.feedback_at) {
      return errorResponse(
        "Feedback already submitted for this script",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    // Update script with feedback
    const now = new Date().toISOString()
    await firestore.collection("style_test_scripts").doc(script_id).update({
      status: approved ? "approved" : "rejected",
      feedback_notes: notes || null,
      feedback_by: user.email || user.uid,
      feedback_at: now,
    })

    return successResponse({
      message: approved ? "Script approved" : "Script rejected",
      script_id,
    })
  } catch (error: any) {
    console.error("Error submitting feedback:", error)
    return errorResponse(
      `Failed to submit feedback: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

