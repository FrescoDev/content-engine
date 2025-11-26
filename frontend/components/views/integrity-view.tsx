"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { AlertTriangle, Check, X, RefreshCw, ChevronDown, ChevronUp } from "lucide-react"

const mockFlaggedItems = [
  {
    id: 1,
    risk: "Medium",
    platform: "TikTok",
    cluster: "Culture",
    title: "Celebrity Drama Unfolds on Social Media",
    reason: "Personal/rumour, low-source confidence",
    reframes: [
      "What this tells us about platform moderation and celebrity PR",
      "How social media shapes public narratives around high-profile figures",
    ],
  },
]

export function IntegrityView() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showScript, setShowScript] = useState(false)

  const currentItem = mockFlaggedItems[currentIndex]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">Integrity Review</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {currentIndex + 1} of {mockFlaggedItems.length} items flagged for review
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex(currentIndex - 1)}
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={currentIndex === mockFlaggedItems.length - 1}
              onClick={() => setCurrentIndex(currentIndex + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 lg:p-6 max-w-4xl mx-auto">
          <div className="space-y-4">
            <Card className="p-4 lg:p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="p-2 rounded-lg bg-warning/10">
                  <AlertTriangle className="w-5 h-5 text-warning" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="border-warning text-warning">
                      {currentItem.risk} Risk
                    </Badge>
                    <Badge variant="secondary">{currentItem.platform}</Badge>
                    <Badge variant="secondary">{currentItem.cluster}</Badge>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">{currentItem.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium">Reason flagged:</span> {currentItem.reason}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowScript(!showScript)}
                  className="w-full justify-between"
                >
                  <span className="text-sm font-medium">View Script Snippet</span>
                  {showScript ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </Button>
                {showScript && (
                  <div className="mt-2 p-3 bg-muted rounded-lg border border-border">
                    <p className="text-sm text-foreground font-mono">
                      "Breaking: Sources close to the celebrity say... This could be the biggest scandal of the year.
                      While we can't verify all details, the internet is already buzzing..."
                    </p>
                  </div>
                )}
              </div>

              <div className="mb-4 p-4 bg-muted rounded-lg">
                <p className="text-sm font-medium text-foreground mb-2">Suggested reframes:</p>
                <ul className="space-y-2">
                  {currentItem.reframes.map((reframe, index) => (
                    <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary mt-0.5">→</span>
                      <span>{reframe}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-4 p-3 bg-primary/5 rounded-lg border border-primary/20">
                <p className="text-xs font-medium text-foreground mb-1">Preview: Reframe Option 1</p>
                <p className="text-sm text-muted-foreground">
                  "What this tells us about platform moderation and celebrity PR" - This angle shifts focus to systemic
                  issues rather than rumor-chasing.
                </p>
              </div>

              <div className="mb-4">
                <label className="text-sm text-muted-foreground mb-2 block">Reason (optional):</label>
                <Textarea placeholder="Add notes about your decision..." className="min-h-[80px]" />
              </div>

              <div className="flex flex-col sm:flex-row gap-2">
                <Button variant="outline" size="sm" className="flex-1 bg-transparent">
                  <Check className="w-4 h-4 mr-2" />
                  Publish As Is
                </Button>
                <Button variant="default" size="sm" className="flex-1">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reframe (Option 1)
                </Button>
                <Button variant="destructive" size="sm" className="flex-1">
                  <X className="w-4 h-4 mr-2" />
                  Skip
                </Button>
              </div>

              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">P</kbd> publish •{" "}
                  <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">R</kbd> reframe •{" "}
                  <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">S</kbd> skip
                </p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
