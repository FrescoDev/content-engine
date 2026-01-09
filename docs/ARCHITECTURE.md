# Content Engine - Architecture Overview

Comprehensive system architecture and component interactions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Content Engine System                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   External Sources   │         │   Human Curator      │
├──────────────────────┤         ├──────────────────────┤
│  • Reddit            │         │  • Topic Review      │
│  • Hacker News       │         │  • Script Editing    │
│  • RSS Feeds         │         │  • Style Curation    │
│  • Manual Entry      │         │  • Ethics Review     │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                 │
           │                                 │
           ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Application Layer                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────┐    ┌────────────────────────────────┐│
│  │     Backend (Python)         │    │    Frontend (Next.js)          ││
│  ├──────────────────────────────┤    ├────────────────────────────────┤│
│  │  CLI-based Operations        │    │  • React 19 + TypeScript       ││
│  │  • Topic Ingestion           │    │  • Firebase Client SDK         ││
│  │  • Scoring                   │    │  • Real-time Updates           ││
│  │  • Style Extraction          │    │  • shadcn/ui Components        ││
│  │  • Content Generation        │◄───┤  • Review Console              ││
│  │  • Audit Logging             │    │  • Metrics Dashboard           ││
│  └──────────┬───────────────────┘    └────────────┬───────────────────┘│
│             │                                      │                     │
└─────────────┼──────────────────────────────────────┼─────────────────────┘
              │                                      │
              │                                      │
              ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure Layer                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Firestore     │  │  Cloud Storage  │  │  Secret Manager │         │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤         │
│  │ • Topics        │  │ • Files         │  │ • API Keys      │         │
│  │ • Scores        │  │ • Exports       │  │ • Credentials   │         │
│  │ • Content       │  │ • Backups       │  │                 │         │
│  │ • Audit Logs    │  │                 │  │                 │         │
│  │ • Metrics       │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐                               │
│  │  Cloud Run Jobs │  │   OpenAI API    │                               │
│  ├─────────────────┤  ├─────────────────┤                               │
│  │ • Scheduled     │  │ • GPT-4o-mini   │                               │
│  │   Ingestion     │  │ • Embeddings    │                               │
│  │ • Scoring       │  │ • Moderation    │                               │
│  │ • Learning      │  │                 │                               │
│  └─────────────────┘  └─────────────────┘                               │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Diagram

### Backend Components

```
backend/
│
├── src/
│   │
│   ├── core/                         # Foundation
│   │   ├── config.py                 # Pydantic settings from env
│   │   ├── logging.py                # Structured JSON logging
│   │   └── types.py                  # Common type definitions
│   │
│   ├── infra/                        # Infrastructure Services
│   │   ├── firestore_service.py      # Firestore client wrapper
│   │   │   • get_document()
│   │   │   • set_document()
│   │   │   • query_collection()
│   │   │   • batch_write()
│   │   │
│   │   ├── gcs_service.py            # Cloud Storage wrapper
│   │   │   • upload_bytes()
│   │   │   • download_bytes()
│   │   │   • list_blobs()
│   │   │
│   │   └── openai_service.py         # OpenAI API wrapper
│   │       • chat()                  # Chat completions
│   │       • embed()                 # Embeddings
│   │       • moderate()              # Content moderation
│   │
│   ├── content/                      # Domain Logic
│   │   │
│   │   ├── models.py                 # Data Models
│   │   │   • TopicCandidate
│   │   │   • TopicScore
│   │   │   • ContentOption
│   │   │   • PublishedContent
│   │   │   • AuditEvent
│   │   │   • ContentMetrics
│   │   │   • StyleProfile
│   │   │
│   │   ├── sources/                  # Topic Sources
│   │   │   ├── base.py               # Abstract source interface
│   │   │   ├── reddit.py             # Reddit scraper
│   │   │   ├── hackernews.py         # HN API client
│   │   │   ├── rss.py                # RSS feed parser
│   │   │   └── manual.py             # Manual entry handler
│   │   │
│   │   ├── processing/               # Processing Utilities
│   │   │   ├── entity_extraction.py  # NER using patterns
│   │   │   ├── clustering.py         # Topic categorization
│   │   │   └── deduplication.py      # Duplicate detection
│   │   │
│   │   ├── ingestion_service.py      # Topic Ingestion
│   │   │   • fetch_from_sources()
│   │   │   • process_raw_topics()
│   │   │   • save_topics()
│   │   │
│   │   ├── scoring_service.py        # Topic Scoring
│   │   │   • calculate_recency()
│   │   │   • calculate_velocity()
│   │   │   • calculate_audience_fit()
│   │   │   • apply_integrity_check()
│   │   │
│   │   ├── audit_service.py          # Audit Logging
│   │   │   • log_decision()
│   │   │   • fetch_audit_trail()
│   │   │
│   │   ├── script_refinement_service.py  # AI Script Editing
│   │   │   • tighten()               # Make concise
│   │   │   • casualize()             # Adjust tone
│   │   │   • regenerate()            # Fresh wording
│   │   │
│   │   └── style_extraction_service.py   # Style Learning
│   │       • extract_style_profile()
│   │       • apply_style()
│   │
│   ├── jobs/                         # Cloud Run Jobs
│   │   ├── topic_ingestion_job.py
│   │   ├── topic_scoring_job.py
│   │   ├── job_tracker.py
│   │   └── cloud_job_runner.py       # Entry point
│   │
│   └── cli/                          # Command Line Interface
│       └── main.py                   # Typer CLI app
│
└── tests/                            # Test Suite
    ├── content/                      # Unit tests
    ├── integration/                  # Integration tests
    └── fixtures/                     # Test data
```

