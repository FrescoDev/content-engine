"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
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
  Loader2,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRouter } from "next/navigation";
import type { TopicReviewItem } from "@/lib/api-types";
import { formatDistanceToNow } from "date-fns";

// Transformed topic type for the view
interface ViewTopic {
  id: string;
  rank: number;
  title: string;
  cluster: string;
  platform: string;
  score: number;
  badge?: string;
  recency: number;
  velocity: number;
  audienceFit: number;
  integrityPenalty: number;
  reasoning?: {
    recency?: string;
    velocity?: string;
    audience_fit?: string;
    integrity_penalty?: string;
  };
  weights?: {
    recency?: number;
    velocity?: number;
    audience_fit?: number;
  };
  llmUsed?: boolean;
  costUsd?: number;
  source: string;
  pulledAt: string;
  entities: string[];
  status: "pending" | "approved" | "rejected" | "deferred";
  source_url: string | null;
}

function transformTopicReviewItem(item: TopicReviewItem): ViewTopic {
  const topic = item.topic;
  const score = item.score;

  // Format platform name
  const platformMap: Record<string, string> = {
    reddit: "Reddit",
    hackernews: "Hacker News",
    rss: "RSS Feed",
    youtube: "YouTube",
    tiktok: "TikTok",
    x: "X (Twitter)",
    news: "News",
    manual: "Manual",
  };

  const platform = platformMap[topic.source_platform] || topic.source_platform;

  // Format cluster name
  const cluster = topic.topic_cluster
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  // Check if topic is "NEW" (created within last 24 hours)
  const createdAt = new Date(topic.created_at);
  const hoursAgo = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60);
  const badge = hoursAgo < 24 ? "NEW" : undefined;

  // Format pulled time
  const pulledAt = formatDistanceToNow(createdAt, { addSuffix: true });

  return {
    id: topic.id,
    rank: item.rank,
    title: topic.title,
    cluster,
    platform,
    score: score.score || 0,
    badge,
    recency: score.components?.recency || 0,
    velocity: score.components?.velocity || 0,
    audienceFit: score.components?.audience_fit || 0,
    integrityPenalty: score.components?.integrity_penalty || 0,
    reasoning: score.reasoning || {},
    weights: score.weights || {
      recency: 0.3,
      velocity: 0.4,
      audience_fit: 0.3,
    },
    llmUsed: score.metadata?.llm_used || false,
    costUsd: score.metadata?.cost_usd || 0,
    source: platform,
    pulledAt,
    entities: topic.entities || [],
    status: item.status,
    source_url: topic.source_url,
  };
}

export function TodayView() {
  const router = useRouter();
  const [topics, setTopics] = useState<ViewTopic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<ViewTopic | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [rejectReason, setRejectReason] = useState("");
  const [showMobileDetail, setShowMobileDetail] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch topics from API
  useEffect(() => {
    const fetchTopics = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/topics?status=pending&limit=50");
        const data = await response.json();

        if (data.success && data.data) {
          const transformed = data.data.map(transformTopicReviewItem);
          setTopics(transformed);
          if (transformed.length > 0) {
            setSelectedTopic(transformed[0]);
            setSelectedIndex(0);
          }
        } else {
          setError(data.error?.error || "Failed to fetch topics");
        }
      } catch (err) {
        console.error("Failed to fetch topics:", err);
        setError("Failed to fetch topics");
      } finally {
        setLoading(false);
      }
    };

    fetchTopics();
  }, []);

  useEffect(() => {
    if (!selectedTopic) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => {
          const next = Math.min(prev + 1, topics.length - 1);
          setSelectedTopic(topics[next]);
          return next;
        });
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => {
          const next = Math.max(prev - 1, 0);
          setSelectedTopic(topics[next]);
          return next;
        });
      } else if (e.key === "a") {
        e.preventDefault();
        handleApprove(selectedTopic.id);
      } else if (e.key === "r") {
        e.preventDefault();
        if (rejectReason) handleReject(selectedTopic.id);
      } else if (e.key === "d") {
        e.preventDefault();
        handleDefer(selectedTopic.id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedTopic, selectedIndex, topics, rejectReason]);

  const handleApprove = async (id: string) => {
    try {
      const response = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_id: id, action: "approve" }),
      });

      if (response.ok) {
        setTopics(
          topics.map((t) => (t.id === id ? { ...t, status: "approved" } : t))
        );
        if (selectedTopic?.id === id) {
          setSelectedTopic({ ...selectedTopic, status: "approved" });
        }
      }
    } catch (err) {
      console.error("Failed to approve topic:", err);
    }
  };

  const handleReject = async (id: string) => {
    if (!rejectReason) return;

    try {
      const response = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic_id: id,
          action: "reject",
          reason: rejectReason,
          reason_code: rejectReason,
        }),
      });

      if (response.ok) {
        setTopics(
          topics.map((t) => (t.id === id ? { ...t, status: "rejected" } : t))
        );
        if (selectedTopic?.id === id) {
          setSelectedTopic({ ...selectedTopic, status: "rejected" });
        }
        setRejectReason("");
      }
    } catch (err) {
      console.error("Failed to reject topic:", err);
    }
  };

  const handleDefer = async (id: string) => {
    try {
      const response = await fetch("/api/topics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_id: id, action: "defer" }),
      });

      if (response.ok) {
        setTopics(
          topics.map((t) => (t.id === id ? { ...t, status: "deferred" } : t))
        );
        if (selectedTopic?.id === id) {
          setSelectedTopic({ ...selectedTopic, status: "deferred" });
        }
      }
    } catch (err) {
      console.error("Failed to defer topic:", err);
    }
  };

  const approvedCount = topics.filter((t) => t.status === "approved").length;
  const rejectedCount = topics.filter((t) => t.status === "rejected").length;
  const remainingCount = topics.filter((t) => t.status === "pending").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  if (topics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <p className="text-muted-foreground">No pending topics found</p>
      </div>
    );
  }

  if (!selectedTopic) {
    return null;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">
              Today
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {new Date().toLocaleDateString("en-GB", {
                weekday: "short",
                day: "numeric",
                month: "short",
              })}{" "}
              · {topics.length} candidates · {approvedCount} / 6 slots filled ·
              ~{remainingCount} left
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 lg:gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-success" />
              <span className="text-muted-foreground">Approved:</span>
              <span className="font-medium text-foreground">
                {approvedCount}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <X className="w-4 h-4 text-destructive" />
              <span className="text-muted-foreground">Rejected:</span>
              <span className="font-medium text-foreground">
                {rejectedCount}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-warning" />
              <span className="text-muted-foreground">Remaining:</span>
              <span className="font-medium text-foreground">
                {remainingCount}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        <div
          className={`${
            showMobileDetail ? "hidden lg:flex" : "flex"
          } w-full lg:w-96 border-r border-border overflow-y-auto flex-shrink-0`}
        >
          <div className="p-3 lg:p-4 space-y-2 w-full">
            {topics.map((topic, index) => (
              <Card
                key={topic.id}
                className={`p-3 lg:p-4 cursor-pointer transition-colors ${
                  selectedTopic.id === topic.id
                    ? "bg-accent border-primary"
                    : "hover:bg-accent/50"
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
                  setSelectedTopic(topic);
                  setSelectedIndex(index);
                  // On mobile, show detail view. On desktop, detail view is always visible
                  if (window.innerWidth < 1024) {
                    setShowMobileDetail(true);
                  }
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground">
                      #{topic.rank}
                    </span>
                    {topic.badge && (
                      <Badge variant="secondary" className="text-xs">
                        {topic.badge}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-xs">
                      <Sparkles className="w-3 h-3 text-primary" />
                      <span className="font-medium text-foreground">
                        {topic.score.toFixed(2)}
                      </span>
                    </div>
                    {topic.status === "pending" && (
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 hover:bg-success/20"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApprove(topic.id);
                          }}
                        >
                          <Check className="w-3 h-3 text-success" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 hover:bg-destructive/20"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleReject(topic.id);
                          }}
                        >
                          <X className="w-3 h-3 text-destructive" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDefer(topic.id);
                          }}
                        >
                          <MoreHorizontal className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                <h3 className="text-sm font-medium text-foreground mb-2 line-clamp-2">
                  {topic.title}
                </h3>

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

        <div
          className={`${
            showMobileDetail ? "flex" : "hidden lg:flex"
          } flex-1 overflow-y-auto min-w-0`}
        >
          <div className="p-4 lg:p-6 max-w-3xl w-full">
            <Button
              variant="ghost"
              size="sm"
              className="mb-4 lg:hidden"
              onClick={() => setShowMobileDetail(false)}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back to Queue
            </Button>

            <div className="mb-4 p-3 bg-muted/50 rounded-lg border border-border">
              <p className="text-xs text-muted-foreground">
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">
                  J/K
                </kbd>{" "}
                navigate •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">
                  A
                </kbd>{" "}
                approve •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">
                  R
                </kbd>{" "}
                reject •{" "}
                <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">
                  D
                </kbd>{" "}
                defer
              </p>
            </div>

            <div className="space-y-6">
              {/* Title */}
              <div>
                <h2 className="text-lg lg:text-xl font-semibold text-foreground mb-2">
                  {selectedTopic.title}
                </h2>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <span>Source:</span>
                    <span className="text-foreground font-medium">
                      {selectedTopic.source}
                    </span>
                    {selectedTopic.source_url && (
                      <a
                        href={selectedTopic.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-foreground"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">
                        Recency
                        <span className="text-xs ml-1 opacity-70">
                          (×{(selectedTopic.weights?.recency || 0.3).toFixed(1)}
                          )
                        </span>
                      </span>
                      <span className="font-medium text-foreground">
                        {selectedTopic.recency.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-primary-gradient h-1.5 rounded-full"
                        style={{
                          width: `${Math.min(
                            selectedTopic.recency * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                    {selectedTopic.reasoning?.recency && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {selectedTopic.reasoning.recency}
                      </p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">
                        Velocity
                        <span className="text-xs ml-1 opacity-70">
                          (×
                          {(selectedTopic.weights?.velocity || 0.4).toFixed(1)})
                        </span>
                      </span>
                      <span className="font-medium text-foreground">
                        {selectedTopic.velocity.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-info-gradient h-1.5 rounded-full"
                        style={{
                          width: `${Math.min(
                            selectedTopic.velocity * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                    {selectedTopic.reasoning?.velocity && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {selectedTopic.reasoning.velocity}
                      </p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">
                        Audience Fit
                        <span className="text-xs ml-1 opacity-70">
                          (×
                          {(selectedTopic.weights?.audience_fit || 0.3).toFixed(
                            1
                          )}
                          )
                        </span>
                      </span>
                      <span className="font-medium text-foreground">
                        {selectedTopic.audienceFit.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-success-gradient h-1.5 rounded-full"
                        style={{
                          width: `${Math.min(
                            selectedTopic.audienceFit * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                    {selectedTopic.reasoning?.audience_fit && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {selectedTopic.reasoning.audience_fit}
                      </p>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">
                        Integrity Penalty
                      </span>
                      <span className="font-medium text-foreground">
                        {selectedTopic.integrityPenalty.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div
                        className="bg-warning-gradient h-1.5 rounded-full"
                        style={{
                          width: `${Math.min(
                            Math.abs(selectedTopic.integrityPenalty) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                    {selectedTopic.reasoning?.integrity_penalty && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {selectedTopic.reasoning.integrity_penalty}
                      </p>
                    )}
                  </div>
                </div>

                {/* Score Calculation Breakdown */}
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-xs text-muted-foreground mb-2">
                    Composite Score Calculation:
                  </p>
                  <div className="text-xs font-mono space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        ({(selectedTopic.weights?.recency || 0.3).toFixed(1)} ×{" "}
                        {selectedTopic.recency.toFixed(2)})
                      </span>
                      <span className="text-foreground">
                        ={" "}
                        {(
                          (selectedTopic.weights?.recency || 0.3) *
                          selectedTopic.recency
                        ).toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        + ({(selectedTopic.weights?.velocity || 0.4).toFixed(1)}{" "}
                        × {selectedTopic.velocity.toFixed(2)})
                      </span>
                      <span className="text-foreground">
                        ={" "}
                        {(
                          (selectedTopic.weights?.velocity || 0.4) *
                          selectedTopic.velocity
                        ).toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        + (
                        {(selectedTopic.weights?.audience_fit || 0.3).toFixed(
                          1
                        )}{" "}
                        × {selectedTopic.audienceFit.toFixed(2)})
                      </span>
                      <span className="text-foreground">
                        ={" "}
                        {(
                          (selectedTopic.weights?.audience_fit || 0.3) *
                          selectedTopic.audienceFit
                        ).toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        + ({selectedTopic.integrityPenalty.toFixed(2)})
                      </span>
                      <span className="text-foreground">
                        = {selectedTopic.integrityPenalty.toFixed(3)}
                      </span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-border mt-1">
                      <span className="font-semibold text-foreground">
                        Total Score:
                      </span>
                      <span className="font-semibold text-primary">
                        {selectedTopic.score.toFixed(3)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 italic">
                      Note: Actual score may differ slightly due to weight
                      normalization or rounding.
                    </p>
                  </div>
                </div>

                {/* LLM Cost Info */}
                {selectedTopic.llmUsed &&
                  selectedTopic.costUsd &&
                  selectedTopic.costUsd > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <Sparkles className="w-3 h-3" />
                          LLM Enhanced
                        </span>
                        <span className="text-muted-foreground">
                          Cost: ${selectedTopic.costUsd.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  )}
              </Card>

              {/* Signals */}
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  Signals
                </h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-muted-foreground">
                      Entities:
                    </span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedTopic.entities.length > 0 ? (
                        selectedTopic.entities.map((entity, i) => (
                          <Badge key={i} variant="secondary">
                            {entity}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground italic">
                          No entities detected
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Actions */}
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  Actions
                </h3>
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
                      onClick={() =>
                        router.push(`/scripts?topic=${selectedTopic.id}`)
                      }
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
                    <Select
                      value={rejectReason}
                      onValueChange={setRejectReason}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select rejection reason..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="too_generic">Too generic</SelectItem>
                        <SelectItem value="not_on_brand">
                          Not on brand
                        </SelectItem>
                        <SelectItem value="speculative">
                          Too speculative
                        </SelectItem>
                        <SelectItem value="duplicate">
                          Duplicate topic
                        </SelectItem>
                        <SelectItem value="ethics">Ethics concern</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={() => handleReject(selectedTopic.id)}
                      disabled={
                        selectedTopic.status === "rejected" || !rejectReason
                      }
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
  );
}
