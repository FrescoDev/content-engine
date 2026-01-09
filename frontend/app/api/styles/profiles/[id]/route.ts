import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * GET /api/styles/profiles/[id]
 * Get a single style profile by ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await requireAuth(request)

    const { firestore } = getFirebaseAdmin()
    const { id: profileId } = await params

    const profileDoc = await firestore
      .collection("style_profiles")
      .doc(profileId)
      .get()

    if (!profileDoc.exists) {
      return errorResponse("Profile not found", ApiErrorCode.NOT_FOUND, 404)
    }

    return successResponse({
      id: profileDoc.id,
      ...profileDoc.data(),
    })
  } catch (error: any) {
    console.error("Error fetching profile:", error)
    return errorResponse(
      `Failed to fetch profile: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

/**
 * PUT /api/styles/profiles/[id]
 * Update a style profile
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const body = await request.json()
    const { id: profileId } = await params

    const { firestore } = getFirebaseAdmin()

    const profileRef = firestore.collection("style_profiles").doc(profileId)
    const profileDoc = await profileRef.get()

    if (!profileDoc.exists) {
      return errorResponse("Profile not found", ApiErrorCode.NOT_FOUND, 404)
    }

    // Update allowed fields
    const updates: any = {
      updated_at: new Date().toISOString(),
    }

    // Allow updating specific fields
    const allowedFields = [
      "tone",
      "literary_devices",
      "cultural_markers",
      "example_phrases",
      "tags",
      "category",
      "curator_notes",
    ]

    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        updates[field] = body[field]
      }
    }

    // Auto-approve if edited from pending
    const currentData = profileDoc.data()
    if (currentData?.status === "pending") {
      updates.status = "approved"
      updates.curated_by = user.email || user.uid
      updates.curated_at = new Date().toISOString()
    }

    await profileRef.update(updates)

    return successResponse({
      message: "Profile updated",
      profile_id: profileId,
    })
  } catch (error: any) {
    console.error("Error updating profile:", error)
    return errorResponse(
      `Failed to update profile: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

