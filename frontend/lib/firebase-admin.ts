/**
 * Firebase Admin SDK setup for Next.js API routes.
 * This is server-side only.
 */

import { initializeApp, getApps, cert, type App } from "firebase-admin/app"
import { getAuth, type Auth } from "firebase-admin/auth"
import { getFirestore, type Firestore } from "firebase-admin/firestore"

let app: App | undefined
let auth: Auth | undefined
let firestore: Firestore | undefined

export function getFirebaseAdmin(): { app: App; auth: Auth; firestore: Firestore } {
    if (app && auth && firestore) {
        return { app, auth, firestore }
    }

    // Initialize if not already initialized
    if (getApps().length === 0) {
        const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT_KEY
            ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY)
            : undefined

        if (serviceAccount) {
            app = initializeApp({
                credential: cert(serviceAccount),
                projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
            })
        } else {
            // Use Application Default Credentials (for GCP environments)
            app = initializeApp({
                projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
            })
        }
    } else {
        app = getApps()[0]
    }

    auth = getAuth(app)
    firestore = getFirestore(app, process.env.NEXT_PUBLIC_FIREBASE_DATABASE_ID || "main-db")

    return { app, auth, firestore }
}

/**
 * Verify Firebase auth token from request headers.
 */
export async function verifyAuthToken(token: string | null): Promise<{ uid: string; email?: string } | null> {
    if (!token) {
        return null
    }

    try {
        const { auth } = getFirebaseAdmin()
        const decodedToken = await auth.verifyIdToken(token)
        return {
            uid: decodedToken.uid,
            email: decodedToken.email,
        }
    } catch (error) {
        // Log error for debugging, but don't expose details to client
        console.error("Token verification failed:", error instanceof Error ? error.message : "Unknown error")
        return null
    }
}

