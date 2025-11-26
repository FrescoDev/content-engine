# Content Engine Backend

AI-powered content intelligence and production system backend.

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Configure `.env` with your GCP project ID, OpenAI API key, and other settings.

4. Run tests:
```bash
poetry run pytest
```

## Project Structure

- `src/core/` - Core infrastructure (config, logging, types)
- `src/infra/` - Infrastructure services (Firestore, GCS, OpenAI)
- `src/content/` - Domain models and business logic
- `src/jobs/` - Cloud Run Job implementations
- `src/cli/` - CLI commands

## Development

The backend follows the architecture specified in `backend.md`:
- Python 3.12+
- Poetry for dependency management
- Async/await patterns
- Firestore for data persistence
- GCS for file storage
- OpenAI for LLM operations

