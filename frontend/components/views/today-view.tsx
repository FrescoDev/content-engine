"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  TrendingUp,
  ExternalLink,
  Check,
  X,
  Clock,
  Sparkles,
  ChevronLeft,
  FileText,
  MoreHorizontal,
} from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useRouter } from "next/navigation"

// Mock data
const mockTopics = [
  {
    id: 1,
    rank: 1,
    title: "Anthropic Releases Claude 3.5 with Extended Context",
    cluster: "AI Infrastructure",
    platform: "YouTube Trending",
    score: 0.86,
    badge: "NEW",
    recency: 0.9,
    velocity: 0.85,
    audienceFit: 0.8,
    integrityPenalty: -0.05,
    source: "YouTube",
    pulledAt: "08:13",
    entities: ["Anthropic", "Claude", "AI"],
    status: "pending",
  },
  {
    id: 2,
    rank: 2,
    title: "Drake's Latest Album Strategy Reshapes Music Industry",
    cluster: "Culture & Music",
    platform: "TikTok Trending",
    score: 0.82,
    recency: 0.88,
    velocity: 0.75,
    audienceFit: 0.85,
    integrityPenalty: -0.1,
    source: "TikTok",
    pulledAt: "07:45",
    entities: ["Drake", "Music Industry", "Streaming"],
    status: "pending",
  },
  {
    id: 3,
    rank: 3,
    title: "Major Tech Layoffs Signal Industry Restructuring",
    cluster: "Business & Economy",
    platform: "X Trending",
    score: 0.79,
    recency: 0.85,
    velocity: 0.7,
    audienceFit: 0.82,
    integrityPenalty: -0.08,
    source: "X (Twitter)",
    pulledAt: "09:00",
    entities: ["Tech", "Layoffs", "Economy"],
    status: "pending",
  },
  {
    id: 4,
    rank: 4,
    title: "Insurance Tech Startup Raises $200M Series C",
    cluster: "Applied Industry",
    platform: "News Feed",
    score: 0.75,
    recency: 0.8,
    velocity: 0.65,
    audienceFit: 0.78,
    integrityPenalty: -0.03,
    source: "TechCrunch",
    pulledAt: "10:15",
    entities: ["InsurTech", "Funding", "Series C"],
    status: "pending",
  },
]

