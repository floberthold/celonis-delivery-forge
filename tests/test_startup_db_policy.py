import importlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import OperationalError


def _reset_settings_cache() -> None:
    import foundry.settings as settings_module

    settings_module.get_settings.cache_clear()


def test_init_db_falls_back_to_local_database_in_dev(monkeypatch, tmp_path: Path) -> None:
    db_file = tmp_path / "fallback.db"
    monkeypatch.setenv("FORGE_ENV", "dev")
    monkeypatch.setenv("FORGE_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/foundry")
    monkeypatch.setenv("FORGE_LOCAL_DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("FORGE_DATABASE_FALLBACK_TO_LOCAL", "true")
    _reset_settings_cache()

    import foundry.db as db_module

    db_module = importlib.reload(db_module)

    attempted_urls: list[str] = []

    def fake_initialize_schema(_engine) -> None:
        attempted_urls.append(db_module._active_database_url)
        if len(attempted_urls) == 1:
            raise OperationalError("SELECT 1", {}, RuntimeError("offline"))

    monkeypatch.setattr(db_module, "_initialize_schema", fake_initialize_schema)

    db_module.init_db()

    assert attempted_urls == [
        "postgresql+psycopg://postgres:postgres@localhost:5432/foundry",
        f"sqlite:///{db_file.as_posix()}",
    ]
    assert db_module.get_database_backend() == "sqlite"
    assert db_module.get_database_startup_mode() == "local_fallback"


def test_init_db_stays_strict_when_fallback_disabled(monkeypatch) -> None:
    monkeypatch.setenv("FORGE_ENV", "dev")
    monkeypatch.setenv("FORGE_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/foundry")
    monkeypatch.setenv("FORGE_DATABASE_FALLBACK_TO_LOCAL", "false")
    _reset_settings_cache()

    import foundry.db as db_module

    db_module = importlib.reload(db_module)

    def fake_initialize_schema(_engine) -> None:
        raise OperationalError("SELECT 1", {}, RuntimeError("offline"))

    monkeypatch.setattr(db_module, "_initialize_schema", fake_initialize_schema)

    with pytest.raises(OperationalError):
        db_module.init_db()

    assert db_module.get_database_backend() == "postgresql"
    assert db_module.get_database_startup_mode() == "configured"


def test_health_reports_database_startup_mode(monkeypatch) -> None:
    import foundry.api.main as main_module

    monkeypatch.setattr(main_module, "settings", SimpleNamespace(app_name="Forge", env="dev"))
    monkeypatch.setattr(main_module, "get_database_backend", lambda: "sqlite")
    monkeypatch.setattr(main_module, "get_database_startup_mode", lambda: "local_fallback")

    payload = main_module.healthcheck()

    assert payload == {
        "status": "ok",
        "app": "Forge",
        "env": "dev",
        "database_backend": "sqlite",
        "database_startup_mode": "local_fallback",
    }


@pytest.fixture(autouse=True)
def _restore_env(monkeypatch) -> None:
    original_env = dict(os.environ)
    yield
    monkeypatch.setattr(os, "environ", original_env)
    _reset_settings_cache()