### Frontend Components

```
frontend/
│
├── app/                              # App Router Pages
│   │
│   ├── today/                        # Topic Review
│   │   └── page.tsx
│   │
│   ├── scripts/                      # Script Editing
│   │   └── page.tsx
│   │
│   ├── styles/                       # Style Curation
│   │   └── page.tsx
│   │
│   ├── integrity/                    # Ethics Review
│   │   └── page.tsx
│   │
│   ├── history/                      # Audit Trail
│   │   └── page.tsx
│   │
│   ├── performance/                  # Metrics Dashboard
│   │   └── page.tsx
│   │
│   └── api/                          # API Routes
│       ├── topics/route.ts           # Topic operations
│       ├── options/route.ts          # Content options
│       ├── scripts/                  # Script operations
│       │   ├── [option_id]/route.ts
│       │   └── refine/route.ts
│       └── audit/route.ts            # Audit events
│
├── components/
│   ├── layout/                       # Layout Components
│   │   └── app-shell.tsx
│   │
│   ├── views/                        # View Components
│   │   ├── today-view.tsx
│   │   ├── scripts-view.tsx
│   │   ├── styles-view.tsx
│   │   └── history-view.tsx
│   │
│   └── ui/                           # shadcn/ui Components
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       └── ...
│
└── lib/                              # Utilities
    ├── firebase.ts                   # Firebase client setup
    ├── firebase-admin.ts             # Admin SDK setup
    ├── api-helpers.ts                # API utilities
    ├── api-types.ts                  # Type definitions
    └── validators.ts                 # Input validation
```

## Data Flow Diagrams

### 1. Topic Ingestion Flow

```
┌──────────┐
│ Sources  │
└────┬─────┘
     │ fetch
     ▼
┌──────────────────┐
│ Raw Topics       │
│ • title          │
│ • url            │
│ • platform       │
└────┬─────────────┘
     │ process
     ▼
┌──────────────────┐
│ Entity           │
│ Extraction       │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Topic            │
│ Clustering       │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Deduplication    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ TopicCandidate   │
│ [Firestore]      │
│ status: pending  │
└──────────────────┘
```

### 2. Scoring Flow

```
┌──────────────────┐
│ TopicCandidate   │
│ status: pending  │
└────┬─────────────┘
     │ query
     ▼
┌──────────────────┐
│ Recency Score    │
│ (age-based)      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Velocity Score   │
│ (trending)       │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Audience Fit     │
│ (cluster match)  │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Integrity Check  │
│ (penalty)        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ TopicScore       │
│ [Firestore]      │
│ • components     │
│ • weights        │
│ • reasoning      │
└──────────────────┘
```

### 3. Content Generation Flow

```
┌──────────────────┐
│ TopicCandidate   │
│ status: approved │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Load Prompts     │
│ • hook_v1        │
│ • script_v1      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Build Context    │
│ • topic          │
│ • entities       │
│ • cluster        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ OpenAI API       │
│ (GPT-4o-mini)    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ ContentOption    │
│ [Firestore]      │
│ • hooks (3x)     │
│ • script         │
└──────────────────┘
```

