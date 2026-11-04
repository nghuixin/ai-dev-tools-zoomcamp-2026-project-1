"""Observability: OpenTelemetry traces, JSON logs with trace IDs, Prometheus metrics.

Everything is configured from environment variables so local runs and unit tests
need nothing extra:

- ``OTEL_EXPORTER_OTLP_ENDPOINT`` (e.g. ``http://tempo:4318``): when set, spans are
  exported over OTLP/HTTP. When unset, spans are still created (so logs carry a
  trace ID) but not exported.
- ``OTEL_SERVICE_NAME``: service name on spans (default ``site-issue-triage-api``).
- ``LOG_LEVEL``: root log level (default ``INFO``).
- ``FAULT_CREATE_ISSUE_500_RATE``: 0–1, share of ``POST /api/issues`` requests that
  fail with a 500 on purpose. Default 0 (off). Used only to demonstrate the alert.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator

DEFAULT_SERVICE_NAME = "site-issue-triage-api"
REQUEST_LOGGER = "app.request"
_EXTRA_FIELDS = ("method", "path", "route", "status", "duration_ms", "error")


def current_trace_ids() -> tuple[str | None, str | None]:
    """Trace and span ID of the active span, as lowercase hex, or (None, None)."""
    context = trace.get_current_span().get_span_context()
    if not context.is_valid:
        return None, None
    return format(context.trace_id, "032x"), format(context.span_id, "016x")


class JsonFormatter(logging.Formatter):
    """One JSON object per line, including the active trace and span IDs."""

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = current_trace_ids()
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "span_id": span_id,
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
    # Request lines come from the middleware below, with trace IDs.
    logging.getLogger("uvicorn.access").disabled = True


_tracer_provider: TracerProvider | None = None


def configure_tracing() -> TracerProvider:
    global _tracer_provider
    if _tracer_provider is None:
        service = os.environ.get("OTEL_SERVICE_NAME", DEFAULT_SERVICE_NAME)
        provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service}))
        if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer_provider = provider
    return _tracer_provider


def fault_rate() -> float:
    try:
        return min(max(float(os.environ.get("FAULT_CREATE_ISSUE_500_RATE", "0")), 0.0), 1.0)
    except ValueError:
        return 0.0


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def setup_observability(app: FastAPI) -> None:
    """Call after routers are included and before the SPA catch-all is mounted."""
    configure_logging()
    log = logging.getLogger(REQUEST_LOGGER)

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        start = time.perf_counter()
        if (
            request.method == "POST"
            and request.url.path == "/api/issues"
            and random.random() < fault_rate()
        ):
            response = JSONResponse(status_code=500, content={"error": "injected fault"})
            error = "injected fault (FAULT_CREATE_ISSUE_500_RATE)"
        else:
            try:
                response = await call_next(request)
                error = None
            except Exception:
                log.exception(
                    "unhandled error",
                    extra={"method": request.method, "path": request.url.path, "status": 500},
                )
                raise
        status = response.status_code
        log.log(
            logging.ERROR if status >= 500 else logging.INFO,
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "route": route_template(request),
                "status": status,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                "error": error,
            },
        )
        return response

    # Added after the logging middleware so it wraps it and counts injected 500s too.
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # Outermost: every request gets a server span, so the inner middleware sees a trace ID.
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=configure_tracing(),
        excluded_urls="metrics",
    )
