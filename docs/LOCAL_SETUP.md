# Local Development Setup

Quick reference for running Content Engine locally.

## Prerequisites

1. **GCP Project**: `hinsko-dev` must be set up (see `GCP_SETUP.md`)
2. **Application Default Credentials**: Configured for local development
   ```bash
   gcloud auth application-default login --project=hinsko-dev
   ```
3. **gcloud CLI**: Project set to `hinsko-dev`
   ```bash
   gcloud config set project hinsko-dev
   ```

## Environment Variables

### Frontend (`frontend/.env.local`)

Required:
```bash
NEXT_PUBLIC_FIREBASE_PROJECT_ID=hinsko-dev
NEXT_PUBLIC_FIREBASE_DATABASE_ID=main-db
```

Optional (for Firebase client SDK):
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=hinsko-dev.firebaseapp.com
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=hinsko-dev.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
```

For OpenAI features:
```bash
OPENAI_API_KEY=your-openai-key
```

### Backend (`backend/.env`)

```bash
GCP_PROJECT_ID=hinsko-dev
FIRESTORE_DATABASE_ID=main-db
DEFAULT_REGION=europe-west2
GCS_BUCKET_NAME=content-engine-storage-hinsko-dev
OPENAI_API_KEY=your-key  # Optional if using Secret Manager
ENVIRONMENT=local
LOG_LEVEL=INFO
```

## Running the Stack

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Access at: `http://localhost:3000`

### Backend (CLI)

The backend is CLI-based, not a server:

```bash
cd backend
poetry install
poetry run python -m src.cli.main check-infra
poetry run python -m src.cli.main ingest-topics
```

## Troubleshooting

### Permission Denied Errors

If you see `PERMISSION_DENIED` errors:

1. **Verify Application Default Credentials**:
   ```bash
   gcloud auth application-default print-access-token
   ```

2. **Check quota project (critical for Firestore access)**:
   ```bash
   cat ~/.config/gcloud/application_default_credentials.json | jq -r '.quota_project_id'
   # Should output: hinsko-dev
   ```

3. **Set quota project if incorrect**:
   ```bash
   gcloud auth application-default set-quota-project hinsko-dev
   ```

4. **Re-authenticate if needed**:
   ```bash
   gcloud auth application-default login --project=hinsko-dev
   ```

5. **Check project is set correctly**:
   ```bash
   gcloud config get-value project
   # Should output: hinsko-dev
   ```

### Missing Environment Variables

The frontend requires `NEXT_PUBLIC_FIREBASE_PROJECT_ID` to be set. If missing, you'll see:
```
Error: NEXT_PUBLIC_FIREBASE_PROJECT_ID environment variable is required
```

Solution: Create `frontend/.env.local` with the required variables (see above).

### Firestore Connection Issues

- Verify Firestore database exists:
  ```bash
  gcloud firestore databases list --project=hinsko-dev
  ```

- Check database ID matches: Should be `main-db`

## Verification

Run these commands to verify setup:

```bash
# 1. Check GCP project
gcloud config get-value project
# Expected: hinsko-dev

# 2. Check Application Default Credentials
gcloud auth application-default print-access-token
# Expected: Access token printed

# 3. Check Firestore database
gcloud firestore databases list --project=hinsko-dev
# Expected: main-db listed

# 4. Test backend connection
cd backend
poetry run python -m src.cli.main check-infra
# Expected: Infrastructure check complete

# 5. Test frontend
cd frontend
npm run dev
# Expected: Server starts on http://localhost:3000
```

