# Interactive Review CLI

Interactive command-line interface for reviewing and curating content in the Content Engine system.

## Quick Start

From the `backend` directory:

```bash
# Review topics
poetry run python review topics

# Review scripts
poetry run python review scripts

# Review integrity/ethics
poetry run python review integrity

# Review style profiles
poetry run python review styles
```

## Commands

### `review topics`

Interactive topic review workflow for approving, rejecting, or deferring topics.

**Usage:**
```bash
poetry run python review topics [OPTIONS]
```

**Options:**
- `--limit INTEGER` - Maximum topics to review (default: 50)
- `--min-score FLOAT` - Minimum score threshold (optional)
- `--status TEXT` - Topic status filter: pending, approved, rejected, deferred (default: pending)
- `--resume TEXT` - Resume from session file (optional)

**Examples:**
```bash
# Review 20 pending topics
poetry run python review topics --limit 20

# Review only high-scoring topics
poetry run python review topics --min-score 0.7

# Review approved topics
poetry run python review topics --status approved

# Resume interrupted session
poetry run python review topics --resume .review_session.json
```

**Interactive Actions:**
- `[1-10]` - Select a topic by number
- `[A]pprove` - Approve the topic
- `[R]eject` - Reject the topic (will prompt for reason code)
- `[D]efer` - Defer for later review
- `[S]kip` - Skip this topic
- `[B]ack` - Go back to topic list
- `[U]ndo` - Undo last action
- `[N]ext` - Next page
- `[Q]uit` - Save and exit

**Rejection Reason Codes:**
1. Too generic
2. Not on brand
3. Speculative
4. Duplicate
5. Ethics

### `review scripts`

Interactive script/content review workflow for reviewing hooks and scripts.

**Usage:**
```bash
poetry run python review scripts [OPTIONS]
```

**Options:**
- `--limit INTEGER` - Maximum topics to review (default: 20)

**Examples:**
```bash
# Review scripts for approved topics
poetry run python review scripts

# Review with custom limit
poetry run python review scripts --limit 10
```

**Interactive Actions:**
- `[1-3]` - Select a hook by number
- `[E]dit` - Edit script (collects notes)
- `[R]efine` - AI refine script (tighten/casual/regenerate)
- `[M]ark ready` - Mark as ready for publication
- `[F]lag ethics` - Flag for ethics review
- `[S]kip` - Skip this topic

**Refinement Types:**
- `[T]ighten` - Make script more concise and punchy
- `[C]asual` - Adjust tone to be more conversational
- `[R]egenerate` - Fresh wording while keeping core message

### `review integrity`

Interactive integrity/ethics review workflow for reviewing flagged content.

**Usage:**
```bash
poetry run python review integrity [OPTIONS]
```

**Options:**
- `--limit INTEGER` - Maximum items to review (default: 20)

**Examples:**
```bash
# Review flagged topics
poetry run python review integrity

# Review with custom limit
poetry run python review integrity --limit 10
```

**Interactive Actions:**
- `[P]ublish as-is` - Publish despite integrity flag
- `[R]eframe` - Request content reframe
- `[S]kip` - Skip this item

**Risk Levels:**
- 🔴 High risk (integrity penalty < -0.3)
- 🟡 Medium risk (integrity penalty < -0.2)
- 🟢 Low risk (integrity penalty >= -0.2)

### `review styles`

Interactive style profile curation workflow for reviewing extracted style profiles.

**Usage:**
```bash
poetry run python review styles [OPTIONS]
```

**Options:**
- `--limit INTEGER` - Maximum profiles to review (default: 20)
- `--status TEXT` - Profile status filter: pending, approved, rejected, all (default: pending)

**Examples:**
```bash
# Review pending style profiles
poetry run python review styles

# Review approved profiles
poetry run python review styles --status approved

# Review with custom limit
poetry run python review styles --limit 10
```

**Interactive Actions:**
- `[A]pprove` - Approve style profile
- `[R]eject` - Reject style profile (will prompt for reason)
- `[T]est` - Test profile generation (not yet implemented)
- `[S]kip` - Skip this profile

## Features

### Rich Terminal UI
- Color-coded tables and panels
- Progress indicators
- Score breakdowns with visual formatting
- Keyboard shortcuts for quick actions

