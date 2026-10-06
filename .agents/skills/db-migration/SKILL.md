---
name: db-migration
description: Apply a portable schema change without Alembic (create_all + careful ALTER)
---

# DB schema change

There is **no Alembic** in this repo (`docs/tasks.md`: deferred). Schema is SQLAlchemy models + `Base.metadata.create_all`. Do not generate `alembic revision` unless a human explicitly asks to adopt Alembic.

`create_all` creates **missing tables**. It does **not** add columns to a table that already exists. That is why a new field works in `make test` (fresh in-memory SQLite) and then 500s against `backend/triage.db` or a Compose volume.

## Steps

1. Confirm the column/table is already in `docs/spec.md` §8 and `openapi.yaml`. No extra fields.
2. Add the mapping in `backend/app/db_models.py` with **portable** types only:
   - `Integer` PKs, `String` / `Text`, `Date`, `DateTime(timezone=True)`, `Boolean`, `JSON` (not JSONB)
   - String vocab columns, not native Postgres `ENUM`
   - `UniqueConstraint` / `ForeignKey` — no `PRAGMA`, no SQLite JSON1, no dialect SQL
3. Wire Pydantic in `backend/app/models.py` and `backend/app/store.py`. Engine setup stays in `backend/app/database.py` (`DATABASE_URL`; `postgres://` / `postgresql://` already become `postgresql+psycopg://`).
4. Fresh DBs (pytest via `create_memory_session_factory`, brand-new `triage.db`, new Compose volume) pick up **new tables** on next `get_store()` (`backend/app/deps.py` calls `create_all`).
5. Existing DBs + a **new column**: write a one-shot portable `ALTER TABLE … ADD COLUMN …` that is valid on both SQLite and Postgres (simple `VARCHAR` / `INTEGER` / `BOOLEAN` / nullable). Run it against local SQLite only unless a human approved prod. Or, for **local empty** data only, delete `backend/triage.db` / recreate a **dev** volume — that is destructive; see `docs/permissions.md`.
6. Category/severity **value** changes are not schema changes (`String(32)` / `String(16)`). Use `new-issue-category` / `new-severity`.
7. Seed still runs only when `studies` is empty (`backend/app/main.py` lifespan + `Store.seed()`). Schema change ≠ re-seed.
8. Tests: `backend/tests/test_database.py` plus any API test for the new field. `make test`. Compose Postgres: `make up` then `make test-integration` if the column is on the HTTP path.

## Never without approval

Production Postgres (`docker-compose.prod.yaml` volume `postgres_data_prod`), `docker compose … down -v` on prod, or any host `DROP` / wipe. Local `down -v` on **dev** still deletes data — ask first.
