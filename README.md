# Content Engine

AI-assisted, high-integrity media engine that continuously discovers high-engagement topics, auto-drafts platform-native content, and learns from performance.

## Overview

Content Engine is a self-improving content intelligence and production system that:
- Discovers topics from multiple sources (YouTube, TikTok, X, news feeds)
- Scores and ranks topics using recency, velocity, audience fit, and integrity metrics
- Generates content options (hooks, scripts) using LLMs
- Provides a review console for human-in-the-loop decision making
- Learns from performance metrics and human choices

## Architecture

### Backend (`backend/`)
- Python 3.12+ with Poetry
- GCP services (Firestore, GCS, Cloud Run Jobs)
- OpenAI integration
- Domain models for topics, content, audit events, metrics
- Async job processing

### Frontend (`frontend/`)
- Next.js 16 with TypeScript
- Tailwind CSS + shadcn/ui components
- Firebase SDK for real-time data
- Responsive, keyboard-first UI

## Quick Start

### Backend Setup

```bash
cd backend
poetry install
cp .env.example .env
# Edit .env with your configuration
```

### Frontend Setup

```bash
cd frontend
npm install
# Configure Firebase in lib/firebase.ts
npm run dev
```

## Project Structure

```
content-engine/
├── backend/          # Python backend
│   ├── src/
│   │   ├── core/     # Config, logging, types
│   │   ├── infra/    # Firestore, GCS, OpenAI services
│   │   ├── content/  # Domain models
│   │   ├── jobs/     # Cloud Run Jobs
│   │   └── cli/      # CLI commands
│   └── pyproject.toml
├── frontend/         # Next.js frontend
│   ├── app/          # App Router pages
│   ├── components/   # React components
│   └── lib/          # Utilities
└── README.md
```

## Documentation

### Project Specifications
See the project specs in `project-specs/next-gen-media-production/`:
- `vision.md` - Vision and strategy
- `backend.md` - Backend architecture and implementation plan
- `journeys.md` - User journeys and UX specifications

### Setup & Configuration
- [`GCP_SETUP.md`](GCP_SETUP.md) - Complete guide for setting up GCP resources
- [`VERIFICATION_RESULTS.md`](VERIFICATION_RESULTS.md) - GCP connectivity verification results
- [`FUNCTIONALITY_VERIFICATION.md`](FUNCTIONALITY_VERIFICATION.md) - Functionality test results and data inspection

## License

Private project.

