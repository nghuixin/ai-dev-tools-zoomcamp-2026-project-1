---
name: add-endpoint
description: Add a route the spec already requires, OpenAPI first, then client, FastAPI, tests
---

# Add endpoint

Order matters. The first time this was done backwards (router first), the contract-checker failed and the frontend kept calling a path that did not exist in `openapi.yaml`.

This skill is instructions only. **Do not invent** a path or field that is missing from `docs/spec.md`. If the user asked for CAPA, auth, `/health`, notifications, or anything in spec §10, refuse and stop.

## Allowed paths today

`GET /api/studies` · `GET|POST /api/sites` · `POST /api/issues/analyze` · `GET|POST /api/issues` · `GET /api/issues.csv` · `GET|PATCH /api/issues/{id}` · `POST /api/issues/{id}/notes`

If the route is not in that list **and** not being added to spec + OpenAPI in this change, do not implement it.

## Steps

1. Read `docs/spec.md`. Quote the requirement. If it is not there, stop — PM grooms it first (`docs/process.md`).
2. Add the operation to `openapi.yaml` first: path, method, snake_case schemas (`study_id`, `due_date`, `ai_suggestion`), errors `{ "error": string }`, `security: []`. No `Authorization`, no camelCase.
3. Mirror the URL in `frontend/src/services/httpIssueService.ts` (the only place pages may reach the network). Extend `frontend/src/services/issueService.ts` and the `frontend/src/api.ts` wrapper. **Never** `fetch(` from `frontend/src/pages` or `frontend/src/components`.
4. Implement the matching FastAPI handler in `backend/app/routers/` (`issues.py`, `sites.py`, or `studies.py`). Include the router in `backend/app/main.py` if you add a file. Pydantic models live in `backend/app/models.py`. Persistence in `backend/app/store.py` + `backend/app/db_models.py` (portable types; see `db-migration`).
5. Analyze failures stay `{ "error": "suggestion unavailable" }` and must not block save.
6. Tests: `backend/tests/test_api.py` (and `test_analyze.py` / `test_database.py` if those layers moved). Compose flow: `tests/integration/test_workflows.py` (`make test-integration` against `make up`). `make test` first.
7. Run `.agents/skills/check-contract`. All three surfaces must list the same path + fields.

## Leave alone

Do not add auth, cookies, CTMS/EDC, email, CAPA, notifications, or duplicate detection. Do not change `.github/workflows/ci.yml` publish gating as part of an endpoint change.
