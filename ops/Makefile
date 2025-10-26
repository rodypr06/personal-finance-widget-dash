.PHONY: help init migrate seed up down restart logs logs-api logs-db test format clean build health backup restore

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Personal Finance Automation - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development Setup
init: ## Initialize development environment (create venv, install deps)
	@echo "$(CYAN)Initializing development environment...$(NC)"
	cd ../api && python3 -m venv .venv
	cd ../api && .venv/bin/pip install --upgrade pip setuptools wheel
	cd ../api && .venv/bin/pip install -r requirements.txt
	cd ../api && .venv/bin/pip install pytest pytest-cov black ruff
	@echo "$(GREEN)✓ Virtual environment created and dependencies installed$(NC)"
	@echo "$(YELLOW)Activate with: source ../api/.venv/bin/activate$(NC)"

# Database Management
migrate: ## Run database migrations (alembic upgrade head)
	@echo "$(CYAN)Running database migrations...$(NC)"
	cd ../api && alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

seed: ## Seed database with initial data
	@echo "$(CYAN)Seeding database...$(NC)"
	@if [ ! -f .env ]; then echo "$(RED)Error: .env file not found. Copy .env.example to .env first.$(NC)"; exit 1; fi
	@. .env && docker compose exec -T postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB < ../seed/seed_rules.sql
	@. .env && docker compose exec -T postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB < ../seed/seed_vendors.sql
	@echo "$(GREEN)✓ Database seeded$(NC)"

# Docker Operations
build: ## Build Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Build completed$(NC)"

up: ## Start all services (docker compose up -d)
	@echo "$(CYAN)Starting services...$(NC)"
	@if [ ! -f .env ]; then echo "$(RED)Error: .env file not found. Copy .env.example to .env first.$(NC)"; exit 1; fi
	docker compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)Run 'make logs' to view logs or 'make health' to check status$(NC)"

down: ## Stop all services (docker compose down)
	@echo "$(CYAN)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(CYAN)Restarting services...$(NC)"
	docker compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

# Logs
logs: ## Tail logs from all services
	docker compose logs -f

logs-api: ## Tail logs from API service only
	docker compose logs -f api

logs-db: ## Tail logs from PostgreSQL service only
	docker compose logs -f postgres

# Testing
test: ## Run tests with pytest
	@echo "$(CYAN)Running tests...$(NC)"
	cd ../api && .venv/bin/pytest -q --cov=app --cov-report=term-missing
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(CYAN)Running tests (verbose)...$(NC)"
	cd ../api && .venv/bin/pytest -v --cov=app --cov-report=html
	@echo "$(GREEN)✓ Tests completed. Coverage report: ../api/htmlcov/index.html$(NC)"

# Code Quality
format: ## Format code with ruff and black
	@echo "$(CYAN)Formatting code...$(NC)"
	cd ../api && .venv/bin/ruff check --fix app/ tests/
	cd ../api && .venv/bin/black app/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code with ruff
	@echo "$(CYAN)Linting code...$(NC)"
	cd ../api && .venv/bin/ruff check app/ tests/
	@echo "$(GREEN)✓ Linting completed$(NC)"

# Maintenance
health: ## Check health status of all services
	@echo "$(CYAN)Checking service health...$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(CYAN)API Health Check:$(NC)"
	@curl -f http://localhost:8080/health 2>/dev/null && echo "$(GREEN)✓ API is healthy$(NC)" || echo "$(RED)✗ API is not responding$(NC)"

clean: ## Clean up containers, volumes, and cache files
	@echo "$(YELLOW)Warning: This will remove all containers, volumes, and cached data.$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(CYAN)Cleaning up...$(NC)"; \
		docker compose down -v; \
		cd ../api && rm -rf .venv __pycache__ .pytest_cache .ruff_cache htmlcov .coverage; \
		find ../api -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
		echo "$(GREEN)✓ Cleanup completed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

# Backup & Restore
backup: ## Backup PostgreSQL database
	@echo "$(CYAN)Creating database backup...$(NC)"
	@mkdir -p backups
	@. .env && docker compose exec -T postgres pg_dump -U $$POSTGRES_USER $$POSTGRES_DB | gzip > backups/finance_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)✓ Backup created in backups/$(NC)"

restore: ## Restore PostgreSQL database (usage: make restore FILE=backups/finance_20250124.sql.gz)
	@if [ -z "$(FILE)" ]; then echo "$(RED)Error: Please specify FILE=path/to/backup.sql.gz$(NC)"; exit 1; fi
	@echo "$(YELLOW)Warning: This will overwrite the current database.$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(CYAN)Restoring database...$(NC)"; \
		. .env && gunzip < $(FILE) | docker compose exec -T postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB; \
		echo "$(GREEN)✓ Database restored$(NC)"; \
	else \
		echo "$(YELLOW)Restore cancelled$(NC)"; \
	fi

# Quick Start
quickstart: init up migrate seed ## Complete setup: init, up, migrate, seed
	@echo ""
	@echo "$(GREEN)✓✓✓ Quick start completed! ✓✓✓$(NC)"
	@echo ""
	@echo "$(CYAN)Your Personal Finance Automation system is ready!$(NC)"
	@echo "  • API: http://localhost:8080"
	@echo "  • Dashboard: http://localhost:8080/dashboard"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Configure n8n workflows"
	@echo "  2. Set up Google Drive integration"
	@echo "  3. Upload test statements"
	@echo ""
