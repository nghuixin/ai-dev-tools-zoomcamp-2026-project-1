# Design decisions

Record of choices made for Site Issue Triage (Zoomcamp Project 1). Each item is a decision, not a leftover todo. Product rules live in `docs/spec.md`; this file is *why* the repo looks the way it does.

## Process

- [x] **Spec-driven, frontend-first**  
  `docs/spec.md` is the product source of truth. Build the three screens against the spec with a mock service, extract `openapi.yaml` from the frontend HTTP client, then implement FastAPI against that contract. Do not invent endpoints or fields that are not in both the client and the YAML.

- [x] **Python + uv FastAPI, not Node**  
  An early Express + `node:sqlite` API was discarded when the layout became `frontend/` + empty `backend/` + contract. Backend is Python 3.11+ via uv so the course toolchain (`uv sync`, `uv run pytest`) applies.

- [x] **`make run` is the API**  
  Same convention as the homework: `make run` / `make backend` starts uvicorn on **8000**; `make dev` is Vite on **5173**; `make test` is backend pytest. Port 8000 matches `openapi.yaml` and `DEFAULT_API_URL`, not the homework's 8091.

- [x] **No authentication module**  
  MVP is a single local user. Every OpenAPI operation is `security: []`. The client never sends `Authorization`.

## Product / data model

- [x] **Operational site issues only**  
  No clinical advice, causality, or dosing in Analyze output. Description hint: no names, DOBs, MRNs, or contact details. `phi_flag` is a heuristic, not a compliance control.

- [x] **Closed vocabularies**  
  Category (12 values), severity (`CRITICAL` / `HIGH` / `MEDIUM` / `LOW`), status (`OPEN` / `IN_PROGRESS` / `ESCALATED` / `RESOLVED`). Severity is **impact**, not urgency.

- [x] **Due dates default from severity**  
  CRITICAL 1d, HIGH 5d, MEDIUM 15d, LOW 30d when the user leaves due date blank.

- [x] **Status may move in any order**  
  `RESOLVED` requires `resolution_note` and sets `resolved_at` on first resolve only.

- [x] **List default: hide `RESOLVED`; sort severity then oldest**  
  Query `status=active` (or omitted) hides resolved. `ALL` includes every status. CSV uses the same filters as the list.

- [x] **Keep original `ai_suggestion` beside saved values**  
  Compare category / severity / summary / recommended_action and mark `edited_fields`. No suggestion stored if Analyze never ran or failed.

- [x] **Analyze failure never blocks save**  
  Invalid or failed Analyze returns `{ "error": "suggestion unavailable" }` (400/422). `LogIssuePage` `tweaks.analyze === "unavailable"` shows that string without calling the API (demo/test hook).

- [x] **Study/site seeded; site can be added inline**  
  Three studies / six sites in seed data. Duplicate site `code` per study is rejected.

## Frontend

- [x] **All backend I/O through `frontend/src/services`**  
  Pages call `api.ts`, which calls `IssueService`. No `fetch` from pages or components.

- [x] **Snake_case JSON**  
  `study_id`, `due_date`, `ai_suggestion` match `openapi.yaml`. Errors are `{ "error": string }` (not homework `{ "detail" }`).

- [x] **Mock then HTTP**  
  `createMockIssueService()` (localStorage) shipped the prototype. Live app now uses `createHttpIssueService()` (`VITE_API_URL`, default `http://127.0.0.1:8000`). Mock kept for tests only.

- [x] **Heuristic Analyze in both mock and API**  
  Same keyword rules as `frontend/src/services/analyze.ts`. No live LLM in MVP; operational next-step copy only.

- [x] **Three screens**  
  Log (`/log`), list (`/issues`), detail (`/issues/:id`). Tweaks control in the header for Analyze unavailable.

## Backend / contract

- [x] **`openapi.yaml` is extracted from the HTTP client**  
  Ten operations: studies, sites (list/create), analyze, issues (list/create), CSV, get/patch issue, add note. No `/health`, no extra fields.

- [x] **Routers + Pydantic models + store**  
  Split as `app/routers`, `app/models`, `app/store`, `app/analyze`. No auth package.

- [x] **CORS for Vite**  
  `http://localhost:5173` and `http://127.0.0.1:5173`.

- [x] **Validation errors reshaped to `{ "error": string }`**  
  FastAPI 422 `detail` is converted to 400 `{ error }` so the client can display the message.

## Persistence

- [x] **SQLAlchemy, not an in-memory dict, for the running API**  
  In-memory store was the first backend slice. Replaced so data survives restart (spec success criterion).

- [x] **`DATABASE_URL` is the connection string**  
  Default `sqlite:///./triage.db`. `postgres://` and `postgresql://` normalize to `postgresql+psycopg://`. `psycopg` is already a dependency so Postgres can be pointed at later without a SQLite-only schema.

- [x] **Database-agnostic schema**  
  Integer PKs, string enums (not native DB enums), portable `JSON` (not JSONB), `Date` / timezone-aware `DateTime`, `UniqueConstraint`. No SQLite JSON1, `PRAGMA`, or dialect SQL. `check_same_thread` / `StaticPool` are engine knobs for SQLite/tests only.

- [x] **`create_all` + seed-if-empty**  
  No Alembic in MVP. Lifespan seeds studies/sites/issues only when `studies` is empty. Tests use an isolated in-memory SQLite engine.

- [x] **One Docker image: Node build → Python runtime serving the Vite dist**  
  `VITE_API_URL` is empty in the image so the UI calls same-origin `/api`. FastAPI mounts the static build last so API routes stay first; unknown paths return `index.html` for client routes (`/log`, `/issues/:id`).

- [x] **Docker Compose: API + Postgres**  
  `docker-compose.yaml` is the **dev** stack (`name: site-issue-triage-dev`, port 8000, volume `postgres_data`). API `DATABASE_URL` points at that stack’s `postgres`. Seed still runs when `studies` is empty.

- [x] **Independent production copy of the stack**  
  `docker-compose.prod.yaml` is a second Compose project (`site-issue-triage-prod`). Separate volume (`postgres_data_prod`), port **8080**, default DB password `triage_prod`, `APP_ENV=production`, `restart: unless-stopped`. Can run beside dev. GitHub Actions CD publishes `site-issue-triage:prod` to GHCR (`PROD_IMAGE`).

- [x] **Compose integration tests isolated from unit tests**  
  `tests/integration/` is HTTP-only (`INTEGRATION_BASE_URL`). `make test` stays in-process SQLite. CI starts `docker-compose.yaml` and runs `make test-integration`.

## Deferred (chose not to build)

These were decided *against* for this MVP, not forgotten:

- CTMS / EDC integration
- Authentication, multi-user access, sharing
- Email ingestion, CAPA, notifications, duplicate detection
- Clinical decision support
- Hosted LLM Analyze (heuristic only)
- Alembic migrations
- Frontend Vitest suite (mock remains for when tests exist)
- Frontend Vitest suite (mock remains for when tests exist)
- Extra routes (`/health`, auth, pagination) not in `openapi.yaml`
