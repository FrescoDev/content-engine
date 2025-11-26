import { NextRequest } from "next/server"
import { getFirebaseAdmin } from "@/lib/firebase-admin"
import { errorResponse, successResponse } from "@/lib/api-helpers"
import { ApiErrorCode } from "@/lib/api-errors"

/**
 * Generate content options (hooks and scripts) for approved topics that don't have them yet.
 * This endpoint uses OpenAI to generate hooks and scripts for topics.
 */
export async function POST(request: NextRequest) {
    try {
        const { firestore } = getFirebaseAdmin()
        const body = await request.json()
        const topicId = body.topic_id as string | undefined
        const limit = body.limit ? parseInt(body.limit as string) : 5

        // Import OpenAI dynamically
        const { OpenAI } = await import("openai")
        const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

        if (!process.env.OPENAI_API_KEY) {
            return errorResponse("OpenAI API key not configured", ApiErrorCode.INTERNAL_ERROR, 500)
        }

        // Helper function to generate hook
        const generateHook = async (topicTitle: string): Promise<string> => {
            const prompt = `Generate a short, engaging hook (1-2 sentences) for a short-form video about:

${topicTitle}

The hook should:
- Be attention-grabbing and conversational
- Make viewers want to watch more
- Be under 100 characters if possible
- Sound natural and not clickbait-y

Hook:`

            const completion = await openai.chat.completions.create({
                model: "gpt-4o-mini",
                messages: [
                    {
                        role: "system",
                        content: "You are a professional content creator writing hooks for short-form videos. Keep it concise and engaging.",
                    },
                    { role: "user", content: prompt },
                ],
                temperature: 0.8,
                max_tokens: 100,
            })

            return completion.choices[0]?.message?.content?.trim() || `Check out this: ${topicTitle.slice(0, 50)}...`
        }

        // Helper function to generate script
        const generateScript = async (topicTitle: string): Promise<string> => {
            const prompt = `Write a short-form video script (2-3 paragraphs) about:

${topicTitle}

The script should:
- Be conversational and engaging
- Be suitable for YouTube Shorts or TikTok
- Include 2-3 key points
- End with a call to action or thought-provoking question
- Be around 150-200 words

Script:`

            const completion = await openai.chat.completions.create({
                model: "gpt-4o-mini",
                messages: [
                    {
                        role: "system",
                        content: "You are a professional content creator writing scripts for short-form videos. Be engaging and conversational.",
                    },
                    { role: "user", content: prompt },
                ],
                temperature: 0.8,
                max_tokens: 300,
            })

            return completion.choices[0]?.message?.content?.trim() || `Let's talk about ${topicTitle}. This is an interesting topic that deserves attention.`
        }

        const results: Array<{ topic_id: string; topic_title: string; hooks_created: number; scripts_created: number }> = []

        if (topicId) {
            // Generate for specific topic
            const topicDoc = await firestore.collection("topic_candidates").doc(topicId).get()
            if (!topicDoc.exists) {
                return errorResponse("Topic not found", ApiErrorCode.TOPIC_NOT_FOUND, 404)
            }

            const topicData = topicDoc.data()
            const topicTitle = topicData?.title || "Untitled"

            // Check if options already exist
            const existingOptions = await firestore
                .collection("content_options")
                .where("topic_id", "==", topicId)
                .get()

            if (!existingOptions.empty) {
                return successResponse({
                    message: "Options already exist for this topic",
                    topic_id: topicId,
                    hooks_created: 0,
                    scripts_created: 0,
                })
            }

            // Generate hooks (3 hooks)
            const hooksCreated: string[] = []
            for (let i = 1; i <= 3; i++) {
                const hookContent = await generateHook(topicTitle)
                const hookId = `${topicId}-hook-${i}`
                await firestore.collection("content_options").doc(hookId).set({
                    id: hookId,
                    topic_id: topicId,
                    option_type: "short_hook",
                    content: hookContent,
                    prompt_version: "short_hook_v1",
                    model: "gpt-4o-mini",
                    metadata: {},
                    created_at: new Date().toISOString(),
                })
                hooksCreated.push(hookId)
            }

            // Generate script (1 script)
            const scriptContent = await generateScript(topicTitle)
            const scriptId = `${topicId}-script-1`
            await firestore.collection("content_options").doc(scriptId).set({
                id: scriptId,
                topic_id: topicId,
                option_type: "short_script",
                content: scriptContent,
                prompt_version: "short_script_v1",
                model: "gpt-4o-mini",
                metadata: {},
                created_at: new Date().toISOString(),
            })

            results.push({
                topic_id: topicId,
                topic_title: topicTitle,
                hooks_created: hooksCreated.length,
                scripts_created: 1,
            })
        } else {
            // Generate for approved topics without options
            const approvedTopics = await firestore
                .collection("topic_candidates")
                .where("status", "==", "approved")
                .limit(limit * 2) // Fetch more to account for filtering
                .get()

            const topicsToProcess: Array<{ id: string; title: string }> = []

            for (const topicDoc of approvedTopics.docs) {
                const topicId = topicDoc.id
                const topicData = topicDoc.data()

                // Check if options already exist
                const existingOptions = await firestore
                    .collection("content_options")
                    .where("topic_id", "==", topicId)
                    .limit(1)
                    .get()

                if (existingOptions.empty) {
                    topicsToProcess.push({
                        id: topicId,
                        title: topicData?.title || "Untitled",
                    })
                }

                if (topicsToProcess.length >= limit) {
                    break
                }
            }

            // Generate options for each topic
            for (const topic of topicsToProcess) {
                // Generate hooks (3 hooks)
                const hooksCreated: string[] = []
                for (let i = 1; i <= 3; i++) {
                    const hookContent = await generateHook(topic.title)
                    const hookId = `${topic.id}-hook-${i}`
                    await firestore.collection("content_options").doc(hookId).set({
                        id: hookId,
                        topic_id: topic.id,
                        option_type: "short_hook",
                        content: hookContent,
                        prompt_version: "short_hook_v1",
                        model: "gpt-4o-mini",
                        metadata: {},
                        created_at: new Date().toISOString(),
                    })
                    hooksCreated.push(hookId)
                }

                // Generate script (1 script)
                const scriptContent = await generateScript(topic.title)
                const scriptId = `${topic.id}-script-1`
                await firestore.collection("content_options").doc(scriptId).set({
                    id: scriptId,
                    topic_id: topic.id,
                    option_type: "short_script",
                    content: scriptContent,
                    prompt_version: "short_script_v1",
                    model: "gpt-4o-mini",
                    metadata: {},
                    created_at: new Date().toISOString(),
                })

                results.push({
                    topic_id: topic.id,
                    topic_title: topic.title,
                    hooks_created: hooksCreated.length,
                    scripts_created: 1,
                })

                // Small delay to avoid rate limits
                await new Promise((resolve) => setTimeout(resolve, 1000))
            }
        }

        return successResponse({
            message: `Generated options for ${results.length} topic(s)`,
            results,
        })
    } catch (error: any) {
        console.error("Error generating options:", error)
        return errorResponse(
            `Failed to generate options: ${error.message || String(error)}`,
            ApiErrorCode.INTERNAL_ERROR,
            500
        )
    }
}

