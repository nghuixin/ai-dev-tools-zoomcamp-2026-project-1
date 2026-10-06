from app.database import Base, create_engine_from_url, create_session_factory
from app.db_models import IssueRow, NoteRow, SiteRow, StudyRow  # noqa: F401
from app.store import Store

_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        engine = create_engine_from_url()
        Base.metadata.create_all(engine)
        _store = Store(create_session_factory(engine))
    return _store


def reset_store() -> None:
    global _store
    _store = None
