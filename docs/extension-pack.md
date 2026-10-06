# Extension pack

Course extras for Site Issue Triage (AI Dev Tools Zoomcamp 2026 — Project 1). Product scope is unchanged: `docs/spec.md` is truth, `openapi.yaml` is the contract, no invented routes, no auth, snake_case, operational issues only.

The documented pack is `.agents/` plus `docs/process.md` and `docs/permissions.md`. Skills under `.agents/skills/` are instructions only — they do not add API routes.

## 1. Skills

Project skills live at `.agents/skills/<name>/SKILL.md` (YAML `name` + `description`).

| Skill | Use when |
|---|---|
| `new-issue-category` | Add a category to spec, OpenAPI, Pydantic, `vocab.ts`, Analyze, tests |
| `new-severity` | Same for severity + `DUE_DAYS` + list rank + chip CSS |
| `add-endpoint` | Spec already requires a path: OpenAPI → `httpIssueService` → FastAPI → tests |
| `db-migration` | Schema change. Honest: **no Alembic**; `create_all` + portable ALTER |
| `seed-data` | Edit `backend/app/seed_data.py`; lifespan is seed-if-empty |
| `release` | `make test` → tag → CI publishes GHCR `:prod`; host pull is manual |
| `check-contract` | Confirm `openapi.yaml`, `httpIssueService.ts`, and FastAPI routers still match |

**Discoverability:** course / Claude / Cursor index `.agents/skills/` at startup (see `.claude/README.md` if a Claude build does not).

## 2. Subagents

| Role | Path | Job |
|---|---|---|
| PM | `.agents/agents/pm.md` | Intake → scoped issue against `docs/spec.md` (not `product-spec.md`) |
| SWE | `.agents/agents/swe.md` | Implement against spec + `openapi.yaml`; do not invent routes |
| QA | `.agents/agents/qa-engineer.md` | Independently verify; tests + log → Analyze → save → list → resolve; **PASS/FAIL only**; do not fix |

## 3. Orchestration

[docs/process.md](./process.md): PM grooms → SWE implements → QA checks → FAIL loops to SWE. The main session enforces the loop.

Parallel: worktrees, non-overlapping files, merge passing branches one at a time.

## 4. Permissions

[docs/permissions.md](./permissions.md): agents may edit code, tests, and schema models. They may not touch prod DB, deploys, data wipes, or secrets without an explicit human yes. Includes the Terraform / prod-volume wipe cautionary tale.

A reusable GitHub workflow lives at `.github/workflows/reusable-verify.yml` (`workflow_call`; not in the `:prod` publish graph). `ci.yml` publish gating is unchanged: `publish` `needs: [test, compose]`.
