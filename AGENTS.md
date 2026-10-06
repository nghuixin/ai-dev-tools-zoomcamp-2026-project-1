# AGENTS.md

Site Issue Triage is spec-driven and frontend-first. Keep the OpenAPI contract stable. Replace the mock service with HTTP, then implement the backend against that contract.

## Layout

```
/frontend      React + TypeScript (Vite) — the running prototype
/backend       Python + uv FastAPI app (SQLAlchemy; SQLite now, Postgres-ready) against openapi.yaml
/docs/spec.md  Product source of truth
/docs/tasks.md Design decisions (chose vs deferred)
/docs/process.md            PM → SWE → QA loop
/docs/permissions.md        What agents may touch
AGENTS.md
openapi.yaml   Frontend/backend contract
Makefile
Dockerfile
docker-compose.yaml
docker-compose.prod.yaml
tests/integration
.github/workflows/ci.yml   CI/CD: unit pytest + compose validate, then GHCR :prod on main/master
.agents                     Course pack: skills + PM / SWE / QA
docs/extension-pack.md      Pack map (skills, subagents, orchestration, permissions)
README.md
```

`docs/spec.md` is the product source of truth. `docs/tasks.md` is the decision log. `openapi.yaml` is the frontend/backend contract. Do not invent endpoints or fields that are not in both. No auth module.

## Commands

Frontend:

```
cd frontend && npm i && npm run dev
```

App: http://localhost:5173

The running app uses `createHttpIssueService()` (`VITE_API_URL`, default `http://127.0.0.1:8000`). An empty `VITE_API_URL` means same-origin `/api` (Docker image). Keep `createMockIssueService()` for tests only.

Backend uses **Python + uv** and SQLAlchemy. Connection string is `DATABASE_URL` (default `sqlite:///./triage.db`). Postgres URLs (`postgresql://` / `postgres://`) are normalized to `postgresql+psycopg://`. Do not use SQLite-only SQL. Run from `backend/` for uv commands.

```
uv sync
uv add <pkg>
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
```

```
make run       # API on http://127.0.0.1:8000  (docs at /docs)
make backend   # same as make run
make dev       # frontend on http://localhost:5173
make test      # backend pytest (in-process SQLite)
make test-integration  # HTTP vs Compose; set INTEGRATION_BASE_URL (http://127.0.0.1:8000)
make image     # Docker image: Vite build + FastAPI serving it
make up        # dev compose: http://127.0.0.1:8000
make down      # stop dev compose (volume kept)
make up-prod   # production compose: http://127.0.0.1:8080
make down-prod # stop production compose (volume kept)
```

Commit to git regularly.

## Rules

- All backend calls go through `frontend/src/services`. Do not call `fetch` from pages or components.
- JSON is snake_case (`study_id`, `due_date`, `ai_suggestion`) to match `openapi.yaml`.
- Errors are `{ "error": string }`. Analyze failures must return `suggestion unavailable` and must not block save.
- No authentication in MVP. Single local user.
- Operational site issues only. No clinical advice, causality, or dosing. Description hint: no names, DOBs, MRNs, or contact details.
- Vocabularies are closed enums in the spec: category, severity (impact, not urgency), status. Status may move in any order; `RESOLVED` requires `resolution_note` and sets `resolved_at` on first resolve.
- Due dates default from severity: CRITICAL 1d, HIGH 5d, MEDIUM 15d, LOW 30d.
- List default: hide `RESOLVED`; sort severity then oldest. CSV export uses the active filters.
- Store original `ai_suggestion` beside saved values and mark edited fields.
- `LogIssuePage` takes a `tweaks` prop. `tweaks.analyze === "unavailable"` must show **suggestion unavailable** without calling Analyze.
- Keep `openapi.yaml` in sync when adding or changing endpoints.
- Do not add CTMS/EDC, email ingestion, CAPA, notifications, duplicate detection, or multi-user auth.

Work loop: PM grooms → SWE implements → QA checks (`docs/process.md`). Permissions: `docs/permissions.md`.

Course skills and PM/SWE/QA agents live under `.agents/`. See `docs/extension-pack.md`.
