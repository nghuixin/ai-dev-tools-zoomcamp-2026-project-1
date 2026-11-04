# Criteria log

| Criterion | Status | Evidence |
|---|---|---|
| OpenAPI matches frontend and is the backend contract | met | `openapi.yaml` from `httpIssueService` / `api.ts`; FastAPI implements those routes; no auth |
| Backend structured, follows OpenAPI, core tests | met | routers / models / store; pytest for CRUD, filters, resolve gate, notes, CSV, analyze |
| DB integrated, multi-env, documented | met | SQLAlchemy + `DATABASE_URL`; SQLite default, Postgres-ready; README / AGENTS |
| Independent prod Compose + GitHub Actions CI/CD | met | `docker-compose.prod.yaml`; `ci.yml` (`CI/CD`) → GHCR `:prod` after tests |
| Full system via Docker / Compose with instructions | met | `make up` :8000 (dev), `make up-prod` :8080 (prod); `Dockerfile` + README |
| Integration tests against Compose | met | `tests/integration/` HTTP vs `docker-compose.yaml`; `make test-integration`; CI `integration` job |
| CI/CD pipeline runs tests and deploys when tests pass | met | `ci.yml` (`CI/CD`): `publish` `needs: [test, compose]`, then `deploy-dev` (SSH `docker compose pull && up -d`, dev stack :8081, auto) → `deploy-prod` (`production` environment with required reviewer, same `:<sha>` image, :80). Needs `EC2_HOST` / `EC2_SSH_KEY` (`docs/deployment.md`). Integration (`make test-all`) runs on every push. |
| Deployed and reachable | met | Live at http://3.238.5.106/log; screenshot `docs/screenshots/live-ec2-log.png` |
| One command runs the full test suite | met | `make test-all` → `scripts/test-all.sh` (Compose up, wait, unit + integration, teardown); CI `integration` job runs the same target |
| Work tracked as issues with acceptance criteria | met | GitHub Issues #1–#12, each with an acceptance-criteria checklist; #1–#6 closed by commit, #7–#12 by PR |
| Observability: traces, logs, metrics | met | `backend/app/telemetry.py` (OTel FastAPI auto-instrumentation, JSON logs with `trace_id`, `/metrics`); Compose `observability` profile with Grafana, Tempo, Loki (Alloy), Prometheus; dashboard provisioned |
| Alerting | met | Prometheus `CreateIssue5xxRateHigh` (>5% 5xx on POST /api/issues for 1m); `make alert-demo` fires it; screenshot `docs/screenshots/observability/prometheus-alert-firing.png` |
| Alerts reach a coding agent | met | `scripts/poll_alerts.py` → incident brief with logs + trace IDs → `ALERT_AGENT_CMD`; example `docs/observability/example-alert-brief.md` |
| Documented extension pack (instructions, workflow, subagent, MCP, hook, permissions) | met | Course pack `.agents/skills` + `.agents/agents` (PM/SWE/QA); `docs/process.md` + `docs/permissions.md`; `docs/extension-pack.md` maps the pack |
