import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import {
  requireAuth,
  errorResponse,
  successResponse,
} from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * POST /api/styles/profiles/[id]/test
 * Generate a test script segment using the style profile
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const body = await request.json()
    const { id: profileId } = await params
    const { topic, length = "short" } = body as { topic?: string; length?: "short" | "medium" }

    const { firestore } = getFirebaseAdmin()

    // Get style profile
    const profileDoc = await firestore.collection("style_profiles").doc(profileId).get()
    if (!profileDoc.exists) {
      return errorResponse("Profile not found", ApiErrorCode.NOT_FOUND, 404)
    }

    const profile = profileDoc.data()
    if (!profile || profile.status !== "approved") {
      return errorResponse(
        "Profile must be approved to test",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    // Import OpenAI
    const { OpenAI } = await import("openai")
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

    if (!process.env.OPENAI_API_KEY) {
      return errorResponse("OpenAI API key not configured", ApiErrorCode.INTERNAL_ERROR, 500)
    }

    // Build style context (same as in content generation)
    const styleParts: string[] = []
    if (profile.tone) {
      styleParts.push(`Tone: ${profile.tone}`)
    }
    if (profile.example_phrases && profile.example_phrases.length > 0) {
      const examples = profile.example_phrases.slice(0, 3)
      const examplesText = examples.map((e: string) => `"${e.substring(0, 100)}"`).join(", ")
      styleParts.push(`Example phrases: ${examplesText}`)
    }
    if (profile.literary_devices && profile.literary_devices.length > 0) {
      const devices = profile.literary_devices.slice(0, 5).join(", ")
      styleParts.push(`Literary devices: ${devices}`)
    }
    if (profile.cultural_markers && profile.cultural_markers.length > 0) {
      const markers = profile.cultural_markers.slice(0, 5).join(", ")
      styleParts.push(`Cultural markers: ${markers}`)
    }

    // Validate style context exists
    if (styleParts.length === 0) {
      return errorResponse(
        "Profile missing style data (tone, example phrases, literary devices, or cultural markers)",
        ApiErrorCode.VALIDATION_ERROR,
        400
      )
    }

    const styleContext = styleParts.join("\n")
    const maxChars = 2000
    const truncatedContext = styleContext.length > maxChars
      ? styleContext.substring(0, maxChars) + "..."
      : styleContext

    // Use generic test topic if not provided, validate if provided
    let testTopic = topic || "AI's impact on creative industries"
    
    if (topic) {
      // Validate topic length
      const trimmedTopic = topic.trim()
      if (trimmedTopic.length === 0 || trimmedTopic.length > 200) {
        return errorResponse(
          "Topic must be between 1 and 200 characters",
          ApiErrorCode.VALIDATION_ERROR,
          400
        )
      }
      // Sanitize: remove newlines, extra spaces
      testTopic = trimmedTopic.replace(/\n+/g, " ").replace(/\s+/g, " ")
    }

    // Build prompt based on length
    const lengthInstructions =
      length === "short"
        ? "Write a short script segment (2-3 sentences, 50-100 words)"
        : "Write a medium script segment (4-5 sentences, 100-150 words)"

    const basePrompt = `${lengthInstructions} about:

${testTopic}

The script should:
- Be conversational and engaging
- Be suitable for YouTube Shorts or TikTok
- Include 1-2 key points
- Sound natural and authentic

Script:`

    const enhancedPrompt = `${basePrompt}

STYLISTIC CONTEXT:
${truncatedContext}

When generating content, incorporate these stylistic elements naturally while maintaining the core message.`

    // Generate script with retry logic
    let completion
    let lastError = null
    const maxRetries = 3
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        completion = await openai.chat.completions.create({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content:
                "You are a professional content creator writing scripts for short-form videos. Apply the stylistic context provided to create authentic, engaging content.",
            },
            { role: "user", content: enhancedPrompt },
          ],
          temperature: 0.8,
          max_tokens: length === "short" ? 150 : 250,
        })
        break // Success
      } catch (error: any) {
        lastError = error
        if (attempt < maxRetries - 1) {
          // Exponential backoff
          await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)))
          continue
        }
        throw error
      }
    }
    
    if (!completion) {
      throw lastError || new Error("Failed to generate script after retries")
    }

    const scriptText = completion.choices[0]?.message?.content?.trim()
    if (!scriptText) {
      return errorResponse("Failed to generate script", ApiErrorCode.INTERNAL_ERROR, 500)
    }

    // Calculate cost using actual token usage from API response
    const usage = completion.usage
    const inputTokens = usage?.prompt_tokens || 0
    const outputTokens = usage?.completion_tokens || 0
    const costUsd = (inputTokens / 1_000_000) * 0.15 + (outputTokens / 1_000_000) * 0.6

    // Save test script to database (use Firestore auto-ID for uniqueness)
    const testScriptRef = firestore.collection("style_test_scripts").doc()
    const testScriptId = testScriptRef.id
    
    await testScriptRef.set({
      id: testScriptId,
      profile_id: profileId,
      script_text: scriptText,
      test_topic: testTopic,
      status: "pending",
      feedback_notes: null,
      feedback_by: null,
      feedback_at: null,
      generated_by: user.email || user.uid,
      generation_cost_usd: costUsd,
      generation_model: "gpt-4o-mini",
      created_at: new Date().toISOString(),
    })

    return successResponse({
      script_id: testScriptId,
      script: scriptText,
      cost_usd: costUsd,
      model: "gpt-4o-mini",
      topic: testTopic,
    })
  } catch (error: any) {
    console.error("Error generating test script:", error)
    return errorResponse(
      `Failed to generate test script: ${error.message || String(error)}`,
      ApiErrorCode.INTERNAL_ERROR,
      500
    )
  }
}

