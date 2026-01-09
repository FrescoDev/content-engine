.PHONY: help install dev test lint clean check qa fix verify ci
.PHONY: backend-% frontend-%

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BOLD := \033[1m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║       Content Engine - Root Makefile Commands            ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BOLD)Full Stack Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "backend-\|frontend-" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Backend Commands:$(NC)"
	@echo "  $(YELLOW)backend-<cmd>$(NC)        Run backend command (e.g., backend-test)"
	@echo "  See backend/Makefile for full list"
	@echo ""
	@echo "$(BOLD)Frontend Commands:$(NC)"
	@echo "  $(YELLOW)frontend-<cmd>$(NC)       Run frontend command (e.g., frontend-test)"
	@echo "  See frontend/Makefile for full list"

# Installation
install: ## Install all dependencies (backend + frontend)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	@$(MAKE) backend-install
	@$(MAKE) frontend-install
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

# Development
dev: ## Start both backend shell and frontend dev server
	@echo "$(BLUE)Starting development environment...$(NC)"
	@echo "$(YELLOW)Starting backend in poetry shell and frontend dev server$(NC)"
	@echo "$(YELLOW)Note: Run 'make backend-dev' and 'make frontend-dev' in separate terminals$(NC)"

# Testing
test: ## Run all tests (backend + frontend)
	@echo "$(BLUE)Running all tests...$(NC)"
	@$(MAKE) backend-test
	@$(MAKE) frontend-test
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-fast: ## Run fast tests (no coverage)
	@echo "$(BLUE)Running fast tests...$(NC)"
	@$(MAKE) backend-test-fast
	@$(MAKE) frontend-test
	@echo "$(GREEN)✓ Fast tests passed$(NC)"

# Code Quality
lint: ## Lint all code (backend + frontend)
	@echo "$(BLUE)Linting all code...$(NC)"
	@$(MAKE) backend-lint
	@$(MAKE) frontend-lint
	@echo "$(GREEN)✓ No linting issues$(NC)"

lint-fix: ## Auto-fix linting issues (backend + frontend)
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	@$(MAKE) backend-lint-fix
	@$(MAKE) frontend-lint-fix
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format all code (backend)
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(MAKE) backend-format
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting (backend)
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@$(MAKE) backend-format-check
	@echo "$(GREEN)✓ Code is properly formatted$(NC)"

type-check: ## Type check all code (backend + frontend)
	@echo "$(BLUE)Type checking all code...$(NC)"
	@$(MAKE) backend-type-check
	@$(MAKE) frontend-type-check
	@echo "$(GREEN)✓ Type checking passed$(NC)"

# Combined checks
check: ## Run all checks without modifying code
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║              Running Full Code Quality Checks             ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)1/4 Checking code formatting...$(NC)"
	@$(MAKE) backend-format-check
	@echo ""
	@echo "$(BLUE)2/4 Linting code...$(NC)"
	@$(MAKE) lint
	@echo ""
	@echo "$(BLUE)3/4 Type checking...$(NC)"
	@$(MAKE) type-check
	@echo ""
	@echo "$(BLUE)4/4 Running tests...$(NC)"
	@$(MAKE) test-fast
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ All checks passed! Code is clean.$(NC)"

qa: ## Full QA (format, lint, type-check, test)
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║                  Running Full QA Suite                     ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)1/5 Checking code formatting...$(NC)"
	@$(MAKE) backend-format-check
	@echo ""
	@echo "$(BLUE)2/5 Linting code...$(NC)"
	@$(MAKE) lint
	@echo ""
	@echo "$(BLUE)3/5 Type checking...$(NC)"
	@$(MAKE) type-check
	@echo ""
	@echo "$(BLUE)4/5 Running backend tests with coverage...$(NC)"
	@$(MAKE) backend-test
	@echo ""
	@echo "$(BLUE)5/5 Building frontend...$(NC)"
	@$(MAKE) frontend-build
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ Full QA passed! Ready for production.$(NC)"

fix: ## Auto-fix all issues (format + lint-fix)
	@echo "$(BLUE)Auto-fixing all issues...$(NC)"
	@$(MAKE) backend-fix
	@$(MAKE) frontend-fix
	@echo "$(GREEN)✓ All fixes applied$(NC)"

verify: ## Verify app still works (quick smoke test)
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║            Verifying App Functionality                    ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)Testing backend functionality...$(NC)"
	@$(MAKE) backend-verify-working
	@echo ""
	@echo "$(BLUE)Building frontend...$(NC)"
	@$(MAKE) frontend-build
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ App verification complete! Everything works.$(NC)"

# Cleanup
clean: ## Clean all generated files (backend + frontend)
	@echo "$(BLUE)Cleaning all generated files...$(NC)"
	@$(MAKE) backend-clean
	@$(MAKE) frontend-clean
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: ## Clean everything including dependencies
	@echo "$(BLUE)Cleaning everything...$(NC)"
	@$(MAKE) backend-clean-all
	@$(MAKE) frontend-clean-all
	@echo "$(GREEN)✓ Everything cleaned$(NC)"

# Safety checks before committing/pushing
pre-commit: ## Run before committing (quick checks + auto-fix)
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║                Pre-Commit Checks                          ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@$(MAKE) fix
	@$(MAKE) test-fast
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ Ready to commit!$(NC)"

pre-push: ## Run before pushing (full QA)
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║                  Pre-Push QA Checks                        ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@$(MAKE) qa
	@$(MAKE) verify
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ Ready to push! All checks passed.$(NC)"

# CI/CD simulation
ci: ## Simulate full CI pipeline
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║              Simulating CI Pipeline                       ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@$(MAKE) install
	@$(MAKE) qa
	@$(MAKE) verify
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ CI simulation passed!$(NC)"

# Status and info
status: ## Show project status and health
	@echo "$(BOLD)$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BOLD)$(BLUE)║              Content Engine Status                        ║$(NC)"
	@echo "$(BOLD)$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BOLD)Backend:$(NC)"
	@cd backend && poetry --version 2>/dev/null && echo "  $(GREEN)✓ Poetry available$(NC)" || echo "  $(RED)✗ Poetry not found$(NC)"
	@cd backend && [ -d .venv ] && echo "  $(GREEN)✓ Virtual environment exists$(NC)" || echo "  $(YELLOW)⚠ Virtual environment not created$(NC)"
	@cd backend && [ -f .env ] && echo "  $(GREEN)✓ .env file exists$(NC)" || echo "  $(YELLOW)⚠ .env file missing$(NC)"
	@echo ""
	@echo "$(BOLD)Frontend:$(NC)"
	@cd frontend && npm --version 2>/dev/null && echo "  $(GREEN)✓ npm available$(NC)" || echo "  $(RED)✗ npm not found$(NC)"
	@cd frontend && [ -d node_modules ] && echo "  $(GREEN)✓ node_modules exists$(NC)" || echo "  $(YELLOW)⚠ Dependencies not installed$(NC)"
	@cd frontend && [ -f .env.local ] && echo "  $(GREEN)✓ .env.local file exists$(NC)" || echo "  $(YELLOW)⚠ .env.local file missing$(NC)"
	@echo ""
	@echo "$(BOLD)Documentation:$(NC)"
	@ls -1 *.md 2>/dev/null | wc -l | xargs echo "  Documentation files:" | sed 's/^/  /'
	@echo ""

# Delegated commands (run in subdirectories)
backend-%:
	@$(MAKE) -C backend $*

frontend-%:
	@$(MAKE) -C frontend $*

# Quick shortcuts
b-%: backend-%
	@true

f-%: frontend-%
	@true

