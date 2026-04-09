import os
from pathlib import Path

import pytest

import foundry.db as db_module


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

    os.environ["FORGE_DATABASE_URL"] = database_url
    db_module._set_engine(database_url)
    setattr(request.module, "engine", db_module.engine)

    try:
        yield
    finally:
        db_module.engine.dispose()
        db_module.engine = previous_engine
        db_module._active_database_url = previous_url
        setattr(request.module, "engine", previous_engine)