# Content Engine - User Workflows & End-to-End Journeys

**Analysis Date**: 2025-01-27  
**Documentation Version**: 1.0

---

## Table of Contents

1. [User Persona & Mental Model](#user-persona--mental-model)
2. [Core User Workflows](#core-user-workflows)
3. [End-to-End User Journeys](#end-to-end-user-journeys)
4. [System Workflows](#system-workflows)
5. [Data Flow Sequences](#data-flow-sequences)
6. [Interaction Patterns](#interaction-patterns)

---

## User Persona & Mental Model

### Primary User: Editor-in-Chief / Content Operator

**Role**: Content curator and decision-maker  
**Goal**: Efficiently review AI-generated content proposals and make high-leverage decisions

**Mental Model**:
- The system is a **"review console for an AI production line"** (not a generic CMS)
- System constantly **proposes** topics + scripts
- User makes **small, high-leverage decisions**
- Everything is **logged** for learning and transparency

**Usage Pattern**:
- **Daily**: Short 10-15 minute review sessions
- **Periodic**: Deep dives into performance, decisions, and system tuning

---

## Core User Workflows

### 1. Morning Topic Review Workflow

**Goal**: Decide "what we should talk about today" in ~10-15 minutes

**Entry Point**: `/today` page

**Steps**:

1. **Open Application**
   - User navigates to `/today` (default landing page)
   - System displays ranked queue of 8-12 topic candidates

2. **Review Topic Queue**
   - Topics displayed in ranked order (highest score first)
   - Each topic shows:
     - Title
     - Platform/source (Reddit, HN, RSS, Manual)
     - Cluster category (ai-infra, culture, business, etc.)
     - Composite score (0.0-1.0)
     - Badge indicators (NEW, trending, etc.)

3. **Inspect Topic Details**
   - Click topic to see detail panel:
     - Score breakdown (recency, velocity, audience fit, integrity penalty)
     - Extracted entities (companies, people, concepts)
     - Source URL and metadata
     - Reasoning from scoring system

4. **Make Decision**
   - **Approve**: Topic moves to content generation queue
     - Status changes: `pending` → `approved`
     - Triggers content generation (hooks + scripts)
   - **Reject**: Topic marked as rejected
     - Select reason code: `too_generic`, `not_on_brand`, `speculative`, `duplicate`, `ethics`
     - Optional note field
     - Status changes: `pending` → `rejected`
   - **Defer**: Topic postponed for later review
     - Status changes: `pending` → `deferred`
     - Can be reviewed again later

5. **Audit Event Creation**
   - Every decision creates `AuditEvent`:
     - Stage: `topic_selection`
     - System decision (score components, ranking)
     - Human action (approve/reject/defer + reason)
     - Actor (user ID/email)
     - Timestamp

6. **Session Summary**
   - Live counter: "Approved 4 / Rejected 3 / Remaining 2"
   - Toast notification: "Logged decision · (view audit)"

**Keyboard Shortcuts**:
- `j/k` or arrows: Navigate queue
- `A`: Approve
- `R`: Reject
- `D`: Defer

**Backend Flow**:
```
User Action → POST /api/topics
  → Firestore Transaction
    → Update topic_candidates.status
    → Create audit_events entry
  → Return success
```

**Artifacts Created**:
- Updated `TopicCandidate` (status change)
- New `AuditEvent` (decision record)

---

### 2. Script/Option Selection & Edit Workflow

**Goal**: Pick the best framing + words with minimal typing

**Entry Point**: `/scripts` page

**Steps**:

1. **Navigate to Scripts View**
   - User clicks "Scripts" in navigation
   - System displays approved topics with generated content options

2. **Review Content Options**
   - For each approved topic:
     - **Hooks**: 2-3 AI-generated attention-grabbing opening lines
     - **Scripts**: 1-2 full short-form video scripts
     - Metadata: prompt version, model used, generation timestamp

3. **Select Hook**
   - Radio button selection for preferred hook
   - Selection marks which `ContentOption` is chosen

4. **Review & Edit Script**
   - Display selected script in textarea
   - User can:
     - **Manual edit**: Type directly in textarea
     - **AI Refinement**:
       - **Tighten**: Make more concise
       - **Casual**: Adjust tone to be more casual
       - **Regenerate**: Fresh wording with same prompt
   - Auto-save on blur (computes diff for learning)

5. **Mark as Ready**
   - **Mark Ready**: Creates `PublishedContent` draft
     - Status: `draft`
     - Platform: `youtube_short` (default)
     - Links to selected option
   - **Needs Ethics Review**: Flags for integrity queue
     - Moves to `/integrity` view
     - Status: `needs_ethics_review`

6. **Audit Event Creation**
   - Creates `AuditEvent`:
     - Stage: `option_selection`
     - System decision (all options presented, recommended)
     - Human action (selected option, rejected options, edits, reason)
     - Diff tracking (if edited)

**Backend Flow**:
```
User Action → POST /api/options
  → Firestore Transaction
    → Verify topic & option exist
    → Compute diff (if edited)
    → Create audit_events entry
    → Create published_content (if marked ready)
  → Return success
```

**AI Refinement Flow**:
```
User Action → POST /api/scripts/refine
  → OpenAI API call
    → Apply refinement prompt
    → Return refined content
  → Update content_options
  → Return refined text
```

**Artifacts Created**:
- Updated `ContentOption` (if refined)
- New `PublishedContent` (if marked ready)
- New `AuditEvent` (selection decision)

---

### 3. Ethics / Integrity Review Workflow

**Goal**: Stop messy stuff, or reframe it as industry/business commentary

**Entry Point**: `/integrity` page

**Steps**:

1. **Navigate to Integrity View**
   - System displays flagged topics/scripts
   - Items flagged due to:
     - Low integrity confidence score
     - Manual flagging from Scripts view
     - Integrity penalty threshold exceeded

2. **Review Flagged Item**
   - Display:
     - Risk badge (Low/Medium/High)
     - Platform and cluster
     - Title/content
     - **Why flagged**: Reason (e.g., "personal rumour", "speculative", "low-source confidence")
     - **Suggested reframes**: Alternative angles (e.g., "What this tells us about label PR strategy")

3. **Make Decision**
   - **Publish as is**: Override flag, publish normally
   - **Reframe**: Apply reframe template
     - System regenerates content with reframe angle
     - Uses LLM with reframe prompt
   - **Skip**: Reject this content
     - Optional reason: "too speculative", "too personal", etc.

4. **Audit Event Creation**
   - Creates `AuditEvent`:
     - Stage: `ethics_review`
     - System decision (flag reason, suggested reframes)
     - Human action (decision, reframe applied, notes)
     - Used to adjust integrity penalty weights over time

**Backend Flow**:
```
User Action → POST /api/integrity
  → Firestore Transaction
    → Create audit_events entry (stage: ethics_review)
    → (If skip) Update topic_candidates.status to "rejected"
    → (If reframe) Store reframe request in topic metadata (needs_reframe flag)
    → (If publish) Topic status unchanged
  → Return success
  Note: Reframe request stored in metadata; actual regeneration would be triggered by separate job/endpoint
```

**Artifacts Created**:
- Updated `PublishedContent` (status change)
- New `AuditEvent` (ethics review decision)
- (If reframe) New `ContentOption` (reframed version)

---

### 4. Audit & Decision History Exploration Workflow

**Goal**: Understand "why did we do X?" or "why is the system picking these now?"

**Entry Point**: `/history` page

**Steps**:

1. **Navigate to History View**
   - System displays audit trail table
   - Columns: Time, Stage, Topic, Actor

2. **Filter Audit Trail**
   - **By date range**: Last 7 days, 30 days, custom
   - **By stage**: `topic_selection`, `option_selection`, `ethics_review`
   - **By platform**: Reddit, HN, RSS, Manual
   - **By cluster**: ai-infra, culture, business, etc.
   - Note: Timeline view may show `published` stage from PublishedContent records, but this is not an AuditEvent stage

3. **View Topic Timeline**
   - Click row to open timeline side-panel
   - Shows complete lifecycle:
     ```
     - Ingested from: [source] at [time]
     - Scored [score] (components breakdown)
     - System suggested rank [X]/[total]
     - [User] approved/rejected (note: "...")
     - Options generated (hooks v3, script v1)
     - [User] selected Hook B, edited script (diff link)
     - Published on [platform] at [time]
     - Metrics: [views], [retention], [engagement]
     ```

4. **Use Cases**
   - Debugging weird recommendations
   - Understanding drift/bias in system
   - Writing internal notes ("we avoid X now because...")
   - Performance analysis

**Backend Flow**:
```
User Request → GET /api/audit
  → Firestore Query
    → Apply filters (date, stage, platform, cluster)
    → Order by created_at DESC
    → Return audit_events
```

**Timeline View**:
```
User Request → GET /api/audit/timeline/[topic_id]
  → Firestore Query
    → Fetch all audit_events for topic_id
    → Fetch topic_candidates, topic_scores, content_options, published_content
    → Build chronological timeline
    → Return structured timeline
```

---

### 5. Performance & Tuning Workflow

**Goal**: See if learning loop is doing something sane + occasionally nudge it

**Entry Point**: `/performance` page

**Steps**:

1. **Navigate to Performance View**
   - System displays metrics dashboard

2. **View Metrics**
   - **Charts**:
     - Average view duration over time
     - Performance by pillar (AI vs culture vs business)
     - CTR by platform
     - Engagement trends
   - **Current Scoring Weights**:
     - Recency: 0.3 (default) or 0.4 (if configured)
     - Velocity: 0.4 (default) or 0.3 (if configured)
     - Audience fit: 0.3
     - Integrity penalty: -0.20 (applied as penalty)

3. **Review Learning Suggestions**
   - System shows suggested adjustments:
     - "Increase audience_fit for culture by +0.05"
     - "Increase integrity penalty by -0.05"
   - Last learning update timestamp

4. **Manual Override (Optional)**
   - Click "Edit manually"
   - Modal opens with weight sliders
   - User adjusts weights:
     - Recency: [slider]
     - Velocity: [slider]
     - Audience fit: [slider]
     - Integrity penalty: [slider]
   - Save changes

5. **System Behavior**
   - Manual overrides treated as high-priority config
   - Weekly learning job still runs but bounded by explicit choices
   - Changes logged in audit trail

**Backend Flow**:
```
User Request → GET /api/performance
  → Firestore Query
    → Fetch content_metrics
    → Fetch current scoring weights
    → Calculate trends
    → Return metrics + weights
```

**Weight Update**:
```
User Action → POST /api/performance/weights
  → Firestore Update
    → Update scoring_weights config
    → Create audit_events entry (config change)
  → Return success
```

---

### 6. Style Curation Workflow

**Goal**: Curate writing styles from successful content sources

**Entry Point**: `/styles` page

**Steps**:

1. **Add Style Source** (CLI or UI)
   ```bash
   poetry run python -m src.cli.main add-style-source \
     --url "https://www.reddit.com/r/hiphopheads/" \
     --name "Hip-Hop Community" \
     --tags "hip-hop,culture"
   ```

2. **System Ingests Source**
   - Fetches content from source (Reddit, podcast transcripts, etc.)
   - Stores as `StylisticContent` in Firestore
   - Status: `pending`

3. **Extract Style Profiles**
   ```bash
   poetry run python -m src.cli.main extract-styles \
     --source-id source-123 \
     --limit 10
   ```
   - LLM analyzes content samples
   - Extracts: tone, structure, vocabulary, hooks
   - Creates `StyleProfile` with status: `pending`

4. **Review Style Profiles** (Frontend `/styles`)
   - View extracted profiles
   - See: source name, tone, structure patterns, example hooks
   - Test profile: Generate sample content with style

5. **Approve/Reject Profile**
   - **Approve**: Profile becomes active
     - Status: `pending` → `approved`
     - Can be applied to new content generation
   - **Reject**: Profile discarded
     - Status: `pending` → `rejected`
     - Use POST /api/styles/profiles/[id]/reject
     - Reason captured

6. **Apply Style to Content**
   - When generating content options:
     - User can select style profile
     - Prompt enhanced with style instructions
     - Generated content matches style

**Backend Flow**:
```
CLI: add-style-source
  → StylisticSourceIngestionService
    → Fetch content from URL
    → Store StylisticContent
    → (If auto) Extract styles
      → StyleExtractionService
        → LLM analysis
        → Create StyleProfile
```

**Profile Approval**:
```
User Action → POST /api/styles/profiles (with profile_id in body)
  OR PUT /api/styles/profiles/[id] (auto-approves if editing pending profile)
  → Update StyleProfile.status to "approved"
  → Set curated_by, curated_at, curator_notes
  → Return success
```

---

## End-to-End User Journeys

### Journey 1: Complete Content Creation Flow

**Scenario**: User discovers topic → approves → generates content → publishes

**Timeline**: ~30-45 minutes (mostly waiting for AI generation)

**Sequence**:

1. **Topic Discovery** (Automated - Background)
   ```
   CLI: ingest-topics
     → Fetch Reddit, HN, RSS
     → Parse & normalize
     → Extract entities
     → Cluster topics
     → Deduplicate
     → Save TopicCandidate (status: pending)
   ```

2. **Topic Scoring** (Automated - Background)
   ```
   CLI: score-topics
     → Fetch pending topics
     → Calculate recency (age-based decay)
     → Calculate velocity (trending indicators)
     → Calculate audience fit (cluster match)
     → Apply integrity penalty
     → Save TopicScore
   ```

3. **Topic Review** (User - 10 min)
   ```
   User → /today
     → View ranked topics
     → Review score breakdown
     → Approve topic "AI Safety Summit"
     → POST /api/topics
       → Update status: approved
       → Create AuditEvent
   ```

4. **Content Generation** (Manual Trigger)
   ```
   User → /scripts
     → Click "Generate Options" (manual action)
     → POST /api/options/generate
       → Fetch approved topics without options
       → For each topic:
         → Load prompt templates
         → Build context (topic, entities, cluster)
         → Call OpenAI API (GPT-4o-mini)
         → Generate 3 hooks + 1 script
         → Save ContentOption entries
   ```
   Note: Content generation is not automatic after approval - user must manually trigger it

5. **Script Selection** (User - 5 min)
   ```
   User → /scripts
     → View generated hooks & scripts
     → Select Hook B
     → Edit script (minor tweaks)
     → Mark as ready
     → POST /api/options
       → Create PublishedContent (status: draft)
       → Create AuditEvent
   ```

6. **Publishing** (Future - Automated)
   ```
   System → Platform API (YouTube, TikTok)
     → Upload content
     → Schedule publish
     → Update PublishedContent
       → status: published
       → external_id: [platform_id]
       → published_at: [timestamp]
   ```

7. **Metrics Collection** (Future - Automated)
   ```
   System → Platform API
     → Fetch metrics (views, engagement, retention)
     → Save ContentMetrics
     → Trigger learning job
       → Analyze performance
       → Adjust scoring weights
   ```

**Total User Time**: ~15 minutes  
**Total System Time**: ~30 minutes (AI generation)

---

### Journey 2: Rejection & Learning Flow

**Scenario**: User rejects topic → system learns from feedback

**Sequence**:

1. **Topic Appears in Queue**
   ```
   User → /today
     → Sees topic "Celebrity Gossip"
     → Score: 0.75
   ```

2. **User Reviews & Rejects**
   ```
   User → Click topic
     → See score breakdown
     → See entities: [Celebrity Name]
     → Reject with reason: "not_on_brand"
     → POST /api/topics
       → Status: rejected
       → AuditEvent: reason_code: "not_on_brand"
   ```

3. **System Learning** (Weekly Job)
   ```
   Learning Service
     → Analyze audit_events
     → Find patterns:
       - Topics with [celebrity entities] → 80% rejected
       - Reason: "not_on_brand"
     → Adjust scoring:
       - Increase integrity penalty for celebrity topics
       - Reduce audience_fit for gossip clusters
     → Update scoring_weights config
   ```

4. **Future Impact**
   ```
   Next similar topic
     → Integrity penalty: -0.15 (was -0.05)
     → Score: 0.60 (was 0.75)
     → Ranked lower in queue
     → Less likely to be shown
   ```

---

### Journey 3: Ethics Review & Reframe Flow

**Scenario**: Content flagged → user reframes → publishes

**Sequence**:

1. **Content Flagged**
   ```
   Scoring Service
     → Topic: "Artist Controversy"
     → Integrity check: low confidence
     → Integrity penalty: -0.20
     → Still approved (score: 0.70)
   ```

2. **Content Generated**
   ```
   Content Generation
     → Generates hooks & script
     → Script mentions personal details
     → Flagged for ethics review
   ```

3. **User Reviews in Integrity Queue**
   ```
   User → /integrity
     → Sees flagged content
     → Reason: "personal/rumour"
     → Suggested reframes:
       - "What this tells us about label PR strategy"
       - "How platforms shape narratives"
   ```

4. **User Reframes**
   ```
   User → Click "Reframe using option 1"
     → POST /api/integrity
       → Decision: "reframe"
       → Store reframe request in topic metadata
       → Create AuditEvent (ethics_review stage)
       → Note: Actual reframe generation would be triggered by separate job/endpoint
       → (Future: Automatic regeneration with reframe prompt)
   ```

5. **User Approves Reframed Content**
   ```
   User → /scripts
     → Review reframed script
     → Mark as ready
     → Content published with industry angle
   ```

---

### Journey 4: Style Learning & Application Flow

**Scenario**: User discovers successful content → extracts style → applies to new content

**Sequence**:

1. **Add Style Source**
   ```
   User (CLI)
     → add-style-source --url "https://reddit.com/r/hiphopheads/"
     → System ingests 50 posts
     → Stores as StylisticContent
   ```

2. **Extract Style Profiles**
   ```
   User (CLI)
     → extract-styles --source-id source-123
     → LLM analyzes samples
     → Extracts:
       - Tone: Casual, energetic, authentic
       - Structure: Hook → Context → Personal take → Callout
       - Vocabulary: Slang, cultural references
     → Creates StyleProfile (status: pending)
   ```

3. **Review & Approve Profile**
   ```
   User → /styles
     → View extracted profile
     → Test: Generate sample content
     → Approve profile
     → Status: approved
   ```

4. **Apply Style to New Content**
   ```
   User → /scripts
     → Generate options for topic
     → Select style profile: "Hip-Hop Community"
     → POST /api/options/generate
       → Prompt enhanced with style instructions
       → Generated content matches style:
         - Casual tone
         - Cultural references
         - Authentic voice
   ```

5. **Content Performs Well**
   ```
   Metrics Collection
     → Content with style profile: 25% better retention
     → System learns: This style works for culture topics
     → Future: Auto-suggest style for similar topics
   ```

---

## System Workflows

### Automated Background Workflows

#### 1. Topic Ingestion Job (Scheduled)

**Frequency**: Every 4-6 hours (or manual trigger)

**Process**:
```python
CLI: ingest-topics
  → TopicIngestionService.fetch_from_sources()
    → RedditSource.fetch() → [raw_topics]
    → HackerNewsSource.fetch() → [raw_topics]
    → RSSSource.fetch() → [raw_topics]
  → Process raw topics:
    → EntityExtractor.extract_entities()
    → TopicClusterer.cluster_topic()
    → Deduplicator.check_duplicates()
  → Save TopicCandidate (status: pending)
```

**Output**: New `TopicCandidate` entries in Firestore

---

#### 2. Topic Scoring Job (Scheduled)

**Frequency**: Every 2-4 hours (or manual trigger)

**Process**:
```python
CLI: score-topics --limit 100
  → ScoringService.score_topics()
    → Fetch pending topics
    → For each topic:
      → calculate_recency() → 0.0-1.0
      → calculate_velocity() → 0.0-1.0
      → calculate_audience_fit() → 0.0-1.0
      → apply_integrity_check() → 0.0 to -0.5
      → Composite score = weighted sum
    → Save TopicScore
```

**Output**: New `TopicScore` entries linked to topics

---

#### 3. Content Generation (Manual Trigger)

**Trigger**: User manually triggers via frontend (not automatic after approval)

**Process**:
```python
POST /api/options/generate
  → Fetch approved topics without options
  → For each topic:
    → Load prompt templates (hook_v1, script_v1)
    → Build context:
      - Topic title
      - Entities
      - Cluster
      - Style profile (if selected)
    → OpenAI API call:
      - Model: gpt-4o-mini
      - Generate 3 hooks
      - Generate 1 script
    → Save ContentOption entries
```

**Output**: New `ContentOption` entries (hooks + scripts)

---

#### 4. Learning Job (Weekly)

**Frequency**: Weekly (future)

**Process**:
```python
Learning Service
  → Analyze audit_events (last 7 days)
  → Correlate with ContentMetrics
  → Find patterns:
    - High-performing topics → scoring components
    - Rejected topics → reasons
    - Edited content → common changes
  → Adjust scoring weights
  → Update prompt templates
  → Save config updates
```

**Output**: Updated `scoring_weights` config

---

## Data Flow Sequences

### Sequence 1: Topic Discovery → Approval

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Sources   │    │  Ingestion   │    │  Firestore  │    │   Scoring    │
│  (Reddit)   │    │   Service    │    │             │    │   Service    │
└──────┬──────┘    └──────┬───────┘    └──────┬──────┘    └──────┬───────┘
       │                  │                   │                   │
       │ 1. Fetch posts   │                   │                   │
       │─────────────────>│                   │                   │
       │                  │                   │                   │
       │ 2. Return posts  │                   │                   │
       │<─────────────────│                   │                   │
       │                  │                   │                   │
       │                  │ 3. Process        │                   │
       │                  │    (entities,     │                   │
       │                  │     cluster,      │                   │
       │                  │     dedupe)       │                   │
       │                  │                   │                   │
       │                  │ 4. Save TopicCandidate
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │                   │ 5. Fetch pending  │
       │                  │                   │──────────────────>│
       │                  │                   │                   │
       │                  │                   │ 6. Return topics  │
       │                  │                   │<──────────────────│
       │                  │                   │                   │
       │                  │                   │ 7. Calculate scores
       │                  │                   │                   │
       │                  │                   │ 8. Save TopicScore
       │                  │                   │<──────────────────│
       │                  │                   │                   │
```

### Sequence 2: Approval → Content Generation

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Frontend  │    │  API Route   │    │  Firestore  │    │   OpenAI     │
│   (/today)  │    │  (/api/topics)│    │             │    │     API     │
└──────┬──────┘    └──────┬───────┘    └──────┬──────┘    └──────┬───────┘
       │                  │                   │                   │
       │ 1. Approve topic │                   │                   │
       │─────────────────>│                   │                   │
       │                  │                   │                   │
       │                  │ 2. Transaction   │                   │
       │                  │    Update status  │                   │
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 3. Create AuditEvent
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 4. Return success│                   │
       │<─────────────────│                   │                   │
       │                  │                   │                   │
       │ 5. Generate options                  │                   │
       │─────────────────────────────────────────────────────────>│
       │                  │                   │                   │
       │                  │ 6. Fetch topic   │                   │
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 7. Build prompt  │                   │
       │                  │                   │                   │
       │                  │ 8. Generate content
       │                  │───────────────────────────────────────>│
       │                  │                   │                   │
       │                  │ 9. Return hooks + script
       │                  │<───────────────────────────────────────│
       │                  │                   │                   │
       │                  │ 10. Save ContentOptions
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │ 11. Return success                  │                   │
       │<─────────────────│                   │                   │
```

### Sequence 3: Script Selection → Publishing

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Frontend  │    │  API Route   │    │  Firestore  │    │   Platform   │
│  (/scripts) │    │ (/api/options)│    │             │    │   (Future)   │
└──────┬──────┘    └──────┬───────┘    └──────┬──────┘    └──────┬───────┘
       │                  │                   │                   │
       │ 1. Select hook + script             │                   │
       │    Edit content                      │                   │
       │    Mark ready                        │                   │
       │─────────────────>│                   │                   │
       │                  │                   │                   │
       │                  │ 2. Transaction   │                   │
       │                  │    Verify topic & option
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 3. Compute diff   │                   │
       │                  │                   │                   │
       │                  │ 4. Create AuditEvent
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 5. Create PublishedContent
       │                  │──────────────────>│                   │
       │                  │                   │                   │
       │                  │ 6. Return success│                   │
       │<─────────────────│                   │                   │
       │                  │                   │                   │
       │                  │                   │ 7. Publish (future)
       │                  │                   │──────────────────>│
       │                  │                   │                   │
       │                  │                   │ 8. Return metrics │
       │                  │                   │<──────────────────│
       │                  │                   │                   │
       │                  │ 9. Save ContentMetrics
       │                  │<──────────────────│                   │
```

---

## Interaction Patterns

### Pattern 1: High-Leverage Decision Making

**Principle**: User makes small decisions with big impact

**Examples**:
- Approve/reject topic → Triggers content generation pipeline
- Select hook → Determines content framing
- Mark ready → Moves to publishing queue

**UI Support**:
- Clear decision points
- Minimal friction (one-click actions)
- Keyboard shortcuts
- Batch operations (future)

---

### Pattern 2: Explainable AI Decisions

**Principle**: Every system recommendation shows "why"

**Examples**:
- Score breakdown (recency, velocity, audience fit)
- Integrity penalty explanation
- Suggested reframes with reasoning

**UI Support**:
- Expandable detail panels
- Score component visualization
- Reasoning text
- "Why this?" tooltips

---

### Pattern 3: Audit Everything

**Principle**: Complete decision trail for learning and transparency

**Examples**:
- Every approve/reject → AuditEvent
- Every edit → Diff tracked
- Every weight change → Config audit

**UI Support**:
- Toast notifications: "Logged decision"
- History view with filters
- Timeline visualization
- Export audit trail (future)

---

### Pattern 4: Human-in-the-Loop Learning

**Principle**: System learns from human feedback

**Examples**:
- Rejection reasons → Adjust scoring
- Edit patterns → Improve prompts
- Performance metrics → Tune weights

**UI Support**:
- Performance dashboard
- Learning suggestions
- Manual override controls
- "What changed?" indicators

---

### Pattern 5: Short Sessions, High Value

**Principle**: Optimize for 10-15 minute daily sessions

**Examples**:
- Queue size indicators: "8 items remaining"
- Time estimates: "~6 minutes left"
- Progress tracking
- Quick actions

**UI Support**:
- Keyboard-first navigation
- Batch operations
- Smart defaults
- Minimal clicks to decision

---

## Summary

### Core User Journeys

1. **Daily Review** (10-15 min): Topic approval → Content selection → Mark ready
2. **Periodic Deep Dive** (30-60 min): History exploration → Performance analysis → Weight tuning
3. **Style Curation** (as needed): Add source → Extract styles → Approve → Apply

### Key Workflows

1. **Topic Discovery** → Scoring → Review → Approval
2. **Content Generation** → Selection → Editing → Publishing
3. **Ethics Review** → Reframe → Approval
4. **Performance Learning** → Weight Adjustment → Impact

### System Characteristics

- **Human-in-the-loop**: User makes high-leverage decisions
- **Explainable**: Every recommendation shows reasoning
- **Auditable**: Complete decision trail
- **Learning**: System improves from feedback
- **Efficient**: Optimized for short daily sessions

---

**End of Document**

