import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * POST /api/styles/sources
 * Add a stylistic source from URL - fully automated
 */
export async function POST(request: NextRequest) {
  try {
    await requireAuth(request)
    const body = await request.json()
    const { url, source_name, description, tags, auto_extract = true } = body as {
      url: string
      source_name?: string
      description?: string
      tags?: string[]
      auto_extract?: boolean
    }

    if (!url || typeof url !== "string") {
      return errorResponse("URL is required", ApiErrorCode.VALIDATION_ERROR, 400)
    }

    // Call backend service via Cloud Function or direct API
    // For MVP, we'll call the backend CLI via a subprocess
    // In production, this should be a Cloud Function or direct service call
    
    // For now, return success and let user know to use CLI
    // TODO: Implement backend API call or Cloud Function
    
    return successResponse({
      message: "Source ingestion initiated",
      url,
      note: "This endpoint will trigger automated ingestion. Implementation pending.",
    })
  } catch (error: any) {
    console.error("Error adding source:", error)
    return errorResponse(
      `Failed to add source: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

/**
 * GET /api/styles/sources
 * List all stylistic sources
 */
export async function GET(request: NextRequest) {
  try {
    await requireAuth(request)
    const { firestore } = getFirebaseAdmin()

    const sourcesSnapshot = await firestore.collection("stylistic_sources").get()
    const sources = sourcesSnapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }))

    return successResponse(sources)
  } catch (error: any) {
    console.error("Error fetching sources:", error)
    return errorResponse(
      `Failed to fetch sources: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}





