import { NextRequest, NextResponse } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { requireAuth, errorResponse } from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * GET /api/job-runs
 * List job runs with optional filtering
 */
export async function GET(request: NextRequest) {
  try {
    // Auth optional for local development
    if (process.env.NODE_ENV === "production") {
      await requireAuth(request)
    }

    const { searchParams } = new URL(request.url)
    const jobType = searchParams.get("job_type")
    const status = searchParams.get("status")
    const limit = parseInt(searchParams.get("limit") || "50")
    const startAfter = searchParams.get("start_after") // Document ID for pagination

    const { firestore } = getFirebaseAdmin()

    let query = firestore
      .collection("job_runs")
      .orderBy("started_at", "desc")
      .limit(limit)

    if (jobType) {
      query = query.where("job_type", "==", jobType)
    }

    if (status) {
      query = query.where("status", "==", status)
    }

    if (startAfter) {
      const startAfterDoc = await firestore.collection("job_runs").doc(startAfter).get()
      if (startAfterDoc.exists) {
        query = query.startAfter(startAfterDoc)
      }
    }

    const snapshot = await query.get()
    const jobRuns = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }))

    return NextResponse.json({
      success: true,
      data: jobRuns,
      next_cursor: snapshot.docs.length === limit ? snapshot.docs[snapshot.docs.length - 1].id : null,
    })
  } catch (error) {
    if (error instanceof Error && error.message === "UNAUTHORIZED") {
      return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
    }
    console.error("Failed to fetch job runs:", error)
    return errorResponse("Failed to fetch job runs", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

/**
 * DELETE /api/job-runs
 * Delete a job run (admin only)
 */
export async function DELETE(request: NextRequest) {
  try {
    // Auth optional for local development
    if (process.env.NODE_ENV === "production") {
      await requireAuth(request)
    }

    const { searchParams } = new URL(request.url)
    const jobRunId = searchParams.get("id")

    if (!jobRunId) {
      return errorResponse("Job run ID required", ApiErrorCode.VALIDATION_ERROR, 400)
    }

    const { firestore } = getFirebaseAdmin()
    await firestore.collection("job_runs").doc(jobRunId).delete()

    return NextResponse.json({ success: true })
  } catch (error) {
    if (error instanceof Error && error.message === "UNAUTHORIZED") {
      return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
    }
    console.error("Failed to delete job run:", error)
    return errorResponse("Failed to delete job run", ApiErrorCode.INTERNAL_ERROR, 500)
  }
}

