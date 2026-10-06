---
name: release
description: Run tests, tag, and rely on CI/CD to publish GHCR :prod (host pull is manual)
---

# Release

CI already publishes. You do not SSH to a host. The first time this was easy to overbuild: people added deploy steps; this repo’s CD artifact is the image tag only.

## Steps

1. Tests locally: `make test` (backend pytest, in-process SQLite). Optionally `make up` then `make test-integration` (`INTEGRATION_BASE_URL=http://127.0.0.1:8000`). Compose file sanity: `docker compose -f docker-compose.yaml config` and `docker compose -f docker-compose.prod.yaml config`.
2. Do **not** change `.github/workflows/ci.yml` publish gating. `publish` must stay `needs: [test, compose]`. The `integration` job is CI-only and does **not** block the image.
3. After tests pass and a human asked to release: commit (only if they asked), tag, push the tag / merge to `main` or `master`. `workflow_dispatch` on `CI/CD` also publishes when `test` + `compose` succeed.
4. Actions then builds `ghcr.io/<owner>/<repo>/site-issue-triage:prod` and `:<sha>`. Watch that workflow; if `test` or `compose` fails, `:prod` is not pushed.
5. **Host pull is manual.** On the production machine (human):

```bash
export PROD_IMAGE=ghcr.io/<owner>/<repo>/site-issue-triage:prod
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
```

Default prod URL is `http://127.0.0.1:8080` (`PROD_PORT` overrides). `make up-prod` / `make down-prod` keep the volume. `down -v` wipes it — never do that on prod without explicit approval.

6. Confirm the running container is the new digest. Do not `docker compose` against the prod project from an agent session unless the user approved a host operation.

## Leave alone

No AWS SSH in Actions. No extra secrets. Do not retag `:prod` over a failed test run.
