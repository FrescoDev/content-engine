import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { ApiErrorCode } from "@/lib/api-errors"
import { requireAuth, errorResponse, successResponse } from "@/lib/api-helpers"
import { z } from "zod"

const UpdateScriptRequestSchema = z.object({
    content: z.string().min(1),
})

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ option_id: string }> }
) {
    try {
        const user = await requireAuth(request)
        const body = await request.json()
        const validationResult = UpdateScriptRequestSchema.safeParse(body)

        if (!validationResult.success) {
            return errorResponse(
                "Validation failed",
                ApiErrorCode.VALIDATION_ERROR,
                400,
                { errors: validationResult.error.errors }
            )
        }

        const { content } = validationResult.data
        const { option_id } = await params
        const { firestore } = getFirebaseAdmin()

        // Fetch ContentOption
        const optionDoc = await firestore.collection("content_options").doc(option_id).get()
        if (!optionDoc.exists) {
            return errorResponse("Content option not found", ApiErrorCode.OPTION_NOT_FOUND, 404)
        }

        const optionData = optionDoc.data()
        if (optionData?.option_type !== "short_script") {
            return errorResponse("Can only edit scripts", ApiErrorCode.VALIDATION_ERROR, 400)
        }

        // Update ContentOption
        const now = new Date().toISOString()
        const editHistory = optionData.edit_history || []
        editHistory.push({
            timestamp: now,
            editor_id: user.uid,
            change_type: "manual_edit",
        })

        await firestore.collection("content_options").doc(option_id).update({
            edited_content: content,
            edited_at: now,
            editor_id: user.uid,
            edit_history: editHistory,
        })

        // Fetch updated option
        const updatedDoc = await firestore.collection("content_options").doc(option_id).get()
        const updatedData = updatedDoc.data()

        return successResponse({
            option: {
                id: option_id,
                ...updatedData,
            },
        })
    } catch (error: any) {
        console.error("Error updating script:", error)

        if (error.message === "UNAUTHORIZED") {
            return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
        }

        return errorResponse("Failed to update script", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}

