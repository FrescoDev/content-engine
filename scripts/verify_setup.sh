#!/bin/bash
# Quick Setup Verification for Content Engine
# Run this after initial setup to ensure everything is configured correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

success() {
  echo -e "${GREEN}✓${NC} $1"
}

error() {
  echo -e "${RED}✗${NC} $1"
}

warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

ERRORS=0

# Header
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   Content Engine Setup Verification   ║"
echo "╔════════════════════════════════════════╝"
echo ""

# 1. Check Prerequisites
section "1. Prerequisites"

# Python
if command -v python3 &> /dev/null; then
  PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
  if [[ "$PYTHON_VERSION" > "3.12" ]] || [[ "$PYTHON_VERSION" == "3.12"* ]]; then
    success "Python $PYTHON_VERSION (>= 3.12)"
  else
    error "Python $PYTHON_VERSION found, but 3.12+ required"
    ERRORS=$((ERRORS + 1))
  fi
else
  error "Python 3 not found"
  ERRORS=$((ERRORS + 1))
fi

# Poetry
if command -v poetry &> /dev/null; then
  POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
  success "Poetry $POETRY_VERSION"
else
  error "Poetry not found"
  info "Install: curl -sSL https://install.python-poetry.org | python3 -"
  ERRORS=$((ERRORS + 1))
fi

# Node.js
if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version)
  success "Node.js $NODE_VERSION"
else
  error "Node.js not found"
  ERRORS=$((ERRORS + 1))
fi

# npm
if command -v npm &> /dev/null; then
  NPM_VERSION=$(npm --version)
  success "npm $NPM_VERSION"
else
  error "npm not found"
  ERRORS=$((ERRORS + 1))
fi

# gcloud
if command -v gcloud &> /dev/null; then
  GCLOUD_VERSION=$(gcloud --version | head -n1 | cut -d' ' -f4)
  success "gcloud $GCLOUD_VERSION"
else
  error "gcloud CLI not found"
  info "Install: https://cloud.google.com/sdk/docs/install"
  ERRORS=$((ERRORS + 1))
fi

# 2. Check GCP Configuration
section "2. GCP Configuration"

# Project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -n "$PROJECT_ID" ]; then
  success "GCP Project: $PROJECT_ID"
else
  error "No GCP project configured"
  info "Run: gcloud config set project hinsko-dev"
  ERRORS=$((ERRORS + 1))
fi

# Authentication
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -n1)
if [ -n "$ACTIVE_ACCOUNT" ]; then
  success "Authenticated as: $ACTIVE_ACCOUNT"
else
  error "No active gcloud authentication"
  info "Run: gcloud auth login"
  ERRORS=$((ERRORS + 1))
fi

# Application Default Credentials
if gcloud auth application-default print-access-token &>/dev/null; then
  success "Application Default Credentials configured"
else
  warning "Application Default Credentials not configured"
  info "Run: gcloud auth application-default login --project=hinsko-dev"
fi

# Check Firestore
if [ -n "$PROJECT_ID" ]; then
  if gcloud firestore databases list --project="$PROJECT_ID" 2>/dev/null | grep -q "main-db"; then
    success "Firestore database 'main-db' exists"
  else
    warning "Firestore database 'main-db' not found"
    info "Run: ./scripts/setup_gcp.sh"
  fi
fi

# Check GCS bucket
if [ -n "$PROJECT_ID" ]; then
  if gcloud storage buckets list --project="$PROJECT_ID" 2>/dev/null | grep -q "content-engine-storage"; then
    success "GCS bucket exists"
  else
    warning "GCS bucket not found"
    info "Run: ./scripts/setup_gcp.sh"
  fi
fi

# 3. Check Backend Setup
section "3. Backend Setup"

cd backend 2>/dev/null || { error "backend/ directory not found"; exit 1; }

# Poetry dependencies
if [ -f "poetry.lock" ]; then
  success "Poetry lock file exists"
else
  warning "Poetry dependencies not installed"
  info "Run: cd backend && poetry install"
fi

# Environment file
if [ -f ".env" ]; then
  success "Backend .env file exists"
  
  # Check required variables
  if grep -q "GCP_PROJECT_ID=" .env; then
    success "  GCP_PROJECT_ID configured"
  else
    warning "  GCP_PROJECT_ID not set in .env"
  fi
  
  if grep -q "FIRESTORE_DATABASE_ID=" .env; then
    success "  FIRESTORE_DATABASE_ID configured"
  else
    warning "  FIRESTORE_DATABASE_ID not set in .env"
  fi
else
  warning "Backend .env file not found"
  info "Create .env file with required variables (see README.md)"
fi

# Test import
if poetry run python -c "import src.core" &>/dev/null; then
  success "Backend Python modules importable"
else
  error "Cannot import backend modules"
  info "Run: cd backend && poetry install"
  ERRORS=$((ERRORS + 1))
fi

cd ..

# 4. Check Frontend Setup
section "4. Frontend Setup"

cd frontend 2>/dev/null || { error "frontend/ directory not found"; exit 1; }

# Node modules
if [ -d "node_modules" ]; then
  success "Frontend dependencies installed"
else
  warning "Frontend dependencies not installed"
  info "Run: cd frontend && npm install"
fi

# Environment file
if [ -f ".env.local" ]; then
  success "Frontend .env.local file exists"
  
  if grep -q "NEXT_PUBLIC_FIREBASE_PROJECT_ID=" .env.local; then
    success "  NEXT_PUBLIC_FIREBASE_PROJECT_ID configured"
  else
    warning "  NEXT_PUBLIC_FIREBASE_PROJECT_ID not set"
  fi
else
  warning "Frontend .env.local file not found"
  info "Create .env.local with Firebase configuration (see README.md)"
fi

cd ..

# 5. Connectivity Tests
section "5. Connectivity Tests"

cd backend

# Test Firestore connection
info "Testing Firestore connectivity..."
if poetry run python -m src.cli.main check-infra &>/dev/null; then
  success "Firestore and GCS connectivity verified"
else
  warning "Infrastructure check failed"
  info "Run: cd backend && poetry run python -m src.cli.main check-infra"
fi

cd ..

# Summary
section "Summary"

if [ $ERRORS -eq 0 ]; then
  echo ""
  success "All checks passed! System is ready to use."
  echo ""
  info "Next steps:"
  echo "  1. Start frontend: cd frontend && npm run dev"
  echo "  2. Ingest topics: cd backend && poetry run python -m src.cli.main ingest-topics"
  echo "  3. Visit: http://localhost:3000"
  echo ""
else
  echo ""
  error "$ERRORS error(s) found. Please fix the issues above."
  echo ""
  info "See README.md for detailed setup instructions"
  echo ""
  exit 1
fi

