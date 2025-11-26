# GCP Setup Guide for Content Engine

This document provides a comprehensive guide for setting up Google Cloud Platform (GCP) resources for the Content Engine project.

## Project Configuration

**Project:** `hinsko-dev`  
**Project Number:** `505410332970`  
**Region:** `europe-west2` (for Cloud Run, GCS, Artifact Registry)  
**Firestore Location:** `europe-west1` (separate from region)

**Required Resources:**
- Firestore Database (`main-db`)
- GCS Bucket (`content-engine-storage-hinsko-dev`)
- Artifact Registry Repository (`content-engine-images`)
- Service Account (`content-engine-runner`)
- Secret Manager Secret (`openai-api-key`)

---

## Prerequisites

### Enable Billing

**Important:** GCS buckets, Artifact Registry repositories, and Secret Manager secrets require billing to be enabled.

#### Via Console
1. Visit: https://console.developers.google.com/billing/enable?project=hinsko-dev
2. Select your billing account
3. Click "Set Account"
4. Wait 2-3 minutes for propagation

#### Via CLI
```bash
# List available billing accounts
gcloud billing accounts list

# Link billing account to project
gcloud billing projects link hinsko-dev \
  --billing-account=YOUR_BILLING_ACCOUNT_ID

# Verify billing is enabled
gcloud billing projects describe hinsko-dev \
  --format="value(billingAccountName,billingEnabled)"
```

**Note:** After enabling billing, wait 15-30 minutes for services to recognize it. Some services may report billing as disabled during this propagation period.

---

## Setup Steps

### 1. Set GCP Project Context

```bash
# Verify current project
gcloud config get-value project

# Set project if needed
gcloud config set project hinsko-dev

# Verify authentication
gcloud auth list
```

### 2. Enable Required APIs

Enable all required Google Cloud APIs:

```bash
# Enable APIs
gcloud services enable firestore.googleapis.com --project=hinsko-dev
gcloud services enable run.googleapis.com --project=hinsko-dev
gcloud services enable cloudscheduler.googleapis.com --project=hinsko-dev
gcloud services enable secretmanager.googleapis.com --project=hinsko-dev
gcloud services enable artifactregistry.googleapis.com --project=hinsko-dev

# Verify APIs are enabled
gcloud services list --enabled --project=hinsko-dev | grep -E "(firestore|run|scheduler|secretmanager|artifactregistry)"
```

**Note:** API enablement can take a few minutes. Wait 2-3 minutes after enabling before proceeding.

### 3. Create Service Account

Create a service account for Cloud Run Jobs to use:

```bash
# Service account details
SERVICE_ACCOUNT_NAME="content-engine-runner"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@hinsko-dev.iam.gserviceaccount.com"
DISPLAY_NAME="Content Engine Pipeline Runner"
DESCRIPTION="Service account for Content Engine pipeline jobs"

# Create service account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
  --display-name="${DISPLAY_NAME}" \
  --description="${DESCRIPTION}" \
  --project=hinsko-dev

# Verify creation
gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=hinsko-dev
```

### 4. Grant IAM Roles to Service Account

Grant necessary permissions to the service account:

```bash
SERVICE_ACCOUNT_EMAIL="content-engine-runner@hinsko-dev.iam.gserviceaccount.com"

# Grant roles
gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding hinsko-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.invoker"

# Verify roles
gcloud projects get-iam-policy hinsko-dev \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --format="table(bindings.role)"
```

### 5. Create Firestore Database

Create a Firestore Native database:

```bash
DATABASE_ID="main-db"
LOCATION="europe-west1"  # Firestore location (different from Cloud Run region)

# Create database
gcloud firestore databases create \
  --database=${DATABASE_ID} \
  --location=${LOCATION} \
  --type=firestore-native \
  --project=hinsko-dev

# Verify creation
gcloud firestore databases list --project=hinsko-dev
```

**Important Notes:**
- Firestore location (`europe-west1`) is separate from Cloud Run region (`europe-west2`)
- Firestore location cannot be changed after creation
- Database creation can take several minutes

