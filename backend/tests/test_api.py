from fastapi.testclient import TestClient


def test_list_studies(client: TestClient) -> None:
    response = client.get("/api/studies")
    assert response.status_code == 200
    codes = [row["code"] for row in response.json()]
    assert codes == ["ST-018", "ST-104", "ST-221"]


def test_list_sites_can_filter_by_study(client: TestClient) -> None:
    all_sites = client.get("/api/sites")
    assert all_sites.status_code == 200
    assert len(all_sites.json()) == 6
    filtered = client.get("/api/sites", params={"study_id": 1})
    assert {row["code"] for row in filtered.json()} == {"01", "04", "12"}
    assert all(row["study_id"] == 1 for row in filtered.json())


def test_create_site_and_reject_duplicate_code(client: TestClient) -> None:
    created = client.post(
        "/api/sites",
        json={"study_id": 1, "code": "15", "name": "East Annex"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["code"] == "15"
    assert body["name"] == "East Annex"
    auto = client.post("/api/sites", json={"study_id": 3, "name": "River Clinic"})
    assert auto.status_code == 201
    assert auto.json()["code"] == "02"
    duplicate = client.post(
        "/api/sites",
        json={"study_id": 1, "code": "01", "name": "Metro duplicate"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json() == {
        "error": "Could not add site. Use a unique site number for this study."
    }


def test_list_issues_hides_resolved_by_default_and_sorts(client: TestClient) -> None:
    default_list = client.get("/api/issues")
    assert default_list.status_code == 200
    rows = default_list.json()
    assert rows
    assert all(row["status"] != "RESOLVED" for row in rows)
    ranks = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    keys = [(ranks[row["severity"]], row["created_at"], row["id"]) for row in rows]
    assert keys == sorted(keys)
    assert "notes" not in rows[0] or rows[0]["notes"] is None

    active = client.get("/api/issues", params={"status": "active"})
    assert [row["id"] for row in active.json()] == [row["id"] for row in rows]

    everyone = client.get("/api/issues", params={"status": "ALL"})
    statuses = {row["status"] for row in everyone.json()}
    assert "RESOLVED" in statuses
    assert len(everyone.json()) > len(rows)


def test_list_issues_filters(client: TestClient) -> None:
    by_study = client.get("/api/issues", params={"study_id": 1, "status": "ALL"})
    assert all(row["study_id"] == 1 for row in by_study.json())
    by_severity = client.get("/api/issues", params={"severity": "CRITICAL"})
    assert all(row["severity"] == "CRITICAL" for row in by_severity.json())
    assert by_severity.json()
    assert by_severity.json()[0]["overdue"] is True


def test_get_issue_includes_notes_and_edited_fields(client: TestClient) -> None:
    consent = client.get("/api/issues/3")
    assert consent.status_code == 200
    body = consent.json()
    assert body["category"] == "CONSENT"
    assert body["severity"] == "HIGH"
    assert body["ai_suggestion"]["severity"] == "MEDIUM"
    assert "severity" in body["edited_fields"]
    assert isinstance(body["notes"], list)

    missing = client.get("/api/issues/999")
    assert missing.status_code == 404
    assert missing.json() == {"error": "Issue not found"}


def test_create_issue_returns_201(client: TestClient) -> None:
    response = client.post(
        "/api/issues",
        json={
            "study_id": 1,
            "site_id": 1,
            "description": "Screening log is missing Friday outcomes.",
            "category": "ENROLLMENT",
            "severity": "MEDIUM",
            "summary": "Screening log gap",
            "recommended_action": "Backfill the log before the next slot.",
            "ai_suggestion": {
                "category": "ENROLLMENT",
                "severity": "MEDIUM",
                "summary": "Screening log gap",
                "recommended_action": "Backfill the log before the next slot.",
                "rationale": "Contained enrollment process issue.",
                "phi_flag": False,
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["edited_fields"] == []
    assert body["due_date"]
    assert body["study"]["code"] == "ST-104"
    assert body["site"]["code"] == "01"


def test_create_issue_rejects_mismatched_site(client: TestClient) -> None:
    response = client.post(
        "/api/issues",
        json={
            "study_id": 1,
            "site_id": 4,
            "description": "Wrong site for this study.",
            "category": "OTHER",
            "severity": "LOW",
        },
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Site does not belong to the selected study"}


def test_patch_status_and_resolve_gate(client: TestClient) -> None:
    started = client.patch("/api/issues/1", json={"status": "IN_PROGRESS"})
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"
    assert started.json()["resolved_at"] is None

    blocked = client.patch("/api/issues/1", json={"status": "RESOLVED"})
    assert blocked.status_code == 400
    assert blocked.json() == {"error": "Resolution note required"}

    resolved = client.patch(
        "/api/issues/1",
        json={"status": "RESOLVED", "resolution_note": "Sponsor notified; clock documented."},
    )
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "RESOLVED"
    assert body["resolved_at"]
    assert body["overdue"] is False


def test_add_note(client: TestClient) -> None:
    response = client.post("/api/issues/1/notes", json={"body": "Called pharmacy."})
    assert response.status_code == 201
    note = response.json()
    assert note["issue_id"] == 1
    assert note["body"] == "Called pharmacy."
    detail = client.get("/api/issues/1")
    bodies = [row["body"] for row in detail.json()["notes"]]
    assert "Called pharmacy." in bodies

    empty = client.post("/api/issues/1/notes", json={"body": "  "})
    assert empty.status_code == 400
    assert empty.json() == {"error": "Note body is required"}


def test_csv_export_matches_list_filters(client: TestClient) -> None:
    listed = client.get("/api/issues", params={"study_id": 1, "status": "active"})
    csv_response = client.get("/api/issues.csv", params={"study_id": 1, "status": "active"})
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    lines = [line for line in csv_response.text.strip().splitlines() if line]
    assert lines[0] == "id,study,site,severity,status,summary,category,owner,due_date,age_days,overdue"
    assert len(lines) - 1 == len(listed.json())
    assert "RESOLVED" not in csv_response.text
    ids = {str(row["id"]) for row in listed.json()}
    exported_ids = {line.split(",", 1)[0] for line in lines[1:]}
    assert exported_ids == ids


def test_analyze_is_not_captured_as_issue_id(client: TestClient) -> None:
    response = client.post(
        "/api/issues/analyze",
        json={
            "study": "ST-104",
            "site": "01 Metro",
            "description": "Pharmacy documented a temperature excursion on IP kits.",
        },
    )
    assert response.status_code == 200
    assert response.json()["category"] == "IP_MANAGEMENT"


def test_no_auth_required(client: TestClient) -> None:
    response = client.get("/api/studies")
    assert response.status_code == 200
    assert "www-authenticate" not in {key.lower() for key in response.headers}
