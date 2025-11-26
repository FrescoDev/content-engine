#!/bin/bash
# GCP Setup Script for Content Engine (FIXED VERSION)
# This script sets up all required GCP resources with proper error handling

# Don't use set -e because we handle errors explicitly
set -u  # Exit on undefined variables
set -o pipefail  # Exit on pipe failures

PROJECT_ID="${GCP_PROJECT_ID:-hinsko-dev}"
REGION="${GCP_REGION:-europe-west2}"
FIRESTORE_LOCATION="${FIRESTORE_LOCATION:-europe-west1}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-content-engine-runner}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
DATABASE_ID="${DATABASE_ID:-main-db}"
BUCKET_NAME="${BUCKET_NAME:-content-engine-storage-${PROJECT_ID}}"
REPO_NAME="${REPO_NAME:-content-engine-images}"

# Track failures
FAILED_APIS=()
FAILED_ROLES=()
FAILURES=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
  echo -e "${RED}ERROR:${NC} $1" >&2
  FAILURES=$((FAILURES + 1))
}

warning() {
  echo -e "${YELLOW}WARNING:${NC} $1" >&2
}

success() {
  echo -e "${GREEN}✓${NC} $1"
}

info() {
  echo "$1"
}

# Validate project exists
validate_project() {
  info "Validating project ${PROJECT_ID}..."
  if ! gcloud projects describe "${PROJECT_ID}" &>/dev/null; then
    error "Project ${PROJECT_ID} does not exist or is not accessible"
    return 1
  fi
  success "Project validated"
  return 0
}

# Validate authentication
validate_auth() {
  info "Validating authentication..."
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
    return 1
  fi
  success "Authentication validated"
  return 0
}

# Check if API is enabled
is_api_enabled() {
  local api="$1"
  gcloud services list --enabled --project="${PROJECT_ID}" --format="value(config.name)" 2>/dev/null | grep -q "^${api}$"
}

# Enable API with proper error handling
enable_api() {
  local api="$1"
  
  if is_api_enabled "${api}"; then
    info "  ${api} already enabled"
    return 0
  fi
  
  info "  Enabling ${api}..."
  if gcloud services enable "${api}" --project="${PROJECT_ID}" --quiet 2>&1; then
    success "  ${api} enabled"
    return 0
  else
    local exit_code=$?
    error "Failed to enable ${api} (exit code: ${exit_code})"
    FAILED_APIS+=("${api}")
    return 1
  fi
}

# Wait for APIs to be ready (polling)
wait_for_apis() {
  info "Waiting for APIs to be ready..."
  local max_attempts=12
  local attempt=0
  
  while [ ${attempt} -lt ${max_attempts} ]; do
    local all_ready=true
    for api in firestore.googleapis.com run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com; do
      if ! is_api_enabled "${api}"; then
        all_ready=false
        break
      fi
    done
    
    if [ "${all_ready}" = "true" ]; then
      success "All APIs are ready"
      return 0
    fi
    
    attempt=$((attempt + 1))
    info "  Waiting... (${attempt}/${max_attempts})"
    sleep 5
  done
  
  warning "Some APIs may not be fully ready yet"
  return 0
}

# Check if service account exists
service_account_exists() {
  gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" --project="${PROJECT_ID}" &>/dev/null
}

