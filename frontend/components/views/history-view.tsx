"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Clock, User, Cpu, XIcon, ExternalLink } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const mockAuditEvents = [
  { time: "10:45", stage: "published", topic: "AI layoffs in tech sector", actor: "system" },
  { time: "10:20", stage: "option_selection", topic: "AI layoffs in tech sector", actor: "editor" },
  { time: "10:14", stage: "topic_selection", topic: "AI layoffs in tech sector", actor: "editor" },
  { time: "10:12", stage: "topic_selection", topic: "AI layoffs in tech sector", actor: "system" },
  { time: "09:58", stage: "ingestion", topic: "Drake album release strategy", actor: "system" },
  { time: "09:45", stage: "published", topic: "Insurance tech funding round", actor: "system" },
]

export function HistoryView() {
  const [stageFilter, setStageFilter] = useState("all")
  const [dateFilter, setDateFilter] = useState("7d")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedEvent, setSelectedEvent] = useState<(typeof mockAuditEvents)[0] | null>(null)

  const filteredEvents = mockAuditEvents.filter((event) => {
    if (stageFilter !== "all" && event.stage !== stageFilter) return false
    if (searchQuery && !event.topic.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">History</h1>
            <p className="text-sm text-muted-foreground mt-1">Audit trail of all decisions and events</p>
          </div>
        </div>
      </div>

      <div className="border-b border-border bg-card px-4 lg:px-6 py-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <Select value={stageFilter} onValueChange={setStageFilter}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="All stages" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All stages</SelectItem>
              <SelectItem value="ingestion">Ingestion</SelectItem>
              <SelectItem value="topic_selection">Topic Selection</SelectItem>
              <SelectItem value="option_selection">Option Selection</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="ethics_review">Ethics Review</SelectItem>
            </SelectContent>
          </Select>

          <Select value={dateFilter} onValueChange={setDateFilter}>
            <SelectTrigger className="w-full sm:w-[150px]">
              <SelectValue placeholder="Date range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24 hours</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>

          <Input
            placeholder="Search by topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        <div className={`${selectedEvent ? "hidden lg:block" : "block"} flex-1 overflow-y-auto`}>
          <div className="p-4 lg:p-6">
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-border">
                    <tr className="text-left">
                      <th className="px-4 py-3 text-sm font-medium text-muted-foreground">Time</th>
                      <th className="px-4 py-3 text-sm font-medium text-muted-foreground">Stage</th>
                      <th className="px-4 py-3 text-sm font-medium text-muted-foreground">Topic</th>
                      <th className="px-4 py-3 text-sm font-medium text-muted-foreground">Actor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEvents.map((event, index) => (
                      <tr
                        key={index}
                        className="border-b border-border hover:bg-accent/50 cursor-pointer transition-colors"
                        onClick={() => setSelectedEvent(event)}
                      >
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Clock className="w-3 h-3" />
                            {event.time}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-xs">
                            {event.stage}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-foreground">{event.topic}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            {event.actor === "system" ? (
                              <>
                                <Cpu className="w-3 h-3" />
                                <span>system</span>
                              </>
                            ) : (
                              <>
                                <User className="w-3 h-3" />
                                <span>editor</span>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>

        {selectedEvent && (
          <div className="w-full lg:w-96 border-l border-border bg-card overflow-y-auto">
            <div className="p-4 lg:p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-foreground">Event Details</h2>
                <Button size="sm" variant="ghost" onClick={() => setSelectedEvent(null)}>
                  <XIcon className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Topic</Label>
                  <p className="text-sm font-medium text-foreground mt-1">{selectedEvent.topic}</p>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">Stage</Label>
                  <div className="mt-1">
                    <Badge variant="outline">{selectedEvent.stage}</Badge>
                  </div>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">Time</Label>
                  <p className="text-sm text-foreground mt-1">{selectedEvent.time}</p>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">Actor</Label>
                  <p className="text-sm text-foreground mt-1">{selectedEvent.actor}</p>
                </div>

                <div className="pt-4 border-t border-border">
                  <Label className="text-xs text-muted-foreground mb-2 block">Context</Label>
                  <div className="space-y-2 text-sm">
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="font-medium text-foreground mb-1">Inputs</p>
                      <p className="text-xs text-muted-foreground">
                        Score: 0.86 (recency: 0.9, velocity: 0.85, audience: 0.8)
                      </p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="font-medium text-foreground mb-1">System Decision</p>
                      <p className="text-xs text-muted-foreground">Ranked #1 of 4 candidates</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="font-medium text-foreground mb-1">Human Action</p>
                      <p className="text-xs text-muted-foreground">Approved for script generation</p>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <Label className="text-xs text-muted-foreground mb-2 block">Quick Links</Label>
                  <div className="flex flex-col gap-2">
                    <Button size="sm" variant="outline" className="justify-start bg-transparent">
                      <ExternalLink className="w-3 h-3 mr-2" />
                      View in Today
                    </Button>
                    <Button size="sm" variant="outline" className="justify-start bg-transparent">
                      <ExternalLink className="w-3 h-3 mr-2" />
                      View in Scripts
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
