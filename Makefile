# Agentic Company Makefile
# Common commands for development and deployment

.PHONY: help install dev test lint format serve docker-build docker-up docker-down clean

# Default target
help:
	@echo "Agentic Company Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make dev          Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run all tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Run linters"
	@echo "  make format       Format code"
	@echo "  make serve        Start development server"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-up    Start all services"
	@echo "  make docker-down  Stop all services"
	@echo "  make docker-dev   Start development mode"
	@echo "  make docker-logs  View logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod         Start production server"
	@echo "  make monitoring   Start with monitoring stack"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        Clean build artifacts"
	@echo "  make health       Check system health"

# ============== Setup ==============

install:
	pip install -e .

dev:
	pip install -e ".[dev,anthropic,openai]"
	pre-commit install || true

# ============== Testing ==============

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=orchestration --cov-report=html --cov-report=term

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m integration

test-stress:
	pytest tests/test_stress.py -v --timeout=300

# ============== Code Quality ==============

lint:
	ruff check orchestration/ tests/
	mypy orchestration/ --ignore-missing-imports

format:
	black orchestration/ tests/
	ruff check --fix orchestration/ tests/

# ============== Development Server ==============

serve:
	uvicorn orchestration.api:app --reload --host 0.0.0.0 --port 8000

serve-prod:
	uvicorn orchestration.api:app --host 0.0.0.0 --port 8000 --workers 4

# ============== CLI ==============

cli-health:
	python -m orchestration.cli health

cli-config:
	python -m orchestration.cli config show

# ============== Docker ==============

docker-build:
	docker build -t agentic:latest .

docker-build-dev:
	docker build -t agentic:dev --target development .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-dev:
	docker-compose --profile dev up -d

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --rmi local

# ============== Production ==============

prod:
	docker-compose up -d agentic redis

monitoring:
	docker-compose --profile monitoring up -d

tracing:
	docker-compose --profile tracing up -d

postgres:
	docker-compose --profile postgres up -d

celery:
	docker-compose --profile celery up -d

full-stack:
	docker-compose --profile monitoring --profile postgres --profile celery up -d

# ============== Database ==============

db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-reset:
	alembic downgrade base && alembic upgrade head

# ============== Utilities ==============

health:
	curl -s http://localhost:8000/health | python -m json.tool

metrics:
	curl -s http://localhost:8000/metrics | python -m json.tool

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ============== Documentation ==============

docs:
	mkdocs serve

docs-build:
	mkdocs build

# ============== Release ==============

version:
	@python -c "from orchestration._version import __version__; print(__version__)"

release-patch:
	bump2version patch

release-minor:
	bump2version minor

release-major:
	bump2version major