### 4. Review & Refinement Flow

```
┌──────────────────┐
│ ContentOption    │
│ [Firestore]      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Frontend UI      │
│ • Display        │
│ • Edit           │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Human Actions    │
│ • Select hook    │
│ • Edit script    │
│ • Refine (AI)    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Script           │
│ Refinement       │
│ Service          │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Updated Option   │
│ [Firestore]      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Mark Ready       │
│ status: ready    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ AuditEvent       │
│ [Firestore]      │
└──────────────────┘
```

### 5. Learning Flow

```
┌──────────────────┐
│ AuditEvent       │
│ • decisions      │
│ • reasons        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ ContentMetrics   │
│ • views          │
│ • engagement     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Learning         │
│ Service          │
│ • Analyze        │
│ • Correlate      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Weight           │
│ Adjustments      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Updated Scoring  │
│ [Config]         │
└──────────────────┘
```

## Technology Stack Details

### Backend Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.12+ | Modern Python with type hints |
| Dependency Mgmt | Poetry | Lock file, virtual envs |
| Web Framework | - | CLI-based, no server |
| Async Runtime | asyncio | Async I/O operations |
| Data Validation | Pydantic 2.x | Settings, models |
| CLI Framework | Typer | Command-line interface |
| Testing | pytest | Unit/integration tests |
| Code Quality | Black, Ruff, mypy | Formatting, linting, types |
| Database | Firestore | NoSQL document database |
| File Storage | Cloud Storage | Binary file storage |
| LLM API | OpenAI | Content generation |
| Secrets | Secret Manager | API key management |

### Frontend Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 16 | React framework |
| React Version | React 19 | UI library |
| Language | TypeScript 5 | Type safety |
| Styling | Tailwind CSS 4 | Utility-first CSS |
| UI Components | shadcn/ui | Accessible components |
| Database | Firestore (client) | Real-time data |
| Auth | Firebase Auth | User authentication |
| Forms | React Hook Form | Form management |
| Validation | Zod | Runtime type checking |
| Charts | Recharts | Data visualization |
| Testing | Jest | Unit/component tests |
| API Client | Fetch API | HTTP requests |

### Infrastructure Stack

| Service | Purpose | Location |
|---------|---------|----------|
| Firestore | Primary database | europe-west1 |
| Cloud Storage | File storage | europe-west2 |
| Cloud Run Jobs | Scheduled tasks | europe-west2 |
| Artifact Registry | Docker images | europe-west2 |
| Secret Manager | Sensitive data | Global |
| Cloud Logging | Log aggregation | Global |
| Cloud Monitoring | Metrics | Global |

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Security Layers                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Layer 1: Authentication                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • GCP Application Default Credentials                        │   │
│  │ • Firebase Auth (users)                                      │   │
│  │ • Service Account (Cloud Run)                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Layer 2: Authorization                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • IAM Roles (Firestore, GCS, Secret Manager)                │   │
│  │ • Firestore Security Rules                                  │   │
│  │ • API Route Protection                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Layer 3: Data Protection                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Secrets in Secret Manager (not env vars)                  │   │
│  │ • Firestore encryption at rest                              │   │
│  │ • TLS in transit                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Layer 4: Audit & Monitoring                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • AuditEvent collection (all decisions)                     │   │
│  │ • Cloud Logging (structured logs)                           │   │
│  │ • Cloud Monitoring (alerts)                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Current Scale (MVP)
- Topics: 100-1000 per day
- Content: 10-50 pieces per day
- Users: 1-5 concurrent
- LLM calls: 100-500 per day

### Growth Path
1. **Phase 1** (Current): Single project, manual scaling
2. **Phase 2** (Next): Cloud Run Jobs, auto-scaling
3. **Phase 3** (Future): Multi-region, caching, CDN

### Bottlenecks & Solutions

| Bottleneck | Solution |
|------------|----------|
| LLM rate limits | Semaphore, queue, retry with backoff |
| Firestore reads | Query optimization, caching, indexes |
| Large result sets | Pagination, cursor-based queries |
| Cold starts | Keep-alive pings, reserved instances |

---

For implementation details, see [README.md](README.md) and individual component documentation.

