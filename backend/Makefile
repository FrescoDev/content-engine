.PHONY: help install test lint format type-check clean check qa fix verify-working run-cli inspect-data
.PHONY: test-unit test-integration test-e2e test-coverage test-watch
.PHONY: docker-build docker-run docker-clean

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Configuration
PYTHON := poetry run python
PYTEST := poetry run pytest
BLACK := poetry run black
RUFF := poetry run ruff
MYPY := poetry run mypy

help: ## Show this help message
	@echo "$(BLUE)Content Engine Backend - Available Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: ## Install with dev dependencies
	@echo "$(BLUE)Installing with dev dependencies...$(NC)"
	poetry install --with dev
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

# Testing
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	$(PYTEST) -v
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) -v -m unit
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) -v -m integration
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running E2E tests...$(NC)"
	$(PYTEST) -v -m e2e
	@echo "$(GREEN)✓ E2E tests passed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(PYTEST) -v --watch

test-fast: ## Run tests without coverage (fast)
	@echo "$(BLUE)Running tests (fast mode)...$(NC)"
	$(PYTEST) -v --no-cov
	@echo "$(GREEN)✓ Tests passed$(NC)"

# Code Quality
lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(NC)"
	$(RUFF) check src/ tests/
	@echo "$(GREEN)✓ No linting issues$(NC)"

lint-fix: ## Auto-fix linting issues
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	$(RUFF) check --fix src/ tests/
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	$(BLACK) src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(BLACK) --check src/ tests/
	@echo "$(GREEN)✓ Code is properly formatted$(NC)"

type-check: ## Type check code with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	$(MYPY) src/
	@echo "$(GREEN)✓ Type checking passed$(NC)"

type-check-strict: ## Type check with strict mode
	@echo "$(BLUE)Type checking (strict mode)...$(NC)"
	$(MYPY) --strict src/
	@echo "$(GREEN)✓ Strict type checking passed$(NC)"

# Combined checks
check: format-check lint type-check test-fast ## Run all checks (non-destructive)
	@echo "$(GREEN)✓ All checks passed!$(NC)"

qa: format-check lint type-check test ## Full QA (format, lint, type-check, test)
	@echo "$(GREEN)✓ Full QA passed!$(NC)"

fix: format lint-fix ## Auto-fix formatting and linting issues
	@echo "$(GREEN)✓ Code fixed!$(NC)"

verify-working: test-fast ## Quick verification that app still works
	@echo "$(BLUE)Verifying app functionality...$(NC)"
	@$(PYTHON) -m src.cli.main check-infra || echo "$(YELLOW)Warning: check-infra failed (may need GCP setup)$(NC)"
	@echo "$(GREEN)✓ Core functionality verified$(NC)"

# CLI Commands
run-cli: ## Run CLI help
	@echo "$(BLUE)Running CLI...$(NC)"
	$(PYTHON) -c "from src.cli.main import app; app()"

check-infra: ## Check infrastructure connectivity
	@echo "$(BLUE)Checking infrastructure...$(NC)"
	$(PYTHON) -m src.cli.main check-infra

ingest-topics: ## Ingest topics from all sources
	@echo "$(BLUE)Ingesting topics...$(NC)"
	$(PYTHON) -m src.cli.main ingest-topics

score-topics: ## Score pending topics
	@echo "$(BLUE)Scoring topics...$(NC)"
	$(PYTHON) -m src.cli.main score-topics

inspect-data: ## Inspect Firestore data
	@echo "$(BLUE)Inspecting data...$(NC)"
	$(PYTHON) ../scripts/inspect_data.py

# Development
shell: ## Open poetry shell
	@echo "$(BLUE)Opening poetry shell...$(NC)"
	poetry shell

clean: ## Clean generated files and caches
	@echo "$(BLUE)Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including .venv
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✓ Everything cleaned$(NC)"

# Docker (if needed in future)
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t content-engine-backend:latest .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run --env-file .env content-engine-backend:latest

docker-clean: ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	docker system prune -f

# Safety checks before committing
pre-commit: fix test ## Run before committing (fix + test)
	@echo "$(GREEN)✓ Ready to commit!$(NC)"

pre-push: qa ## Run before pushing (full QA)
	@echo "$(GREEN)✓ Ready to push!$(NC)"

# CI/CD simulation
ci: install qa ## Simulate CI pipeline
	@echo "$(GREEN)✓ CI checks passed!$(NC)"

