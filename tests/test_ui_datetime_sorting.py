# ruff: noqa: E402

import os
from collections.abc import Generator
from datetime import datetime, timezone, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_ui_datetime_sorting_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_ui_datetime_sorting_test.db")


def _cleanup_db_file() -> None:
    for path in (
        DB_FILE,
        DB_FILE.with_name(f"{DB_FILE.name}-journal"),
        DB_FILE.with_name(f"{DB_FILE.name}-wal"),
        DB_FILE.with_name(f"{DB_FILE.name}-shm"),
    ):
        try:
            path.unlink()
        except (FileNotFoundError, PermissionError):
            continue


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


@pytest.fixture(autouse=True)
def _isolate_ui_datetime_test_engine() -> Generator[None, None, None]:
    previous_url = db_module._active_database_url
    _cleanup_db_file()
    db_module._set_engine("sqlite:///./tmp_ui_datetime_sorting_test.db")
    yield
    db_module.engine.dispose()
    db_module._set_engine(previous_url)
    _cleanup_db_file()


def _seed_people_with_mixed_datetime_kinds() -> tuple[str, str]:
    with Session(db_module.engine) as session:
        org = Organization(name="UI Date Sort Org", slug="ui-date-sort-org")
        session.add(org)
        session.commit()
        session.refresh(org)

        primary_person = Person(
            email="datetime-primary@example.com",
            name="Datetime Primary",
            hashed_password=hash_password("secret"),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        secondary_person = Person(
            email="datetime-secondary@example.com",
            name="Datetime Secondary",
            hashed_password=hash_password("secret"),
            created_at=datetime.now(timezone.utc),
        )
        session.add(primary_person)
        session.add(secondary_person)
        session.commit()
        session.refresh(primary_person)
        session.refresh(secondary_person)

        session.add(
            OrganizationMembership(
                organization_id=org.id,
                person_id=primary_person.id,
                role=OrganizationRole.owner,
            )
        )
        session.add(
            OrganizationMembership(
                organization_id=org.id,
                person_id=secondary_person.id,
                role=OrganizationRole.member,
            )
        )
        session.commit()

        return str(primary_person.id), str(org.id)


def test_ui_pages_handle_mixed_datetime_kinds_without_500() -> None:
    _reset_db()
    person_id, org_id = _seed_people_with_mixed_datetime_kinds()
    auth_token = create_access_token(person_id, org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        for path in ["/people-ui", "/reviews-ui", "/todos-ui", "/templates-ui", "/timeline-ui"]:
            response = api_client.get(path)
            assert response.status_code == 200, f"{path} failed: {response.text}"


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_ui_pages_handle_mixed_datetime_kinds_without_500()

