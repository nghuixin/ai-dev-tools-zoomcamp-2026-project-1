"""HTTP tests against a running Compose API. Requires INTEGRATION_BASE_URL."""

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.integration


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: HTTP tests against a running Compose API"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("INTEGRATION_BASE_URL"):
        return
    skip = pytest.mark.skip(reason="INTEGRATION_BASE_URL is unset")
    for item in items:
        item.add_marker(skip)


@pytest.fixture
def base_url() -> str:
    return os.environ["INTEGRATION_BASE_URL"].rstrip("/")


@pytest.fixture
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=30.0) as http:
        yield http
