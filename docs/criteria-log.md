# Criteria log

| Criterion | Status | Evidence |
|---|---|---|
| OpenAPI matches frontend and is the backend contract | met | `openapi.yaml` from `httpIssueService` / `api.ts`; FastAPI implements those routes; no auth |
| Backend structured, follows OpenAPI, core tests | met | routers / models / store; pytest for CRUD, filters, resolve gate, notes, CSV, analyze |
| DB integrated, multi-env, documented | met | SQLAlchemy + `DATABASE_URL`; SQLite default, Postgres-ready; README / AGENTS |
| Independent prod Compose + GitHub Actions CI/CD | met | `docker-compose.prod.yaml`; `ci.yml` (`CI/CD`) → GHCR `:prod` after tests |
| Full system via Docker / Compose with instructions | met | `make up` :8000 (dev), `make up-prod` :8080 (prod); `Dockerfile` + README |
| Integration tests against Compose | met | `tests/integration/` HTTP vs `docker-compose.yaml`; `make test-integration`; CI `integration` job |
| CI/CD pipeline runs tests and deploys when tests pass | met | `ci.yml` (`CI/CD`): `publish` `needs: [test, compose]` so GHCR `:prod` is built only after unit pytest + compose validate succeed on `main`/`master` (or dispatch). Integration is CI-only and does not gate deploy. Host pull of `:prod` is manual (no AWS SSH in Actions). |
| Documented extension pack (instructions, workflow, subagent, MCP, hook, permissions) | met | Course pack `.agents/skills` + `.agents/agents` (PM/SWE/QA); `docs/process.md` + `docs/permissions.md`; `docs/extension-pack.md` maps the pack |
