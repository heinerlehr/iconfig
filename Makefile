# Makefile for iConfig project

.PHONY: help docs docs-serve test lint format clean install

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	uv sync --dev
	uv pip install -e .
	@$(MAKE) build-docs

test:  ## Run tests
	uv run pytest

lint:  ## Run linting
	uv run ruff check .

format:  ## Format code
	uv run black .
	uv run ruff check --fix .

build-docs:  ## Build documentation
	@echo "Building documentation..."
	@cd docs && LC_ALL=C uv run sphinx-build -b html . _build/html
	@echo "Documentation built in docs/_build/html/"

serve-docs:  ## Build and serve documentation locally
	@echo "Building and serving documentation..."
	@cd docs && LC_ALL=C uv run sphinx-build -b html . _build/html
	@echo "Starting web server at http://localhost:8000"
	@cd docs/_build/html && uv run python -m http.server 8000

commit:  ## Build docs and prepare for commit
	@$(MAKE) build-docs
	@echo "Documentation built. Ready to commit."

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete