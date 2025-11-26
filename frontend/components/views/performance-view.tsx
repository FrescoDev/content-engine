"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { TrendingUp, Settings, ArrowUp, ArrowDown } from "lucide-react"

export function PerformanceView() {
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [weights, setWeights] = useState({
    recency: 0.4,
    velocity: 0.3,
    audienceFit: 0.3,
    integrityPenalty: -0.2,
  })

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">Performance</h1>
            <p className="text-sm text-muted-foreground mt-1">System learning and optimization metrics</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 lg:p-6 max-w-5xl">
          <div className="space-y-6">
            {/* Metrics Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Avg View Duration</span>
                  <TrendingUp className="w-4 h-4 text-success" />
                </div>
                <div className="text-2xl font-semibold text-foreground">2:34</div>
                <div className="text-xs text-success mt-1">+12% vs last week</div>
              </Card>

              <Card className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Engagement Rate</span>
                  <TrendingUp className="w-4 h-4 text-success" />
                </div>
                <div className="text-2xl font-semibold text-foreground">8.4%</div>
                <div className="text-xs text-success mt-1">+3.2% vs last week</div>
              </Card>

              <Card className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Content Published</span>
                </div>
                <div className="text-2xl font-semibold text-foreground">42</div>
                <div className="text-xs text-muted-foreground mt-1">Last 7 days</div>
              </Card>
            </div>

            {/* Scoring Weights */}
            <Card className="p-4 lg:p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Current Scoring Weights</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Recency</span>
                    <span className="text-sm font-medium text-foreground">0.40</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-primary h-2 rounded-full" style={{ width: "40%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Velocity</span>
                    <span className="text-sm font-medium text-foreground">0.30</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-info h-2 rounded-full" style={{ width: "30%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Audience Fit</span>
                    <span className="text-sm font-medium text-foreground">0.30</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-success h-2 rounded-full" style={{ width: "30%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Integrity Penalty</span>
                    <span className="text-sm font-medium text-foreground">-0.20</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-warning h-2 rounded-full" style={{ width: "20%" }} />
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                  <div>
                    <p className="text-sm font-medium text-foreground">Last learning update</p>
                    <p className="text-xs text-muted-foreground">2025-11-24</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setShowEditDialog(true)}>
                    <Settings className="w-4 h-4 mr-2" />
                    Edit Manually
                  </Button>
                </div>

                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm font-medium text-foreground mb-3">Suggested adjustments:</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Audience fit (culture)</span>
                      <div className="flex items-center gap-2">
                        <span className="text-foreground">0.30</span>
                        <ArrowUp className="w-3 h-3 text-success" />
                        <span className="text-success font-medium">0.35</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Integrity penalty</span>
                      <div className="flex items-center gap-2">
                        <span className="text-foreground">-0.20</span>
                        <ArrowDown className="w-3 h-3 text-warning" />
                        <span className="text-warning font-medium">-0.25</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                <p className="text-sm font-medium text-foreground mb-3">Recent Learning Events</p>
                <div className="space-y-2">
                  <div className="flex items-start gap-3 text-sm">
                    <span className="text-xs text-muted-foreground whitespace-nowrap">2025-11-24</span>
                    <p className="text-muted-foreground">
                      Integrity penalty increased due to 3 low-integrity rejections
                    </p>
                  </div>
                  <div className="flex items-start gap-3 text-sm">
                    <span className="text-xs text-muted-foreground whitespace-nowrap">2025-11-22</span>
                    <p className="text-muted-foreground">
                      Audience fit weight adjusted based on engagement performance
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Scoring Weights</DialogTitle>
            <DialogDescription>
              Adjust weights in small increments. Changes will be logged as configuration changes.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="space-y-2">
              <Label>Recency: {weights.recency.toFixed(2)}</Label>
              <Slider
                value={[weights.recency]}
                onValueChange={([value]) => setWeights({ ...weights, recency: value })}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label>Velocity: {weights.velocity.toFixed(2)}</Label>
              <Slider
                value={[weights.velocity]}
                onValueChange={([value]) => setWeights({ ...weights, velocity: value })}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label>Audience Fit: {weights.audienceFit.toFixed(2)}</Label>
              <Slider
                value={[weights.audienceFit]}
                onValueChange={([value]) => setWeights({ ...weights, audienceFit: value })}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label>Integrity Penalty: {weights.integrityPenalty.toFixed(2)}</Label>
              <Slider
                value={[Math.abs(weights.integrityPenalty)]}
                onValueChange={([value]) => setWeights({ ...weights, integrityPenalty: -value })}
                min={0}
                max={0.5}
                step={0.05}
                className="w-full"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowEditDialog(false)} className="flex-1">
              Cancel
            </Button>
            <Button
              onClick={() => {
                setShowEditDialog(false)
                alert("Weights updated. This will be recorded as a configuration change.")
              }}
              className="flex-1"
            >
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
