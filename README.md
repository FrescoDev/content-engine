# Content Engine

AI-powered content intelligence and production system that discovers high-engagement topics, generates platform-native content, and learns from performance.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [GCP Setup](#gcp-setup)
- [Running the Application](#running-the-application)
  - [Local Development](#local-development)
  - [CLI Commands](#cli-commands)
  - [Frontend Development](#frontend-development)
- [Testing](#testing)
  - [Backend Tests](#backend-tests)
  - [Frontend Tests](#frontend-tests)
  - [Manual Testing](#manual-testing)
- [How It Works](#how-it-works)
  - [Data Flow](#data-flow)
  - [Core Concepts](#core-concepts)
  - [System Components](#system-components)
- [Workflows](#workflows)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Documentation](#documentation)

---

## Overview

Content Engine is a self-improving content intelligence and production system designed for modern media creators. It:

- **Discovers** high-engagement topics from multiple sources (Reddit, Hacker News, RSS feeds, manual entries)
- **Scores & ranks** topics using recency, velocity, audience fit, and integrity metrics
- **Generates** content options (hooks, scripts) using LLMs with customizable prompts
- **Provides** a review console for human-in-the-loop decision making
- **Learns** from performance metrics and human choices to improve over time
- **Maintains** full audit trail for transparency and system improvement

### Key Features

- **Multi-source ingestion**: Automated topic discovery from diverse platforms
- **Intelligent scoring**: Composite scoring with configurable weights
- **LLM-powered generation**: AI-driven content creation with prompt versioning
- **Human-in-the-loop**: Review and approval workflow with reason capture
- **Style learning**: Analyze and replicate successful content styles
- **Performance tracking**: Metrics collection and learning feedback loop
- **Full observability**: Complete audit trail for all decisions

---

## Architecture

### Tech Stack

**Backend:**
- Python 3.12+
- Poetry (dependency management)
- Google Cloud Platform:
  - Firestore (database)
  - Cloud Storage (file storage)
  - Cloud Run Jobs (scheduled tasks)
  - Secret Manager (API keys)
- OpenAI API (LLM operations)
- Async/await patterns throughout

**Frontend:**
- Next.js 16 (App Router)
- React 19
- TypeScript
- Firebase SDK (Firestore, Auth)
- Tailwind CSS + shadcn/ui
- Real-time updates

**Infrastructure:**
- CLI-based backend (no server)
- Frontend connects directly to Firebase
- Cloud Run Jobs for scheduled operations
- GCP for all cloud services

### Design Principles

1. **Clean separation**: Core infra, domain models, services, jobs
2. **Type safety**: Full type hints in Python, TypeScript in frontend
3. **Async-first**: Async/await for all I/O operations
4. **Observable**: Structured logging and audit events
5. **Testable**: Unit, integration, and E2E tests
6. **Configurable**: Environment-based configuration

---

## Quick Start

### TL;DR

```bash
# Backend (one-time setup)
cd backend
poetry install
cp .env.example .env  # Edit with your config
poetry run python -m src.cli.main check-infra

# Frontend (development)
cd frontend
npm install
cp .env.local.example .env.local  # Edit with Firebase config
npm run dev  # http://localhost:3000

# Run topic ingestion
cd backend
poetry run python -m src.cli.main ingest-topics
```

---

## Project Structure

```
content-engine/
├── backend/                    # Python backend
│   ├── src/
│   │   ├── core/              # Config, logging, types
│   │   │   ├── config.py      # Pydantic settings
│   │   │   ├── logging.py     # Structured logging
│   │   │   └── types.py       # Common types
│   │   ├── infra/             # Infrastructure services
│   │   │   ├── firestore_service.py
│   │   │   ├── gcs_service.py
│   │   │   └── openai_service.py
│   │   ├── content/           # Domain models & services
│   │   │   ├── models.py      # Data models (TopicCandidate, etc.)
│   │   │   ├── ingestion_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── sources/       # Topic sources
│   │   │   │   ├── reddit.py
│   │   │   │   ├── hackernews.py
│   │   │   │   ├── rss.py
│   │   │   │   └── manual.py
│   │   │   └── processing/    # Processing utilities
│   │   │       ├── clustering.py
│   │   │       ├── deduplication.py
│   │   │       └── entity_extraction.py
│   │   ├── jobs/              # Cloud Run Jobs
│   │   │   ├── topic_ingestion_job.py
│   │   │   ├── topic_scoring_job.py
│   │   │   └── cloud_job_runner.py
│   │   └── cli/               # CLI commands
│   │       └── main.py
│   ├── tests/                 # Tests
│   │   ├── content/           # Unit tests
│   │   ├── integration/       # Integration tests
│   │   └── fixtures/          # Test fixtures
│   ├── scripts/               # Utility scripts
│   ├── pyproject.toml         # Poetry dependencies
│   └── pytest.ini             # Test configuration
│
├── frontend/                  # Next.js frontend
│   ├── app/                   # App Router pages
│   │   ├── today/            # Topic review
│   │   ├── scripts/          # Script review & editing
│   │   ├── styles/           # Style curation
│   │   ├── integrity/        # Ethics review
│   │   ├── history/          # Audit trail
│   │   ├── performance/      # Metrics dashboard
│   │   └── api/              # API routes
│   ├── components/
│   │   ├── layout/           # App shell
│   │   ├── views/            # View components
│   │   └── ui/               # shadcn/ui components
│   ├── lib/                   # Utilities
│   │   ├── firebase.ts       # Firebase setup
│   │   ├── firebase-admin.ts # Admin SDK
│   │   └── api-helpers.ts    # API utilities
│   └── package.json
│
├── docs/                      # Documentation
│   ├── GCP_SETUP.md          # GCP infrastructure setup
│   ├── LOCAL_SETUP.md        # Local development guide
│   └── MANUAL_TESTING_GUIDE.md
│
├── scripts/                   # Project-level scripts
│   ├── setup_gcp.sh          # Automated GCP setup
│   ├── verify_gcp_setup.sh   # Verification script
│   └── inspect_data.py       # Data inspection tool
│
└── README.md                  # This file
```

---

## Setup Guide

### Prerequisites

1. **Python 3.12+** (for backend)
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Poetry** (Python dependency management)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Node.js 18+** (for frontend)
   ```bash
   node --version  # Should be 18 or higher
   npm --version
   ```

4. **Google Cloud SDK** (gcloud CLI)
   ```bash
   # Install: https://cloud.google.com/sdk/docs/install
   gcloud --version
   ```

5. **GCP Project** with billing enabled
   - Project ID: `hinsko-dev` (or your project)
   - Billing account linked

6. **OpenAI API Key** (for LLM operations)
   - Get from: https://platform.openai.com/api-keys

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   poetry install
   ```

2. **Create environment file:**
   ```bash
   cat > .env << EOF
   GCP_PROJECT_ID=hinsko-dev
   FIRESTORE_DATABASE_ID=main-db
   DEFAULT_REGION=europe-west2
   GCS_BUCKET_NAME=content-engine-storage-hinsko-dev
   OPENAI_API_KEY=your-openai-key  # Optional if using Secret Manager
   ENVIRONMENT=local
   LOG_LEVEL=INFO
   EOF
   ```

3. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud config set project hinsko-dev
   gcloud auth application-default login --project=hinsko-dev
   ```

4. **Verify setup:**
   ```bash
   poetry run python -m src.cli.main check-infra
   ```
   Expected output:
   ```
   ✓ Firestore service initialized
   ✓ GCS service initialized
   Infrastructure check complete
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file:**
   ```bash
   cat > .env.local << EOF
   # Required
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=hinsko-dev
   NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db

   # Optional (for Firebase client SDK features)
   NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=hinsko-dev.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=hinsko-dev.appspot.com
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

   # For script refinement features
   OPENAI_API_KEY=your-openai-key
   EOF
   ```

3. **Verify setup:**
   ```bash
   npm run dev
   ```
   Access at: http://localhost:3000

### GCP Setup

Complete GCP infrastructure setup is required before running the application.

#### Automated Setup

```bash
cd content-engine
./scripts/setup_gcp.sh
```

This script creates:
- Firestore database (`main-db`)
- GCS bucket (`content-engine-storage-hinsko-dev`)
- Artifact Registry repository (`content-engine-images`)
- Service account (`content-engine-runner`)
- Secret Manager secret (`openai-api-key`)
- Required IAM roles

#### Manual Setup

See [docs/GCP_SETUP.md](docs/GCP_SETUP.md) for detailed manual setup instructions.

#### Verification

```bash
./scripts/verify_gcp_setup.sh
```

Or manually:
```bash
# Check Firestore
gcloud firestore databases list --project=hinsko-dev

# Check GCS
gcloud storage buckets list --project=hinsko-dev

# Check service account
gcloud iam service-accounts describe content-engine-runner@hinsko-dev.iam.gserviceaccount.com
```

---

## Running the Application

### Local Development

The backend is CLI-based and doesn't run as a server. The frontend connects directly to Firebase/Firestore.

**Terminal 1 - Frontend (development server):**
```bash
cd frontend
npm run dev
```
Access at: http://localhost:3000

**Terminal 2 - Backend operations (as needed):**
```bash
cd backend

# Check infrastructure
poetry run python -m src.cli.main check-infra

# Ingest topics from sources
poetry run python -m src.cli.main ingest-topics

# Score topics
poetry run python -m src.cli.main score-topics

# Add manual topic
poetry run python -m src.cli.main add-topic \
  "OpenAI Releases GPT-5" \
  --cluster "ai-infra" \
  --url "https://example.com/news"
```

### CLI Commands

The backend provides a rich CLI for all operations:

#### Infrastructure

```bash
# Check connectivity to Firestore, GCS
poetry run python -m src.cli.main check-infra
```

#### Topic Management

```bash
# Ingest topics from all sources (Reddit, HN, RSS)
poetry run python -m src.cli.main ingest-topics

# Add manual topic
poetry run python -m src.cli.main add-topic \
  "Topic Title" \
  --cluster "ai-infra" \
  --url "https://source.com" \
  --notes "Optional notes"

# Score topics
poetry run python -m src.cli.main score-topics \
  --limit 100 \
  --min-age-hours 0 \
  --status pending
```

#### Style Management

```bash
# Add stylistic source (auto-fetches content and extracts styles)
poetry run python -m src.cli.main add-style-source \
  --url "https://www.reddit.com/r/hiphopheads/" \
  --name "Hip-Hop Community" \
  --tags "hip-hop,culture"

# List style profiles
poetry run python -m src.cli.main list-style-profiles \
  --status pending \
  --limit 20

# Approve style profile
poetry run python -m src.cli.main approve-style-profile \
  profile-id \
  --curator "user-id" \
  --notes "Great tone and style"

# Reject style profile
poetry run python -m src.cli.main reject-style-profile \
  profile-id \
  --curator "user-id" \
  --reason "Not on-brand"

# Extract styles from content
poetry run python -m src.cli.main extract-styles \
  --source-id source-123 \
  --limit 10
```

#### Testing & Validation

```bash
# Test scoring system
poetry run python -m src.cli.main test-scoring

# Inspect Firestore data
python scripts/inspect_data.py
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build
npm start

# Linting
npm run lint

# Tests
npm test
npm run test:watch
npm run test:coverage
```

---

## Testing

### Backend Tests

The backend has comprehensive test coverage with unit, integration, and E2E tests.

#### Run All Tests

```bash
cd backend
poetry run pytest
```

#### Test Categories

```bash
# Unit tests only
poetry run pytest -m unit

# Integration tests
poetry run pytest -m integration

# End-to-end tests
poetry run pytest -m e2e

# Slow tests
poetry run pytest -m slow
```

#### Specific Test Files

```bash
# Test topic ingestion
poetry run pytest tests/content/test_ingestion_service.py -v

# Test scoring
poetry run pytest tests/content/test_scoring_service.py -v

# Test sources
poetry run pytest tests/content/sources/ -v
```

#### Coverage Reports

```bash
# Terminal report
poetry run pytest --cov=src --cov-report=term-missing

# HTML report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### Manual Testing

See [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) for comprehensive manual testing procedures.

#### Quick Manual Test Flow

1. **Infrastructure check:**
   ```bash
   cd backend
   poetry run python -m src.cli.main check-infra
   ```

2. **Ingest topics:**
   ```bash
   poetry run python -m src.cli.main ingest-topics
   ```

3. **Inspect data:**
   ```bash
   python scripts/inspect_data.py
   ```

4. **Check frontend:**
   ```bash
   cd frontend
   npm run dev
   # Visit http://localhost:3000/today
   ```

5. **Verify topic display:**
   - Topics should appear in "Today" view
   - Check status, cluster, entities
   - Verify scoring components

---

## How It Works

### Data Flow

```
┌─────────────────┐
│  Topic Sources  │  Reddit, HN, RSS, Manual
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Ingestion     │  Fetch, parse, deduplicate
│    Service      │  Extract entities, cluster
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Firestore     │  Store TopicCandidate
│ topic_candidates│  status: pending
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Scoring       │  Recency, velocity, fit
│    Service      │  Integrity check
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Firestore     │  Store TopicScore
│  topic_scores   │  with components
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend UI    │  Review & approve
│  (Human Loop)   │  Reject with reason
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      LLM        │  Generate hooks
│   Generation    │  Generate scripts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Firestore     │  Store ContentOption
│ content_options │  Multiple variants
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend UI    │  Select/edit script
│  (Review)       │  Refine with AI
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Firestore     │  PublishedContent
│published_content│  Ready for platform
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Platform      │  YouTube, TikTok
│   Publishing    │  (future integration)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Metrics       │  Performance data
│   Collection    │  Views, engagement
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Learning      │  Adjust weights
│    Service      │  Improve prompts
└─────────────────┘
```

### Core Concepts

#### 1. Topic Candidates

Raw topics discovered from sources. Each has:
- **Source**: Where it came from (reddit, hackernews, rss, manual)
- **Title**: The topic description
- **Entities**: Extracted names, companies, concepts
- **Cluster**: Category (ai-infra, business-socioeconomic, etc.)
- **Status**: pending, approved, rejected, deferred

#### 2. Topic Scoring

Multi-component scoring system:
- **Recency** (0-1): How fresh is the topic?
- **Velocity** (0-1): How fast is it trending?
- **Audience Fit** (0-1): Matches target audience?
- **Integrity Penalty** (0 to -0.5): Quality/ethics check

**Formula:**
```
score = (w_recency × recency) + (w_velocity × velocity) + 
        (w_audience × audience_fit) + integrity_penalty

Default weights: recency=0.3, velocity=0.4, audience_fit=0.3
```

#### 3. Content Options

LLM-generated content variations:
- **Hooks**: Attention-grabbing opening lines
- **Scripts**: Full short-form video scripts
- **Variants**: Different tones and approaches

Each option includes:
- Prompt version used
- Model used (gpt-4o-mini, etc.)
- Generation metadata

#### 4. Audit Events

Complete decision trail:
- **System Decision**: What the AI recommended
- **Human Action**: What the curator chose
- **Reason**: Why (with codes)
- **Actor**: Who made the decision

This enables:
- Transparency
- Learning from human feedback
- Performance analysis

#### 5. Style Profiles

Learned writing styles from successful content:
- **Tone**: Casual, professional, energetic, etc.
- **Structure**: How content is organized
- **Vocabulary**: Word choices and patterns
- **Hooks**: Opening strategies that work

Extracted using LLMs and can be applied to new content.

### System Components

#### Backend Services

**Core Infrastructure:**
- `FirestoreService`: Database operations with async support
- `GCSService`: File storage and retrieval
- `OpenAIService`: LLM API wrapper with rate limiting

**Domain Services:**
- `TopicIngestionService`: Fetches and processes topics
- `ScoringService`: Calculates topic scores
- `AuditService`: Records decision events
- `ScriptRefinementService`: AI-powered script editing

**Sources:**
- `RedditSource`: r/programming, r/artificial, etc.
- `HackerNewsSource`: Top stories from HN
- `RSSSource`: News feeds, blogs
- `ManualSource`: Human-added topics

**Processing:**
- `EntityExtractor`: Identifies key entities in text
- `TopicClusterer`: Categorizes topics
- `Deduplicator`: Prevents duplicate topics

#### Frontend Views

- **Today** (`/today`): Review and approve/reject topics
- **Scripts** (`/scripts`): Edit and refine content options
- **Styles** (`/styles`): Curate style profiles
- **Integrity** (`/integrity`): Ethics review queue
- **History** (`/history`): Audit trail and decisions
- **Performance** (`/performance`): Metrics dashboard

---

## Workflows

### 1. Topic Discovery Workflow

```bash
# Automated (scheduled)
poetry run python -m src.cli.main ingest-topics

# Or manual
poetry run python -m src.cli.main add-topic \
  "AI Safety Summit Announced" \
  --cluster "ai-infra" \
  --url "https://news.com/ai-summit"
```

**What happens:**
1. Sources fetched (Reddit, HN, RSS)
2. Content parsed and normalized
3. Entities extracted (companies, people, concepts)
4. Topic clustered by category
5. Deduplication by URL and similarity
6. Saved to Firestore with status=pending

### 2. Topic Scoring Workflow

```bash
poetry run python -m src.cli.main score-topics --limit 100
```

**What happens:**
1. Fetch pending topics from Firestore
2. For each topic:
   - Calculate recency score (age-based decay)
   - Calculate velocity score (trending indicators)
   - Calculate audience fit (cluster match)
   - Apply integrity penalty (quality check)
3. Store TopicScore with components
4. Frontend displays ranked topics

### 3. Topic Review Workflow

**In Frontend** (`/today`):
1. View scored topics (highest first)
2. Review title, source, cluster, entities
3. See score breakdown
4. **Approve**: Topic moves to content generation
5. **Reject**: Select reason (off-brand, low-quality, speculative)
6. Audit event recorded with decision

### 4. Content Generation Workflow

**Triggered after approval:**
1. Load active prompt templates
2. For each prompt:
   - Build prompt with topic context
   - Call OpenAI API
   - Parse response
3. Save ContentOption instances
4. Link to original topic

### 5. Script Review & Refinement Workflow

**In Frontend** (`/scripts`):
1. View topics with generated options
2. **Select Hook**: Choose from hook options
3. **Edit Script**: Manual editing with auto-save
4. **AI Refinement**:
   - **Tighten**: Make more concise
   - **Casual**: Adjust tone
   - **Regenerate**: Fresh wording
5. **Mark Ready**: Flag as ready for publication
6. **Ethics Review**: Flag for manual review

### 6. Style Learning Workflow

```bash
# Add source
poetry run python -m src.cli.main add-style-source \
  --url "https://www.reddit.com/r/hiphopheads/"

# Extract styles
poetry run python -m src.cli.main extract-styles \
  --source-id source-123

# Review in frontend (/styles)
# Approve/reject profiles

# Apply to new content
# (automatic in content generation)
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied (Firestore)

**Error:**
```
google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions
```

**Solution:**
```bash
# Check Application Default Credentials
gcloud auth application-default print-access-token

# Check quota project
cat ~/.config/gcloud/application_default_credentials.json | jq -r '.quota_project_id'
# Should be: hinsko-dev

# Re-authenticate with correct project
gcloud auth application-default login --project=hinsko-dev
```

#### 2. Missing Environment Variables

**Error:**
```
Error: NEXT_PUBLIC_FIREBASE_PROJECT_ID environment variable is required
```

**Solution:**
```bash
cd frontend
cat > .env.local << EOF
NEXT_PUBLIC_FIREBASE_PROJECT_ID=hinsko-dev
NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db
EOF
```

#### 3. Firestore Database Not Found

**Error:**
```
Database main-db not found
```

**Solution:**
```bash
# List databases
gcloud firestore databases list --project=hinsko-dev

# Create if missing
gcloud firestore databases create \
  --database=main-db \
  --location=europe-west1 \
  --type=firestore-native \
  --project=hinsko-dev
```

#### 4. Poetry Not Found

**Error:**
```
poetry: command not found
```

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

#### 5. Tests Failing

**Error:**
```
ImportError: No module named 'src'
```

**Solution:**
```bash
# Ensure pytest.ini has correct pythonpath
cd backend
poetry run pytest  # Use poetry run, not bare pytest
```

#### 6. Frontend Build Errors

**Error:**
```
Module not found: Can't resolve 'firebase'
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Debug Tips

1. **Check logs:**
   ```bash
   # Backend logs (structured JSON in production)
   LOG_LEVEL=DEBUG poetry run python -m src.cli.main ingest-topics
   
   # Frontend logs
   # Check browser console (F12)
   ```

2. **Inspect Firestore data:**
   ```bash
   python scripts/inspect_data.py
   ```

3. **Test individual components:**
   ```bash
   # Test Firestore connection
   poetry run python -m src.cli.main check-infra
   
   # Test single source
   poetry run pytest tests/content/sources/test_reddit.py -v
   ```

4. **Check API quotas:**
   ```bash
   # OpenAI usage
   # Visit: https://platform.openai.com/usage
   
   # GCP quotas
   gcloud compute project-info describe --project=hinsko-dev
   ```

### Getting Help

1. Check [docs/](docs/) folder for detailed guides
2. Review test files for usage examples
3. Check audit logs in Firestore for system behavior
4. Enable DEBUG logging for detailed output

---

## Contributing

### Code Style

**Python:**
- Black formatter (line length: 100)
- Type hints everywhere
- Docstrings for public functions
- Async/await for I/O operations

**TypeScript:**
- ESLint + Next.js config
- Functional components
- Type all props and return values

### Running Quality Checks

**Using Make (Recommended)**:
```bash
# Quick check (non-destructive)
make check

# Auto-fix issues
make fix

# Full QA before pushing
make qa

# Verify app still works
make verify
```

See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for complete Makefile documentation.

**Manual Commands**:
```bash
# Backend
cd backend
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
poetry run pytest --cov=src

# Frontend
cd frontend
npm run lint
npm run test
npm run build  # Check for build errors
```

### Testing Requirements

- **Unit tests** for all new services
- **Integration tests** for Firestore operations
- **E2E tests** for critical workflows
- **100% test pass rate** required

### Pull Request Checklist

**Automated Checks**:
```bash
make pre-push    # Runs all checks + verification
```

**Manual Checklist**:
- [ ] All tests passing (`make test`)
- [ ] No linting errors (`make lint`)
- [ ] Type checking passed (`make type-check`)
- [ ] Code formatted (`make format`)
- [ ] App verified working (`make verify`)
- [ ] Type hints added (Python)
- [ ] TypeScript types defined
- [ ] Docstrings/comments for complex logic
- [ ] Manual testing completed
- [ ] README updated if needed

---

## Documentation

### Core Documentation

- **[GCP_SETUP.md](docs/GCP_SETUP.md)**: Complete GCP infrastructure setup guide
- **[LOCAL_SETUP.md](docs/LOCAL_SETUP.md)**: Local development quick reference
- **[MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md)**: Comprehensive testing procedures

### Project Specifications

Located in `../project-specs/next-gen-media-production/`:
- **vision.md**: Vision, strategy, and OKRs
- **backend.md**: Backend architecture and implementation plan
- **journeys.md**: User journeys and UX specifications

### API Documentation

**Backend CLI:**
```bash
poetry run python -m src.cli.main --help
```

**Frontend API Routes:**
- `GET /api/topics` - Fetch topics with scores
- `POST /api/topics` - Record topic decision
- `GET /api/options` - Fetch content options
- `POST /api/options` - Mark script ready/flag for review
- `POST /api/scripts/refine` - AI script refinement
- `GET /api/audit` - Fetch audit events
- `GET /api/performance` - Performance metrics

### Data Models

See `backend/src/content/models.py` for complete model definitions:
- `TopicCandidate`
- `TopicScore`
- `ContentOption`
- `PublishedContent`
- `AuditEvent`
- `ContentMetrics`
- `PromptDefinition`
- `StylisticSource`
- `StyleProfile`

---

## Roadmap

### Phase 1: Foundation ✅
- [x] Core infrastructure (Firestore, GCS, OpenAI)
- [x] Topic ingestion from multiple sources
- [x] Scoring system with configurable weights
- [x] Frontend review console
- [x] Audit trail

### Phase 2: Intelligence (Current)
- [x] LLM content generation
- [x] Script refinement service
- [x] Style extraction and learning
- [ ] A/B testing for prompts
- [ ] Performance-based weight adjustment

### Phase 3: Automation
- [ ] Cloud Run Jobs scheduling
- [ ] Automated content generation pipeline
- [ ] Platform publishing integration (YouTube, TikTok)
- [ ] Metrics collection from platforms
- [ ] Weekly learning job

### Phase 4: Scale
- [ ] Multi-user support
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard
- [ ] Custom source integrations
- [ ] API for external integrations

---

## License

Private project. All rights reserved.

---

## Contact

For questions or issues, contact the development team.

---

**Built with ❤️ for modern content creators**
