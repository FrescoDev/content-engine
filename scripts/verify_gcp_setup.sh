#!/bin/bash
# GCP Setup Verification Script
# Verifies all GCP resources are correctly configured

set -e

PROJECT_ID="hinsko-dev"
REGION="europe-west2"
FIRESTORE_LOCATION="europe-west1"
SERVICE_ACCOUNT_NAME="content-engine-runner"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
DATABASE_ID="main-db"
BUCKET_NAME="content-engine-storage-${PROJECT_ID}"
REPO_NAME="content-engine-images"

echo "=========================================="
echo "GCP Setup Verification"
echo "=========================================="
echo ""

ERRORS=0

# Check project
echo "1. Checking project..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ "${CURRENT_PROJECT}" = "${PROJECT_ID}" ]; then
  echo "   ✓ Project set to ${PROJECT_ID}"
else
  echo "   ✗ Project is ${CURRENT_PROJECT}, expected ${PROJECT_ID}"
  ERRORS=$((ERRORS + 1))
fi

# Check APIs
echo ""
echo "2. Checking enabled APIs..."
REQUIRED_APIS=(
  "firestore.googleapis.com"
  "run.googleapis.com"
  "cloudscheduler.googleapis.com"
  "secretmanager.googleapis.com"
  "artifactregistry.googleapis.com"
  "storage.googleapis.com"
  "logging.googleapis.com"
  "monitoring.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
  if gcloud services list --enabled --project=${PROJECT_ID} --format="value(config.name)" | grep -q "^${api}$"; then
    echo "   ✓ ${api}"
  else
    echo "   ✗ ${api} (not enabled)"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check service account
echo ""
echo "3. Checking service account..."
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=${PROJECT_ID} &>/dev/null; then
  echo "   ✓ Service account exists"
else
  echo "   ✗ Service account does not exist"
  ERRORS=$((ERRORS + 1))
fi

# Check Firestore database
echo ""
echo "4. Checking Firestore database..."
if gcloud firestore databases list --project=${PROJECT_ID} --format="value(name)" | grep -q "${DATABASE_ID}"; then
  echo "   ✓ Database exists"
else
  echo "   ✗ Database does not exist"
  ERRORS=$((ERRORS + 1))
fi

# Check GCS bucket
echo ""
echo "5. Checking GCS bucket..."
if gcloud storage buckets list --project=${PROJECT_ID} --format="value(name)" | grep -q "${BUCKET_NAME}"; then
  echo "   ✓ Bucket exists"
else
  echo "   ✗ Bucket does not exist"
  ERRORS=$((ERRORS + 1))
fi

# Check Artifact Registry repository
echo ""
echo "6. Checking Artifact Registry repository..."
if gcloud artifacts repositories list --project=${PROJECT_ID} --location=${REGION} --format="value(name)" | grep -q "${REPO_NAME}"; then
  echo "   ✓ Repository exists"
else
  echo "   ✗ Repository does not exist"
  ERRORS=$((ERRORS + 1))
fi

# Check Secret Manager secret
echo ""
echo "7. Checking Secret Manager secret..."
if gcloud secrets describe openai-api-key --project=${PROJECT_ID} &>/dev/null; then
  echo "   ✓ Secret exists"
else
  echo "   ✗ Secret does not exist"
  ERRORS=$((ERRORS + 1))
fi

# Check Application Default Credentials
echo ""
echo "8. Checking Application Default Credentials..."
if gcloud auth application-default print-access-token &>/dev/null; then
  echo "   ✓ ADC configured"
else
  echo "   ✗ ADC not configured (run: gcloud auth application-default login)"
  ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=========================================="
if [ ${ERRORS} -eq 0 ]; then
  echo "✓ All checks passed!"
  echo "=========================================="
  exit 0
else
  echo "✗ Found ${ERRORS} issue(s)"
  echo "=========================================="
  echo ""
  echo "Run setup script to fix issues:"
  echo "  ./scripts/setup_gcp.sh"
  exit 1
fi

