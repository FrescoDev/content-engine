#!/bin/bash
# Comprehensive test runner script

set -e

echo "🧪 Running Comprehensive Test Suite"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Function to run tests and track results
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ ${test_name} PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ ${test_name} FAILED${NC}"
        ((FAILED++))
    fi
    echo ""
}

# 1. Unit Tests - Sources
echo "📦 Unit Tests - Sources"
echo "----------------------"
run_test "Reddit Source Tests" "poetry run pytest tests/content/sources/test_reddit.py -v"
run_test "Hacker News Source Tests" "poetry run pytest tests/content/sources/test_hackernews.py -v"
run_test "RSS Source Tests" "poetry run pytest tests/content/sources/test_rss.py -v"
run_test "Manual Source Tests" "poetry run pytest tests/content/sources/test_manual.py -v"

# 2. Unit Tests - Processing
echo "⚙️  Unit Tests - Processing"
echo "-------------------------"
run_test "Deduplication Tests" "poetry run pytest tests/content/processing/test_deduplication.py -v"
run_test "Entity Extraction Tests" "poetry run pytest tests/content/processing/test_entity_extraction.py -v"
run_test "Clustering Tests" "poetry run pytest tests/content/processing/test_clustering.py -v"

# 3. Unit Tests - Services
echo "🔧 Unit Tests - Services"
echo "----------------------"
run_test "Ingestion Service Tests" "poetry run pytest tests/content/test_ingestion_service.py -v"

# 4. Integration Tests
echo "🔗 Integration Tests"
echo "-------------------"
run_test "Job Tests" "poetry run pytest tests/jobs/test_topic_ingestion_job.py -v"
run_test "End-to-End Tests" "poetry run pytest tests/integration/test_end_to_end.py -v"

# 5. All Tests with Coverage
echo "📊 Full Test Suite with Coverage"
echo "--------------------------------"
run_test "All Tests with Coverage" "poetry run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -v"

# Summary
echo "===================================="
echo "📈 Test Summary"
echo "===================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: ${FAILED}${NC}"
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi

