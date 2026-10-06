from __future__ import annotations

from contextlib import contextmanager
from csv import writer
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from io import StringIO
from typing import Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.analyze import detect_phi
from app.database import create_memory_session_factory
from app.db_models import IssueRow, NoteRow, SiteRow, StudyRow
from app.errors import StoreError
from app.models import (
    DUE_DAYS,
    EDIT_COMPARE_FIELDS,
    AiSuggestion,
    Category,
    CreateIssueRequest,
    CreateSiteRequest,
    Issue,
    IssueNote,
    Severity,
    Site,
    Status,
    Study,
    UpdateIssueRequest,
)
from app.seed_data import ISSUES, SITES, STUDIES

SEVERITY_RANK = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return utc_now().date()


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _dump_suggestion(suggestion: AiSuggestion | None) -> dict | None:
    if suggestion is None:
        return None
    return suggestion.model_dump(mode="json")


def _load_suggestion(raw: dict | None) -> AiSuggestion | None:
    if not raw:
        return None
    return AiSuggestion.model_validate(raw)


class Store:
    def __init__(self, session_factory: sessionmaker | None = None) -> None:
        self._session_factory = session_factory or create_memory_session_factory()

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def seed(self) -> None:
        with self._session() as session:
            if session.scalar(select(func.count()).select_from(StudyRow)):
                return
            studies: dict[str, StudyRow] = {}
            for item in STUDIES:
                row = StudyRow(code=item["code"], name=item["name"])
                session.add(row)
                session.flush()
                studies[row.code] = row
            sites: dict[tuple[str, str], SiteRow] = {}
            for item in SITES:
                study = studies[item["study_code"]]
                row = SiteRow(study_id=study.id, code=item["code"], name=item["name"])
                session.add(row)
                session.flush()
                sites[(item["study_code"], item["code"])] = row
            for item in ISSUES:
                created_at = utc_now() + timedelta(days=item["created"])
                due = today() + timedelta(days=item["created"] + DUE_DAYS[item["severity"]])
                resolved_at = None
                if item["status"] == Status.RESOLVED:
                    resolved_at = utc_now() + timedelta(days=item.get("resolved", 0))
                site = sites[(item["study_code"], item["site_code"])]
                issue = IssueRow(
                    study_id=site.study_id,
                    site_id=site.id,
                    description=item["description"],
                    category=_enum_value(item["category"]),
                    severity=_enum_value(item["severity"]),
                    summary=item["summary"],
                    recommended_action=item["recommended_action"],
                    status=_enum_value(item["status"]),
                    owner=item["owner"],
                    due_date=due,
                    resolution_note=item.get("resolution_note"),
                    ai_suggestion=_dump_suggestion(item["ai"]),
                    phi_flag=False,
                    created_at=created_at,
                    updated_at=created_at,
                    resolved_at=resolved_at,
                )
                session.add(issue)
                session.flush()
                if item["status"] == Status.IN_PROGRESS:
                    session.add(
                        NoteRow(
                            issue_id=issue.id,
                            body="Owner assigned; waiting on documentation.",
                            created_at=created_at + timedelta(days=1),
                        )
                    )

    def list_studies(self) -> list[Study]:
        with self._session() as session:
            rows = list(session.scalars(select(StudyRow).order_by(StudyRow.code)))
            return [Study(id=row.id, code=row.code, name=row.name) for row in rows]

    def list_sites(self, study_id: int | None = None) -> list[Site]:
        with self._session() as session:
            stmt = select(SiteRow)
            if study_id is not None:
                stmt = stmt.where(SiteRow.study_id == study_id)
            rows = list(session.scalars(stmt.order_by(SiteRow.code)))
            return [
                Site(id=row.id, study_id=row.study_id, code=row.code, name=row.name) for row in rows
            ]

    def create_site(self, payload: CreateSiteRequest) -> Site:
        with self._session() as session:
            study = session.get(StudyRow, payload.study_id)
            if study is None:
                raise StoreError("Unknown study")
            name = payload.name.strip()
            if not name:
                raise StoreError("study_id and name are required")
            code = (payload.code or "").strip()
            if not code:
                count = session.scalar(
                    select(func.count()).select_from(SiteRow).where(SiteRow.study_id == payload.study_id)
                ) or 0
                code = f"{count + 1:02d}"
            exists = session.scalar(
                select(SiteRow.id).where(SiteRow.study_id == payload.study_id, SiteRow.code == code)
            )
            if exists is not None:
                raise StoreError("Could not add site. Use a unique site number for this study.")
            row = SiteRow(study_id=payload.study_id, code=code, name=name)
            session.add(row)
            session.flush()
            return Site(id=row.id, study_id=row.study_id, code=row.code, name=row.name)

    def _require_site(self, session: Session, study_id: int, site_id: int) -> SiteRow:
        site = session.get(SiteRow, site_id)
        if site is None or site.study_id != study_id:
            raise StoreError("Site does not belong to the selected study")
        return site

    def _load_issue(self, session: Session, issue_id: int, include_notes: bool) -> IssueRow:
        options = [joinedload(IssueRow.study), joinedload(IssueRow.site)]
        if include_notes:
            options.append(joinedload(IssueRow.notes))
        row = session.scalars(
            select(IssueRow).options(*options).where(IssueRow.id == issue_id)
        ).unique().one_or_none()
        if row is None:
            raise StoreError("Issue not found", 404)
        return row

    def _to_issue(self, record: IssueRow, include_notes: bool) -> Issue:
        suggestion = _load_suggestion(record.ai_suggestion)
        edited = []
        if suggestion is not None:
            for field_name in EDIT_COMPARE_FIELDS:
                saved = _enum_value(getattr(record, field_name) or "").strip()
                original = _enum_value(getattr(suggestion, field_name) or "").strip()
                if saved != original:
                    edited.append(field_name)
        created = record.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = max(0, (utc_now().date() - created.date()).days)
        status = Status(record.status)
        overdue = bool(
            record.due_date
            and status != Status.RESOLVED
            and record.due_date < today()
        )
        notes = None
        if include_notes:
            notes = [
                IssueNote(id=note.id, issue_id=note.issue_id, body=note.body, created_at=note.created_at)
                for note in record.notes
            ]
        return Issue(
            id=record.id,
            study_id=record.study_id,
            site_id=record.site_id,
            study=Study(id=record.study.id, code=record.study.code, name=record.study.name),
            site=Site(
                id=record.site.id,
                study_id=record.site.study_id,
                code=record.site.code,
                name=record.site.name,
            ),
            description=record.description,
            category=Category(record.category),
            severity=Severity(record.severity),
            summary=record.summary,
            recommended_action=record.recommended_action,
            status=status,
            owner=record.owner,
            due_date=record.due_date,
            resolution_note=record.resolution_note,
            ai_suggestion=suggestion,
            edited_fields=edited,
            phi_flag=record.phi_flag,
            created_at=record.created_at,
            updated_at=record.updated_at,
            resolved_at=record.resolved_at,
            age_days=age,
            overdue=overdue,
            notes=notes,
        )

    def list_issues(
        self,
        study_id: int | None = None,
        site_id: int | None = None,
        status: str | None = None,
        severity: Severity | None = None,
    ) -> list[Issue]:
        with self._session() as session:
            stmt = select(IssueRow).options(joinedload(IssueRow.study), joinedload(IssueRow.site))
            if study_id is not None:
                stmt = stmt.where(IssueRow.study_id == study_id)
            if site_id is not None:
                stmt = stmt.where(IssueRow.site_id == site_id)
            if severity is not None:
                stmt = stmt.where(IssueRow.severity == _enum_value(severity))
            status_value = status or "active"
            if status_value == "active":
                stmt = stmt.where(IssueRow.status != Status.RESOLVED.value)
            elif status_value != "ALL":
                try:
                    wanted = Status(status_value)
                except ValueError as exc:
                    raise StoreError("Invalid status") from exc
                stmt = stmt.where(IssueRow.status == wanted.value)
            rows = list(session.scalars(stmt).unique())
            rows.sort(
                key=lambda row: (SEVERITY_RANK[Severity(row.severity)], row.created_at, row.id),
            )
            return [self._to_issue(row, include_notes=False) for row in rows]

    def get_issue(self, issue_id: int) -> Issue:
        with self._session() as session:
            return self._to_issue(self._load_issue(session, issue_id, include_notes=True), True)

    def create_issue(self, payload: CreateIssueRequest) -> Issue:
        description = payload.description.strip()
        if not description:
            raise StoreError("description is required")
        with self._session() as session:
            self._require_site(session, payload.study_id, payload.site_id)
            now = utc_now()
            due = payload.due_date or (today() + timedelta(days=DUE_DAYS[payload.severity]))
            row = IssueRow(
                study_id=payload.study_id,
                site_id=payload.site_id,
                description=description,
                category=_enum_value(payload.category),
                severity=_enum_value(payload.severity),
                summary=(payload.summary or "").strip(),
                recommended_action=(payload.recommended_action or "").strip(),
                status=Status.OPEN.value,
                owner=(payload.owner or "").strip() or None,
                due_date=due,
                resolution_note=None,
                ai_suggestion=_dump_suggestion(payload.ai_suggestion),
                phi_flag=payload.phi_flag if payload.phi_flag is not None else detect_phi(description),
                created_at=now,
                updated_at=now,
                resolved_at=None,
            )
            session.add(row)
            session.flush()
            return self._to_issue(self._load_issue(session, row.id, include_notes=True), True)

    def update_issue(self, issue_id: int, payload: UpdateIssueRequest) -> Issue:
        with self._session() as session:
            existing = session.get(IssueRow, issue_id)
            if existing is None:
                raise StoreError("Issue not found", 404)
            was_resolved = existing.resolved_at
            data = payload.model_dump(exclude_unset=True)
            for key, value in data.items():
                if key in {"category", "severity", "status"} and value is not None:
                    setattr(existing, key, _enum_value(value))
                else:
                    setattr(existing, key, value)
            if "owner" in data:
                existing.owner = (payload.owner or "").strip() or None
            if "resolution_note" in data:
                existing.resolution_note = (payload.resolution_note or "").strip() or None
            if "description" in data:
                existing.description = (payload.description or "").strip()
                if not existing.description:
                    raise StoreError("description is required")
            self._require_site(session, existing.study_id, existing.site_id)
            if existing.status == Status.RESOLVED.value and not (existing.resolution_note or "").strip():
                raise StoreError("Resolution note required")
            if not existing.due_date:
                existing.due_date = today() + timedelta(days=DUE_DAYS[Severity(existing.severity)])
            if existing.status == Status.RESOLVED.value and was_resolved is None:
                existing.resolved_at = utc_now()
            existing.updated_at = utc_now()
            session.flush()
            return self._to_issue(self._load_issue(session, issue_id, include_notes=True), True)

    def add_note(self, issue_id: int, body: str) -> IssueNote:
        text = body.strip()
        if not text:
            raise StoreError("Note body is required")
        with self._session() as session:
            issue = session.get(IssueRow, issue_id)
            if issue is None:
                raise StoreError("Issue not found", 404)
            note = NoteRow(issue_id=issue_id, body=text, created_at=utc_now())
            session.add(note)
            session.flush()
            return IssueNote(id=note.id, issue_id=note.issue_id, body=note.body, created_at=note.created_at)

    def export_csv(
        self,
        study_id: int | None = None,
        site_id: int | None = None,
        status: str | None = None,
        severity: Severity | None = None,
    ) -> str:
        rows = self.list_issues(study_id=study_id, site_id=site_id, status=status, severity=severity)
        buffer = StringIO()
        csv_writer = writer(buffer)
        csv_writer.writerow(
            [
                "id",
                "study",
                "site",
                "severity",
                "status",
                "summary",
                "category",
                "owner",
                "due_date",
                "age_days",
                "overdue",
            ]
        )
        for row in rows:
            csv_writer.writerow(
                [
                    row.id,
                    f"{row.study.code} {row.study.name}",
                    f"{row.site.code} {row.site.name}",
                    row.severity.value,
                    row.status.value,
                    row.summary,
                    row.category.value,
                    row.owner or "",
                    row.due_date.isoformat() if row.due_date else "",
                    row.age_days,
                    "yes" if row.overdue else "no",
                ]
            )
        return buffer.getvalue()
