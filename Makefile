export INTEGRATION_BASE_URL ?= http://127.0.0.1:8000

.PHONY: run backend dev test test-integration test-all image up down up-prod down-prod up-obs down-obs alert-demo poll-alerts

run backend:
	cd backend && uv run uvicorn app.main:app --reload --reload-dir app --port 8000

dev:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest

test-integration:
	cd backend && uv run pytest ../tests/integration -m integration

# Start Compose, wait for the API, run unit + integration tests, tear down (same steps as CI).
test-all:
	bash scripts/test-all.sh

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

# Dev stack + Grafana (:3000), Prometheus (:9090), Loki (:3100), Tempo, Alloy.
up-obs: export OTEL_EXPORTER_OTLP_ENDPOINT = http://tempo:4318
up-obs:
	docker compose -f docker-compose.yaml --profile observability up --build -d

down-obs:
	docker compose -f docker-compose.yaml --profile observability down

# Restart the API with half of POST /api/issues failing, to fire CreateIssue5xxRateHigh.
alert-demo: export OTEL_EXPORTER_OTLP_ENDPOINT = http://tempo:4318
alert-demo: export FAULT_CREATE_ISSUE_500_RATE = 0.5
alert-demo:
	docker compose -f docker-compose.yaml --profile observability up -d api

# Poll Prometheus for firing alerts and hand them to ALERT_AGENT_CMD (dry run if unset).
poll-alerts:
	uv run --project backend python scripts/poll_alerts.py
