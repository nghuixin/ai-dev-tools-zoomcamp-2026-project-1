# Deployment

The app runs on an AWS EC2 host as two Compose stacks built from `docker-compose.prod.yaml`:

| Stack | Compose project | Port | Deployed by |
|---|---|---|---|
| Production | `site-issue-triage-prod` | 80 (live: http://3.238.5.106/log) | `deploy-prod`, after approval |
| Dev | `site-issue-triage-dev` | 8081 | `deploy-dev`, automatically |

Both run the image CI built from the same commit (`ghcr.io/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/site-issue-triage:<sha>`), so production only ever receives an artifact that already ran in dev.

## Pipeline

```
test ─┐
      ├─► publish ─► deploy-dev ─► [required reviewer approves] ─► deploy-prod
compose ┘
```

- **`publish`** pushes `:prod` and `:<sha>` to GHCR on `master` / `main` (or a manual dispatch), once the unit tests and Compose validation pass.
- **`deploy-dev`**, in the `development` environment:
  1. copies `docker-compose.prod.yaml` to the host;
  2. runs `docker compose pull && up -d` for the dev project on `DEV_PORT`;
  3. waits for `/api/studies` to return 200.
- **`deploy-prod`**, in the `production` environment: GitHub pauses it until a required reviewer approves, then it pulls the same `:<sha>` and restarts the production project on `PROD_PORT`, with the same health check.

## GitHub setup

Environments (already created):

| Environment | Protection |
|---|---|
| `development` | none (auto-deploy) |
| `production` | required reviewer `nghuixin`; deployments only from `master` |

Add these under **Settings → Secrets and variables → Actions**:

| Name | Kind | Value |
|---|---|---|
| `EC2_HOST` | variable | `3.238.5.106`. **Deploy jobs are skipped while this is unset.** |
| `EC2_USER` | variable | SSH user (default `ubuntu`; `ec2-user` on Amazon Linux) |
| `EC2_SSH_KEY` | secret | Private key for that user (the `.pem` contents) |
| `DEPLOY_DIR` | variable, optional | Directory on the host holding the compose file and `.env` (default `site-issue-triage`, relative to the user's home) |
| `DEV_PORT` / `PROD_PORT` | variable, optional | Defaults `8081` / `80` |

With the GitHub CLI:

```bash
gh variable set EC2_HOST --body 3.238.5.106
gh variable set EC2_USER --body ubuntu
gh secret set EC2_SSH_KEY < path/to/key.pem
```

## Host requirements

- Docker with the Compose plugin; the SSH user can run `docker` (in the `docker` group).
- The EC2 security group allows inbound SSH from GitHub Actions runners (or use a self-hosted runner), plus ports 80 and 8081.
- `DEPLOY_DIR/.env` sets `POSTGRES_PASSWORD`. It's shared by both stacks; each stack has its own volume.
- If the GHCR package is private, run `docker login ghcr.io` once on the host with a token that has `read:packages`, or make the package public.

## Manual deploy

```bash
export PROD_IMAGE=ghcr.io/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/site-issue-triage:prod PROD_PORT=80
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
```
