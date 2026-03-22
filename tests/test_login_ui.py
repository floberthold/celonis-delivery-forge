import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_login_ui_test.db")

from foundry.api.main import app
from foundry.db import engine


DB_FILE = Path("tmp_login_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_login_page_includes_account_creation_guide() -> None:
    _reset_db()

    with TestClient(app) as api_client:
        response = api_client.get("/login")
        assert response.status_code == 200

        html = response.text
        assert "How to get an account" in html
        assert "Contact your delivery lead or workspace admin." in html
        assert "Self-registration is not available on this page." in html
        assert "Admin note: create users in People management after signing in." in html


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
