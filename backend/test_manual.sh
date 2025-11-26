#!/bin/bash
# Manual test script for topic ingestion

set -e

echo "🧪 Manual Testing - Topic Ingestion System"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. Testing CLI Help${NC}"
poetry run python -m src.cli.main --help > /dev/null && echo -e "${GREEN}✓ CLI help works${NC}" || echo "✗ CLI help failed"
echo ""

echo -e "${YELLOW}2. Testing Manual Topic Entry${NC}"
poetry run python -m src.cli.main add-topic \
  "Test Topic: OpenAI Releases GPT-5" \
  --cluster "ai-infra" \
  --url "https://example.com/test" \
  --notes "Manual test entry" && echo -e "${GREEN}✓ Manual topic entry works${NC}" || echo "✗ Manual topic entry failed"
echo ""

echo -e "${YELLOW}3. Testing Infrastructure Check${NC}"
poetry run python -m src.cli.main check-infra && echo -e "${GREEN}✓ Infrastructure check works${NC}" || echo "⚠ Infrastructure check (may fail if GCP not configured)"
echo ""

echo -e "${YELLOW}4. Testing Topic Ingestion (Dry Run - Will Make Real API Calls)${NC}"
echo "Note: This will fetch real data from Reddit, Hacker News, and RSS feeds"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    poetry run python -m src.cli.main ingest-topics && echo -e "${GREEN}✓ Topic ingestion works${NC}" || echo "✗ Topic ingestion failed"
else
    echo "Skipped ingestion test"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Manual testing complete!${NC}"