### 6. Create GCS Bucket

Create a Google Cloud Storage bucket for file storage:

```bash
BUCKET_NAME="content-engine-storage-hinsko-dev"
REGION="europe-west2"

# Create bucket
gcloud storage buckets create gs://${BUCKET_NAME} \
  --project=hinsko-dev \
  --location=${REGION}

# Verify creation
gcloud storage buckets list --project=hinsko-dev
```

**Bucket Naming Rules:**
- 3-63 characters
- Lowercase letters, numbers, hyphens, dots, underscores
- Must start and end with alphanumeric character
- Globally unique across all GCS buckets

### 7. Create Artifact Registry Repository

Create a Docker repository for storing container images:

```bash
REPO_NAME="content-engine-images"
REGION="europe-west2"

# Create repository
gcloud artifacts repositories create ${REPO_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="Docker images for Content Engine" \
  --project=hinsko-dev

# Verify creation
gcloud artifacts repositories list --project=hinsko-dev --location=${REGION}
```

### 8. Create Secret Manager Secrets

Create secrets for sensitive configuration:

```bash
# Create OpenAI API key secret
gcloud secrets create openai-api-key \
  --project=hinsko-dev

# Add secret value (you'll be prompted to enter the value)
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key \
  --data-file=- \
  --project=hinsko-dev

# Grant service account access to secret
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:content-engine-runner@hinsko-dev.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=hinsko-dev

# Verify secret exists
gcloud secrets list --project=hinsko-dev
```

**Alternative:** Use a file to set the secret value:
```bash
echo -n "YOUR_OPENAI_API_KEY" > /tmp/openai-key.txt
gcloud secrets versions add openai-api-key \
  --data-file=/tmp/openai-key.txt \
  --project=hinsko-dev
rm /tmp/openai-key.txt  # Clean up
```

### 9. Configure Application Default Credentials

Set up Application Default Credentials for local development:

```bash
# Authenticate for Application Default Credentials
gcloud auth application-default login --project=hinsko-dev

# Verify credentials
gcloud auth application-default print-access-token
```

---

## Verification Checklist

Run these commands to verify all resources are set up correctly:

```bash
# 1. Verify project
gcloud config get-value project
# Expected: hinsko-dev

# 2. Verify APIs are enabled
gcloud services list --enabled --project=hinsko-dev | grep -E "(firestore|run|scheduler|secretmanager|artifactregistry|storage|logging|monitoring)"
# Expected: All APIs listed

# 3. Verify service account exists
gcloud iam service-accounts describe content-engine-runner@hinsko-dev.iam.gserviceaccount.com --project=hinsko-dev
# Expected: Service account details

# 4. Verify Firestore database exists
gcloud firestore databases list --project=hinsko-dev
# Expected: Database "main-db" listed

# 5. Verify GCS bucket exists
gcloud storage buckets list --project=hinsko-dev | grep content-engine-storage
# Expected: Bucket listed

# 6. Verify Artifact Registry repository exists
gcloud artifacts repositories list --project=hinsko-dev --location=europe-west2 | grep content-engine-images
# Expected: Repository listed

# 7. Verify secrets exist
gcloud secrets list --project=hinsko-dev | grep openai-api-key
# Expected: Secret listed

# 8. Verify Application Default Credentials
gcloud auth application-default print-access-token
# Expected: Access token printed
```

---

## Environment Variables

After setup, configure your backend `.env` file:

```bash
# Backend .env file
GCP_PROJECT_ID=hinsko-dev
FIRESTORE_DATABASE_ID=main-db
DEFAULT_REGION=europe-west2
GCS_BUCKET_NAME=content-engine-storage
OPENAI_API_KEY=  # Leave empty if using Secret Manager
ENVIRONMENT=local
LOG_LEVEL=INFO
```

For production/Cloud Run, use Secret Manager instead of environment variables for sensitive data.

---

## Resource Summary

