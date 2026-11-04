# Observability screenshots

Captured from the local `observability` Compose profile during an alert demo: the API ran with `FAULT_CREATE_ISSUE_500_RATE=0.5`, so about half of `POST /api/issues` requests returned 500 on purpose, under steady traffic. All screenshots come from the same run.

| Screenshot | What it proves |
|---|---|
| [`grafana-dashboard.png`](./grafana-dashboard.png) | The provisioned **Site Issue Triage API** dashboard: request rate by route and status (Prometheus), the POST /api/issues 5xx ratio crossing the 5% alert line (red), p95 latency, and API error logs (Loki) |
| [`grafana-loki-error-logs.png`](./grafana-loki-error-logs.png) | **Logs:** Loki query `{service="api"} \| json \| status >= 500`. Each line is JSON with `trace_id`, `span_id`, route, status and duration |
| [`grafana-tempo-trace.png`](./grafana-tempo-trace.png) | **Traces:** the trace for the top log line in the Loki screenshot (trace ID `0c0a7370528b095fe4c7ae8e3fcf01c6`, same timestamp, 10:35:27.727). The service is `site-issue-triage-api`, the span is `POST /api/issues`, and the error status is marked. The same ID in both screenshots shows logs and traces are linked |
| [`prometheus-alert-firing.png`](./prometheus-alert-firing.png) | **Alerting:** `CreateIssue5xxRateHigh` (from `ops/observability/alerts.yml`) in the **firing** state |
| [`prometheus-targets.png`](./prometheus-targets.png) | **Metrics:** Prometheus scraping the API's `/metrics` endpoint; target `UP` |

The alert's next hop, the poller's incident brief for a coding agent, is in [`../../observability/example-alert-brief.md`](../../observability/example-alert-brief.md).

## Reproduce

```bash
make up-obs          # API :8000, Grafana :3000, Prometheus :9090, Loki :3100
make alert-demo      # API restarts with half of creates failing
# send some POST /api/issues requests (use the UI at :8000/log, or curl); the alert fires after ~1–2 minutes
make poll-alerts     # writes the incident brief to .alerts/
make down-obs
```

If those ports are taken, set `API_PORT`, `GRAFANA_PORT`, `PROMETHEUS_PORT` and `LOKI_PORT`. These screenshots were taken on 18000, 13000, 13100 and 19090.
