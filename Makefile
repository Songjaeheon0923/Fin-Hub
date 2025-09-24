# Fin-Hub Development Makefile

.PHONY: help setup-dev build up down logs clean test lint format docs

# Default target
help: ## Show help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Setup
setup-dev: ## Setup development environment
	@echo "Setting up development environment..."
	@./scripts/setup/init.sh
	@echo "Installing pre-commit hooks..."
	@pre-commit install

# Docker Operations
build: ## Build all Docker images
	@echo "Building Docker images..."
	@docker-compose build --parallel

up: ## Start all services
	@echo "Starting all services..."
	@docker-compose up -d

down: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down

restart: ## Restart all services
	@make down
	@make up

logs: ## Show logs for all services
	@docker-compose logs -f

logs-hub: ## Show logs for hub-server
	@docker-compose logs -f hub-server

logs-market: ## Show logs for market-spoke
	@docker-compose logs -f market-spoke

logs-risk: ## Show logs for risk-spoke
	@docker-compose logs -f risk-spoke

logs-pfolio: ## Show logs for pfolio-spoke
	@docker-compose logs -f pfolio-spoke

# Development Servers
dev-hub: ## Start hub-server in development mode
	@cd services/hub-server && python -m uvicorn app.main:app --reload --port 8000

dev-market: ## Start market-spoke in development mode
	@cd services/market-spoke && python -m uvicorn app.main:app --reload --port 8001

dev-risk: ## Start risk-spoke in development mode
	@cd services/risk-spoke && python -m uvicorn app.main:app --reload --port 8002

dev-pfolio: ## Start pfolio-spoke in development mode
	@cd services/pfolio-spoke && python -m uvicorn app.main:app --reload --port 8003

# Testing
test: ## Run all tests
	@echo "Running all tests..."
	@python -m pytest tests/ -v

test-unit: ## Run unit tests
	@python -m pytest tests/unit/ -v

test-integration: ## Run integration tests
	@python -m pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	@python -m pytest tests/e2e/ -v

test-load: ## Run load tests
	@python -m pytest tests/load/ -v

# Code Quality
lint: ## Run linting
	@echo "Running linting..."
	@ruff check .
	@mypy services/

format: ## Format code
	@echo "Formatting code..."
	@black .
	@isort .
	@ruff format .

# Database Operations
db-migrate: ## Run database migrations
	@cd services/hub-server && alembic upgrade head

db-migration: ## Create new migration (Usage: make db-migration message="description")
	@cd services/hub-server && alembic revision --autogenerate -m "$(message)"

db-reset: ## Reset database
	@docker-compose exec postgres psql -U fin_hub -d fin_hub_registry -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@make db-migrate

# Monitoring
status: ## Show service status
	@docker-compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq .
	@curl -s http://localhost:8001/health | jq .
	@curl -s http://localhost:8002/health | jq .
	@curl -s http://localhost:8003/health | jq .

metrics: ## Show Prometheus metrics
	@open http://localhost:9090

dashboard: ## Open Grafana dashboard
	@open http://localhost:3000

# Documentation
docs: ## Generate API documentation
	@echo "Generating API documentation..."
	@cd documentation/api && make build

docs-serve: ## Serve documentation locally
	@cd documentation && python -m http.server 8080

# Cleanup
clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	@docker-compose down -v
	@docker system prune -f

clean-all: ## Clean up all Docker resources including images
	@echo "Cleaning up all Docker resources..."
	@docker-compose down -v --rmi all
	@docker system prune -af

# Deployment
deploy-dev: ## Deploy to development environment
	@echo "Deploying to development environment..."
	@./scripts/deployment/deploy-dev.sh

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production environment..."
	@./scripts/deployment/deploy-prod.sh

# Utility
shell-hub: ## Open shell in hub-server container
	@docker-compose exec hub-server /bin/bash

shell-market: ## Open shell in market-spoke container
	@docker-compose exec market-spoke /bin/bash

shell-risk: ## Open shell in risk-spoke container
	@docker-compose exec risk-spoke /bin/bash

shell-pfolio: ## Open shell in pfolio-spoke container
	@docker-compose exec pfolio-spoke /bin/bash

# MCP Testing
mcp-test: ## Test MCP server functionality
	@echo "Testing MCP server functionality..."
	@python tools/cli/mcp_test.py

# Environment
env-create: ## Create environment file from template
	@cp .env.template .env
	@echo "Created .env file. Please edit it with your settings."