.PHONY: help install dev test lint format clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (Python + Node)
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Start backend + frontend for development
	./scripts/start_dev.sh

test: ## Run Python tests
	pytest tests/ -v --tb=short

lint: ## Run linters (ruff + eslint)
	ruff check .
	cd frontend && npm run lint

format: ## Auto-format code
	ruff format .
	ruff check --fix .

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache htmlcov .coverage
