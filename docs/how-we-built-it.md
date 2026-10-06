# How we built Site Issue Triage

A short walkthrough of Zoomcamp 2026 Project 1, in the order the work happened. Product rules live in [spec.md](./spec.md). Why each choice was made lives in [tasks.md](./tasks.md). This page is the path, not a dump of either.

**Site Issue Triage** is a local app for one site manager. They describe an operational site issue in their own words, optionally get an AI triage suggestion, edit it, save it, and track it until it is resolved. No login. No patient data.

---

## 1. Spec first

We wrote [docs/spec.md](./spec.md) before code. It names the problem, the eight-step flow (pick study/site → describe → optional Analyze → save → list → detail → resolve), the closed lists for category / severity / status, and what is out of scope (auth, CTMS/EDC, email, CAPA).

Severity means **impact**, not “how soon.” If the user leaves due date blank, it defaults from severity: CRITICAL 1 day, HIGH 5, MEDIUM 15, LOW 30. Analyze is optional. A failed suggestion must never block save.

## 2. Frontend prototype

We built three screens in React + TypeScript (Vite) first:

| Screen | Route | Job |
|---|---|---|
| Log | `/log` | Study, site, description, optional Analyze, save |
| List | `/issues` | Filters, default hide RESOLVED, sort by severity then oldest, CSV |
| Detail | `/issues/:id` | Edit fields, change status, append notes, resolve with a note |

Pages never call `fetch`. They go through `frontend/src/services`. The first service was a **mock**: fake data in the browser (`localStorage`). That let the UI run without a server. Analyze used the same keyword rules on both sides — not a live LLM.

## 3. OpenAPI from the frontend client

Once the HTTP client (`httpIssueService`) knew the URLs and JSON fields it needed, we wrote [openapi.yaml](../openapi.yaml) to match it. That file is the **contract**: the written agreement of paths and fields.

Ten operations: studies, sites (list/create), analyze, issues (list/create), CSV, get/patch issue, add note. Snake_case (`study_id`, `due_date`). Errors are `{ "error": string }`. No extra routes, no auth.

## 4. FastAPI against that contract

The live app switched from the mock to `createHttpIssueService()` (`VITE_API_URL`, default `http://127.0.0.1:8000`). Then we implemented a Python API with **uv** (a fast Python package runner) and **FastAPI** (a web framework) so every route matched the YAML.

Routers, Pydantic models (typed request/response shapes), and a store. CORS allowed the Vite app on port 5173. FastAPI’s default 422 errors were reshaped to `{ "error": string }` so the UI could show them.

## 5. SQLAlchemy + DATABASE_URL

An in-memory dict was the first API store. The spec requires data to survive restart, so we replaced it with **SQLAlchemy** (a library that talks to databases in Python).

`DATABASE_URL` is the connection string. Default is SQLite (`sqlite:///./triage.db`). Postgres URLs are normalized so we can point at Postgres later without SQLite-only SQL. Schema uses portable types (string enums, JSON, not Postgres-only JSONB). No Alembic (a migration tool) in MVP: `create_all` plus seed-if-empty on startup.

## 6. Docker image + compose

**Docker** packages the app so it runs the same on any machine. One image: Node builds the frontend, then Python serves that build and the API. Inside the image, `VITE_API_URL` is empty so the UI calls same-origin `/api`.

**Compose** starts the API plus Postgres as a stack:

- Dev: `docker-compose.yaml` → [http://127.0.0.1:8000](http://127.0.0.1:8000) (`make up`)
- Prod: `docker-compose.prod.yaml` → [http://127.0.0.1:8080](http://127.0.0.1:8080) (`make up-prod`)

Separate project names and volumes, so they can run side by side. AWS EC2 hosting was optional and was not finished in this repo.

## 7. Two kinds of tests

| Kind | Where | What it hits |
|---|---|---|
| Unit | `backend/tests/` | FastAPI in-process + in-memory SQLite (`make test`) |
| Integration | `tests/integration/` | Real HTTP against a running Compose stack (`make test-integration`) |

Unit tests stay fast and isolated. Integration tests prove the Docker stack answers the contract.

## 8. GitHub Actions: test, then publish `:prod`

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) is one pipeline:

1. `test` — unit pytest
2. `compose` — validate both Compose files
3. `integration` — Compose HTTP tests (CI only; does not block publish)
4. `publish` — only on `main`/`master`, and only after `test` + `compose` pass: push `site-issue-triage:prod` to GHCR (GitHub’s container registry)

A host pulls that image and runs the prod Compose file by hand. The workflow does not SSH-deploy.

## 9. Agents pack

Course extras sit under `.agents/` and are mapped in [extension-pack.md](./extension-pack.md). They do not add product features.

- **Skills** — repeatable how-tos (new category, new severity, add an endpoint the spec already requires, seed data, contract check, release).
- **Roles** — PM grooms a scoped issue, SWE implements against spec + OpenAPI, QA verifies and says PASS or FAIL only.
- **Process** — [process.md](./process.md) is that loop. [permissions.md](./permissions.md) says agents may edit local code and tests, not prod data, deploys, or secrets.