# Create service account with validation
create_service_account() {
  info "Checking service account..."
  
  if service_account_exists; then
    success "Service account already exists"
    return 0
  fi
  
  # Validate name
  if [ ${#SERVICE_ACCOUNT_NAME} -lt 6 ] || [ ${#SERVICE_ACCOUNT_NAME} -gt 30 ]; then
    error "Service account name must be 6-30 characters (got ${#SERVICE_ACCOUNT_NAME})"
    return 1
  fi
  
  if ! echo "${SERVICE_ACCOUNT_NAME}" | grep -qE '^[a-z0-9-]+$'; then
    error "Service account name must contain only lowercase letters, numbers, and hyphens"
    return 1
  fi
  
  info "Creating service account..."
  if gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Content Engine Pipeline Runner" \
    --description="Service account for Content Engine pipeline jobs" \
    --project="${PROJECT_ID}" 2>&1; then
    success "Service account created"
    return 0
  else
    local exit_code=$?
    error "Failed to create service account (exit code: ${exit_code})"
    return 1
  fi
}

# Check if IAM role is granted
role_is_granted() {
  local role="$1"
  gcloud projects get-iam-policy "${PROJECT_ID}" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL} AND bindings.role:${role}" \
    --format="value(bindings.role)" 2>/dev/null | grep -q "^${role}$"
}

# Grant IAM role with validation
grant_iam_role() {
  local role="$1"
  
  if role_is_granted "${role}"; then
    info "  ${role} already granted"
    return 0
  fi
  
  info "  Granting ${role}..."
  if gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${role}" \
    --quiet 2>&1; then
    success "  ${role} granted"
    return 0
  else
    local exit_code=$?
    error "Failed to grant ${role} (exit code: ${exit_code})"
    FAILED_ROLES+=("${role}")
    return 1
  fi
}

# Check if Firestore database exists (exact match)
firestore_database_exists() {
  local db_list
  db_list=$(gcloud firestore databases list --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null)
  if [ $? -ne 0 ]; then
    return 1  # Command failed
  fi
  
  # Check for exact match (database ID appears as last segment)
  echo "${db_list}" | while IFS= read -r db_path; do
    if [ -n "${db_path}" ] && echo "${db_path}" | grep -qE "/databases/${DATABASE_ID}$"; then
      return 0
    fi
  done
  return 1
}

# Create Firestore database
create_firestore_database() {
  info "Checking Firestore database..."
  
  if firestore_database_exists; then
    success "Database already exists"
    return 0
  fi
  
  # Validate database ID
  if ! echo "${DATABASE_ID}" | grep -qE '^[a-z0-9-]+$'; then
    error "Database ID must contain only lowercase letters, numbers, and hyphens"
    return 1
  fi
  
  info "Creating Firestore database..."
  if gcloud firestore databases create \
    --database="${DATABASE_ID}" \
    --location="${FIRESTORE_LOCATION}" \
    --type=firestore-native \
    --project="${PROJECT_ID}" 2>&1; then
    success "Database created"
    return 0
  else
    local exit_code=$?
    error "Failed to create database (exit code: ${exit_code})"
    return 1
  fi
}

# Check if GCS bucket exists (exact match)
gcs_bucket_exists() {
  local bucket_list
  bucket_list=$(gcloud storage buckets list --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null)
  if [ $? -ne 0 ]; then
    return 1
  fi
  
  # Check for exact match (bucket name or gs://bucket-name)
  echo "${bucket_list}" | while IFS= read -r bucket_name; do
    if [ -n "${bucket_name}" ]; then
      # Remove gs:// prefix if present
      local clean_name="${bucket_name#gs://}"
      if [ "${clean_name}" = "${BUCKET_NAME}" ]; then
        return 0
      fi
    fi
  done
  return 1
}

# Create GCS bucket
create_gcs_bucket() {
  info "Checking GCS bucket..."
  
  if gcs_bucket_exists; then
    success "Bucket already exists"
    return 0
  fi
  
  # Validate bucket name
  if [ ${#BUCKET_NAME} -lt 3 ] || [ ${#BUCKET_NAME} -gt 63 ]; then
    error "Bucket name must be 3-63 characters (got ${#BUCKET_NAME})"
    return 1
  fi
  
  if ! echo "${BUCKET_NAME}" | grep -qE '^[a-z0-9][a-z0-9._-]*[a-z0-9]$'; then
    error "Bucket name must be DNS-compliant (lowercase, start/end with alphanumeric)"
    return 1
  fi
  
  info "Creating GCS bucket..."
  if gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" 2>&1; then
    success "Bucket created"
    return 0
  else
    local exit_code=$?
    error "Failed to create bucket (exit code: ${exit_code})"
    return 1
  fi
}

# Check if Artifact Registry repository exists (exact match)
artifact_repo_exists() {
  local repo_list
  repo_list=$(gcloud artifacts repositories list --project="${PROJECT_ID}" --location="${REGION}" --format="value(name)" 2>/dev/null)
  if [ $? -ne 0 ]; then
    return 1
  fi
  
  # Check for exact match (repo name appears as last segment)
  echo "${repo_list}" | while IFS= read -r repo_path; do
    if [ -n "${repo_path}" ] && echo "${repo_path}" | grep -qE "/${REPO_NAME}$"; then
      return 0
    fi
  done
  return 1
}

# Create Artifact Registry repository
create_artifact_repo() {
  info "Checking Artifact Registry repository..."
  
  if artifact_repo_exists; then
    success "Repository already exists"
    return 0
  fi
  
  info "Creating Artifact Registry repository..."
  if gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker images for Content Engine" \
    --project="${PROJECT_ID}" 2>&1; then
    success "Repository created"
    return 0
  else
    local exit_code=$?
    error "Failed to create repository (exit code: ${exit_code})"
    return 1
  fi
}

# Check if secret exists
secret_exists() {
  gcloud secrets describe "openai-api-key" --project="${PROJECT_ID}" &>/dev/null
}

# Create Secret Manager secret
create_secret() {
  info "Checking Secret Manager secret..."
  
  if secret_exists; then
    success "Secret already exists"
    return 0
  fi
  
  info "Creating Secret Manager secret..."
  if echo "PLACEHOLDER_UPDATE_ME" | gcloud secrets create "openai-api-key" \
    --data-file=- \
    --project="${PROJECT_ID}" 2>&1; then
    success "Secret created (update with actual value)"
    return 0
  else
    local exit_code=$?
    error "Failed to create secret (exit code: ${exit_code})"
    return 1
  fi
}

# Grant secret access
grant_secret_access() {
  info "Granting secret access to service account..."
  
  if gcloud secrets add-iam-policy-binding "openai-api-key" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" \
    --quiet 2>&1; then
    success "Secret access granted"
    return 0
  else
    local exit_code=$?
    # Check if already granted
    if gcloud secrets get-iam-policy "openai-api-key" --project="${PROJECT_ID}" 2>/dev/null | \
       grep -q "serviceAccount:${SERVICE_ACCOUNT_EMAIL}"; then
      info "  Secret access already granted"
      return 0
    else
      warning "Failed to grant secret access (exit code: ${exit_code})"
      return 1
    fi
  fi
}

# Main execution
main() {
  echo "=========================================="
  echo "Content Engine GCP Setup"
  echo "=========================================="
  echo "Project: ${PROJECT_ID}"
  echo "Region: ${REGION}"
  echo "Firestore Location: ${FIRESTORE_LOCATION}"
  echo ""
  
  # Pre-flight checks
  if ! validate_project; then
    exit 1
  fi
  
  if ! validate_auth; then
    exit 1
  fi
  
  # Set project
  info "Setting GCP project..."
  gcloud config set project "${PROJECT_ID}" || {
    error "Failed to set project"
    exit 1
  }
  
  # Enable APIs
  echo ""
  info "Enabling required APIs..."
  APIS=(
    "firestore.googleapis.com"
    "run.googleapis.com"
    "cloudscheduler.googleapis.com"
    "secretmanager.googleapis.com"
    "artifactregistry.googleapis.com"
  )
  
  for api in "${APIS[@]}"; do
    enable_api "${api}"
  done
  
  # Wait for APIs
  if [ ${#FAILED_APIS[@]} -eq 0 ]; then
    wait_for_apis
  else
    warning "Some APIs failed to enable, but continuing..."
  fi
  
  # Create service account
  echo ""
  create_service_account || exit 1
  
  # Grant IAM roles
  echo ""
  info "Granting IAM roles..."
  ROLES=(
    "roles/firebase.admin"
    "roles/storage.objectAdmin"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
    "roles/run.invoker"
  )
  
  for role in "${ROLES[@]}"; do
    grant_iam_role "${role}"
  done
  
  # Create resources
  echo ""
  create_firestore_database || exit 1
  
  echo ""
  create_gcs_bucket || exit 1
  
  echo ""
  create_artifact_repo || exit 1
  
  echo ""
  create_secret || exit 1
  
  echo ""
  grant_secret_access
  
  # Summary
  echo ""
  echo "=========================================="
  if [ ${FAILURES} -eq 0 ]; then
    success "Setup Complete!"
  else
    warning "Setup completed with ${FAILURES} error(s)"
  fi
  echo "=========================================="
  echo ""
  
  if [ ${#FAILED_APIS[@]} -gt 0 ]; then
    warning "Failed to enable APIs:"
    for api in "${FAILED_APIS[@]}"; do
      echo "  - ${api}"
    done
  fi
  
  if [ ${#FAILED_ROLES[@]} -gt 0 ]; then
    warning "Failed to grant roles:"
    for role in "${FAILED_ROLES[@]}"; do
      echo "  - ${role}"
    done
  fi
  
  echo ""
  info "Next steps:"
  echo "1. Update OpenAI API key secret:"
  echo "   echo -n 'YOUR_KEY' | gcloud secrets versions add openai-api-key --data-file=- --project=${PROJECT_ID}"
  echo ""
  echo "2. Set up Application Default Credentials:"
  echo "   gcloud auth application-default login --project=${PROJECT_ID}"
  echo ""
  echo "3. Configure backend .env file with:"
  echo "   GCP_PROJECT_ID=${PROJECT_ID}"
  echo "   FIRESTORE_DATABASE_ID=${DATABASE_ID}"
  echo "   GCS_BUCKET_NAME=${BUCKET_NAME}"
  
  exit ${FAILURES}
}

main "$@"

