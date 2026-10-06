---
name: new-severity
description: Add or change a severity level and its default due-date days end-to-end
---

# New severity

Severity is **impact**, not urgency. Today: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` with due defaults 1 / 5 / 15 / 30 days (`docs/spec.md` §6.2). Adding a fifth level is a product change — if it is not in the spec, stop and send it back to PM.

Missed this the first time: list sort and chip CSS do not follow the enum automatically.

## Steps

1. Update `docs/spec.md` §6.2 (definition + default due). Same string everywhere after that.
2. Enum + due map (both sides):
   - `openapi.yaml` → `components.schemas.Severity.enum`
   - `backend/app/models.py` → `class Severity` and `DUE_DAYS`
   - `frontend/src/types.ts` → `Severity` union
   - `frontend/src/vocab.ts` → `SEVERITIES`, `SEVERITY_LABELS`, `DUE_DAYS` (`dueHint` reads the map)
3. List sort rank: `backend/app/store.py` `SEVERITY_RANK` (0 = highest, shown first). A new level with no rank KeyErrors on `GET /api/issues`.
4. UI that already maps `SEVERITIES`: `LogIssuePage.tsx`, `IssueDetailPage.tsx`, `IssuesListPage.tsx` filter. `SeverityChip` uses `chip-${severity.toLowerCase()}` — add a matching class in `frontend/src/index.css` (see `.chip-critical` / `.chip-high` / `.chip-medium` / `.chip-low`).
5. Analyze: `frontend/src/services/analyze.ts` `pickSeverity` and `backend/app/analyze.py` `_pick_severity`. Keep the new level in the allowed set (`SEVERITIES` / `Severity` enum). Operational impact only.
6. Defaults apply on **create** (and when severity changes with a blank due) via `DUE_DAYS` in `store.py`. Saved `due_date` values are not backfilled. Seed rows use `created` offset + `DUE_DAYS[severity]` in `store.seed()`.
7. `frontend/src/services/mockIssueService.ts` rejects unknown severities against `SEVERITIES` — it picks up the vocab list.
8. Tests: due-date default in `backend/tests/test_api.py` / integration `test_workflows.py`; analyze mapping in `backend/tests/test_analyze.py`. `make test`.
9. `/check-contract` for schema enum drift.

## Leave alone

`IssueRow.severity` is `String(16)`. No Alembic / no native DB enum. Do not invent a new API field for “urgency”.