export function TodayView() {
  const router = useRouter()
  const [topics, setTopics] = useState(mockTopics)
  const [selectedTopic, setSelectedTopic] = useState(mockTopics[0])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [rejectReason, setRejectReason] = useState("")
  const [showMobileDetail, setShowMobileDetail] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex((prev) => {
          const next = Math.min(prev + 1, topics.length - 1)
          setSelectedTopic(topics[next])
          return next
        })
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex((prev) => {
          const next = Math.max(prev - 1, 0)
          setSelectedTopic(topics[next])
          return next
        })
      } else if (e.key === "a") {
        e.preventDefault()
        handleApprove(selectedTopic.id)
      } else if (e.key === "r") {
        e.preventDefault()
        if (rejectReason) handleReject(selectedTopic.id)
      } else if (e.key === "d") {
        e.preventDefault()
        handleDefer(selectedTopic.id)
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [selectedTopic, selectedIndex, topics, rejectReason])

  const handleApprove = (id: number) => {
    setTopics(topics.map((t) => (t.id === id ? { ...t, status: "approved" } : t)))
  }

  const handleReject = (id: number) => {
    setTopics(topics.map((t) => (t.id === id ? { ...t, status: "rejected" } : t)))
  }

  const handleDefer = (id: number) => {
    setTopics(topics.map((t) => (t.id === id ? { ...t, status: "deferred" } : t)))
  }

  const approvedCount = topics.filter((t) => t.status === "approved").length
  const rejectedCount = topics.filter((t) => t.status === "rejected").length
  const remainingCount = topics.filter((t) => t.status === "pending").length

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">Today</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Wed 26 Nov · {topics.length} candidates · {approvedCount} / 6 slots filled · ~{remainingCount} left
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 lg:gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-success" />
              <span className="text-muted-foreground">Approved:</span>
              <span className="font-medium text-foreground">{approvedCount}</span>
            </div>
            <div className="flex items-center gap-2">
              <X className="w-4 h-4 text-destructive" />
              <span className="text-muted-foreground">Rejected:</span>
              <span className="font-medium text-foreground">{rejectedCount}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-warning" />
              <span className="text-muted-foreground">Remaining:</span>
              <span className="font-medium text-foreground">{remainingCount}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        <div
          className={`${showMobileDetail ? "hidden lg:flex" : "flex"} w-full lg:w-96 border-r border-border overflow-y-auto`}
        >
          <div className="p-3 lg:p-4 space-y-2 w-full">
            {topics.map((topic, index) => (
              <Card
                key={topic.id}
                className={`p-3 lg:p-4 cursor-pointer transition-colors ${
                  selectedTopic.id === topic.id ? "bg-accent border-primary" : "hover:bg-accent/50"
                } ${
                  topic.status === "approved"
                    ? "opacity-60"
                    : topic.status === "rejected"
                      ? "opacity-40"
                      : topic.status === "deferred"
                        ? "opacity-50"
                        : ""
                }`}
                onClick={() => {
                  setSelectedTopic(topic)
                  setSelectedIndex(index)
                  setShowMobileDetail(true)
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground">#{topic.rank}</span>
                    {topic.badge && (
                      <Badge variant="secondary" className="text-xs">
                        {topic.badge}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-xs">
                      <Sparkles className="w-3 h-3 text-primary" />
                      <span className="font-medium text-foreground">{topic.score.toFixed(2)}</span>
                    </div>
                    {topic.status === "pending" && (
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 hover:bg-success/20"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleApprove(topic.id)
                          }}
                        >
                          <Check className="w-3 h-3 text-success" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 hover:bg-destructive/20"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleReject(topic.id)
                          }}
                        >
                          <X className="w-3 h-3 text-destructive" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDefer(topic.id)
                          }}
                        >
                          <MoreHorizontal className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                <h3 className="text-sm font-medium text-foreground mb-2 line-clamp-2">{topic.title}</h3>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className="text-xs">
                    {topic.cluster}
                  </Badge>
                  <span>·</span>
                  <span>{topic.platform}</span>
                </div>

                {topic.status !== "pending" && (
                  <div className="mt-3 pt-3 border-t border-border">
                    <span
                      className={`text-xs font-medium ${
                        topic.status === "approved"
                          ? "text-success"
                          : topic.status === "rejected"
                            ? "text-destructive"
                            : "text-warning"
                      }`}
                    >
                      {topic.status.toUpperCase()}
                    </span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>

        <div className={`${showMobileDetail ? "flex" : "hidden lg:flex"} flex-1 overflow-y-auto`}>
          <div className="p-4 lg:p-6 max-w-3xl w-full">
            <Button variant="ghost" size="sm" className="mb-4 lg:hidden" onClick={() => setShowMobileDetail(false)}>
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back to Queue
            </Button>

            <div className="mb-4 p-3 bg-muted/50 rounded-lg border border-border">
              <p className="text-xs text-muted-foreground">
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">J/K</kbd> navigate •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">A</kbd> approve •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">R</kbd> reject •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">D</kbd> defer
              </p>
            </div>

            <div className="space-y-6">
              {/* Title */}
              <div>
                <h2 className="text-lg lg:text-xl font-semibold text-foreground mb-2">{selectedTopic.title}</h2>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <span>Source:</span>
                    <span className="text-foreground font-medium">{selectedTopic.source}</span>
                    <ExternalLink className="w-3 h-3" />
                  </div>
                  <span className="hidden sm:inline">·</span>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>Pulled: {selectedTopic.pulledAt}</span>
                  </div>
                </div>
              </div>

              {/* Why suggested */}
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-primary" />
                  Why this is suggested
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Recency</span>
                      <span className="font-medium text-foreground">{selectedTopic.recency.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-primary-gradient h-1.5 rounded-full"
                        style={{ width: `${selectedTopic.recency * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Velocity</span>
                      <span className="font-medium text-foreground">{selectedTopic.velocity.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-info-gradient h-1.5 rounded-full"
                        style={{ width: `${selectedTopic.velocity * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Audience Fit</span>
                      <span className="font-medium text-foreground">{selectedTopic.audienceFit.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-success-gradient h-1.5 rounded-full"
                        style={{ width: `${selectedTopic.audienceFit * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Integrity Penalty</span>
                      <span className="font-medium text-foreground">{selectedTopic.integrityPenalty.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-warning-gradient h-1.5 rounded-full"
                        style={{ width: `${Math.abs(selectedTopic.integrityPenalty) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Signals */}
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Signals</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">Entities:</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedTopic.entities.map((entity, i) => (
                        <Badge key={i} variant="secondary">
                          {entity}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Actions */}
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Actions</h3>
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button
                      onClick={() => handleApprove(selectedTopic.id)}
                      disabled={selectedTopic.status === "approved"}
                      className="flex-1 animate-glow"
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => router.push(`/scripts?topic=${selectedTopic.id}`)}
                      className="flex-1"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Open in Script Studio
                    </Button>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleDefer(selectedTopic.id)}
                      disabled={selectedTopic.status === "deferred"}
                      className="flex-1"
                    >
                      <Clock className="w-4 h-4 mr-2" />
                      Defer
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <Select value={rejectReason} onValueChange={setRejectReason}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select rejection reason..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="off-brand">Off-brand</SelectItem>
                        <SelectItem value="low-quality">Low quality source</SelectItem>
                        <SelectItem value="too-speculative">Too speculative</SelectItem>
                        <SelectItem value="duplicate">Duplicate topic</SelectItem>
                        <SelectItem value="ethics">Ethics concern</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={() => handleReject(selectedTopic.id)}
                      disabled={selectedTopic.status === "rejected" || !rejectReason}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
