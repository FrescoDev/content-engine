"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  CheckCircle,
  XCircle,
  Edit,
  Eye,
  Loader2,
  AlertCircle,
  Sparkles,
  RefreshCw,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface StyleProfile {
  id: string
  source_name: string
  tone: string
  literary_devices: string[]
  cultural_markers: string[]
  example_phrases: string[]
  status: "pending" | "approved" | "rejected" | "archived" | "needs_review"
  curator_notes?: string
  quality_issues?: string[]
  created_at: string
}

interface TestScript {
  script_id: string
  script: string
  cost_usd: number
  model: string
  topic: string
}

export function StylesView() {
  const [profiles, setProfiles] = useState<StyleProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProfile, setSelectedProfile] = useState<StyleProfile | null>(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>("pending")
  const [rejectReason, setRejectReason] = useState("")
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  
  // Test script state
  const [testScript, setTestScript] = useState<TestScript | null>(null)
  const [generatingScript, setGeneratingScript] = useState(false)
  const [testFeedbackNotes, setTestFeedbackNotes] = useState("")
  const [showTestFeedbackDialog, setShowTestFeedbackDialog] = useState(false)
  const [testFeedbackApproved, setTestFeedbackApproved] = useState(true)
  
  const { toast } = useToast()

  const fetchProfiles = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (statusFilter !== "all") {
        params.append("status", statusFilter)
      }
      params.append("limit", "50")

      const response = await fetch(`/api/styles/profiles?${params.toString()}`)
      const data = await response.json()

      if (data.success) {
        setProfiles(data.data || [])
      } else {
        toast({
          title: "Error",
          description: "Failed to fetch profiles",
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Failed to fetch profiles:", error)
      toast({
        title: "Error",
        description: "Failed to fetch profiles",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfiles()
  }, [statusFilter])

  // Clear test script when profile changes
  useEffect(() => {
    setTestScript(null)
    setTestFeedbackNotes("")
    setShowTestFeedbackDialog(false)
  }, [selectedProfile?.id])

  const handleApprove = async (profileId: string) => {
    try {
      const response = await fetch(`/api/styles/profiles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId }),
      })

      const data = await response.json()
      if (data.success) {
        toast({
          title: "Success",
          description: "Profile approved",
        })
        fetchProfiles()
        setShowDetailDialog(false)
      } else {
        // Handle error object structure: {error: {error: string, code: string}}
        const errorMessage = typeof data.error === "string" 
          ? data.error 
          : data.error?.error || "Failed to approve profile"
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Failed to approve profile:", error)
      toast({
        title: "Error",
        description: "Failed to approve profile",
        variant: "destructive",
      })
    }
  }

  const handleReject = async (profileId: string) => {
    if (!rejectReason.trim()) {
      toast({
        title: "Error",
        description: "Please provide a rejection reason",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await fetch(`/api/styles/profiles/${profileId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: rejectReason }),
      })

      const data = await response.json()
      if (data.success) {
        toast({
          title: "Success",
          description: "Profile rejected",
        })
        fetchProfiles()
        setShowRejectDialog(false)
        setShowDetailDialog(false)
        setRejectReason("")
      } else {
        // Handle error object structure: {error: {error: string, code: string}}
        const errorMessage = typeof data.error === "string" 
          ? data.error 
          : data.error?.error || "Failed to reject profile"
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Failed to reject profile:", error)
      toast({
        title: "Error",
        description: "Failed to reject profile",
        variant: "destructive",
      })
    }
  }

  const handleTestStyle = async (profileId: string) => {
    // Remove redundant frontend check - API validates status
    // This prevents race conditions and stale state issues
    setGeneratingScript(true)
    try {
      const response = await fetch(`/api/styles/profiles/${profileId}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ length: "short" }),
      })

      const data = await response.json()
      if (data.success) {
        setTestScript(data.data)
        toast({
          title: "Success",
          description: "Script generated",
        })
      } else {
        const errorMessage = typeof data.error === "string"
          ? data.error
          : data.error?.error || "Failed to generate script"
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Failed to generate test script:", error)
      // Clear old script on error to prevent confusion
      setTestScript(null)
      toast({
        title: "Error",
        description: "Failed to generate test script",
        variant: "destructive",
      })
    } finally {
      setGeneratingScript(false)
    }
  }

  const handleRegenerateScript = async () => {
    if (!selectedProfile) return
    await handleTestStyle(selectedProfile.id)
  }

  const handleTestScriptFeedback = async (approved: boolean) => {
    if (!selectedProfile || !testScript) return

    if (!approved && !testFeedbackNotes.trim()) {
      toast({
        title: "Error",
        description: "Please provide feedback notes when rejecting",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await fetch(`/api/styles/profiles/${selectedProfile.id}/test/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script_id: testScript.script_id,
          approved,
          notes: approved ? null : testFeedbackNotes,
        }),
      })

      const data = await response.json()
      if (data.success) {
        toast({
          title: "Success",
          description: approved ? "Script approved" : "Feedback submitted",
        })
        setTestScript(null)
        setTestFeedbackNotes("")
        setShowTestFeedbackDialog(false)
      } else {
        const errorMessage = typeof data.error === "string"
          ? data.error
          : data.error?.error || "Failed to submit feedback"
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Failed to submit feedback:", error)
      toast({
        title: "Error",
        description: "Failed to submit feedback",
        variant: "destructive",
      })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return (
          <Badge className="bg-success/10 text-success border-success/20">
            Approved
          </Badge>
        )
      case "rejected":
        return (
          <Badge className="bg-destructive/10 text-destructive border-destructive/20">
            Rejected
          </Badge>
        )
      case "pending":
        return (
          <Badge className="bg-primary/10 text-primary border-primary/20">
            Pending
          </Badge>
        )
      case "needs_review":
        return (
          <Badge className="bg-warning/10 text-warning border-warning/20">
            Needs Review
          </Badge>
        )
      default:
        return <Badge>{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">
              Styles
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Review and curate style profiles
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
              <SelectItem value="needs_review">Needs Review</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={fetchProfiles} className="sm:ml-auto">
            Refresh
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 lg:p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : profiles.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-muted-foreground">No profiles found</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {profiles.map((profile) => (
                <Card
                  key={profile.id}
                  className={`p-4 transition-colors ${
                    selectedProfile?.id === profile.id
                      ? "bg-accent border-primary"
                      : "hover:bg-accent/50 cursor-pointer"
                  }`}
                  onClick={() => {
                    setSelectedProfile(profile)
                    setShowDetailDialog(true)
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-foreground">
                          {profile.source_name} Style
                        </h3>
                        {getStatusBadge(profile.status)}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-2">
                        <span>Tone: {profile.tone}</span>
                        {profile.literary_devices && profile.literary_devices.length > 0 && (
                          <>
                            <span>•</span>
                            <span>
                              Devices: {profile.literary_devices.slice(0, 3).join(", ")}
                            </span>
                          </>
                        )}
                      </div>

                      {profile.example_phrases && profile.example_phrases.length > 0 && (
                        <p className="text-sm text-muted-foreground italic line-clamp-1">
                          "{profile.example_phrases[0]}"
                        </p>
                      )}

                      {profile.quality_issues && profile.quality_issues.length > 0 && (
                        <div className="mt-2 flex items-start gap-2 text-sm text-warning">
                          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <span className="line-clamp-1">
                            {profile.quality_issues[0]}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {profile.status === "approved" && (
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedProfile(profile)
                            handleTestStyle(profile.id)
                          }}
                          disabled={generatingScript}
                        >
                          <Sparkles className="w-4 h-4 mr-1" />
                          {generatingScript ? "..." : "Test"}
                        </Button>
                      )}
                      {profile.status === "pending" && (
                        <>
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleApprove(profile.id)
                            }}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedProfile(profile)
                              setShowRejectDialog(true)
                            }}
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedProfile(profile)
                          setShowDetailDialog(true)
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Test Script Panel */}
      {selectedProfile && selectedProfile.status === "approved" && (
        <div className="border-t border-border bg-card px-4 lg:px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-semibold text-foreground">
                  Testing: {selectedProfile.source_name}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Generate script segments to test style application
                </p>
              </div>
              <Button
                onClick={() => handleTestStyle(selectedProfile.id)}
                disabled={generatingScript}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {generatingScript ? "Generating..." : "Generate Script"}
              </Button>
            </div>

            {testScript && (
              <Card className="p-4 mt-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">Test Script</Badge>
                      <span className="text-xs text-muted-foreground">
                        Topic: {testScript.topic}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Cost: ${testScript.cost_usd.toFixed(4)}
                      </span>
                    </div>
                    <div className="bg-muted/50 rounded-md p-3 mb-3">
                      <p className="text-sm whitespace-pre-wrap">{testScript.script}</p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleRegenerateScript}
                    disabled={generatingScript}
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Regenerate
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      setTestFeedbackApproved(true)
                      handleTestScriptFeedback(true)
                    }}
                  >
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setTestFeedbackApproved(false)
                      setShowTestFeedbackDialog(true)
                    }}
                  >
                    <XCircle className="w-4 h-4 mr-1" />
                    Reject
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Style Profile: {selectedProfile?.source_name || "Unknown"}
            </DialogTitle>
            <DialogDescription>
              Status: {selectedProfile?.status || "unknown"}
            </DialogDescription>
          </DialogHeader>

          {selectedProfile && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Tone</Label>
                  <p className="text-sm font-medium mt-1">{selectedProfile.tone}</p>
                </div>
                <div>
                  <Label>Status</Label>
                  <div className="mt-1">{getStatusBadge(selectedProfile.status)}</div>
                </div>
              </div>

              {selectedProfile.literary_devices && selectedProfile.literary_devices.length > 0 && (
                <div>
                  <Label>Literary Devices</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedProfile.literary_devices.map((device, i) => (
                      <Badge key={i}>{device}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedProfile.cultural_markers && selectedProfile.cultural_markers.length > 0 && (
                <div>
                  <Label>Cultural Markers</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedProfile.cultural_markers.map((marker, i) => (
                      <Badge key={i} variant="outline">
                        {marker}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedProfile.example_phrases && selectedProfile.example_phrases.length > 0 && (
                <div>
                  <Label>Example Phrases</Label>
                  <div className="space-y-2 mt-1">
                    {selectedProfile.example_phrases.slice(0, 5).map((phrase, i) => (
                      <Card key={i} className="p-2 bg-muted">
                        <p className="text-sm italic">"{phrase}"</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {selectedProfile.quality_issues && selectedProfile.quality_issues.length > 0 && (
                <div>
                  <Label>Quality Issues</Label>
                  <div className="mt-1 p-3 bg-warning/10 border border-warning/20 rounded-md">
                    <ul className="list-disc list-inside text-sm">
                      {selectedProfile.quality_issues.map((issue, i) => (
                        <li key={i}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {selectedProfile.curator_notes && (
                <div>
                  <Label>Curator Notes</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedProfile.curator_notes}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t">
                {selectedProfile.status === "pending" && (
                  <>
                    <Button onClick={() => handleApprove(selectedProfile.id)}>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowDetailDialog(false)
                        setShowRejectDialog(true)
                      }}
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </>
                )}
                <Button
                  variant="ghost"
                  onClick={() => setShowDetailDialog(false)}
                  className="ml-auto"
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Test Script Feedback Dialog */}
      <Dialog open={showTestFeedbackDialog} onOpenChange={setShowTestFeedbackDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Test Script</DialogTitle>
            <DialogDescription>
              Please provide feedback on why this script doesn't match the style.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="test-feedback-notes">Feedback Notes</Label>
              <Textarea
                id="test-feedback-notes"
                value={testFeedbackNotes}
                onChange={(e) => setTestFeedbackNotes(e.target.value)}
                placeholder="e.g., Too formal, missing humor, wrong tone, needs more cultural references..."
                className="mt-1"
                rows={4}
              />
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowTestFeedbackDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => handleTestScriptFeedback(false)}
                disabled={!testFeedbackNotes.trim()}
              >
                Submit Feedback
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Style Profile</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting this profile.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="reject-reason">Reason</Label>
              <Textarea
                id="reject-reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g., Low quality extraction, generic phrases..."
                className="mt-1"
              />
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (selectedProfile) {
                    handleReject(selectedProfile.id)
                  }
                }}
                disabled={!rejectReason.trim()}
              >
                Reject
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

