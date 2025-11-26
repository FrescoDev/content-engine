# Manual Testing Guide

## Prerequisites

1. Install dependencies:
```bash
cd backend
poetry install
```

2. Set up environment variables (create `.env` file):
```bash
GCP_PROJECT_ID=your-project-id
FIRESTORE_DATABASE_ID=main-db
OPENAI_API_KEY=your-key  # Optional for now
```

3. Ensure Firestore is accessible (local emulator or GCP project configured)

---

## Test Plan

### 1. Unit Tests

Run all unit tests:
```bash
poetry run pytest tests/ -v -m unit
```

Run specific test file:
```bash
poetry run pytest tests/content/sources/test_reddit.py -v
```

Run with coverage:
```bash
poetry run pytest tests/ --cov=src --cov-report=html
```

**Expected**: All tests pass, coverage >80%

---

### 2. Integration Tests

Run integration tests:
```bash
poetry run pytest tests/integration/ -v -m integration
```

**Expected**: All integration tests pass

---

### 3. End-to-End Tests

Run E2E tests:
```bash
poetry run pytest tests/integration/test_end_to_end.py -v -m e2e
```

**Expected**: Full flow works correctly

---

### 4. Manual CLI Testing

#### Test 1: Check Infrastructure
```bash
poetry run python -m src.cli.main check-infra
```

**Expected**: 
- ✓ Firestore service initialized
- ✓ GCS service initialized

---

#### Test 2: Manual Topic Entry
```bash
poetry run python -m src.cli.main add-topic \
  "OpenAI Releases GPT-5" \
  --cluster "ai-infra" \
  --url "https://example.com/news" \
  --notes "Test manual entry"
```

**Expected**:
- Topic created successfully
- Log shows: "✓ Saved manual topic: manual-{timestamp}-{hash}"
- Topic appears in Firestore with status="pending"

**Verify in Firestore**:
- Check `topic_candidates` collection
- Verify topic has correct fields:
  - `source_platform`: "manual"
  - `title`: "OpenAI Releases GPT-5"
  - `topic_cluster`: "ai-infra"
  - `entities`: ["OpenAI", "GPT-5"] (extracted)
  - `status`: "pending"

---

#### Test 3: Reddit Ingestion (Dry Run)

**Note**: This will make real API calls to Reddit. Ensure you have internet access.

```bash
poetry run python -m src.cli.main ingest-topics
```

**Expected**:
- Logs show fetching from reddit, hackernews, rss
- Topics fetched and processed
- Logs show: "Saved X topics to Firestore"
- No errors

**Verify**:
- Check Firestore `topic_candidates` collection
- Topics have:
  - `source_platform`: "reddit", "hackernews", or "rss"
  - `title`: Non-empty
  - `topic_cluster`: One of the 5 clusters
  - `entities`: Extracted entities (may be empty)
  - `status`: "pending"
  - `created_at`: Recent timestamp

---

#### Test 4: Deduplication

1. Add a topic manually:
```bash
poetry run python -m src.cli.main add-topic \
  "Test Deduplication Topic" \
  --cluster "business-socioeconomic" \
  --url "https://example.com/duplicate"
```

2. Try to add same topic again (same URL):
```bash
poetry run python -m src.cli.main add-topic \
  "Different Title But Same URL" \
  --cluster "ai-infra" \
  --url "https://example.com/duplicate"
```

**Expected**:
- First call: Topic saved
- Second call: Topic skipped (duplicate)
- Log shows: "Topic {id} already exists, skipping"

---

#### Test 5: Entity Extraction

Add topics with known entities:
```bash
poetry run python -m src.cli.main add-topic \
  "Google Announces New AI Model" \
  --cluster "ai-infra"

poetry run python -m src.cli.main add-topic \
  "Microsoft Partners with OpenAI on GPT-4" \
  --cluster "ai-infra"
```

**Verify in Firestore**:
- First topic: `entities` contains "Google"
- Second topic: `entities` contains ["Microsoft", "OpenAI", "GPT-4"]

---

#### Test 6: Clustering

Add topics with different keywords:
```bash
# AI/Infra
poetry run python -m src.cli.main add-topic \
  "New Machine Learning Breakthrough" \
  --cluster "ai-infra"

# Business
poetry run python -m src.cli.main add-topic \
  "Tech Startup Raises $100M" \
  --cluster "business-socioeconomic"

# Culture
poetry run python -m src.cli.main add-topic \
  "New Album Wins Grammy" \
  --cluster "culture-music"
```

**Verify in Firestore**:
- Topics are clustered correctly based on keywords
- `topic_cluster` matches expected cluster

---

#### Test 7: Error Handling

Test with invalid source (simulate failure):
- Temporarily break Reddit source (modify URL)
- Run ingestion
- Verify other sources still work

**Expected**:
- Error logged but job continues
- Topics from working sources are saved

---

#### Test 8: Cloud Run Job Simulation

Test job entrypoint:
```bash
JOB_TYPE=topic_ingestion poetry run python -m src.jobs.cloud_job_runner
```

**Expected**:
- Job runs successfully
- Logs show ingestion progress
- Topics saved to Firestore

---

## Verification Checklist

After running all tests, verify:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Manual topic entry works
- [ ] Ingestion from Reddit works
- [ ] Ingestion from Hacker News works
- [ ] Ingestion from RSS works
- [ ] Deduplication works (URL and title)
- [ ] Entity extraction works
- [ ] Clustering works
- [ ] Error handling works (partial failures)
- [ ] Topics appear in Firestore correctly
- [ ] Topic IDs are deterministic
- [ ] Logging is structured and informative

---

## Common Issues

### Issue: "Firestore client not initialized"
**Solution**: Set `GCP_PROJECT_ID` and `FIRESTORE_DATABASE_ID` in `.env`

### Issue: "Reddit API rate limited"
**Solution**: Wait a minute and retry, or reduce `limit_per_source`

### Issue: "RSS feed parse error"
**Solution**: Some feeds may be down, check logs for which feed failed

### Issue: "Topics not appearing in Firestore"
**Solution**: 
- Check Firestore permissions
- Verify collection name: `topic_candidates`
- Check logs for errors

---

## Performance Testing

Test with larger limits:
```bash
# Modify ingestion_service.py temporarily to increase limit
# Then run:
poetry run python -m src.cli.main ingest-topics
```

**Expected**:
- Handles 100+ topics without errors
- Deduplication still works
- Processing completes in reasonable time (<30 seconds)

---

## Security Testing

1. **Input Validation**: Try malicious titles/URLs
2. **Rate Limiting**: Verify delays are applied
3. **Error Messages**: Ensure no sensitive data leaked

---

## Success Criteria

✅ All automated tests pass  
✅ Manual tests complete successfully  
✅ Topics appear correctly in Firestore  
✅ No errors in logs  
✅ Performance acceptable  
✅ Error handling works  

**Ready for deployment when all criteria met.**

