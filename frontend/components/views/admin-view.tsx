"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  Settings,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Trash2,
  ExternalLink,
  Calendar,
  Timer,
  Database,
  AlertCircle,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface JobRun {
  id: string;
  job_type: string;
  status: "running" | "completed" | "failed" | "cancelled";
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  topics_ingested?: number;
  topics_saved?: number;
  topics_processed?: number;
  error_message?: string;
  error_traceback?: string;
  metadata?: Record<string, any>;
}

export function AdminView() {
  const [jobRuns, setJobRuns] = useState<JobRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobRun, setSelectedJobRun] = useState<JobRun | null>(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [jobTypeFilter, setJobTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const fetchJobRuns = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (jobTypeFilter !== "all") params.append("job_type", jobTypeFilter);
      if (statusFilter !== "all") params.append("status", statusFilter);
      params.append("limit", "50");

      const response = await fetch(`/api/job-runs?${params.toString()}`);
      const data = await response.json();

      if (data.success) {
        setJobRuns(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch job runs:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobRuns();
  }, [jobTypeFilter, statusFilter]);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this job run?")) return;

    try {
      const response = await fetch(`/api/job-runs?id=${id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        fetchJobRuns();
      }
    } catch (error) {
      console.error("Failed to delete job run:", error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <Badge className="bg-success/10 text-success border-success/20">
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge className="bg-destructive/10 text-destructive border-destructive/20">
            Failed
          </Badge>
        );
      case "running":
        return (
          <Badge className="bg-primary/10 text-primary border-primary/20">
            Running
          </Badge>
        );
      case "cancelled":
        return (
          <Badge className="bg-muted text-muted-foreground">Cancelled</Badge>
        );
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "N/A";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">
              Admin
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Job execution audit and monitoring
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <Select value={jobTypeFilter} onValueChange={setJobTypeFilter}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="All job types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All job types</SelectItem>
              <SelectItem value="topic_ingestion">Topic Ingestion</SelectItem>
              <SelectItem value="topic_scoring">Topic Scoring</SelectItem>
              <SelectItem value="option_generation">
                Option Generation
              </SelectItem>
              <SelectItem value="weekly_learning">Weekly Learning</SelectItem>
              <SelectItem value="metrics_collection">
                Metrics Collection
              </SelectItem>
            </SelectContent>
          </Select>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            onClick={fetchJobRuns}
            className="sm:ml-auto"
          >
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
          ) : jobRuns.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-muted-foreground">No job runs found</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {jobRuns.map((jobRun) => (
                <Card
                  key={jobRun.id}
                  className="p-4 hover:bg-accent/50 transition-colors cursor-pointer"
                  onClick={() => {
                    setSelectedJobRun(jobRun);
                    setShowDetailDialog(true);
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-foreground capitalize">
                          {jobRun.job_type.replace(/_/g, " ")}
                        </h3>
                        {getStatusBadge(jobRun.status)}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(jobRun.started_at)}</span>
                        </div>
                        {jobRun.duration_seconds && (
                          <div className="flex items-center gap-1">
                            <Timer className="w-3 h-3" />
                            <span>
                              {formatDuration(jobRun.duration_seconds)}
                            </span>
                          </div>
                        )}
                        {jobRun.topics_ingested !== undefined && (
                          <div className="flex items-center gap-1">
                            <Database className="w-3 h-3" />
                            <span>
                              {jobRun.topics_ingested} ingested,{" "}
                              {jobRun.topics_saved || 0} saved
                            </span>
                          </div>
                        )}
                      </div>

                      {jobRun.error_message && (
                        <div className="mt-2 flex items-start gap-2 text-sm text-destructive">
                          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <span className="line-clamp-1">
                            {jobRun.error_message}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(jobRun.id);
                        }}
                        className="h-8 w-8"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Job Run Details</DialogTitle>
            <DialogDescription>
              {selectedJobRun && (
                <>
                  {selectedJobRun.job_type.replace(/_/g, " ")} •{" "}
                  {selectedJobRun.id}
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          {selectedJobRun && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground">
                    Status
                  </label>
                  <div className="mt-1">
                    {getStatusBadge(selectedJobRun.status)}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">
                    Duration
                  </label>
                  <div className="mt-1 text-sm font-medium">
                    {formatDuration(selectedJobRun.duration_seconds)}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">
                    Started At
                  </label>
                  <div className="mt-1 text-sm font-medium">
                    {new Date(selectedJobRun.started_at).toLocaleString()}
                  </div>
                </div>
                {selectedJobRun.completed_at && (
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Completed At
                    </label>
                    <div className="mt-1 text-sm font-medium">
                      {new Date(selectedJobRun.completed_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>

              {(selectedJobRun.topics_ingested !== undefined ||
                selectedJobRun.topics_saved !== undefined ||
                selectedJobRun.topics_processed !== undefined) && (
                <div>
                  <label className="text-sm text-muted-foreground">
                    Metrics
                  </label>
                  <div className="mt-1 grid grid-cols-3 gap-4">
                    {selectedJobRun.topics_ingested !== undefined && (
                      <div>
                        <div className="text-xs text-muted-foreground">
                          Ingested
                        </div>
                        <div className="text-lg font-semibold">
                          {selectedJobRun.topics_ingested}
                        </div>
                      </div>
                    )}
                    {selectedJobRun.topics_saved !== undefined && (
                      <div>
                        <div className="text-xs text-muted-foreground">
                          Saved
                        </div>
                        <div className="text-lg font-semibold">
                          {selectedJobRun.topics_saved}
                        </div>
                      </div>
                    )}
                    {selectedJobRun.topics_processed !== undefined && (
                      <div>
                        <div className="text-xs text-muted-foreground">
                          Processed
                        </div>
                        <div className="text-lg font-semibold">
                          {selectedJobRun.topics_processed}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedJobRun.metadata &&
                Object.keys(selectedJobRun.metadata).length > 0 && (
                  <div>
                    <label className="text-sm text-muted-foreground">
                      Metadata
                    </label>
                    <pre className="mt-1 p-3 bg-muted rounded-md text-xs overflow-x-auto">
                      {JSON.stringify(selectedJobRun.metadata, null, 2)}
                    </pre>
                  </div>
                )}

              {selectedJobRun.error_message && (
                <div>
                  <label className="text-sm text-muted-foreground">Error</label>
                  <div className="mt-1 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <div className="text-sm font-medium text-destructive mb-2">
                      {selectedJobRun.error_message}
                    </div>
                    {selectedJobRun.error_traceback && (
                      <pre className="text-xs text-muted-foreground overflow-x-auto whitespace-pre-wrap">
                        {selectedJobRun.error_traceback}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
