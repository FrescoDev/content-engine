"use client"

import { auth } from "./firebase"

/**
 * Get the current user's ID token for API authentication.
 * Returns null if user is not authenticated or token cannot be retrieved.
 */
export async function getIdToken(): Promise<string | null> {
  const user = auth.currentUser
  if (!user) {
    return null
  }
  try {
    return await user.getIdToken()
  } catch (error) {
    console.error("Error getting ID token:", error)
    return null
  }
}

