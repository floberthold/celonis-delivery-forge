import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_account_ui_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_account_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_people_with_org() -> tuple[str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="account-user@example.com",
            name="Account User",
            hashed_password=hash_password("account-password-1"),
        )
        second_person = Person(
            email="other-user@example.com",
            name="Other User",
            hashed_password=hash_password("other-password-1"),
        )
        session.add(person)
        session.add(second_person)
        session.commit()
        session.refresh(person)
        session.refresh(second_person)

        organization = Organization(name="Account UI Org", slug="account-ui-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.member,
        )
        second_membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=second_person.id,
            role=OrganizationRole.member,
        )
        session.add(membership)
        session.add(second_membership)
        session.commit()

        return str(person.id), str(organization.id), str(second_person.id)


def test_account_ui_renders_current_user_details() -> None:
    _reset_db()
    person_id, organization_id, _ = _seed_people_with_org()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/account-ui")
        assert response.status_code == 200
        assert "My Account" in response.text
        assert "account-user@example.com" in response.text
        assert "Account UI Org" in response.text
        assert "Utility" in response.text
        assert 'href="/account-ui" class="secondary-nav-link is-active"' in response.text


def test_account_ui_updates_profile_and_password() -> None:
    _reset_db()
    person_id, organization_id, _ = _seed_people_with_org()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        update_response = api_client.post(
            "/account-ui/update",
            data={
                "name": "Updated Account User",
                "email": "updated-account-user@example.com",
                "password": "updated-password-123",
                "confirm_password": "updated-password-123",
            },
            follow_redirects=False,
        )

        assert update_response.status_code == 303
        assert update_response.headers["location"].startswith("/account-ui?ok=")

    with TestClient(app) as login_client:
        login_response = login_client.post(
            "/login",
            data={
                "email": "updated-account-user@example.com",
                "password": "updated-password-123",
                "next_path": "/dashboard",
            },
            follow_redirects=False,
        )
        assert login_response.status_code == 303
        assert login_response.headers["location"] == "/dashboard"


def test_account_ui_rejects_duplicate_email() -> None:
    _reset_db()
    person_id, organization_id, _ = _seed_people_with_org()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/account-ui/update",
            data={
                "name": "Account User",
                "email": "other-user@example.com",
                "password": "",
                "confirm_password": "",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"].startswith("/account-ui?err=Email+is+already+in+use")

    with Session(engine) as session:
        person = session.exec(select(Person).where(Person.id == UUID(person_id))).first()
        assert person is not None
        assert person.email == "account-user@example.com"


if __name__ == "__main__":
    if DB_FILE.exists():
        DB_FILE.unlink()
    test_account_ui_renders_current_user_details()
    test_account_ui_updates_profile_and_password()
    test_account_ui_rejects_duplicate_email()
