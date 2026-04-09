# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_people_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password

engine = db_module.engine


DB_FILE = Path("tmp_people_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_admin_with_org() -> tuple[str, str]:
    with Session(engine) as session:
        person = Person(
            email="people-admin@example.com",
            name="People Admin",
            hashed_password=hash_password("admin"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="People UI Org", slug="people-ui-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.owner,
        )
        session.add(membership)
        session.commit()

        return str(person.id), str(organization.id)


def test_people_ui_renders_rows_and_create_flow() -> None:
    _reset_db()
    person_id, organization_id = _seed_admin_with_org()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        list_response = api_client.get("/people-ui")
        assert list_response.status_code == 200
        assert "People Admin" in list_response.text

        create_response = api_client.post(
            "/people-ui/create",
            data={
                "name": "New Person",
                "email": "new.person@example.com",
                "password": "admin",
                "role_global": "admin",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        assert create_response.headers["location"].startswith("/people-ui?")

        post_create_page = api_client.get("/people-ui")
        assert post_create_page.status_code == 200
        assert "new.person@example.com" in post_create_page.text


def test_people_ui_tolerates_string_backed_roles() -> None:
    _reset_db()
    person_id, organization_id = _seed_admin_with_org()
    auth_token = create_access_token(person_id, organization_id)

    # Simulate legacy/manual data where role values are plain strings in storage.
    with Session(engine) as session:
        person = session.exec(select(Person).where(Person.id == UUID(person_id))).first()
        assert person is not None
        person.role_global = "admin"  # type: ignore[assignment]
        session.add(person)
        session.commit()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/people-ui")
        assert response.status_code == 200
        assert "people-admin@example.com" in response.text


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_people_ui_renders_rows_and_create_flow()
    test_people_ui_tolerates_string_backed_roles()
