# Implemented improvements: deployment, testing, issues, observability

What was added to close the gaps in deployment wording, the test command, issue tracking, continuous deployment and observability. Each item has a GitHub issue with acceptance criteria, closed by the pull request that implements it.

| # | Change | Issue | Status |
|---|---|---|---|
| 1 | Live deployment documented, with screenshot | [#7](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/7) | Done |
| 2 | `make test-all` | [#8](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/8) | Done, run locally |
| 3 | GitHub Issues with acceptance criteria | #1–#12 | Done |
| 4 | Deploy jobs: dev automatically, production with approval | [#9](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/9) | Done; **needs EC2 secrets to run** |
| 5 | Observability: traces, JSON logs, metrics, Grafana stack | [#10](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/10) | Done, run locally |
| 6 | Alert on POST /api/issues 5xx rate | [#11](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/11) | Done, fired locally |
| 7 | Alert poller → coding agent | [#12](https://github.com/nghuixin/ai-dev-tools-zoomcamp-2026-project-1/issues/12) | Done, run locally |

## 1. Live deployment wording

The README no longer says EC2 "was attempted". A new **Live deployment** section states **Live at http://3.238.5.106/log** and shows a screenshot of the running page.

- `README.md`, `docs/screenshots/live-ec2-log.png`
- Verified: `/log` and `/api/studies` on the host both returned 200; the screenshot was taken from the live site.

## 2. `make test-all`

One command reproduces CI's full test run, as [`scripts/test-all.sh`](../scripts/test-all.sh):

1. starts `docker-compose.yaml` under its own Compose project (`site-issue-triage-test`), so it never stops a `make up` stack;
2. waits up to 2 minutes for `/api/studies`, printing container logs if the API never comes up;
3. runs backend unit tests, then the HTTP integration tests;
4. tears the stack and its volume down on exit, whether tests pass or fail.

`API_PORT` picks the host port. The CI `integration` job now runs `make test-all` instead of repeating the same steps inline.

- `Makefile`, `scripts/test-all.sh`, `.github/workflows/ci.yml`
- Verified locally: 33 unit and 8 integration tests passed, then teardown.

## 3. GitHub Issues with acceptance criteria

Twelve issues, each with an acceptance-criteria checklist:

- **#1–#6, written retroactively** for work already done: spec, frontend MVP, backend, Docker/Compose, CI, integration tests. Each is closed with a comment naming the commit that implemented it (`4dff9e9`, `15c10b3`, `d436349`).
- **#7–#12** for this work. The pull request references them with `Closes #…`, so they close when it merges.

## 4. Continuous deployment to EC2

Two jobs follow `publish` in `.github/workflows/ci.yml`:

| Job | Environment | What it does |
|---|---|---|
| `deploy-dev` | `development` (auto) | Copies `docker-compose.prod.yaml` to the host over SCP, then over SSH runs `docker compose pull && up -d` for the dev project on port 8081 and waits for a healthy API |
| `deploy-prod` | `production` (required reviewer) | After `deploy-dev` succeeds and a reviewer approves, does the same for the production project on port 80 |

Both deploy the image from the same commit (`:<sha>`), so production gets exactly what ran in dev.

- **Environments:** created in the repo; `production` requires approval from `nghuixin` and accepts deployments only from `master`.
- **Configuration:** the jobs are skipped until the `EC2_HOST` variable and `EC2_SSH_KEY` secret are set. Full setup and host requirements: [`deployment.md`](./deployment.md).
- Files: `.github/workflows/ci.yml`, `docs/deployment.md`
- Verified: `actionlint` reports no issues. **Not yet run against the host**, because that needs the SSH key in repo secrets.

## 5. Observability

**In the API** ([`backend/app/telemetry.py`](../backend/app/telemetry.py)), wired in `main.py`:

- **Traces:** OpenTelemetry auto-instrumentation for FastAPI. Spans are exported over OTLP/HTTP when `OTEL_EXPORTER_OTLP_ENDPOINT` is set. Without it, spans are still created, so logs carry a trace ID.
- **Logs:** JSON, one line per request, with `trace_id`, `span_id`, method, path, route template, status and duration. Server errors log at `ERROR`. Uvicorn's own logs use the same format.
- **Metrics:** Prometheus counters and latency histograms by route, method and status class at `/metrics`, left out of the OpenAPI schema because it's an operations endpoint, not part of the product contract.

**In Compose** (`docker-compose.yaml`, profile `observability`; config in [`ops/observability/`](../ops/observability/)):

| Service | Role |
|---|---|
| Tempo | Receives OTLP traces from the API |
| Alloy | Reads the API container's stdout and ships it to Loki |
| Loki | Stores the JSON logs |
| Prometheus | Scrapes `/metrics` every 5s and evaluates the alert rule |
| Grafana | Pre-provisioned data sources and the **Site Issue Triage API** dashboard. A log line's `trace_id` links straight to its trace in Tempo |

`make up-obs` starts it all; plain `make up` is unchanged. Host ports are configurable (`API_PORT`, `GRAFANA_PORT`, `PROMETHEUS_PORT`, `LOKI_PORT`).

- Tests: `backend/tests/test_observability.py` checks metrics, the schema exclusion, trace IDs in JSON logs and the fault switch.
- Verified locally with the full stack:
  - Prometheus counted 2xx and 5xx creates.
  - Loki held the JSON lines.
  - A trace ID from a failed request's log line returned its trace from Tempo (`service.name=site-issue-triage-api`).
- Screenshots of every local UI, all from one run, are in [`screenshots/observability/`](./screenshots/observability/README.md): the dashboard, Loki error logs, the Tempo trace for one of those log lines (matching trace ID), the firing alert, and the Prometheus scrape target.

## 6. Alert on POST /api/issues 5xx rate

`CreateIssue5xxRateHigh` in [`ops/observability/alerts.yml`](../ops/observability/alerts.yml):

- **Condition:** more than 5% of `POST /api/issues` requests return 5xx over 2 minutes, sustained for 1 minute.
- **Annotations:** summary, description and runbook.

To demonstrate it, `FAULT_CREATE_ISSUE_500_RATE` (0–1, default 0) makes that share of creates return a 500 on purpose. `make alert-demo` restarts the API with it set to 0.5.

- Verified locally: with half of creates failing, the alert went to **firing** at about 45% errors. Screenshot: [`screenshots/observability/prometheus-alert-firing.png`](./screenshots/observability/prometheus-alert-firing.png).

## 7. Alert poller → coding agent

[`scripts/poll_alerts.py`](../scripts/poll_alerts.py) uses only the standard library. Every 30 seconds it:

1. gets firing alerts from Prometheus (`/api/v1/alerts`);
2. skips firing episodes it has already handled (alert labels + start time, kept in `.alerts/seen.json`);
3. pulls the last 15 minutes of 5xx log lines and their trace IDs from Loki;
4. writes an incident brief to `.alerts/<time>-<alert>.md`. The brief asks the agent to find the likely cause in this repo and propose a fix and a test, and tells it not to push, deploy or change infrastructure;
5. runs `ALERT_AGENT_CMD` (for example `claude -p`) with the brief on stdin and saves the reply next to it. If no agent is set, it prints the brief.

`make poll-alerts` runs it; `--once` checks a single time.

- Tests: `backend/tests/test_poll_alerts.py` covers alert IDs, brief content, and handling each alert once.
- Verified locally: during the alert demo the poller picked up `CreateIssue5xxRateHigh` and wrote a brief with the alert, 5xx log lines and trace IDs. Example: [`observability/example-alert-brief.md`](./observability/example-alert-brief.md).

## Best practice: observability for a live site

**Where this project stands.** The observability stack runs locally with the dev Compose stack, not on the live EC2 site. For this course that's enough: the requirement is that traces, logs, metrics and alerting are implemented and demonstrable, which the code, tests and screenshots show. In a real production service you would also monitor the live environment. The practices below are how to do that safely. ✓ marks what this repo already does.

**Exposure and access**
- **Never expose observability UIs publicly without authentication.** The local Grafana uses anonymous admin access for convenience; on a server that would let anyone read logs and change dashboards. Turn anonymous access off, set an admin password from a secret, and put Grafana behind TLS.
- **Prefer private access.** Bind Grafana, Prometheus and Loki to `127.0.0.1` on the host and reach them over an SSH tunnel (`ssh -L 3000:localhost:3000 ubuntu@<host>`) or AWS SSM port forwarding, with no extra open ports in the security group. Treat `/metrics` as internal too.

**Where the stack runs**
- **Keep monitoring separate from what it monitors.** If Grafana and Prometheus run on the same small instance as the app, they compete for memory and go down with it. Use a separate host, or a managed service (Grafana Cloud, Amazon Managed Prometheus/Grafana, CloudWatch with X-Ray), so an outage is still visible.
- **Size for it.** The five extra containers need roughly 1–2 GB of RAM; on a micro instance they can starve the app.

**Data**
- **Never log sensitive data.** ✓ Request logs carry method, route, status and timing, never issue descriptions (`AGENTS.md`). Production retention and access rules matter more once logs live on a server.
- **Set retention and storage limits** for Prometheus, Loki and Tempo, and keep their data on persistent volumes.
- **Sample traces under real load** (for example, a parent-based ratio sampler at 10%), keeping all error traces if the backend supports tail sampling. Locally, every request is traced. ✓ Images are pinned to exact versions and all config is in the repo.

**Alerting**
- **Alert on symptoms users feel,** such as error rate and latency, not on causes. ✓ `CreateIssue5xxRateHigh` measures failed saves directly, with a `for:` window so short blips don't page.
- **Give every alert a runbook.** ✓ The alert carries summary, description and runbook annotations.
- **Monitor the monitoring.** Alert when a scrape target is down (`up == 0`), and add an always-firing "watchdog" alert so you notice if alerting itself stops working.
- **Route and silence alerts with Alertmanager.** In production, Prometheus sends alerts to Alertmanager, which groups duplicates, supports silences during maintenance, and notifies people by email, Slack or paging. The poller in this repo reads Prometheus directly, which suits a demo. In production it would sit behind Alertmanager, for example as a webhook receiver.
- **Keep a human in the loop for agent actions.** ✓ The poller's brief tells the agent not to push, deploy or change infrastructure; fixes still go through a PR, CI and the production approval gate.

**If you add monitoring to the EC2 site**, the minimal safe version is:
1. run `--profile observability` on the host with every UI port bound to `127.0.0.1`;
2. disable anonymous Grafana access;
3. open Grafana through an SSH tunnel.

The better version moves metrics, logs and traces to a managed backend (for example, the Grafana Cloud free tier) and points the app's OTLP endpoint there.

## Still to do by hand

1. Add the `EC2_HOST` variable and `EC2_SSH_KEY` secret ([`deployment.md`](./deployment.md)), then push to `master` to run the first automated deploy and approve it in the Actions tab.
2. Check the EC2 security group allows SSH from GitHub Actions, and that the host can pull from GHCR.
3. Optional: monitor the live site as well, following the best practice above. It isn't needed for the course.
