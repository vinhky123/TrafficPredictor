# TrafficPredictor - Makefile for common development commands
# Usage: make <target>

.PHONY: help backend-install backend-test backend-lint frontend-install frontend-test frontend-build \
        docker-build docker-run docker-stop terraform-init terraform-plan terraform-apply pre-commit-install

# ── Default target ────────────────────────────────────────────────────────
help: ## Show this help message
	@echo "TrafficPredictor - Available commands:"
	@echo ""
	@echo "  Backend:"
	@echo "    make backend-install     Install backend dependencies"
	@echo "    make backend-test        Run backend tests"
	@echo "    make backend-lint        Run backend linter"
	@echo "    make backend-run         Run backend server"
	@echo ""
	@echo "  Frontend:"
	@echo "    make frontend-install    Install frontend dependencies"
	@echo "    make frontend-test       Run frontend tests"
	@echo "    make frontend-build      Build frontend for production"
	@echo "    make frontend-dev        Run frontend dev server"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-build        Build all Docker images"
	@echo "    make docker-run          Start all services with Docker Compose"
	@echo "    make docker-stop         Stop all services"
	@echo "    make docker-logs         View service logs"
	@echo ""
	@echo "  Infrastructure:"
	@echo "    make terraform-init      Initialize Terraform"
	@echo "    make terraform-plan      Plan infrastructure changes"
	@echo "    make terraform-apply     Apply infrastructure changes"
	@echo ""
	@echo "  Development:"
	@echo "    make pre-commit-install  Install pre-commit hooks"
	@echo "    make clean               Clean build artifacts"

# ── Backend ───────────────────────────────────────────────────────────────
backend-install: ## Install backend dependencies
	@cd backend && pip install -r requirements.txt
	@pip install pytest pytest-cov pytest-mock ruff mypy

backend-test: ## Run backend tests
	@pytest tests/ -v --tb=short --cov=backend --cov-report=term-missing

backend-lint: ## Run backend linter
	@ruff check backend/ tests/
	@ruff format --check backend/ tests/

backend-run: ## Run backend server
	@cd backend && python -m app.app

# ── Frontend ──────────────────────────────────────────────────────────────
frontend-install: ## Install frontend dependencies
	@cd web && npm install

frontend-test: ## Run frontend tests
	@cd web && npm test

frontend-build: ## Build frontend for production
	@cd web && npm run build

frontend-dev: ## Run frontend dev server
	@cd web && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────
docker-build: ## Build all Docker images
	@docker compose build

docker-run: ## Start all services with Docker Compose
	@docker compose up -d
	@echo "Services started:"
	@echo "  Backend API:  http://localhost:5000"
	@echo "  Airflow UI:   http://localhost:8080 (airflow / airflow)"
	@echo "  MongoDB:      localhost:27017"

docker-stop: ## Stop all services
	@docker compose down

docker-logs: ## View service logs
	@docker compose logs -f

docker-restart: docker-stop docker-run ## Restart all services

# ── Terraform ─────────────────────────────────────────────────────────────
terraform-init: ## Initialize Terraform
	@cd infra && terraform init

terraform-plan: ## Plan infrastructure changes
	@cd infra && terraform plan -var-file=environments/dev.tfvars \
		-var="docdb_master_password=$$DOCDB_PASSWORD"

terraform-apply: ## Apply infrastructure changes
	@cd infra && terraform apply -var-file=environments/dev.tfvars \
		-var="docdb_master_password=$$DOCDB_PASSWORD"

terraform-destroy: ## Destroy all infrastructure
	@cd infra && terraform destroy -var-file=environments/dev.tfvars \
		-var="docdb_master_password=$$DOCDB_PASSWORD"

# ── Development Tools ─────────────────────────────────────────────────────
pre-commit-install: ## Install pre-commit hooks
	@pip install pre-commit
	@pre-commit install

# ── Cleanup ───────────────────────────────────────────────────────────────
clean: ## Clean build artifacts
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@cd web && rm -rf .next/ node_modules/
	@echo "Cleaned up build artifacts"