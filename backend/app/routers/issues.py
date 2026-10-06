from app.analyze import heuristic_analyze
from app.deps import get_store
from app.models import (
    AiSuggestion,
    AnalyzeRequest,
    CreateIssueRequest,
    CreateNoteRequest,
    Issue,
    IssueNote,
    Severity,
    UpdateIssueRequest,
)
from app.store import Store
from fastapi import APIRouter, Depends, Response, status

router = APIRouter(tags=["issues"])


@router.post("/api/issues/analyze", response_model=AiSuggestion)
def analyze_issue(payload: AnalyzeRequest) -> AiSuggestion:
    return heuristic_analyze(payload)


@router.get("/api/issues.csv")
def export_issues_csv(
    study_id: int | None = None,
    site_id: int | None = None,
    status: str | None = None,
    severity: Severity | None = None,
    store: Store = Depends(get_store),
) -> Response:
    body = store.export_csv(study_id=study_id, site_id=site_id, status=status, severity=severity)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=site-issues.csv"},
    )


@router.get("/api/issues", response_model=list[Issue], response_model_exclude={"notes"})
def list_issues(
    study_id: int | None = None,
    site_id: int | None = None,
    status: str | None = None,
    severity: Severity | None = None,
    store: Store = Depends(get_store),
) -> list[Issue]:
    return store.list_issues(study_id=study_id, site_id=site_id, status=status, severity=severity)


@router.post("/api/issues", response_model=Issue, status_code=status.HTTP_201_CREATED)
def create_issue(payload: CreateIssueRequest, store: Store = Depends(get_store)) -> Issue:
    return store.create_issue(payload)


@router.get("/api/issues/{issue_id}", response_model=Issue)
def get_issue(issue_id: int, store: Store = Depends(get_store)) -> Issue:
    return store.get_issue(issue_id)


@router.patch("/api/issues/{issue_id}", response_model=Issue)
def update_issue(
    issue_id: int,
    payload: UpdateIssueRequest,
    store: Store = Depends(get_store),
) -> Issue:
    return store.update_issue(issue_id, payload)


@router.post(
    "/api/issues/{issue_id}/notes",
    response_model=IssueNote,
    status_code=status.HTTP_201_CREATED,
)
def add_issue_note(
    issue_id: int,
    payload: CreateNoteRequest,
    store: Store = Depends(get_store),
) -> IssueNote:
    return store.add_note(issue_id, payload.body)
