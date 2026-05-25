.PHONY: help install dev test lint run ingest clean

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install    Install dependencies"
	@echo "  dev        Install dev dependencies"
	@echo "  test       Run tests"
	@echo "  lint       Run linter"
	@echo "  run        Start API server"
	@echo "  ingest     Run batch ingestion pipeline"
	@echo "  infra      Start infrastructure (Milvus/Neo4j/Redis)"
	@echo "  clean      Clean generated files"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/ --fix
	ruff format src/ tests/

run:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

ingest:
	python -m scripts.batch_ingest

infra:
	docker compose up -d milvus-standalone neo4j redis

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
