# Content Engine - Quick Start Guide

**Get up and running in 15 minutes**

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Python 3.12+ installed
- [ ] Poetry installed
- [ ] Node.js 18+ installed
- [ ] Google Cloud SDK (gcloud) installed
- [ ] GCP project with billing enabled
- [ ] OpenAI API key

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
cd content-engine
```

### 2. Backend Setup (5 minutes)

```bash
# Install dependencies
cd backend
poetry install

# Create environment file
cat > .env << 'EOF'
GCP_PROJECT_ID=hinsko-dev
FIRESTORE_DATABASE_ID=main-db
DEFAULT_REGION=europe-west2
GCS_BUCKET_NAME=content-engine-storage-hinsko-dev
OPENAI_API_KEY=sk-your-key-here
ENVIRONMENT=local
LOG_LEVEL=INFO
EOF

# Edit .env and replace:
# - hinsko-dev with your GCP project ID
# - sk-your-key-here with your OpenAI API key
```

### 3. GCP Authentication (2 minutes)

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project YOUR-PROJECT-ID

# Setup Application Default Credentials
gcloud auth application-default login --project=YOUR-PROJECT-ID
```

### 4. GCP Infrastructure Setup (5 minutes)

```bash
# Return to project root
cd ..

# Run automated setup
./scripts/setup_gcp.sh
```

This creates:
- Firestore database
- GCS bucket
- Service account
- IAM roles
- Secret Manager secrets

### 5. Verify Backend (1 minute)

```bash
cd backend
poetry run python -m src.cli.main check-infra
```

Expected output:
```
✓ Firestore service initialized
✓ GCS service initialized
Infrastructure check complete
```

### 6. Frontend Setup (3 minutes)

```bash
cd ../frontend
npm install

# Create environment file
cat > .env.local << 'EOF'
NEXT_PUBLIC_FIREBASE_PROJECT_ID=hinsko-dev
NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db
OPENAI_API_KEY=sk-your-key-here
EOF

# Edit .env.local and replace values
```

### 7. Start Development (1 minute)

**Terminal 1 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit: http://localhost:3000

**Terminal 2 - Backend operations:**
```bash
cd backend
poetry run python -m src.cli.main ingest-topics
```

## First Usage

### Ingest Your First Topics

```bash
cd backend

# Ingest from all sources (Reddit, HN, RSS)
poetry run python -m src.cli.main ingest-topics

# Or add a manual topic
poetry run python -m src.cli.main add-topic \
  "OpenAI Launches New Model" \
  --cluster "ai-infra" \
  --url "https://openai.com/blog/new-model"
```

### View Topics in Frontend

1. Open http://localhost:3000/today
2. You'll see discovered topics with scores
3. Review and approve/reject topics
4. Approved topics move to content generation

### Generate Content

```bash
# Score topics (if not already scored)
poetry run python -m src.cli.main score-topics

# Content generation happens after approval in frontend
# Or trigger manually (coming soon)
```

### Review Scripts

1. Navigate to http://localhost:3000/scripts
2. View generated hooks and scripts
3. Edit scripts manually or use AI refinement
4. Mark as ready for publication

## Verification

Run the verification script:

```bash
./scripts/verify_setup.sh
```

This checks:
- All prerequisites installed
- GCP configuration correct
- Backend dependencies installed
- Frontend dependencies installed
- Connectivity to Firestore and GCS

## Common First-Run Issues

### Issue: "poetry: command not found"

**Solution:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### Issue: "Permission denied" (Firestore)

**Solution:**
```bash
gcloud auth application-default login --project=YOUR-PROJECT-ID
```

### Issue: "Database not found"

**Solution:**
```bash
./scripts/setup_gcp.sh
# Or manually:
gcloud firestore databases create \
  --database=main-db \
  --location=europe-west1 \
  --type=firestore-native \
  --project=YOUR-PROJECT-ID
```

### Issue: Frontend shows "No topics"

**Solution:**
```bash
cd backend
poetry run python -m src.cli.main ingest-topics
python ../scripts/inspect_data.py  # Verify topics in Firestore
```

## Next Steps

1. **Explore the UI:**
   - Today: Review topics
   - Scripts: Edit content
   - Styles: Curate writing styles
   - History: View audit trail
   - Performance: Metrics dashboard

2. **Configure sources:**
   - Edit `backend/src/content/sources/` to customize
   - Add custom RSS feeds
   - Adjust Reddit subreddits

3. **Customize scoring:**
   - Adjust weights in `ScoringService`
   - Add custom scoring components

4. **Add style sources:**
   ```bash
   poetry run python -m src.cli.main add-style-source \
     --url "https://www.reddit.com/r/hiphopheads/" \
     --tags "hip-hop,culture"
   ```

5. **Read full documentation:**
   - [README.md](README.md) - Complete guide
   - [docs/GCP_SETUP.md](docs/GCP_SETUP.md) - Detailed GCP setup
   - [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) - Local dev reference
   - [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) - Testing guide

## Getting Help

1. Check logs:
   ```bash
   # Backend (verbose)
   LOG_LEVEL=DEBUG poetry run python -m src.cli.main ingest-topics
   
   # Frontend
   # Browser console (F12)
   ```

2. Inspect data:
   ```bash
   python scripts/inspect_data.py
   ```

3. Run tests:
   ```bash
   cd backend
   poetry run pytest -v
   ```

4. Check GCP setup:
   ```bash
   ./scripts/verify_gcp_setup.sh
   ```

## Success Criteria

You're ready to use Content Engine when:

- ✅ `verify_setup.sh` passes all checks
- ✅ Frontend loads at http://localhost:3000
- ✅ Topics appear in "Today" view
- ✅ Can approve/reject topics
- ✅ Content options generated for approved topics

---

**Happy content creating! 🚀**

For detailed information, see the main [README.md](README.md).

