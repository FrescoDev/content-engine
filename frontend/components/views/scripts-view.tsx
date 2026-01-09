"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Check,
  Shield,
  Mic,
  Upload,
  Wand2,
  FileText,
  ImageIcon,
  Video,
  LayoutGrid,
  Twitter,
  ChevronLeft,
  GripVertical,
  Plus,
  Loader2,
} from "lucide-react";

export function ScriptsView() {
  const searchParams = useSearchParams();
  const topicId = searchParams.get("topic");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [topicsWithOptions, setTopicsWithOptions] = useState<any[]>([]);
  const [selectedScript, setSelectedScript] = useState<any | null>(null);
  const [selectedHook, setSelectedHook] = useState("0");
  const [scriptText, setScriptText] = useState("");
  const [platform, setPlatform] = useState<
    "youtube_short" | "youtube_long" | "tiktok"
  >("youtube_short");
  const [contentType, setContentType] = useState("video-script");
  const [isRecording, setIsRecording] = useState(false);
  const [brainstormText, setBrainstormText] = useState("");
  const [showMobileDetail, setShowMobileDetail] = useState(false);
  const [beats, setBeats] = useState([
    {
      id: 1,
      title: "Context window importance",
      summary: "Explain why 200K context matters for developers",
      status: "keep",
    },
    {
      id: 2,
      title: "Practical use cases",
      summary: "Highlight codebase analysis and multi-doc reasoning",
      status: "keep",
    },
    {
      id: 3,
      title: "Competition angle",
      summary: "Mention the ongoing race for longer context",
      status: "maybe",
    },
  ]);
  const [variants, setVariants] = useState<
    Array<{
      id: number;
      platform: "youtube_short" | "youtube_long" | "tiktok";
      label: string;
    }>
  >([{ id: 1, platform: "youtube_long", label: "YouTube Long" }]);
  const [activeVariant, setActiveVariant] = useState<
    "youtube_short" | "youtube_long" | "tiktok"
  >("youtube_long");
  const [showBeats, setShowBeats] = useState(false);
  const [styleProfiles, setStyleProfiles] = useState<Array<{ id: string; source_name: string; tone: string }>>([]);
  const [selectedStyleId, setSelectedStyleId] = useState<string>("default");

  const handleRecording = () => {
    setIsRecording(!isRecording);
  };

  const handleStructure = () => {
    alert("AI will structure your brainstorm content into a script");
  };

  const handleAddVariant = (
    variantPlatform: "youtube_short" | "youtube_long" | "tiktok",
    variantLabel: string
  ) => {
    setVariants([
      ...variants,
      {
        id: variants.length + 1,
        platform: variantPlatform,
        label: variantLabel,
      },
    ]);
  };

  const toggleBeatStatus = (id: number) => {
    setBeats(
      beats.map((beat) =>
        beat.id === id
          ? {
              ...beat,
              status:
                beat.status === "keep"
                  ? "maybe"
                  : beat.status === "maybe"
                  ? "drop"
                  : "keep",
            }
          : beat
      )
    );
  };

  // Fetch approved style profiles
  useEffect(() => {
    const fetchStyleProfiles = async () => {
      try {
        const response = await fetch("/api/styles/profiles?status=approved&limit=20");
        const data = await response.json();
        if (data.success && data.data) {
          setStyleProfiles(data.data);
        }
      } catch (error) {
        console.error("Failed to fetch style profiles:", error);
      }
    };
    fetchStyleProfiles();
  }, []);

  // Fetch topics with options from API
  useEffect(() => {
    const fetchTopicsWithOptions = async () => {
      setLoading(true);
      setError(null);
      try {
        const url = topicId
          ? `/api/options?topic_id=${encodeURIComponent(topicId)}`
          : `/api/options`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.data) {
          setTopicsWithOptions(data.data);

          // Auto-select topic if topicId is provided
          if (topicId && data.data.length > 0) {
            const matchingTopic = data.data.find(
              (item: any) => item.topic?.id === topicId
            );
            if (matchingTopic) {
              setSelectedScript(matchingTopic);
              // Use edited_content if exists, otherwise content
              const firstScript = matchingTopic.scripts?.[0];
              if (firstScript) {
                setScriptText(
                  firstScript.edited_content || firstScript.content || ""
                );
              }
            }
          } else if (data.data.length > 0) {
            // Select first topic if no specific topicId
            setSelectedScript(data.data[0]);
            const firstScript = data.data[0].scripts?.[0];
            if (firstScript) {
              setScriptText(
                firstScript.edited_content || firstScript.content || ""
              );
            }
          }
        } else {
          setError(data.error?.error || "Failed to fetch topics");
        }
      } catch (err) {
        console.error("Failed to fetch topics with options:", err);
        setError("Failed to fetch topics");
      } finally {
        setLoading(false);
      }
    };

    fetchTopicsWithOptions();
  }, [topicId]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 lg:px-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold text-foreground">
              Scripts
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {loading
                ? "Loading topics..."
                : `${topicsWithOptions.length} topic${
                    topicsWithOptions.length !== 1 ? "s" : ""
                  } with scripts ready for review`}
            </p>
          </div>
          <Button>
            <Wand2 className="w-4 h-4 mr-2" />
            Create New
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Topics */}
        <div
          className={`${
            showMobileDetail ? "hidden lg:flex" : "flex"
          } w-full lg:w-80 border-r border-border overflow-y-auto`}
        >
          {loading ? (
            <div className="flex items-center justify-center h-full w-full">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="p-4">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          ) : topicsWithOptions.length === 0 ? (
            <div className="p-4">
              <p className="text-sm text-muted-foreground">
                No topics with options available
              </p>
            </div>
          ) : (
            <div className="p-3 lg:p-4 space-y-2 w-full">
              {topicsWithOptions.map((topicWithOptions) => {
                const optionsCount =
                  (topicWithOptions.hooks?.length || 0) +
                  (topicWithOptions.scripts?.length || 0);
                const topic = topicWithOptions.topic;
                const cluster =
                  topic?.topic_cluster
                    ?.split("-")
                    .map(
                      (word: string) =>
                        word.charAt(0).toUpperCase() + word.slice(1)
                    )
                    .join(" ") || "Unknown";

                return (
                  <Card
                    key={topic?.id || topicWithOptions.id}
                    className={`p-3 lg:p-4 cursor-pointer transition-colors ${
                      selectedScript?.topic?.id === topic?.id
                        ? "bg-accent border-primary"
                        : "hover:bg-accent/50"
                    }`}
                    onClick={() => {
                      setSelectedScript(topicWithOptions);
                      const firstScript = topicWithOptions.scripts?.[0];
                      if (firstScript) {
                        // Use edited_content if exists, otherwise content
                        setScriptText(
                          firstScript.edited_content ||
                            firstScript.content ||
                            ""
                        );
                      } else {
                        setScriptText("");
                      }
                      setSelectedHook("0");
                      setShowMobileDetail(true);
                    }}
                  >
                    <h3 className="text-sm font-medium text-foreground mb-2 line-clamp-2">
                      {topic?.title || "Untitled Topic"}
                    </h3>

                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-xs">
                        {cluster}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {optionsCount} option{optionsCount !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Collaborative Editor */}
        <div
          className={`${
            showMobileDetail ? "flex" : "hidden lg:flex"
          } flex-1 overflow-y-auto`}
        >
          <div className="p-4 lg:p-6 max-w-4xl w-full">
            <Button
              variant="ghost"
              size="sm"
              className="mb-4 lg:hidden"
              onClick={() => setShowMobileDetail(false)}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back to Topics
            </Button>

            {/* Style, Platform and Content Type Selectors */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 mb-6">
              {/* Style Selector */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 flex-1">
                <Label className="text-sm text-muted-foreground whitespace-nowrap">
                  Style:
                </Label>
                <Select value={selectedStyleId} onValueChange={setSelectedStyleId}>
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <SelectValue placeholder="Select style (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default (No Style)</SelectItem>
                    {styleProfiles.map((profile) => (
                      <SelectItem key={profile.id} value={profile.id}>
                        {profile.source_name} ({profile.tone})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center gap-2 flex-1">
                <Label className="text-sm text-muted-foreground whitespace-nowrap">
                  Platform:
                </Label>
                <Select
                  value={platform}
                  onValueChange={(value) =>
                    setPlatform(
                      value as "youtube_short" | "youtube_long" | "tiktok"
                    )
                  }
                >
                  <SelectTrigger className="w-full sm:w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="youtube_short">
                      <div className="flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        YouTube Short
                      </div>
                    </SelectItem>
                    <SelectItem value="youtube_long">
                      <div className="flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        YouTube Long
                      </div>
                    </SelectItem>
                    <SelectItem value="tiktok">
                      <div className="flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        TikTok
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center gap-2 flex-1">
                <Label className="text-sm text-muted-foreground whitespace-nowrap">
                  Content Type:
                </Label>
                <Select value={contentType} onValueChange={setContentType}>
                  <SelectTrigger className="w-full sm:w-[160px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="video-script">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Video Script
                      </div>
                    </SelectItem>
                    <SelectItem value="short">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Short Video
                      </div>
                    </SelectItem>
                    <SelectItem value="infographic">
                      <div className="flex items-center gap-2">
                        <LayoutGrid className="w-4 h-4" />
                        Infographic Pack
                      </div>
                    </SelectItem>
                    <SelectItem value="carousel">
                      <div className="flex items-center gap-2">
                        <ImageIcon className="w-4 h-4" />
                        IG Carousel
                      </div>
                    </SelectItem>
                    <SelectItem value="thread">
                      <div className="flex items-center gap-2">
                        <Twitter className="w-4 h-4" />X Thread
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Multi-platform variant chips */}
            <div className="mb-6">
              <div className="flex flex-wrap items-center gap-2">
                {variants.map((variant) => (
                  <Badge
                    key={variant.id}
                    variant={
                      activeVariant === variant.platform ? "default" : "outline"
                    }
                    className="cursor-pointer px-3 py-1"
                    onClick={() => setActiveVariant(variant.platform)}
                  >
                    {variant.label}
                  </Badge>
                ))}
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 bg-transparent"
                  onClick={() => handleAddVariant("tiktok", "TikTok")}
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Add Variant
                </Button>
              </div>
            </div>

            {/* Tabs for AI-Assisted and Manual modes */}
            <Tabs defaultValue="assisted" className="space-y-6">
              <TabsList className="w-full sm:w-auto">
                <TabsTrigger value="assisted" className="flex-1 sm:flex-none">
                  AI-Assisted
                </TabsTrigger>
                <TabsTrigger value="manual" className="flex-1 sm:flex-none">
                  Manual Edit
                </TabsTrigger>
              </TabsList>

              {/* AI-Assisted Mode */}
              <TabsContent value="assisted" className="space-y-6">
                {/* Topic Summary */}
                <div>
                  <h2 className="text-lg lg:text-xl font-semibold text-foreground mb-2">
                    {selectedScript?.topic?.title || "Untitled Topic"}
                  </h2>
                  <Badge variant="secondary">
                    {selectedScript?.topic?.topic_cluster
                      ?.split("-")
                      .map(
                        (word: string) =>
                          word.charAt(0).toUpperCase() + word.slice(1)
                      )
                      .join(" ") || "Unknown"}
                  </Badge>
                </div>

                {/* Brainstorm Input section */}
                <Card className="p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
                    <h3 className="text-sm font-semibold text-foreground">
                      Brainstorm Input
                    </h3>
                    <div className="flex flex-col sm:flex-row gap-2">
                      <Button
                        size="sm"
                        variant={isRecording ? "destructive" : "outline"}
                        onClick={handleRecording}
                        className="w-full sm:w-auto"
                      >
                        <Mic className="w-4 h-4 mr-2" />
                        {isRecording ? "Stop Recording" : "Record Audio"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full sm:w-auto bg-transparent"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Audio
                      </Button>
                    </div>
                  </div>

                  <Textarea
                    placeholder="Dump your rough ideas, transcript, or brainstorm here... AI will structure this into beats that you can refine."
                    value={brainstormText}
                    onChange={(e) => setBrainstormText(e.target.value)}
                    className="min-h-[150px] text-sm mb-3"
                  />

                  <Button
                    onClick={() => setShowBeats(true)}
                    className="w-full"
                    disabled={!brainstormText}
                  >
                    <Wand2 className="w-4 h-4 mr-2" />
                    Structure with AI
                  </Button>
                </Card>

                {/* Beats/Structure section for collaborative editing */}
                {showBeats && (
                  <Card className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-foreground">
                        Beats & Structure
                      </h3>
                      <Button size="sm" variant="ghost">
                        <Wand2 className="w-4 h-4 mr-2" />
                        Regenerate
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mb-4">
                      Drag to reorder, click to toggle Keep/Maybe/Drop. These
                      beats will feed all platform variants.
                    </p>
                    <div className="space-y-2">
                      {beats.map((beat) => (
                        <div
                          key={beat.id}
                          className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                            beat.status === "keep"
                              ? "border-success/50 bg-success/5"
                              : beat.status === "maybe"
                              ? "border-warning/50 bg-warning/5"
                              : "border-border bg-muted opacity-50"
                          }`}
                        >
                          <GripVertical className="w-4 h-4 text-muted-foreground mt-0.5 cursor-grab" />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-foreground">
                              {beat.title}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {beat.summary}
                            </p>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 px-2"
                            onClick={() => toggleBeatStatus(beat.id)}
                          >
                            {beat.status === "keep" ? (
                              <Badge
                                variant="outline"
                                className="text-xs border-success text-success"
                              >
                                Keep
                              </Badge>
                            ) : beat.status === "maybe" ? (
                              <Badge
                                variant="outline"
                                className="text-xs border-warning text-warning"
                              >
                                Maybe
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-xs">
                                Drop
                              </Badge>
                            )}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Script / Assets tabs for different content types */}
                <Tabs defaultValue="script" className="space-y-4">
                  <TabsList>
                    <TabsTrigger value="script">Script</TabsTrigger>
                    <TabsTrigger value="assets">Assets</TabsTrigger>
                  </TabsList>

                  <TabsContent value="script" className="space-y-4">
                    {/* Hooks */}
                    <Card className="p-4">
                      <h3 className="text-sm font-semibold text-foreground mb-3">
                        Select Hook
                      </h3>
                      <RadioGroup
                        value={selectedHook}
                        onValueChange={setSelectedHook}
                      >
                        <div className="space-y-3">
                          {selectedScript?.hooks?.map(
                            (hook: any, index: number) => (
                              <div
                                key={hook.id || index}
                                className="flex items-start space-x-3 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                              >
                                <RadioGroupItem
                                  value={index.toString()}
                                  id={`hook-${index}`}
                                  className="mt-0.5"
                                />
                                <Label
                                  htmlFor={`hook-${index}`}
                                  className="text-sm text-foreground cursor-pointer flex-1 font-normal"
                                >
                                  {hook.content || hook}
                                </Label>
                              </div>
                            )
                          )}
                        </div>
                      </RadioGroup>
                    </Card>

                    {/* Script Preview */}
                    <Card className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-foreground">
                          Script Preview
                        </h3>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={async () => {
                              const scriptId = selectedScript?.scripts?.[0]?.id;
                              if (!scriptId) return;
                              try {
                                const response = await fetch(
                                  "/api/scripts/refine",
                                  {
                                    method: "POST",
                                    headers: {
                                      "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                      option_id: scriptId,
                                      refinement_type: "tighten",
                                    }),
                                  }
                                );
                                const data = await response.json();
                                if (data.success && data.data?.option) {
                                  setScriptText(
                                    data.data.option.edited_content ||
                                      data.data.option.content
                                  );
                                }
                              } catch (err) {
                                console.error("Failed to refine script:", err);
                              }
                            }}
                          >
                            Tighten
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={async () => {
                              const scriptId = selectedScript?.scripts?.[0]?.id;
                              if (!scriptId) return;
                              try {
                                const response = await fetch(
                                  "/api/scripts/refine",
                                  {
                                    method: "POST",
                                    headers: {
                                      "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                      option_id: scriptId,
                                      refinement_type: "casual",
                                    }),
                                  }
                                );
                                const data = await response.json();
                                if (data.success && data.data?.option) {
                                  setScriptText(
                                    data.data.option.edited_content ||
                                      data.data.option.content
                                  );
                                }
                              } catch (err) {
                                console.error("Failed to refine script:", err);
                              }
                            }}
                          >
                            More casual
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={async () => {
                              const scriptId = selectedScript?.scripts?.[0]?.id;
                              if (!scriptId) return;
                              try {
                                const response = await fetch(
                                  "/api/scripts/refine",
                                  {
                                    method: "POST",
                                    headers: {
                                      "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                      option_id: scriptId,
                                      refinement_type: "regenerate",
                                    }),
                                  }
                                );
                                const data = await response.json();
                                if (data.success && data.data?.option) {
                                  setScriptText(
                                    data.data.option.edited_content ||
                                      data.data.option.content
                                  );
                                }
                              } catch (err) {
                                console.error("Failed to refine script:", err);
                              }
                            }}
                          >
                            <Wand2 className="w-4 h-4 mr-2" />
                            Regenerate
                          </Button>
                        </div>
                      </div>
                      <Textarea
                        value={scriptText}
                        onChange={(e) => setScriptText(e.target.value)}
                        onBlur={async () => {
                          // Auto-save on blur
                          const scriptId = selectedScript?.scripts?.[0]?.id;
                          if (!scriptId || !scriptText) return;
                          try {
                            await fetch(`/api/scripts/${scriptId}`, {
                              method: "PUT",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ content: scriptText }),
                            });
                          } catch (err) {
                            console.error("Failed to save script:", err);
                          }
                        }}
                        className="min-h-[300px] font-mono text-sm"
                      />
                    </Card>
                  </TabsContent>

                  <TabsContent value="assets" className="space-y-4">
                    <Card className="p-4">
                      <h3 className="text-sm font-semibold text-foreground mb-3">
                        Platform Assets
                      </h3>
                      {(platform === "youtube_short" ||
                        platform === "youtube_long") && (
                        <div className="space-y-4">
                          <div>
                            <Label className="text-sm text-muted-foreground mb-2 block">
                              Thumbnail Ideas
                            </Label>
                            <div className="space-y-2">
                              <div className="p-3 border border-border rounded-lg">
                                <p className="text-sm font-medium text-foreground">
                                  Claude 3.5 Context Window
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  Visual: Split screen showing small vs massive
                                  document
                                </p>
                              </div>
                            </div>
                          </div>
                          <div>
                            <Label className="text-sm text-muted-foreground mb-2 block">
                              Description
                            </Label>
                            <Textarea
                              placeholder="Video description with keywords..."
                              className="min-h-[100px] text-sm"
                            />
                          </div>
                        </div>
                      )}
                      {platform === "tiktok" && (
                        <div className="space-y-4">
                          <div>
                            <Label className="text-sm text-muted-foreground mb-2 block">
                              On-Screen Text
                            </Label>
                            <Textarea
                              placeholder="Key text overlays..."
                              className="min-h-[100px] text-sm"
                            />
                          </div>
                          <div>
                            <Label className="text-sm text-muted-foreground mb-2 block">
                              Caption
                            </Label>
                            <Textarea
                              placeholder="Post caption..."
                              className="min-h-[80px] text-sm"
                            />
                          </div>
                          <div>
                            <Label className="text-sm text-muted-foreground mb-2 block">
                              Hashtags
                            </Label>
                            <Textarea
                              placeholder="#ai #claude #tech..."
                              className="min-h-[60px] text-sm"
                            />
                          </div>
                        </div>
                      )}
                      {contentType === "carousel" && (
                        <div className="space-y-3">
                          <Label className="text-sm text-muted-foreground">
                            Carousel Slides
                          </Label>
                          {[1, 2, 3].map((slide) => (
                            <div
                              key={slide}
                              className="p-3 border border-border rounded-lg"
                            >
                              <p className="text-xs font-medium text-foreground mb-2">
                                Slide {slide}
                              </p>
                              <Textarea
                                placeholder="Slide copy..."
                                className="min-h-[60px] text-sm"
                              />
                            </div>
                          ))}
                        </div>
                      )}
                      {contentType === "infographic" && (
                        <div className="space-y-3">
                          <Label className="text-sm text-muted-foreground">
                            Infographic Elements
                          </Label>
                          <div className="p-3 border border-border rounded-lg">
                            <p className="text-sm font-medium text-foreground mb-2">
                              Chart: Context Window Comparison
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Data: GPT-4: 32K, Claude 3: 200K
                            </p>
                          </div>
                        </div>
                      )}
                    </Card>
                  </TabsContent>
                </Tabs>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button className="flex-1">
                    <Check className="w-4 h-4 mr-2" />
                    Mark Ready
                  </Button>
                  <Button variant="outline" className="flex-1 bg-transparent">
                    <Shield className="w-4 h-4 mr-2" />
                    Needs Ethics Review
                  </Button>
                </div>
              </TabsContent>

              {/* Manual Edit Mode */}
              <TabsContent value="manual" className="space-y-6">
                {/* Topic Summary */}
                <div>
                  <h2 className="text-lg lg:text-xl font-semibold text-foreground mb-2">
                    {selectedScript?.topic?.title || "Untitled Topic"}
                  </h2>
                  <Badge variant="secondary">
                    {selectedScript?.topic?.topic_cluster
                      ?.split("-")
                      .map(
                        (word: string) =>
                          word.charAt(0).toUpperCase() + word.slice(1)
                      )
                      .join(" ") || "Unknown"}
                  </Badge>
                </div>

                {/* Hooks */}
                <Card className="p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-3">
                    Select Hook
                  </h3>
                  <RadioGroup
                    value={selectedHook}
                    onValueChange={setSelectedHook}
                  >
                    <div className="space-y-3">
                      {selectedScript?.hooks?.map(
                        (hook: any, index: number) => (
                          <div
                            key={hook.id || index}
                            className="flex items-start space-x-3 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                          >
                            <RadioGroupItem
                              value={index.toString()}
                              id={`hook-${index}`}
                              className="mt-0.5"
                            />
                            <Label
                              htmlFor={`hook-${index}`}
                              className="text-sm text-foreground cursor-pointer flex-1 font-normal"
                            >
                              {hook.content || hook}
                            </Label>
                          </div>
                        )
                      )}
                    </div>
                  </RadioGroup>
                </Card>

                {/* Script */}
                <Card className="p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-3">
                    Script
                  </h3>
                  <Textarea
                    value={scriptText}
                    onChange={(e) => setScriptText(e.target.value)}
                    onBlur={async () => {
                      // Auto-save on blur
                      const scriptId = selectedScript?.scripts?.[0]?.id;
                      if (!scriptId || !scriptText) return;
                      try {
                        await fetch(`/api/scripts/${scriptId}`, {
                          method: "PUT",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ content: scriptText }),
                        });
                      } catch (err) {
                        console.error("Failed to save script:", err);
                      }
                    }}
                    className="min-h-[300px] font-mono text-sm"
                  />
                  {selectedScript?.scripts?.[0] && (
                    <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border text-xs text-muted-foreground">
                      <span>
                        Prompt:{" "}
                        {selectedScript.scripts[0].prompt_version || "N/A"}
                      </span>
                      <span>·</span>
                      <span>
                        Model: {selectedScript.scripts[0].model || "N/A"}
                      </span>
                    </div>
                  )}
                </Card>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button
                    className="flex-1"
                    onClick={async () => {
                      const scriptId = selectedScript?.scripts?.[0]?.id;
                      if (!scriptId) return;
                      try {
                        const response = await fetch("/api/options", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            topic_id: selectedScript?.topic?.id,
                            selected_option_id: scriptId,
                            edited_content: scriptText,
                            mark_ready: true,
                            platform: platform,
                          }),
                        });
                        const data = await response.json();
                        if (data.success) {
                          alert("Script marked as ready!");
                        }
                      } catch (err) {
                        console.error("Failed to mark ready:", err);
                      }
                    }}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Mark Ready
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1 bg-transparent"
                    onClick={async () => {
                      const scriptId = selectedScript?.scripts?.[0]?.id;
                      if (!scriptId) return;
                      try {
                        const response = await fetch("/api/options", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            topic_id: selectedScript?.topic?.id,
                            selected_option_id: scriptId,
                            edited_content: scriptText,
                            mark_ready: true,
                            needs_ethics_review: true,
                            platform: platform,
                          }),
                        });
                        const data = await response.json();
                        if (data.success) {
                          alert("Script flagged for ethics review");
                        }
                      } catch (err) {
                        console.error("Failed to flag for ethics review:", err);
                      }
                    }}
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Needs Ethics Review
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
