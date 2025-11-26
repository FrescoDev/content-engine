import { NextRequest, NextResponse } from "next/server"
import { ApiErrorCode } from "@/lib/api-errors"
import type { ApiResponse, AuditEventResponse } from "@/lib/api-types"
import { getFirestore } from "firebase-admin/firestore"
import { getFirebaseAdmin } from "@/lib/firebase-admin"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const stage = searchParams.get("stage")
    const topicId = searchParams.get("topic_id")
    const limit = parseInt(searchParams.get("limit") || "50", 10)
    const cursor = searchParams.get("cursor") // For pagination
    const dateFrom = searchParams.get("date_from")
    const dateTo = searchParams.get("date_to")

    const { firestore } = getFirebaseAdmin()

    // Build query
    let query: FirebaseFirestore.Query = firestore.collection("audit_events")

    // Apply filters
    if (stage) {
      query = query.where("stage", "==", stage)
    }
    if (topicId) {
      query = query.where("topic_id", "==", topicId)
    }
    if (dateFrom) {
      query = query.where("created_at", ">=", dateFrom)
    }
    if (dateTo) {
      query = query.where("created_at", "<=", dateTo)
    }

    // Order by created_at descending
    query = query.orderBy("created_at", "desc")

    // Apply cursor for pagination
    if (cursor) {
      const cursorDoc = await firestore.collection("audit_events").doc(cursor).get()
      if (cursorDoc.exists) {
        query = query.startAfter(cursorDoc)
      }
    }

    // Fetch limit + 1 to check if there are more
    const snapshot = await query.limit(limit + 1).get()
    const docs = snapshot.docs
    const hasMore = docs.length > limit
    const events = hasMore ? docs.slice(0, limit) : docs

    // Fetch topic titles for enrichment
    const topicIds = new Set<string>()
    events.forEach((doc) => {
      const data = doc.data()
      if (data.topic_id) {
        topicIds.add(data.topic_id)
      }
    })

    const topicTitles: Record<string, string> = {}
    if (topicIds.size > 0) {
      const topicsSnapshot = await firestore
        .collection("topic_candidates")
        .where("__name__", "in", Array.from(topicIds))
        .get()

      topicsSnapshot.docs.forEach((doc) => {
        topicTitles[doc.id] = doc.data().title || ""
      })
    }

    // Build response
    const result: AuditEventResponse[] = events.map((doc) => {
      const data = doc.data()
      return {
        id: doc.id,
        stage: data.stage,
        topic_id: data.topic_id || undefined,
        topic_title: data.topic_id ? topicTitles[data.topic_id] : undefined,
        actor: data.actor,
        created_at: data.created_at?.toDate?.()?.toISOString() || data.created_at,
        system_decision: data.system_decision || {},
        human_action: data.human_action || null,
      }
    })

    const nextCursor = hasMore && events.length > 0 ? events[events.length - 1].id : null

    return NextResponse.json({
      success: true,
      data: {
        events: result,
        next_cursor: nextCursor,
        has_more: hasMore,
      },
    } satisfies ApiResponse<{ events: AuditEventResponse[]; next_cursor: string | null; has_more: boolean }>)
  } catch (error) {
    console.error("Error fetching audit events:", error)
    return NextResponse.json(
      {
        success: false,
        error: {
          error: "Failed to fetch audit events",
          code: ApiErrorCode.INTERNAL_ERROR,
        },
      } satisfies ApiResponse<never>,
      { status: 500 }
    )
  }
}

