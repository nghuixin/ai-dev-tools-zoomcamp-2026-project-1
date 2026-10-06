from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DEFAULT_DATABASE_URL = "sqlite:///./triage.db"


def database_url() -> str:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        return DEFAULT_DATABASE_URL
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


def create_engine_from_url(url: str | None = None) -> Engine:
    resolved = url or database_url()
    kwargs: dict = {"future": True}
    if make_url(resolved).get_backend_name() == "sqlite":
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(resolved, **kwargs)


def create_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)


def create_memory_session_factory() -> sessionmaker:
    from sqlalchemy.pool import StaticPool

    from app import db_models  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return create_session_factory(engine)
