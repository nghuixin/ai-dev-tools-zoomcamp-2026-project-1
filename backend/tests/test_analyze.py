from app.analyze import detect_phi, heuristic_analyze, validate_suggestion
from app.errors import StoreError
from app.models import AiSuggestion, AnalyzeRequest, Category, Severity
from fastapi.testclient import TestClient
from pytest import raises


def test_heuristic_analyze_safety_reporting_critical() -> None:
    suggestion = heuristic_analyze(
        AnalyzeRequest(
            study="ST-104 HARMONY NSCLC",
            site="01 Metro General",
            description="The 24-hour SAE notification was not sent and the reporting clock is past due.",
        )
    )
    assert suggestion.category == Category.SAFETY_REPORTING
    assert suggestion.severity == Severity.CRITICAL
    assert len(suggestion.summary) <= 200
    assert "Do not assess causality" in suggestion.recommended_action
    assert suggestion.phi_flag is False


def test_heuristic_analyze_requires_fields() -> None:
    with raises(StoreError) as caught:
        heuristic_analyze(AnalyzeRequest(study=" ", site="01", description="consent version"))
    assert caught.value.error == "study, site, and description are required"
    assert caught.value.status == 400


def test_detect_phi_and_flag_on_analyze() -> None:
    text = "Coordinator emailed jane.doe@site.org about the visit window."
    assert detect_phi(text) is True
    suggestion = heuristic_analyze(
        AnalyzeRequest(study="ST-018", site="03 Ridgeview", description=text)
    )
    assert suggestion.phi_flag is True
    assert suggestion.category == Category.PROTOCOL_DEVIATION


def test_validate_suggestion_rejects_blank_or_long_summary() -> None:
    base = AiSuggestion(
        category=Category.OTHER,
        severity=Severity.LOW,
        summary="ok",
        recommended_action="Do the next operational step.",
        rationale="Low impact.",
        phi_flag=False,
    )
    assert validate_suggestion(base) is not None
    assert validate_suggestion(None) is None
    assert validate_suggestion(base.model_copy(update={"summary": "  "})) is None
    too_long = base.model_construct(
        category=base.category,
        severity=base.severity,
        summary="x" * 201,
        recommended_action=base.recommended_action,
        rationale=base.rationale,
        phi_flag=False,
    )
    assert validate_suggestion(too_long) is None
    assert validate_suggestion(base.model_copy(update={"recommended_action": ""})) is None
    assert validate_suggestion(base.model_copy(update={"rationale": " "})) is None


def test_analyze_endpoint_returns_snake_case(client: TestClient) -> None:
    response = client.post(
        "/api/issues/analyze",
        json={
            "study": "ST-221 RIVER Heart Failure",
            "site": "02 Harbor Medical",
            "description": "Two screenings used the wrong consent version after IRB approved 4.1.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "category",
        "severity",
        "summary",
        "recommended_action",
        "rationale",
        "phi_flag",
    }
    assert body["category"] == "CONSENT"
    assert body["severity"] == "HIGH"


def test_analyze_missing_json_fields_use_error_shape(client: TestClient) -> None:
    response = client.post("/api/issues/analyze", json={"study": "ST-104"})
    assert response.status_code == 400
    assert "error" in response.json()
    assert "detail" not in response.json()
