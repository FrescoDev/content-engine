# Interactive Review CLI Usage

## Quick Start

From the `backend` directory:

```bash
# Topic review
poetry run python review topics

# Script review  
poetry run python review scripts

# Integrity review
poetry run python review integrity

# Style curation
poetry run python review styles
```

## Alternative: Direct Python Execution

```bash
cd backend
poetry run python -c "import sys; sys.argv = ['review', 'topics']; from src.cli.review import review_app; review_app()"
```

## Known Issue

There's a typer integration issue when calling through `main.py`. Use the direct wrapper above or call `review_app` directly.
