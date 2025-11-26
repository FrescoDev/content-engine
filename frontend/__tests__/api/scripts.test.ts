/**
 * Tests for scripts API routes.
 */

import { describe, it, expect, beforeEach, jest } from "@jest/globals"

// Mock Firebase Admin
jest.mock("@/lib/firebase-admin", () => ({
    getFirebaseAdmin: jest.fn(() => ({
        firestore: {
            collection: jest.fn(() => ({
                doc: jest.fn(() => ({
                    get: jest.fn(),
                    update: jest.fn(),
                })),
            })),
        },
    })),
}))

// Mock OpenAI
jest.mock("openai", () => ({
    OpenAI: jest.fn(() => ({
        chat: {
            completions: {
                create: jest.fn(),
            },
        },
    })),
}))

describe("Scripts API Routes", () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    describe("POST /api/scripts/refine", () => {
        it("should validate request body", async () => {
            const { NextRequest } = await import("next/server")
            const { POST } = await import("@/app/api/scripts/refine/route")

            const request = new NextRequest("http://localhost/api/scripts/refine", {
                method: "POST",
                body: JSON.stringify({
                    // Missing required fields
                }),
            })

            const response = await POST(request)
            const data = await response.json()

            expect(response.status).toBe(400)
            expect(data.success).toBe(false)
            expect(data.error.code).toBe("VALIDATION_ERROR")
        })

        it("should validate refinement_type enum", async () => {
            const { NextRequest } = await import("next/server")
            const { POST } = await import("@/app/api/scripts/refine/route")

            const request = new NextRequest("http://localhost/api/scripts/refine", {
                method: "POST",
                body: JSON.stringify({
                    option_id: "test-option-1",
                    refinement_type: "invalid_type",
                }),
            })

            const response = await POST(request)
            const data = await response.json()

            expect(response.status).toBe(400)
            expect(data.success).toBe(false)
        })
    })

    describe("PUT /api/scripts/[option_id]", () => {
        it("should validate request body", async () => {
            const { NextRequest } = await import("next/server")
            const { PUT } = await import("@/app/api/scripts/[option_id]/route")

            const request = new NextRequest("http://localhost/api/scripts/test-option-1", {
                method: "PUT",
                body: JSON.stringify({
                    // Missing content
                }),
            })

            const response = await PUT(request, { params: Promise.resolve({ option_id: "test-option-1" }) })
            const data = await response.json()

            expect(response.status).toBe(400)
            expect(data.success).toBe(false)
            expect(data.error.code).toBe("VALIDATION_ERROR")
        })

        it("should require content field", async () => {
            const { NextRequest } = await import("next/server")
            const { PUT } = await import("@/app/api/scripts/[option_id]/route")

            const request = new NextRequest("http://localhost/api/scripts/test-option-1", {
                method: "PUT",
                body: JSON.stringify({
                    content: "",
                }),
            })

            const response = await PUT(request, { params: Promise.resolve({ option_id: "test-option-1" }) })
            const data = await response.json()

            expect(response.status).toBe(400)
            expect(data.success).toBe(false)
        })
    })
})

