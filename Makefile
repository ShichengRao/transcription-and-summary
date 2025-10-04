.PHONY: help install test lint format clean all pre-commit-install pre-commit-run

help:
	@echo "Available commands:"
	@echo "  make install            - Install dependencies"
	@echo "  make test               - Run tests with pytest"
	@echo "  make lint               - Run linters (flake8, pylint)"
	@echo "  make format             - Format code with black and isort"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit on all files"
	@echo "  make clean              - Clean up generated files"
	@echo "  make all                - Format, lint, and test"

install:
	pip install -r requirements.txt
	pre-commit install

pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

pre-commit-run:
	pre-commit run --all-files

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running pylint..."
	pylint src/ --exit-zero

format:
	@echo "Running isort..."
	isort src/ tests/
	@echo "Running black..."
	black src/ tests/

format-check:
	@echo "Checking isort..."
	isort --check-only src/ tests/
	@echo "Checking black..."
	black --check src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

all: format lint test
	@echo "All checks passed!"