| Resource Type | Name | Location/Region | Purpose |
|--------------|------|-----------------|---------|
| **Project** | `hinsko-dev` | N/A | Main GCP project |
| **Firestore Database** | `main-db` | `europe-west1` | Data persistence |
| **GCS Bucket** | `content-engine-storage-hinsko-dev` | `europe-west2` | File storage |
| **Artifact Registry** | `content-engine-images` | `europe-west2` | Docker images |
| **Service Account** | `content-engine-runner` | N/A | Cloud Run Jobs identity |
| **Secret** | `openai-api-key` | N/A | OpenAI API key storage |

---

## Troubleshooting

### API Not Enabled Error
```
ERROR: API [firestore.googleapis.com] not enabled on project [hinsko-dev]
```
**Solution:** Enable the API using `gcloud services enable <api-name> --project=hinsko-dev`

### Permission Denied Error
```
ERROR: Permission denied on project [hinsko-dev]
```
**Solution:** 
1. Verify you're authenticated: `gcloud auth list`
2. Verify you have necessary IAM roles (Owner or Editor)
3. Check project access: `gcloud projects describe hinsko-dev`

### Firestore Database Creation Fails
```
ERROR: Database already exists or location conflict
```
**Solution:** 
1. List existing databases: `gcloud firestore databases list --project=hinsko-dev`
2. Use existing database or choose different location/name

### Service Account Already Exists
```
ERROR: Service account already exists
```
**Solution:** Use existing service account or choose different name

### Bucket Name Already Taken
```
ERROR: Bucket name already exists globally
```
**Solution:** Choose a different globally unique bucket name

---

## Next Steps

After completing GCP setup:

1. **Backend Configuration:**
   ```bash
   cd content-engine/backend
   cp .env.example .env
   # Edit .env with GCP project details
   ```

2. **Test Local Connection:**
   ```bash
   poetry run python -m src.cli.main check-infra
   ```

3. **Run Topic Ingestion Locally:**
   ```bash
   poetry run python scripts/verify_data_local.py
   ```

4. **Build and Deploy Docker Image:**
   ```bash
   # Configure Docker auth
   gcloud auth configure-docker europe-west2-docker.pkg.dev
   
   # Build image
   docker build -t europe-west2-docker.pkg.dev/hinsko-dev/content-engine-images/main:latest .
   
   # Push image
   docker push europe-west2-docker.pkg.dev/hinsko-dev/content-engine-images/main:latest
   ```

5. **Create Cloud Run Job:**
   ```bash
   gcloud run jobs create content-engine-topic-ingestion \
     --image=europe-west2-docker.pkg.dev/hinsko-dev/content-engine-images/main:latest \
     --region=europe-west2 \
     --service-account=content-engine-runner@hinsko-dev.iam.gserviceaccount.com \
     --set-env-vars="JOB_TYPE=topic_ingestion" \
     --max-retries=1 \
     --parallelism=1 \
     --task-timeout=3600
   ```

---

## Quick Reference

### Common Commands
```bash
# Set project
gcloud config set project hinsko-dev

# Check billing status
gcloud billing projects describe hinsko-dev --format="value(billingAccountName)"

# List all resources
gcloud services list --enabled --project=hinsko-dev
gcloud iam service-accounts list --project=hinsko-dev
gcloud firestore databases list --project=hinsko-dev
gcloud storage buckets list --project=hinsko-dev
gcloud artifacts repositories list --project=hinsko-dev --location=europe-west2
gcloud secrets list --project=hinsko-dev
```

### Automated Setup
Use the setup script for automated resource creation:
```bash
cd content-engine
./scripts/setup_gcp.sh
```

### Verification Script
Verify all resources are configured correctly:
```bash
cd content-engine
./scripts/verify_gcp_setup.sh
```

---

## References

- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Cloud Run Jobs Documentation](https://cloud.google.com/run/docs/create-jobs)
- [GCS Documentation](https://cloud.google.com/storage/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [IAM Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Billing Documentation](https://docs.cloud.google.com/billing/docs/how-to/modify-project)

