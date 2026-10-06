from __future__ import annotations

import uuid

import httpx
import pytest

pytestmark = pytest.mark.integration


def _study_id(client: httpx.Client, code: str = "ST-104") -> int:
    studies = client.get("/api/studies")
    assert studies.status_code == 200
    match = next(row for row in studies.json() if row["code"] == code)
    return match["id"]


def _first_site(client: httpx.Client, study_id: int) -> dict:
    sites = client.get("/api/sites", params={"study_id": study_id})
    assert sites.status_code == 200
    assert sites.json()
    return sites.json()[0]


def _create_issue(client: httpx.Client, description: str) -> dict:
    study_id = _study_id(client)
    site = _first_site(client, study_id)
    response = client.post(
        "/api/issues",
        json={
            "study_id": study_id,
            "site_id": site["id"],
            "description": description,
            "category": "OTHER",
            "severity": "LOW",
            "summary": description[:80],
        },
    )
    assert response.status_code in (200, 201)
    return response.json()


def test_seeded_studies(client: httpx.Client) -> None:
    response = client.get("/api/studies")
    assert response.status_code == 200
    codes = {row["code"] for row in response.json()}
    assert {"ST-018", "ST-104", "ST-221"} <= codes


def test_create_site_then_filter(client: httpx.Client) -> None:
    study_id = _study_id(client)
    code = f"i{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/sites",
        json={"study_id": study_id, "code": code, "name": f"Integration {code}"},
    )
    assert created.status_code in (200, 201)
    assert created.json()["code"] == code
    listed = client.get("/api/sites", params={"study_id": study_id})
    assert listed.status_code == 200
    assert any(row["code"] == code for row in listed.json())
    assert all(row["study_id"] == study_id for row in listed.json())


def test_analyze_create_get(client: httpx.Client) -> None:
    token = uuid.uuid4().hex[:8]
    analyze = client.post(
        "/api/issues/analyze",
        json={
            "study": "ST-104 HARMONY NSCLC",
            "site": "01 Metro General",
            "description": f"Screening log gap for integration {token}.",
        },
    )
    assert analyze.status_code == 200
    suggestion = analyze.json()
    study_id = _study_id(client)
    site = _first_site(client, study_id)
    created = client.post(
        "/api/issues",
        json={
            "study_id": study_id,
            "site_id": site["id"],
            "description": f"Screening log gap for integration {token}.",
            "category": suggestion["category"],
            "severity": suggestion["severity"],
            "summary": suggestion["summary"],
            "recommended_action": suggestion["recommended_action"],
            "ai_suggestion": suggestion,
        },
    )
    assert created.status_code in (200, 201)
    detail = client.get(f"/api/issues/{created.json()['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["notes"] == []
    assert body["edited_fields"] == []
    assert body["due_date"]


def test_list_default_and_all(client: httpx.Client) -> None:
    default = client.get("/api/issues")
    assert default.status_code == 200
    rows = default.json()
    assert rows
    assert all(row["status"] != "RESOLVED" for row in rows)
    everyone = client.get("/api/issues", params={"status": "ALL"})
    assert everyone.status_code == 200
    statuses = {row["status"] for row in everyone.json()}
    assert "RESOLVED" in statuses
    assert len(everyone.json()) >= len(rows)


def test_resolve_requires_note(client: httpx.Client) -> None:
    issue = _create_issue(client, f"Resolve-gate issue {uuid.uuid4().hex[:8]}")
    blocked = client.patch(f"/api/issues/{issue['id']}", json={"status": "RESOLVED"})
    assert blocked.status_code == 400
    assert blocked.json() == {"error": "Resolution note required"}
    resolved = client.patch(
        f"/api/issues/{issue['id']}",
        json={"status": "RESOLVED", "resolution_note": "Closed in integration test."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolved_at"]


def test_append_note(client: httpx.Client) -> None:
    issue = _create_issue(client, f"Note issue {uuid.uuid4().hex[:8]}")
    text = f"Called pharmacy {uuid.uuid4().hex[:8]}"
    note = client.post(f"/api/issues/{issue['id']}/notes", json={"body": text})
    assert note.status_code in (200, 201)
    assert note.json()["body"] == text
    detail = client.get(f"/api/issues/{issue['id']}")
    assert text in [row["body"] for row in detail.json()["notes"]]


def test_csv_matches_list_filters(client: httpx.Client) -> None:
    study_id = _study_id(client)
    params = {"study_id": study_id, "status": "active"}
    listed = client.get("/api/issues", params=params)
    csv_response = client.get("/api/issues.csv", params=params)
    assert listed.status_code == 200
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    lines = [line for line in csv_response.text.strip().splitlines() if line]
    assert lines[0].startswith("id,")
    assert len(lines) - 1 == len(listed.json())
    exported_ids = {line.split(",", 1)[0] for line in lines[1:]}
    assert exported_ids == {str(row["id"]) for row in listed.json()}


def test_spa_same_origin(client: httpx.Client) -> None:
    home = client.get("/")
    log = client.get("/log")
    assert home.status_code == 200
    assert log.status_code == 200
    assert "text/html" in home.headers.get("content-type", "")
    assert "text/html" in log.headers.get("content-type", "")
    assert "<html" in home.text.lower()
    assert "<html" in log.text.lower()
