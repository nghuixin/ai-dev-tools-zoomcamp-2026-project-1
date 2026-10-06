# Permissions

What agents may touch in this repo, and what always needs an explicit human “yes” in the same conversation. Project rules and skills do not override this file.

## May touch (local / in-repo)

| Surface | Notes |
|---|---|
| Application code | `frontend/src/**`, `backend/app/**`, `openapi.yaml`, `docs/spec.md` / `docs/tasks.md` when the change is scoped |
| Tests | `backend/tests/**`, `tests/integration/**` |
| Schema models | `backend/app/db_models.py`, `backend/app/database.py` — portable SQLAlchemy only (`create_all`, no Alembic unless a human asks to add it) |
| Local SQLite | Default `sqlite:///./triage.db` for `make run` / pytest in-memory engines |
| Dev Compose | `make up` / `make down` against `docker-compose.yaml` (volume **kept**) |
| Skills / agents / pack docs | `.agents/**`, `docs/extension-pack.md`, `docs/process.md` |

Agents may run `make test`, `make test-integration` (against a stack the user already started or asked to start), and `.agents/skills/check-contract`.

## Never without explicit human approval

| Surface | Why |
|---|---|
| Production database | `docker-compose.prod.yaml` Postgres / volume `postgres_data_prod`. No `DROP`, `TRUNCATE`, re-seed, or “just ALTER prod”. |
| Destructive volume / file wipes | `docker compose … down -v` (dev or prod), deleting `triage.db` when it might have real notes, `rm` of data dirs |
| Deploy / host pull | GHCR `:prod` publish is CI after tests. Pulling and `up -d` on a host is **manual**. No AWS SSH, no unattended `make up-prod` against a shared host. |
| Secrets | `.env`, `POSTGRES_PASSWORD` in a live env, `GITHUB_TOKEN` / PATs, any credential file. Do not commit them. Do not paste them into skills or logs. |
| Deleting user data | Bulk-deleting issues/notes, force-reseed over a non-empty DB, rewriting history that drops data |
| Publish gating | Do not relax `.github/workflows/ci.yml` `publish` `needs: [test, compose]` |
| Out-of-scope product | Auth, CTMS/EDC, CAPA, notifications, PHI, clinical advice |

“The tests would be easier if we wiped prod” is not approval.

## Cautionary tale (Terraform / prod DB wipe)

A familiar failure mode: an agent treats **prod** like a disposable lab. Someone leaves `terraform destroy`, `docker compose down -v`, or a recreate-database script in a “make it match the model” change. The command is valid. The target is the **production** state file or volume. The database comes back empty. `create_all` + seed-if-empty then happily inserts sample studies over what used to be real issues.

This repo is built so that is easy to do by accident:

- `create_all` does not migrate existing columns; the tempting fix is “recreate the volume”.
- Seed runs when `studies` is empty, so a wiped prod DB looks “successfully refreshed”.
- `make down-prod` is safe (volume kept). `docker compose -f docker-compose.prod.yaml down -v` is not.

**Rule:** if the target is prod, a volume, or a destroy/wipe/apply that can drop data, stop and wait for a human sentence that names the environment and the command. Do not infer approval from “fix the schema” or “refresh seed”.

## How to ask

State the exact command, the environment (`local sqlite` / `dev compose` / `prod compose` / `GHCR` / `git remote`), and what data can be lost. Proceed only after the user confirms that command.
