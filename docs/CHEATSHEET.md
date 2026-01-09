# Content Engine - Developer Cheatsheet

Quick reference for common development tasks.

## Daily Development Workflow

### Starting Development

```bash
# Terminal 1: Frontend
cd frontend && npm run dev

# Terminal 2: Backend (as needed)
cd backend && poetry shell
```

### Stopping Development

```bash
# Stop frontend: Ctrl+C in Terminal 1
# Exit backend shell: exit or Ctrl+D
```

## Backend Commands

### Infrastructure

```bash
# Check connectivity
poetry run python -m src.cli.main check-infra

# Inspect Firestore data
python ../scripts/inspect_data.py
```

### Topic Management

```bash
# Ingest all sources
poetry run python -m src.cli.main ingest-topics

# Add manual topic
poetry run python -m src.cli.main add-topic \
  "Topic Title" \
  --cluster "ai-infra" \
  --url "https://example.com" \
  --notes "Optional notes"

# Score topics
poetry run python -m src.cli.main score-topics --limit 100

# Test scoring system
poetry run python -m src.cli.main test-scoring
```

### Style Management

```bash
# Add stylistic source
poetry run python -m src.cli.main add-style-source \
  --url "https://www.reddit.com/r/programming/" \
  --name "Programming Community"

# List style profiles
poetry run python -m src.cli.main list-style-profiles --status pending

# Approve profile
poetry run python -m src.cli.main approve-style-profile PROFILE_ID

# Reject profile
poetry run python -m src.cli.main reject-style-profile PROFILE_ID \
  --reason "Not on-brand"

# Extract styles
poetry run python -m src.cli.main extract-styles --source-id SOURCE_ID
```

## Testing

### Backend Tests

```bash
# All tests
poetry run pytest

# By marker
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e

# Specific file
poetry run pytest tests/content/test_ingestion_service.py -v

# With coverage
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Frontend Tests

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

## Code Quality

### Using Make (Recommended)

```bash
# Quick check (non-destructive)
make check

# Auto-fix issues
make fix

# Full QA
make qa

# Verify app works
make verify

# Before committing
make pre-commit

# Before pushing
make pre-push
```

### Backend (Manual)

```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# All checks
make backend-check
# OR manually:
poetry run black src/ tests/ && \
poetry run ruff check src/ tests/ && \
poetry run mypy src/ && \
poetry run pytest
```

### Frontend

```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build (checks for errors)
npm run build
```

## GCP Operations

### Authentication

```bash
# Login
gcloud auth login

# Set project
gcloud config set project hinsko-dev

# Application Default Credentials
gcloud auth application-default login --project=hinsko-dev

# Check current auth
gcloud auth list
gcloud config get-value project
```

### Resource Management

```bash
# List Firestore databases
gcloud firestore databases list --project=hinsko-dev

# List GCS buckets
gcloud storage buckets list --project=hinsko-dev

# List service accounts
gcloud iam service-accounts list --project=hinsko-dev

# List secrets
gcloud secrets list --project=hinsko-dev
```

### Secret Management

```bash
# Update OpenAI key
echo -n "sk-new-key" | gcloud secrets versions add openai-api-key \
  --data-file=- \
  --project=hinsko-dev

# Access secret
gcloud secrets versions access latest --secret=openai-api-key \
  --project=hinsko-dev
```

## Firestore Operations

### Using Python

```python
# In Python REPL
import asyncio
from src.infra import FirestoreService
from src.content.models import TOPIC_CANDIDATES_COLLECTION

firestore = FirestoreService()

# Get all topics
topics = await firestore.query_collection(
    TOPIC_CANDIDATES_COLLECTION,
    limit=10
)

# Get specific document
doc = await firestore.get_document(
    TOPIC_CANDIDATES_COLLECTION,
    "topic-id"
)
```

### Using gcloud

```bash
# Export data (requires Firestore export API)
gcloud firestore export gs://your-bucket/backup \
  --project=hinsko-dev

# Import data
gcloud firestore import gs://your-bucket/backup \
  --project=hinsko-dev
```

## Frontend Development

### Key Routes

```
/                      # Home (redirects to /today)
/today                 # Topic review
/scripts               # Script editing
/styles                # Style curation
/integrity             # Ethics review
/history               # Audit trail
/performance           # Metrics dashboard
```

### API Routes

```
GET  /api/topics                    # Fetch topics
POST /api/topics                    # Record decision
GET  /api/options                   # Fetch content options
POST /api/options                   # Update status
POST /api/scripts/refine            # AI refinement
GET  /api/audit                     # Audit events
GET  /api/performance               # Metrics
```

## Debugging

### Backend Debug Mode

```bash
# Verbose logging
LOG_LEVEL=DEBUG poetry run python -m src.cli.main ingest-topics

# Python debugger
poetry run python -m pdb -m src.cli.main ingest-topics
```

### Frontend Debug

```javascript
// Browser console
console.log(data)

// React DevTools
// Install extension, then inspect components
```

### Check Data Flow

```bash
# 1. Ingest topics
cd backend
poetry run python -m src.cli.main ingest-topics

# 2. Verify in Firestore
python ../scripts/inspect_data.py

# 3. Check frontend
# Open http://localhost:3000/today

# 4. Check browser console for errors
# F12 > Console tab
```

## Common Troubleshooting

### Clear Local Data

```bash
# Backend: No local data (uses Firestore)

# Frontend: Clear browser storage
# F12 > Application > Storage > Clear site data
```

### Reset Dependencies

```bash
# Backend
cd backend
rm -rf .venv poetry.lock
poetry install

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Fix Permissions

```bash
# Re-authenticate
gcloud auth application-default login --project=hinsko-dev

# Check quota project
cat ~/.config/gcloud/application_default_credentials.json | \
  jq -r '.quota_project_id'
# Should be: hinsko-dev
```

## Environment Variables

### Backend (.env)

```bash
GCP_PROJECT_ID=hinsko-dev
FIRESTORE_DATABASE_ID=main-db
DEFAULT_REGION=europe-west2
GCS_BUCKET_NAME=content-engine-storage-hinsko-dev
OPENAI_API_KEY=sk-...
ENVIRONMENT=local
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_FIREBASE_PROJECT_ID=hinsko-dev
NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db
OPENAI_API_KEY=sk-...
```

## Git Workflow

### Committing Changes

```bash
# Stage changes
git add .

# Check status
git status

# Commit
git commit -m "feat: add new feature"

# Push
git push origin branch-name
```

### Branches

```bash
# Create branch
git checkout -b feature/new-feature

# List branches
git branch -a

# Switch branch
git checkout main

# Delete branch
git branch -d feature/old-feature
```

## Performance Optimization

### Backend

```bash
# Profile code
poetry run python -m cProfile -o profile.stats -m src.cli.main ingest-topics
poetry run python -m pstats profile.stats

# Check async tasks
# Look for bottlenecks in concurrent operations
```

### Frontend

```bash
# Build analysis
npm run build
# Check bundle size

# Lighthouse audit
# F12 > Lighthouse > Generate report
```

## Deployment (Coming Soon)

### Backend (Cloud Run Jobs)

```bash
# Build image
docker build -t content-engine-backend .

# Tag for Artifact Registry
docker tag content-engine-backend \
  europe-west2-docker.pkg.dev/hinsko-dev/content-engine-images/main:latest

# Push
docker push europe-west2-docker.pkg.dev/hinsko-dev/content-engine-images/main:latest
```

### Frontend (Vercel/Cloud Run)

```bash
# Build
npm run build

# Deploy (varies by platform)
vercel deploy
```

## Useful Aliases

Add to your shell config (~/.bashrc or ~/.zshrc):

```bash
# Content Engine aliases
alias ce-backend="cd ~/path/to/content-engine/backend"
alias ce-frontend="cd ~/path/to/content-engine/frontend"
alias ce-ingest="ce-backend && poetry run python -m src.cli.main ingest-topics"
alias ce-check="ce-backend && poetry run python -m src.cli.main check-infra"
alias ce-test="ce-backend && poetry run pytest"
alias ce-inspect="python ~/path/to/content-engine/scripts/inspect_data.py"
```

## Quick Links

- **Frontend**: http://localhost:3000
- **Firebase Console**: https://console.firebase.google.com/project/hinsko-dev
- **GCP Console**: https://console.cloud.google.com/home/dashboard?project=hinsko-dev
- **OpenAI Dashboard**: https://platform.openai.com/usage

---

**Pro tip**: Keep this file open in a separate editor window for quick reference during development! 💡

