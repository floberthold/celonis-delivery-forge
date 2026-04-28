import os
import time
from pathlib import Path

import pytest

import foundry.db as db_module


def _dispose_engine_safely() -> None:
    try:
        db_module.engine.dispose()
    except Exception:
        pass


def _unlink_with_retry(path: Path) -> None:
    for _ in range(5):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError:
            _dispose_engine_safely()
            time.sleep(0.05)


def _cleanup_sqlite_files(db_path: Path) -> None:
    sidecar_paths = (
        db_path,
        db_path.with_name(f"{db_path.name}-journal"),
        db_path.with_name(f"{db_path.name}-wal"),
        db_path.with_name(f"{db_path.name}-shm"),
    )
    for path in sidecar_paths:
        _unlink_with_retry(path)


def _sweep_tmp_sqlite_files() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    roots = (Path.cwd(), repo_root)
    patterns = ("tmp*.db", "tmp*.db-journal", "tmp*.db-wal", "tmp*.db-shm")
    for root in roots:
        for pattern in patterns:
            for path in root.glob(pattern):
                _unlink_with_retry(path)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _dispose_engine_safely()
    _sweep_tmp_sqlite_files()


def pytest_unconfigure(config: pytest.Config) -> None:
    _dispose_engine_safely()
    _sweep_tmp_sqlite_files()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_tmp_sqlite_session_files():
    _sweep_tmp_sqlite_files()
    yield
    _dispose_engine_safely()
    _sweep_tmp_sqlite_files()


@pytest.fixture(autouse=True)
def _rebind_test_database(request: pytest.FixtureRequest):
    db_file = getattr(request.module, "DB_FILE", None)
    if db_file is None:
        yield
        return

    db_path = Path(db_file)
    database_url = f"sqlite:///./{db_path.name}"
    previous_url = db_module._active_database_url
    previous_engine = db_module.engine

    _cleanup_sqlite_files(db_path)
    os.environ["FORGE_DATABASE_URL"] = database_url
    db_module._set_engine(database_url)
    setattr(request.module, "engine", db_module.engine)

    try:
        yield
    finally:
        _dispose_engine_safely()
        db_module.engine = previous_engine
        db_module._active_database_url = previous_url
        os.environ["FORGE_DATABASE_URL"] = previous_url
        try:
            previous_engine.dispose()
        except Exception:
            pass
        setattr(request.module, "engine", previous_engine)
        _cleanup_sqlite_files(db_path)