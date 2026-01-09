.PHONY: help install dev build start test lint type-check clean check qa fix
.PHONY: test-watch test-coverage

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Configuration
NPM := npm

help: ## Show this help message
	@echo "$(BLUE)Content Engine Frontend - Available Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(NPM) install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-clean: ## Clean install dependencies
	@echo "$(BLUE)Clean installing dependencies...$(NC)"
	rm -rf node_modules package-lock.json
	$(NPM) install
	@echo "$(GREEN)✓ Clean install complete$(NC)"

# Development
dev: ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	$(NPM) run dev

build: ## Build for production
	@echo "$(BLUE)Building for production...$(NC)"
	$(NPM) run build
	@echo "$(GREEN)✓ Build complete$(NC)"

start: ## Start production server
	@echo "$(BLUE)Starting production server...$(NC)"
	$(NPM) run start

# Testing
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(NPM) test
	@echo "$(GREEN)✓ Tests passed$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(NPM) run test:watch

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(NPM) run test:coverage
	@echo "$(GREEN)✓ Coverage report generated$(NC)"

# Code Quality
lint: ## Lint code
	@echo "$(BLUE)Linting code...$(NC)"
	$(NPM) run lint
	@echo "$(GREEN)✓ No linting issues$(NC)"

lint-fix: ## Auto-fix linting issues
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	$(NPM) run lint -- --fix
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

type-check: ## Type check code
	@echo "$(BLUE)Type checking...$(NC)"
	npx tsc --noEmit
	@echo "$(GREEN)✓ Type checking passed$(NC)"

format-check: ## Check code formatting (Prettier if configured)
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@echo "$(YELLOW)Note: Add prettier to package.json if needed$(NC)"

# Combined checks
check: lint type-check build ## Run all checks (non-destructive)
	@echo "$(GREEN)✓ All checks passed!$(NC)"

qa: lint type-check test build ## Full QA (lint, type-check, test, build)
	@echo "$(GREEN)✓ Full QA passed!$(NC)"

fix: lint-fix ## Auto-fix linting issues
	@echo "$(GREEN)✓ Code fixed!$(NC)"

# Cleanup
clean: ## Clean generated files
	@echo "$(BLUE)Cleaning...$(NC)"
	rm -rf .next/
	rm -rf out/
	rm -rf coverage/
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including node_modules
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf node_modules/
	@echo "$(GREEN)✓ Everything cleaned$(NC)"

# Safety checks
pre-commit: lint type-check ## Run before committing
	@echo "$(GREEN)✓ Ready to commit!$(NC)"

pre-push: qa ## Run before pushing (full QA)
	@echo "$(GREEN)✓ Ready to push!$(NC)"

# CI/CD simulation
ci: install qa ## Simulate CI pipeline
	@echo "$(GREEN)✓ CI checks passed!$(NC)"

