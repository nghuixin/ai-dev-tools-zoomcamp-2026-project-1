<!-- Example output of scripts/poll_alerts.py from a local alert demo (FAULT_CREATE_ISSUE_500_RATE=0.5), trimmed to 3 log lines. -->

# Incident: CreateIssue5xxRateHigh

You are the on-call engineer for this repository (Site Issue Triage: FastAPI backend in
`backend/`, React frontend in `frontend/`, contract in `openapi.yaml`, rules in `AGENTS.md`).
A production alert is firing. Investigate it in this codebase:

1. Explain the most likely cause, citing files and lines.
2. Propose a minimal fix and a regression test (backend tests live in `backend/tests/`).
3. If the failures are injected by `FAULT_CREATE_ISSUE_500_RATE`, say so; that is a demo, not a bug.
Do not push, deploy or change infrastructure. Reply in Markdown.

## Alert

- **Name:** CreateIssue5xxRateHigh
- **Active since:** 2026-11-04T00:40:32.488407926Z
- **Value:** 4.468085106382979e-01
- **Summary:** Creating issues is failing: 44.68% of POST /api/issues returned 5xx
- **Description:** More than 5% of POST /api/issues requests returned a 5xx status over the last 2 minutes, sustained for 1 minute. Site managers cannot save new issues.
- **Runbook:** Check API logs in Grafana (Loki: {service="api"} | json | status >= 500), open a trace ID in Tempo, then check the database. For a demo, FAULT_CREATE_ISSUE_500_RATE injects failures.
- **Labels:** `{"alertname": "CreateIssue5xxRateHigh", "route": "POST /api/issues", "service": "site-issue-triage-api", "severity": "page"}`

## Recent 5xx log lines (Loki: `{service="api"} | json | status >= 500`)

```json
{"duration_ms": 0.1, "error": "injected fault (FAULT_CREATE_ISSUE_500_RATE)", "level": "ERROR", "logger": "app.request", "message": "request", "method": "POST", "path": "/api/issues", "route": "/api/issues", "span_id": "08326131941b0759", "status": 500, "trace_id": "4e86ee7c6b7be1a7b14a2205d266b84e", "ts": "2026-11-04T00:42:04.455141+00:00"}
{"duration_ms": 0.1, "error": "injected fault (FAULT_CREATE_ISSUE_500_RATE)", "level": "ERROR", "logger": "app.request", "message": "request", "method": "POST", "path": "/api/issues", "route": "/api/issues", "span_id": "0a24536b16350682", "status": 500, "trace_id": "8c3b8da129880ca4f9956177ba68ed44", "ts": "2026-11-04T00:41:31.215119+00:00"}
{"duration_ms": 0.1, "error": "injected fault (FAULT_CREATE_ISSUE_500_RATE)", "level": "ERROR", "logger": "app.request", "message": "request", "method": "POST", "path": "/api/issues", "route": "/api/issues", "span_id": "23860e982396cef5", "status": 500, "trace_id": "cbff456e525a908d96573f33b4346e4a", "ts": "2026-11-04T00:42:35.605492+00:00"}
```

## Trace IDs

- `19ec4895a9256ac2bdb9ff3ae1e3d6a4`
- `2ebf7217615fc2e1131e34eba9904db5`
- `314c2381483554bde9a27348bdcab2e7`
- … (one per log line)

Grafana Explore: http://127.0.0.1:13000/explore (Tempo for traces, Loki for logs)
