import json
import logging

from opentelemetry import trace

from app.telemetry import JsonFormatter, configure_tracing


def _create_payload(client) -> dict:
    study = client.get("/api/studies").json()[0]
    site = client.get("/api/sites", params={"study_id": study["id"]}).json()[0]
    return {
        "study_id": study["id"],
        "site_id": site["id"],
        "description": "Freezer log missing two days of temperature readings",
        "category": "OTHER",
        "severity": "LOW",
    }


def test_metrics_endpoint_counts_requests(client):
    client.get("/api/studies")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert 'handler="/api/studies"' in body


def test_metrics_endpoint_not_in_openapi_schema(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/metrics" not in paths


def test_json_log_line_carries_trace_id():
    tracer = configure_tracing().get_tracer("test")
    record = logging.LogRecord("app.request", logging.INFO, __file__, 1, "request", None, None)
    record.status = 201
    with tracer.start_as_current_span("unit-test") as span:
        line = json.loads(JsonFormatter().format(record))
        expected = format(span.get_span_context().trace_id, "032x")
    assert line["message"] == "request"
    assert line["status"] == 201
    assert line["trace_id"] == expected
    assert len(line["span_id"]) == 16


def test_json_log_line_without_span_has_null_trace_id():
    record = logging.LogRecord("app", logging.INFO, __file__, 1, "hello", None, None)
    assert trace.get_current_span().get_span_context().is_valid is False
    line = json.loads(JsonFormatter().format(record))
    assert line["trace_id"] is None


def test_fault_injection_is_off_by_default(client, monkeypatch):
    monkeypatch.delenv("FAULT_CREATE_ISSUE_500_RATE", raising=False)
    response = client.post("/api/issues", json=_create_payload(client))
    assert response.status_code == 201


def test_fault_injection_returns_500_and_is_counted_as_5xx(client, monkeypatch):
    payload = _create_payload(client)
    monkeypatch.setenv("FAULT_CREATE_ISSUE_500_RATE", "1")
    response = client.post("/api/issues", json=payload)
    assert response.status_code == 500
    assert response.json() == {"error": "injected fault"}
    metrics = client.get("/metrics").text
    assert any(
        'handler="/api/issues"' in line and 'method="POST"' in line and 'status="5xx"' in line
        for line in metrics.splitlines()
        if line.startswith("http_requests_total")
    )
