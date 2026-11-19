.PHONY: help install lint format test dev worker docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install     Install Python dependencies"
	@echo "  make lint        Run Ruff linter and Mypy type-checker"
	@echo "  make format      Auto-format code with Ruff"
	@echo "  make test        Run test suite with Pytest"
	@echo "  make dev         Run FastAPI backend locally"
	@echo "  make worker      Run Celery worker locally"
	@echo "  make docker-up   Start all services via Docker Compose"
	@echo "  make docker-down Stop all Docker Compose services"
	@echo "  make clean       Clean up Python cache files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

lint:
	ruff check .
	mypy backend

format:
	ruff format .

test:
	pytest -v backend/tests

dev:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	celery -A backend.app.workers.celery_app worker --loglevel=info -Q default,retries,dlq -c 4 -Ofair

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache
