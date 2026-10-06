export INTEGRATION_BASE_URL ?= http://127.0.0.1:8000

.PHONY: run backend dev test test-integration image up down up-prod down-prod

run backend:
	cd backend && uv run uvicorn app.main:app --reload --reload-dir app --port 8000

dev:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest

test-integration:
	cd backend && uv run pytest ../tests/integration -m integration

image:
	docker build -t site-issue-triage .

up:
	docker compose -f docker-compose.yaml up --build

down:
	docker compose -f docker-compose.yaml down

up-prod:
	docker compose -f docker-compose.prod.yaml up --build -d

down-prod:
	docker compose -f docker-compose.prod.yaml down
