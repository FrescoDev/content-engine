/**
 * Tests for API helper functions.
 */

import { describe, it, expect } from "@jest/globals"
import { batchArray, parseLimit, toISOString } from "../lib/api-helpers"

describe("api-helpers", () => {
    describe("batchArray", () => {
        it("should batch array into chunks of specified size", () => {
            const array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            const batches = batchArray(array, 3)
            expect(batches).toEqual([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]])
        })

        it("should handle empty array", () => {
            const batches = batchArray([], 10)
            expect(batches).toEqual([])
        })

        it("should handle array smaller than batch size", () => {
            const batches = batchArray([1, 2], 10)
            expect(batches).toEqual([[1, 2]])
        })

        it("should handle exact batch size", () => {
            const batches = batchArray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10)
            expect(batches).toEqual([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
        })
    })

    describe("parseLimit", () => {
        it("should parse valid limit", () => {
            const params = new URLSearchParams("limit=50")
            expect(parseLimit(params, 20, 100)).toBe(50)
        })

        it("should use default when limit not provided", () => {
            const params = new URLSearchParams()
            expect(parseLimit(params, 20, 100)).toBe(20)
        })

        it("should enforce max limit", () => {
            const params = new URLSearchParams("limit=200")
            expect(parseLimit(params, 20, 100)).toBe(100)
        })

        it("should handle invalid limit", () => {
            const params = new URLSearchParams("limit=abc")
            expect(parseLimit(params, 20, 100)).toBe(20)
        })

        it("should handle negative limit", () => {
            const params = new URLSearchParams("limit=-5")
            expect(parseLimit(params, 20, 100)).toBe(20)
        })

        it("should handle zero limit", () => {
            const params = new URLSearchParams("limit=0")
            expect(parseLimit(params, 20, 100)).toBe(20)
        })
    })

    describe("toISOString", () => {
        it("should convert Firestore Timestamp to ISO string", () => {
            const mockTimestamp = {
                toDate: () => new Date("2024-01-01T00:00:00Z"),
            }
            const result = toISOString(mockTimestamp)
            expect(result).toBe("2024-01-01T00:00:00.000Z")
        })

        it("should return ISO string as-is", () => {
            const isoString = "2024-01-01T00:00:00.000Z"
            expect(toISOString(isoString)).toBe(isoString)
        })

        it("should convert Date object to ISO string", () => {
            const date = new Date("2024-01-01T00:00:00Z")
            expect(toISOString(date)).toBe("2024-01-01T00:00:00.000Z")
        })

        it("should handle null/undefined", () => {
            const result = toISOString(null)
            expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/) // Should be valid ISO string
        })
    })
})

