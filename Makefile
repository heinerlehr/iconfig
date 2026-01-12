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

build-docs:  ## Build documentation
	@echo "Building documentation..."
	@cd docs && LC_ALL=C uv run sphinx-build -b html . _build/html
	@echo "Documentation built in docs/_build/html/"

serve-docs:  ## Build and serve documentation locally
	@echo "Building and serving documentation..."
	@cd docs && LC_ALL=C uv run sphinx-build -b html . _build/html
	@echo "Starting web server at http://localhost:8000"
	@cd docs/_build/html && uv run python -m http.server 8000

build:  ## Build distribution packages
	@echo "Building distribution packages..."
	@rm -rf dist/ build/
	uv run python -m build
	@echo "Distribution packages built in dist/"

pre-commit:  ## Run all pre-commit checks (lint, test, docs)
	@echo "Running pre-commit checks..."
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) build-docs
	@echo "All pre-commit checks passed. Ready to commit."

commit:  ## Build docs, distribution, and prepare for commit
	@$(MAKE) pre-commit
	@$(MAKE) build
	@echo "Ready to commit."

version-patch:  ## Bump patch version (0.1.8 -> 0.1.9)
	@echo "Bumping patch version..."
	@python3 -c "\
import re; \
content = open('pyproject.toml').read(); \
version = re.search(r'version = \"(\d+\.\d+\.\d+)\"', content).group(1); \
parts = version.split('.'); \
parts[2] = str(int(parts[2]) + 1); \
new_version = '.'.join(parts); \
new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
open('pyproject.toml', 'w').write(new_content); \
print(f'Version bumped: {version} -> {new_version}'); \
"

version-minor:  ## Bump minor version (0.1.8 -> 0.2.0)
	@echo "Bumping minor version..."
	@python3 -c "\
import re; \
content = open('pyproject.toml').read(); \
version = re.search(r'version = \"(\d+\.\d+\.\d+)\"', content).group(1); \
parts = version.split('.'); \
parts[1] = str(int(parts[1]) + 1); \
parts[2] = '0'; \
new_version = '.'.join(parts); \
new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
open('pyproject.toml', 'w').write(new_content); \
print(f'Version bumped: {version} -> {new_version}'); \
"

version-major:  ## Bump major version (0.1.8 -> 1.0.0)
	@echo "Bumping major version..."
	@python3 -c "\
import re; \
content = open('pyproject.toml').read(); \
version = re.search(r'version = \"(\d+\.\d+\.\d+)\"', content).group(1); \
parts = version.split('.'); \
parts[0] = str(int(parts[0]) + 1); \
parts[1] = '0'; \
parts[2] = '0'; \
new_version = '.'.join(parts); \
new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
open('pyproject.toml', 'w').write(new_content); \
print(f'Version bumped: {version} -> {new_version}'); \
"

release:  ## Build and publish to PyPI (manual git commit required)
	@echo "Starting release process..."
	@$(MAKE) commit
	@echo "Publishing to PyPI using token from ~/.pypirc..."
	@uv run twine upload dist/* --skip-existing
	@echo "✅ Release complete! Now run: git add -A && git commit -m 'Release vX.X.X' && git push"

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete