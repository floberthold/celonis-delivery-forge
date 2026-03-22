import logging

from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine

from foundry.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
_active_database_url = settings.database_url
_startup_database_mode = "configured"


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {"connect_timeout": settings.database_connect_timeout_seconds}


def _build_engine(database_url: str):
    return create_engine(database_url, echo=False, connect_args=_connect_args(database_url))


engine = _build_engine(_active_database_url)


def _set_engine(database_url: str):
    global engine, _active_database_url
    engine = _build_engine(database_url)
    _active_database_url = database_url
    return engine


def _initialize_schema(target_engine) -> None:
    SQLModel.metadata.create_all(target_engine)
    from foundry.services.template_seed import seed_default_templates

    with Session(target_engine) as session:
        seed_default_templates(session)


def _fallback_database_url() -> str | None:
    if not settings.allows_local_database_fallback():
        return None

    fallback_url = settings.local_database_url
    if fallback_url == _active_database_url:
        return None
    return fallback_url


def get_database_backend() -> str:
    if _active_database_url.startswith("sqlite"):
        return "sqlite"
    if _active_database_url.startswith("postgresql"):
        return "postgresql"
    return "other"


def get_database_startup_mode() -> str:
    return _startup_database_mode


def init_db() -> None:
    global _startup_database_mode

    try:
        _initialize_schema(engine)
        _startup_database_mode = "configured"
    except OperationalError:
        fallback_url = _fallback_database_url()
        if fallback_url is None:
            raise

        logger.warning(
            "Configured database is unavailable during startup; falling back to local database",
            extra={
                "configured_backend": settings.database_url.split(":", 1)[0],
                "fallback_backend": fallback_url.split(":", 1)[0],
            },
        )
        _set_engine(fallback_url)
        _initialize_schema(engine)
        _startup_database_mode = "local_fallback"


def get_session():
    with Session(engine) as session:
        yield session
