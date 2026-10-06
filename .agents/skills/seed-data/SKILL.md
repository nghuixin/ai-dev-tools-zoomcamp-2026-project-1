---
name: seed-data
description: Refresh seeded studies, sites, and sample issues (seed-if-empty lifespan)
---

# Seed data

Editing `backend/app/seed_data.py` does nothing to a database that already has rows. Lifespan is seed-**if-empty**:

```python
# backend/app/main.py
if not current.list_studies():
    current.seed()
```

`Store.seed()` also returns immediately if `studies` has a count. Learned that after wondering why Compose still showed the old three studies.

## Steps

1. Edit `backend/app/seed_data.py` only:
   - `STUDIES` — `code`, `name`
   - `SITES` — `study_code` must match a study; `code` unique per study
   - `ISSUES` — `study_code` + `site_code`, closed `Category` / `Severity` / `Status`, operational copy, no names/DOBs/MRNs
2. `created` is a day offset (negative = older). Due date is computed as `today + created + DUE_DAYS[severity]`. Resolved rows need `resolved` offset + `resolution_note`.
3. Optional: keep `frontend/src/services/seed.ts` aligned if the mock snapshot is still used in tests. Live app uses HTTP + backend seed.
4. Existing local SQLite (`backend/triage.db`) or Compose volumes will **not** pick this up. To refresh **local/dev empty** data: stop the API, delete `backend/triage.db`, or recreate the **dev** volume (`docker-compose.yaml` / `postgres_data`) — destructive; confirm first (`docs/permissions.md`). Then `make run` or `make up`.
5. Do not wipe `postgres_data_prod` or re-seed production to “refresh samples”.
6. Check `backend/tests/conftest.py` (in-memory `memory.seed()`) and `tests/integration/test_workflows.py` `test_seeded_studies`. If you rename `ST-104` / site codes, those tests break. `make test`.

## Leave alone

Do not add a “force reseed” endpoint. Do not upsert over live issues.
