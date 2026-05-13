from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_connect_args = {}
_settings = get_settings()
if _settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _settings.database_url,
    echo=False,
    connect_args=_connect_args,
)


def init_db() -> None:
    from app.db import models  # noqa: F401 — register models

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
