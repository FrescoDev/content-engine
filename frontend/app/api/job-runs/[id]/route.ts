import { NextRequest, NextResponse } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { requireAuth, errorResponse } from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * GET /api/job-runs/[id]
 * Get a specific job run by ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    // Auth optional for local development
    if (process.env.NODE_ENV === "production") {
      await requireAuth(request)
    }

    const { id } = await params
    const { firestore } = getFirebaseAdmin()

    const doc = await firestore.collection("job_runs").doc(id).get()

    if (!doc.exists) {
      return errorResponse("Job run not found", ApiErrorCode.VALIDATION_ERROR, 404)
    }

    return NextResponse.json({
      success: true,
      data: {
        id: doc.id,
        ...doc.data(),
      },
    })
  } catch (error) {
    if (error instanceof Error && error.message === "UNAUTHORIZED") {
      return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
    }
    console.error("Failed to fetch job run:", error)
    return errorResponse("Failed to fetch job run", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

