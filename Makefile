.PHONY: help install install-dev clean dev test test-cov lint format pre-commit docker-build docker-up docker-down migrate backup

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
RESET := \033[0m

help:
	@echo "$(GREEN)Available commands:$(RESET)"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make clean        - Remove cache and build files"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make pre-commit   - Run pre-commit hooks"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make migrate      - Run database migrations"
	@echo "  make backup       - Backup database"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v

test-unit:
	pytest tests/ -m unit -v

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports
	black --check src/ tests/

format:
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

pre-commit:
	pre-commit run --all-files

docker-build:
	docker build -f docker/Dockerfile -t transpilation-api:latest .
	docker tag transpilation-api:latest transpilation-api:$(shell date +%Y%m%d)

docker-up:
	docker-compose -f docker/docker-compose.yml up -d
	@echo "$(GREEN)Docker containers started$(RESET)"
	@echo "API available at: http://localhost:8000"
	@echo "API docs at: http://localhost:8000/docs"

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f

migrate:
	python scripts/init_db.py

backup:
	@mkdir -p backups
	docker exec -t transpilation-db pg_dump -U postgres transpilation > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/$(RESET)"