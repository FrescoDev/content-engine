/**
 * Helper functions for API routes.
 */

import { NextRequest } from "next/server"
import { verifyAuthToken } from "./firebase-admin"
import { ApiErrorCode } from "./api-errors"
import type { ApiResponse } from "./api-types"

/**
 * Extract and verify auth token from request.
 * Throws error if unauthorized.
 */
export async function requireAuth(request: NextRequest): Promise<{ uid: string; email?: string }> {
    const authHeader = request.headers.get("authorization")
    const token = authHeader?.replace("Bearer ", "") || null
    const user = await verifyAuthToken(token)

    if (!user) {
        throw new Error("UNAUTHORIZED")
    }

    return user
}

/**
 * Create error response.
 */
export function errorResponse(
    error: string,
    code: ApiErrorCode,
    status: number,
    details?: Record<string, any>
): Response {
    return Response.json(
        {
            success: false,
            error: {
                error,
                code,
                details,
            },
        } satisfies ApiResponse<never>,
        { status }
    )
}

/**
 * Create success response.
 */
export function successResponse<T>(data: T): Response {
    return Response.json({
        success: true,
        data,
    } satisfies ApiResponse<T>)
}

/**
 * Parse and validate limit query parameter.
 */
export function parseLimit(searchParams: URLSearchParams, defaultLimit = 20, maxLimit = 100): number {
    const limitStr = searchParams.get("limit")
    if (!limitStr) return defaultLimit

    const limit = parseInt(limitStr, 10)
    if (isNaN(limit) || limit < 1) return defaultLimit
    if (limit > maxLimit) return maxLimit

    return limit
}

/**
 * Batch array into chunks of specified size.
 */
export function batchArray<T>(array: T[], size: number): T[][] {
    const batches: T[][] = []
    for (let i = 0; i < array.length; i += size) {
        batches.push(array.slice(i, i + size))
    }
    return batches
}

/**
 * Convert Firestore Timestamp or ISO string to ISO string.
 */
export function toISOString(value: any): string {
    if (value?.toDate) {
        return value.toDate().toISOString()
    }
    if (typeof value === "string") {
        return value
    }
    if (value instanceof Date) {
        return value.toISOString()
    }
    return new Date().toISOString()
}

