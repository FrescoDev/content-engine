import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { ApiErrorCode } from "@/lib/api-errors"
import { requireAuth, errorResponse, successResponse } from "@/lib/api-helpers"
import { z } from "zod"

const RefinementRequestSchema = z.object({
    option_id: z.string().min(1),
    refinement_type: z.enum(["tighten", "casual", "regenerate"]),
})

export async function POST(request: NextRequest) {
    try {
        const user = await requireAuth(request)
        const body = await request.json()
        const validationResult = RefinementRequestSchema.safeParse(body)

        if (!validationResult.success) {
            return errorResponse(
                "Validation failed",
                ApiErrorCode.VALIDATION_ERROR,
                400,
                { errors: validationResult.error.errors }
            )
        }

        const { option_id, refinement_type } = validationResult.data
        const { firestore } = getFirebaseAdmin()

        // Fetch ContentOption
        const optionDoc = await firestore.collection("content_options").doc(option_id).get()
        if (!optionDoc.exists) {
            return errorResponse("Content option not found", ApiErrorCode.OPTION_NOT_FOUND, 404)
        }

        const optionData = optionDoc.data()
        if (optionData?.option_type !== "short_script") {
            return errorResponse("Can only refine scripts", ApiErrorCode.VALIDATION_ERROR, 400)
        }

        // Get base content (use edited_content if exists, otherwise content)
        const baseContent = optionData.edited_content || optionData.content

        // Build refinement prompt
        let prompt = `Refine the following script for a short-form video:\n\n${baseContent}\n\n`

        if (refinement_type === "tighten") {
            prompt +=
                "Make this script more concise and punchy. Remove filler words and unnecessary phrases. " +
                "Keep the core message and key points, but make every word count. Aim for 20-30% shorter."
        } else if (refinement_type === "casual") {
            prompt +=
                "Adjust the tone to be more conversational and casual. Make it sound like you're talking to a friend, " +
                "not reading from a script. Keep it engaging and natural while maintaining the core message."
        } else if (refinement_type === "regenerate") {
            prompt +=
                "Regenerate this script with fresh wording while keeping the same core message and structure. " +
                "Make it feel new and engaging while preserving all key points."
        }

        // Call OpenAI (using backend service would be better, but for MVP we'll call directly)
        // TODO: Move to backend service for better error handling and retry logic
        const { OpenAI } = await import("openai")
        const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

        const completion = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [
                {
                    role: "system",
                    content:
                        "You are a professional script editor helping create engaging short-form video content. " +
                        "Maintain the core message while applying the requested refinement.",
                },
                { role: "user", content: prompt },
            ],
            temperature: 0.7,
        })

        const refinedContent = completion.choices[0]?.message?.content?.trim()
        if (!refinedContent) {
            return errorResponse("AI refinement failed", ApiErrorCode.INTERNAL_ERROR, 500)
        }

        // Update ContentOption
        const now = new Date().toISOString()
        const editHistory = optionData.edit_history || []
        editHistory.push({
            timestamp: now,
            editor_id: user.uid,
            change_type: "ai_refinement",
            refinement_type,
        })

        const refinementApplied = optionData.refinement_applied || []
        if (!refinementApplied.includes(refinement_type)) {
            refinementApplied.push(refinement_type)
        }

        await firestore.collection("content_options").doc(option_id).update({
            edited_content: refinedContent,
            edited_at: now,
            editor_id: user.uid,
            edit_history: editHistory,
            refinement_applied: refinementApplied,
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
        console.error("Error refining script:", error)

        if (error.message === "UNAUTHORIZED") {
            return errorResponse("Unauthorized", ApiErrorCode.UNAUTHORIZED, 401)
        }

        return errorResponse("Failed to refine script", ApiErrorCode.INTERNAL_ERROR, 500)
    }
}





