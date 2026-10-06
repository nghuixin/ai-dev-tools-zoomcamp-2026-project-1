# Site Issue Triage Assistant

Local MVP for a single site manager: log a free-text site issue, optionally get an editable AI triage, save it, and track it to resolution.

This repository is **AI Dev Tools Zoomcamp 2026 — Project 1**. It is **frontend-first**: the UI was built first, then [`openapi.yaml`](./openapi.yaml) became the frontend/backend contract, then FastAPI implemented that contract. The API persists with SQLAlchemy (SQLite by default, Postgres-ready).

## Problem

Site managers log operational issues as free text and then reconstruct category, severity, owner, and next steps by hand. Intake is slow, lists are hard to scan, and the original judgment trail is lost when a record is later edited.

This project exists so a site manager can describe an issue in their own words, get an optional AI triage, edit and save it, and track it to resolution without that extra reconstruction work.

## What it does

A site manager picks a study and site, describes an operational issue, and can run **Analyze** to pre-fill category, severity, summary, recommended action, and a one-line rationale. The form stays editable. AI failure never blocks saving.

Saved issues appear in a filterable list (severity, site, summary, status, owner, due date, age). From detail, any field can be edited, status can change, and notes can be appended. Resolving an issue requires a resolution note.

Issues are stored via SQLAlchemy (seeded once when the database is empty). Default is SQLite (`DATABASE_URL` can point at Postgres later). There is no auth, no multi-user access, and no patient data.

## Run locally

Use two terminals. Start the backend first.

```bash
make run    # API on http://127.0.0.1:8000  (Swagger at /docs)
make dev    # frontend on http://localhost:5173
```

Without Make: `cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000`, then `cd frontend && npm install && npm run dev`.

The UI calls `http://127.0.0.1:8000` (`VITE_API_URL` overrides that). Default database is `sqlite:///./triage.db` (`DATABASE_URL` overrides that). Seeded sample data is inserted only when the database is empty.

The header **Tweaks** control can force Analyze to **unavailable** so you can confirm Save still works.

## Docker Compose

Two independent stacks (same services, separate project names, volumes, and ports):

| Command | File | Site |
|---|---|---|
| `make up` | `docker-compose.yaml` | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| `make up-prod` | `docker-compose.prod.yaml` | [http://127.0.0.1:8080](http://127.0.0.1:8080) |

They can run at the same time. `make down` / `make down-prod` stop that stack and keep its volume.

After CI publishes the image, a host can pull and run it by hand: set `PROD_IMAGE=ghcr.io/<owner>/<repo>/site-issue-triage:prod`, then `docker compose -f docker-compose.prod.yaml pull && docker compose -f docker-compose.prod.yaml up -d`.

Single-container image without Postgres (SQLite inside the container): `make image` then `docker run --rm -p 8000:8000 site-issue-triage`.

AWS EC2 was attempted; local `make` and Compose above are the documented run path.

## Tests

| Command | What it hits |
|---|---|
| `make test` | Backend unit tests (`backend/tests/`) — in-process FastAPI + in-memory SQLite |
| `make test-integration` | HTTP tests (`tests/integration/`) against a **running** Compose stack |

Integration tests need the dev stack up and `INTEGRATION_BASE_URL` (default `http://127.0.0.1:8000`):

```bash
make up
# another terminal
set INTEGRATION_BASE_URL=http://127.0.0.1:8000
make test-integration
```

On macOS/Linux: `INTEGRATION_BASE_URL=http://127.0.0.1:8000 make test-integration`.

## CI / CD

One workflow: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml). Every push, PR, and dispatch runs unit pytest and validates both Compose files. On `main` / `master` (or `workflow_dispatch`), after those two jobs succeed, it publishes `site-issue-triage:prod` (and the commit SHA tag) to GHCR.

Host pull is **manual** — this repo does not SSH-deploy. A production host pulls `:prod` and runs `docker-compose.prod.yaml`. Compose HTTP tests also run in CI but do not gate the publish.

## Expected behavior

1. Pick study and site (seeded lists; a site can be added inline).
2. Describe the issue (required). Hint: no names, DOBs, MRNs, or contact details.
3. Optionally run **Analyze**. Filled fields show an **AI** tag, which flips to **EDITED** if you change them.
4. Edit the form and save (category and severity required). Analyze failure does not block save.
5. Find the issue in the list. Default sort is severity, then oldest. `RESOLVED` is hidden unless you filter to it. Overdue dates are red. **Export CSV** uses the current filters.
6. Open detail: edit fields, compare against the original suggestion, move status in any order, append notes. Resolving requires a note and sets `resolved_at`.

## Docs

- Product spec: [`docs/spec.md`](./docs/spec.md)
- Decision log: [`docs/tasks.md`](./docs/tasks.md)
- How we built it: [`docs/how-we-built-it.md`](./docs/how-we-built-it.md)
- Process (PM → SWE → QA): [`docs/process.md`](./docs/process.md)
- Permissions: [`docs/permissions.md`](./docs/permissions.md)
- Extension pack: [`docs/extension-pack.md`](./docs/extension-pack.md)
- Criteria log: [`docs/criteria-log.md`](./docs/criteria-log.md)
- API contract: [`openapi.yaml`](./openapi.yaml)
- Agent instructions: [`AGENTS.md`](./AGENTS.md)

Course extras live under [`.agents/`](./.agents/): skills plus PM / SWE / QA role files. They do not add product features.

## Constraints

| | |
|---|---|
| Users | Single site manager |
| Runtime | Vite frontend + FastAPI + SQLAlchemy (SQLite default) |
| Auth | None |
| Data | Operational site issues only — not real patient data |

Analyze output is operational next steps only. No clinical advice, causality, or dosing guidance.

## Out of scope

CTMS/EDC integration, authentication, email ingestion, CAPA workflow, clinical decision support, notifications, and duplicate detection.

## Success (MVP)

- Full flow works and data survives restart.
- In a 30-issue pilot: ≥70% of AI categories and ≥60% of severities saved unchanged; median log time ≤ 2 minutes.

## Learning in Public
- https://nghuixin.notion.site/Clinical-Trial-Site-Issue-Triage-Assistant-3f072266c5fb80a8b500d9331f392def
