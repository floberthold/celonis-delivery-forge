# ruff: noqa: E402

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_ui_templates_routes_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_ui_templates_routes_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_user() -> tuple[str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email="ui-templates@example.com",
            name="UI Templates Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="UI Templates Org", slug="ui-templates-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        session.add(
            OrganizationMembership(
                organization_id=organization.id,
                person_id=person.id,
                role=OrganizationRole.owner,
            )
        )
        session.commit()

        return str(person.id), str(organization.id)


def test_templates_ui_route_renders() -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/templates-ui")

    assert response.status_code == 200
    assert "Templates" in response.text


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
