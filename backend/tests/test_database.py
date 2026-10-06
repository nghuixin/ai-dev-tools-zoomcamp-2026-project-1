from app.database import database_url
from app.models import CreateIssueRequest, Category, Severity
from app.store import Store


def test_database_url_defaults_to_sqlite(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url() == "sqlite:///./triage.db"


def test_database_url_normalizes_postgres(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://triage:triage@localhost:5432/triage")
    assert database_url() == "postgresql+psycopg://triage:triage@localhost:5432/triage"
    monkeypatch.setenv("DATABASE_URL", "postgres://triage:triage@localhost:5432/triage")
    assert database_url() == "postgresql+psycopg://triage:triage@localhost:5432/triage"


def test_store_survives_new_session_on_same_engine() -> None:
    first = Store()
    first.seed()
    created = first.create_issue(
        CreateIssueRequest(
            study_id=1,
            site_id=1,
            description="Persisted freezer log after restart.",
            category=Category.EQUIPMENT_LAB,
            severity=Severity.MEDIUM,
            summary="Persisted freezer log",
        )
    )
    second = Store(first._session_factory)
    loaded = second.get_issue(created.id)
    assert loaded.summary == "Persisted freezer log"
    assert loaded.description.startswith("Persisted freezer")
    assert len(second.list_studies()) == 3
