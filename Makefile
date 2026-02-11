.PHONY: help install dev test lint format clean docker-up docker-down migrate backup

# Variables
PYTHON := python3.11
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
RUFF := $(PYTHON) -m ruff
MYPY := $(PYTHON) -m mypy
DOCKER_COMPOSE := docker compose

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup & Installation
install: ## Install production dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-dev.txt
	pre-commit install

dev: install-dev ## Setup development environment
	cp env.example .env
	@echo "Development environment ready. Edit .env with your credentials."

# Code Quality
lint: ## Run all linters
	$(RUFF) check src/ tests/
	$(MYPY) src/
	$(BLACK) --check src/ tests/

format: ## Format code with black
	$(BLACK) src/ tests/
	$(RUFF) check --fix src/ tests/

type-check: ## Run mypy type checking
	$(MYPY) src/ --strict

security: ## Run security checks
	gitleaks detect --source . --verbose
	$(PYTHON) -m bandit -r src/ -f json -o reports/bandit.json

# Testing
test: ## Run all tests
	$(PYTEST) tests/ -v

test-unit: ## Run unit tests only
	$(PYTEST) tests/ -m unit -v

test-integration: ## Run integration tests only
	$(PYTEST) tests/ -m integration -v

test-e2e: ## Run end-to-end tests
	$(PYTEST) tests/ -m e2e -v

test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	$(PYTEST) tests/ -f -v

# Docker Operations
docker-build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

docker-up: ## Start all services
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop all services
	$(DOCKER_COMPOSE) down

docker-logs: ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

docker-ps: ## List running containers
	$(DOCKER_COMPOSE) ps

docker-restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

docker-clean: ## Remove all containers, volumes, and images
	$(DOCKER_COMPOSE) down -v --rmi all

# Database Operations
migrate: ## Run database migrations
	$(DOCKER_COMPOSE) run --rm migration alembic upgrade head

migrate-create: ## Create new migration (NAME required)
	$(DOCKER_COMPOSE) run --rm migration alembic revision --autogenerate -m "$(NAME)"

migrate-down: ## Rollback last migration
	$(DOCKER_COMPOSE) run --rm migration alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec timescaledb psql -U pets_user -d pets

redis-shell: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# Backup & Recovery
backup: ## Create database backup
	$(DOCKER_COMPOSE) exec backup /scripts/backup.sh

restore: ## Restore database from backup (BACKUP_FILE required)
	$(DOCKER_COMPOSE) exec backup /scripts/restore.sh $(BACKUP_FILE)

# Bot Management
bot-start: ## Start specific bot (BOT_ID required)
	curl -X POST http://localhost:8000/api/v1/bots/$(BOT_ID)/start

bot-stop: ## Stop specific bot (BOT_ID required)
	curl -X POST http://localhost:8000/api/v1/bots/$(BOT_ID)/stop

bot-status: ## Get bot status (BOT_ID required)
	curl http://localhost:8000/api/v1/bots/$(BOT_ID)

emergency-halt: ## Emergency halt all bots
	curl -X POST http://localhost:8000/api/v1/risk/emergency-halt

# Monitoring
metrics: ## View Prometheus metrics
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

logs-api: ## View API logs
	$(DOCKER_COMPOSE) logs -f api

logs-bot: ## View bot logs (BOT_ID required)
	$(DOCKER_COMPOSE) logs -f bot_$(BOT_ID)

health: ## Check system health
	curl http://localhost:8000/api/v1/health/live
	curl http://localhost:8000/api/v1/health/ready

# Cleanup
clean: ## Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml

clean-all: clean docker-clean ## Clean everything

# Development Helpers
shell: ## Open Python shell with project context
	$(PYTHON) -i -c "import sys; sys.path.insert(0, 'src')"

notebook: ## Start Jupyter notebook
	jupyter notebook notebooks/

dashboard: ## Start Streamlit dashboard locally
	streamlit run src/presentation/dashboard/app.py

api: ## Start FastAPI locally
	uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

# CI/CD
ci: lint type-check test-cov security ## Run all CI checks

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Documentation
docs: ## Generate documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

# Version Info
version: ## Show version info
	@echo "PETS - Polymarket Elite Trading System"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) version)"
