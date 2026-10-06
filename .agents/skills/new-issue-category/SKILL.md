---
name: new-issue-category
description: Add a new category to the issue vocabulary end-to-end
---

# New issue category

Done this once: the dropdowns already map `CATEGORIES`, so the real work is keeping the closed enum identical in spec, OpenAPI, Pydantic, and TypeScript, then teaching Analyze to emit the new value. The column is `String(32)` — no DB migration for a new enum member.

Do not invent an API route. Category is a field on existing issue/analyze schemas.

## Steps

1. Confirm the value is **operational** (not clinical advice). Add it to `docs/spec.md` §6.1 and, if you are recording a decision, `docs/tasks.md`. Keep `OTHER` last.
2. Add the same string to all four enum surfaces in one change:
   - `openapi.yaml` → `components.schemas.Category.enum`
   - `backend/app/models.py` → `class Category` and `CATEGORY_LABELS`
   - `frontend/src/types.ts` → `Category` union
   - `frontend/src/vocab.ts` → `CATEGORIES` and `CATEGORY_LABELS`
3. Skip hardcoding options in pages. `LogIssuePage.tsx` and `IssueDetailPage.tsx` already `{CATEGORIES.map(...)}`. If a new screen hardcodes a `<option>`, fix that instead of copying the list.
4. Teach Analyze or the new value never appears:
   - `frontend/src/services/analyze.ts` — `CATEGORY_RULES` (put specific regexes **above** the `PROTOCOL_DEVIATION` catch-all) and `ACTIONS`
   - `backend/app/analyze.py` — same rule order and `ACTIONS` dict
   - Heuristic must stay operational next-steps only (no causality, dosing, treatment).
5. Optional demo row: `backend/app/seed_data.py` `ISSUES` (and `frontend/src/services/seed.ts` if the mock snapshot should match). Seed-if-empty will **not** refresh an existing DB — use the `seed-data` skill.
6. Tests: add or extend a case in `backend/tests/test_analyze.py` (keyword → new category) and a create/list assertion in `backend/tests/test_api.py` if you want the enum accepted on POST. `make test`.
7. Run `.agents/skills/check-contract`. Paths do not change; schemas must.

## Leave alone

`backend/app/db_models.py` `IssueRow.category` is already a string. Do not switch to a native Postgres ENUM.