### Session Management
- Auto-saves session state every 10 items
- Resume interrupted sessions with `--resume`
- Session file: `.review_session.json`
- Tracks processed items to avoid duplicates

### Progress Tracking
- Real-time statistics: `✓ Approved 3 | ✗ Rejected 2 | ⏸ Deferred 1 | Remaining 4`
- Current item indicator: `Reviewing item 3 of 10`

### Error Handling
- Graceful handling of missing Firestore indexes (fallback to in-memory sorting)
- Retry logic with exponential backoff for network operations
- Clear error messages with actionable guidance

### Undo Support
- Undo last action with `[U]ndo`
- Only available for current session (before exit)

## Workflow Example

```bash
# 1. Start with topic review
cd backend
poetry run python review topics --limit 10

# You'll see a paginated table of topics with scores
# Select a topic, review details, and approve/reject/defer

# 2. After approving topics, review scripts
poetry run python review scripts

# Review hooks and scripts, refine if needed, mark ready

# 3. Check integrity if needed
poetry run python review integrity

# Review any flagged content

# 4. Curate styles
poetry run python review styles

# Approve or reject extracted style profiles
```

## Prerequisites

1. **Firestore Connection**: Ensure GCP credentials are configured
2. **Data Available**: Topics must be ingested and scored first:
   ```bash
   poetry run python -m src.cli.main ingest-topics
   poetry run python -m src.cli.main score-topics
   ```
3. **Interactive Terminal**: Commands require an interactive terminal (not piped input)

## Session Files

Session state is saved to `.review_session.json` in the current working directory:

```json
{
  "workflow": "topics",
  "processed_ids": ["topic-1", "topic-2"],
  "stats": {
    "approved": 1,
    "rejected": 1,
    "deferred": 0,
    "skipped": 0
  },
  "last_action": {
    "topic_id": "topic-2",
    "old_status": "pending",
    "new_status": "rejected",
    "action": "r"
  },
  "saved_at": "2026-01-08T23:49:05.479676+00:00"
}
```

Resume a session:
```bash
poetry run python review topics --resume .review_session.json
```

## Keyboard Shortcuts

### Topic Review
- `1-10` - Select topic
- `A` - Approve
- `R` - Reject
- `D` - Defer
- `S` - Skip
- `B` - Back
- `U` - Undo
- `N` - Next page
- `Q` - Quit

### Script Review
- `1-3` - Select hook
- `E` - Edit
- `R` - Refine
- `M` - Mark ready
- `F` - Flag ethics
- `S` - Skip

### Integrity Review
- `P` - Publish as-is
- `R` - Reframe
- `S` - Skip

### Style Review
- `A` - Approve
- `R` - Reject
- `T` - Test
- `S` - Skip

## Tips

1. **Batch Size**: Use `--limit` to control how many items you review in one session
2. **Score Filtering**: Use `--min-score` to focus on high-quality topics
3. **Quick Exit**: Press `Q` anytime to save progress and exit
4. **Undo Mistakes**: Use `[U]ndo` to revert the last action
5. **Resume Later**: Session files let you resume interrupted reviews
6. **Progress Tracking**: Watch the progress indicator to see your review stats

## Troubleshooting

### "Non-interactive terminal detected"
- Ensure you're running in an interactive terminal (not piped)
- Commands require user input, so they won't work in scripts

### "No pending topics found"
- Run `ingest-topics` and `score-topics` first
- Check topic status with `--status` option

### "The query requires an index"
- The CLI automatically falls back to in-memory sorting
- For better performance, create the suggested Firestore index

### Typer Integration Issue
- If `poetry run python -m src.cli.main review` fails, use the direct wrapper:
  ```bash
  poetry run python review topics
  ```

## Architecture

The CLI is organized into:

- `review.py` - Main review command and subcommands
- `review_utils.py` - Shared utilities (display, prompts, session management)
- `reviewers/` - Individual reviewer implementations:
  - `topic_reviewer.py` - Topic review workflow
  - `script_reviewer.py` - Script review workflow
  - `integrity_reviewer.py` - Integrity review workflow
  - `style_reviewer.py` - Style curation workflow

## Dependencies

- `typer` - CLI framework
- `rich` - Terminal formatting and UI
- `asyncio` - Async operations
- Firestore services for data access

