import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_login_ui_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import OrganizationMembership, Person
from foundry.security import hash_password


DB_FILE = Path("tmp_login_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_user(email: str, name: str, hashed_password: str) -> str:
    with Session(engine) as session:
        person = Person(email=email, name=name, hashed_password=hashed_password)
        session.add(person)
        session.commit()
        session.refresh(person)
        return str(person.id)


def test_login_page_includes_account_creation_guide() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/login")
        assert response.status_code == 200

        html = response.text
        assert "Need an account?" in html
        assert "Create account" in html
        assert "Forgot your password?" in html
        assert "Toggle navigation" in html
        assert "Not signed in" in html


def test_login_invalid_credentials_redirects_with_error() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.post(
            "/login",
            data={
                "email": "missing-user@example.com",
                "password": "bad-password",
                "next_path": "/dashboard",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/login?next_path=%2Fdashboard&err=Invalid+credentials"


def test_registration_flow_creates_person_and_org_membership(monkeypatch) -> None:
    _reset_db()
    sent_messages: list[dict[str, str]] = []

    def _fake_send_email(*, to_email: str, subject: str, body_text: str) -> None:
        sent_messages.append({"to_email": to_email, "subject": subject, "body_text": body_text})

    monkeypatch.setattr("foundry.api.routes.ui.send_email", _fake_send_email)

    with TestClient(app) as api_client:
        register_response = api_client.post(
            "/register",
            data={
                "name": "Registration Tester",
                "email": "register@example.com",
                "password": "register-password-01",
                "confirm_password": "register-password-01",
            },
            follow_redirects=False,
        )

        assert register_response.status_code == 303
        assert register_response.headers["location"].startswith("/register?ok=")
        assert len(sent_messages) == 1
        assert "register/verify?token=" in sent_messages[0]["body_text"]

        token = sent_messages[0]["body_text"].split("register/verify?token=", 1)[1].splitlines()[0].strip()
        verify_response = api_client.get(f"/register/verify?token={token}", follow_redirects=False)

        assert verify_response.status_code == 303
        assert verify_response.headers["location"].startswith("/login?ok=")

    with Session(engine) as session:
        person = session.exec(select(Person).where(Person.email == "register@example.com")).first()
        assert person is not None

        membership = session.exec(
            select(OrganizationMembership).where(OrganizationMembership.person_id == person.id)
        ).first()
        assert membership is not None


def test_forgot_password_flow_updates_password(monkeypatch) -> None:
    _reset_db()
    _seed_user(
        email="forgot@example.com",
        name="Forgot Tester",
        hashed_password=hash_password("initial-password-123"),
    )
    sent_messages: list[dict[str, str]] = []

    def _fake_send_email(*, to_email: str, subject: str, body_text: str) -> None:
        sent_messages.append({"to_email": to_email, "subject": subject, "body_text": body_text})

    monkeypatch.setattr("foundry.api.routes.ui.send_email", _fake_send_email)

    with TestClient(app) as api_client:
        forgot_response = api_client.post(
            "/forgot-password",
            data={"email": "forgot@example.com"},
            follow_redirects=False,
        )

        assert forgot_response.status_code == 303
        assert forgot_response.headers["location"].startswith("/forgot-password?ok=")
        assert len(sent_messages) == 1
        assert "reset-password?token=" in sent_messages[0]["body_text"]

        token = sent_messages[0]["body_text"].split("reset-password?token=", 1)[1].splitlines()[0].strip()
        reset_page = api_client.get(f"/reset-password?token={token}")
        assert reset_page.status_code == 200
        assert "Update Password" in reset_page.text

        reset_submit = api_client.post(
            "/reset-password",
            data={
                "token": token,
                "password": "new-password-123",
                "confirm_password": "new-password-123",
            },
            follow_redirects=False,
        )
        assert reset_submit.status_code == 303
        assert reset_submit.headers["location"].startswith("/login?ok=")

        login_response = api_client.post(
            "/login",
            data={
                "email": "forgot@example.com",
                "password": "new-password-123",
                "next_path": "/dashboard",
            },
            follow_redirects=False,
        )
        assert login_response.status_code == 303
        assert login_response.headers["location"] == "/login?next_path=%2Fdashboard&err=No+organization+membership+found.+Ask+your+admin+for+access."


def test_reset_password_rejects_invalid_token() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/reset-password?token=bad-token")
        assert response.status_code == 200
        assert "Invalid or expired token" in response.text


def test_dashboard_redirects_to_login_when_unauthenticated() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/dashboard", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/login?next_path=%2Fdashboard"


def test_login_page_preserves_next_path() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/login?next_path=%2Fdashboard")

        assert response.status_code == 200
        assert 'name="next_path" value="/dashboard"' in response.text


def test_api_route_still_returns_json_unauthorized() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/people/", headers={"accept": "application/json"})

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}


if __name__ == "__main__":
    if DB_FILE.exists():
        DB_FILE.unlink()
    test_login_page_includes_account_creation_guide()
    test_login_invalid_credentials_redirects_with_error()
