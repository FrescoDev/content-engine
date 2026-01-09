import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
  parseLimit,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * GET /api/styles/profiles
 * List style profiles with optional filters
 */
export async function GET(request: NextRequest) {
  try {
    await requireAuth(request)

    const { searchParams } = new URL(request.url)
    const limit = parseLimit(searchParams, 20, 100)
    const status = searchParams.get("status") || "all"
    const sourceId = searchParams.get("source_id")

    const { firestore } = getFirebaseAdmin()

    // Build query
    let query = firestore.collection("style_profiles")

    // Apply filters
    if (status !== "all") {
      query = query.where("status", "==", status)
    }
    if (sourceId) {
      query = query.where("source_id", "==", sourceId)
    }

    // Fetch without orderBy to avoid composite index requirement
    // Sort in-memory instead (acceptable for MVP with <100 profiles)
    const snapshot = await query.limit(limit * 2).get() // Fetch more for sorting
    const profiles = snapshot.docs
      .map((doc) => ({
        id: doc.id,
        ...doc.data(),
      }))
      .sort((a, b) => {
        const aTime = new Date(a.created_at || 0).getTime()
        const bTime = new Date(b.created_at || 0).getTime()
        return bTime - aTime // Descending
      })
      .slice(0, limit) // Take top N after sorting

    return successResponse(profiles)
  } catch (error: any) {
    console.error("Error fetching style profiles:", error)
    return errorResponse(
      `Failed to fetch profiles: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

/**
 * POST /api/styles/profiles/[id]/approve
 * Approve a style profile
 */
export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    const body = await request.json()
    const { profile_id, notes } = body

    if (!profile_id) {
      return errorResponse(
        "profile_id is required",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    const { firestore } = getFirebaseAdmin()

    // Get profile
    const profileRef = firestore.collection("style_profiles").doc(profile_id)
    const profileDoc = await profileRef.get()

    if (!profileDoc.exists) {
      return errorResponse(
        "Profile not found",
        ApiErrorCode.NOT_FOUND,
        404
      )
    }

    const profileData = profileDoc.data()
    if (!profileData) {
      return errorResponse(
        "Profile data is invalid",
        ApiErrorCode.INTERNAL_ERROR,
        500
      )
    }

    // Validate profile can be approved
    if (profileData.status === "approved") {
      return errorResponse(
        "Profile already approved",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    if (!profileData.tone) {
      return errorResponse(
        "Profile missing required fields (tone)",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    // Update profile
    const now = new Date().toISOString()
    await profileRef.update({
      status: "approved",
      curated_by: user.email || user.uid,
      curated_at: now,
      curator_notes: notes || null,
      updated_at: now,
    })

    return successResponse({
      message: "Profile approved",
      profile_id,
    })
  } catch (error: any) {
    console.error("Error approving profile:", error)
    return errorResponse(
      `Failed to approve profile: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

