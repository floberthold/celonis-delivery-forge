# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_tenant_setup_wizard_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    CelonisConnection,
    CelonisUserToken,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_tenant_setup_wizard_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_actor() -> tuple[str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email="wizard-ui@example.com",
            name="Wizard UI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        org = Organization(name="Wizard Org", slug="wizard-org")
        session.add(org)
        session.commit()
        session.refresh(org)

        membership = OrganizationMembership(
            organization_id=org.id,
            person_id=person.id,
            role=OrganizationRole.owner,
        )
        session.add(membership)
        session.commit()

        return str(person.id), str(org.id)


def test_setup_wizard_page_renders() -> None:
    _reset_db()
    person_id, organization_id = _seed_actor()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/onboarding/celonis-setup")

    assert response.status_code == 200
    assert "Celonis Tenant Setup Wizard" in response.text
    assert "Step 1 - Create Client" in response.text
    assert "Step 4 - Validate Connectivity" in response.text


def test_setup_wizard_full_happy_path(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_actor()
    auth_token = create_access_token(person_id, organization_id)

    class _FakePreflightResult:
        def __init__(self, service: str):
            self.service = service
            self.probe_path = "/"
            self.probe_url = "https://tenant.celonis.cloud/"
            self.has_token = True
            self.request_attempted = True
            self.reachable = True
            self.authenticated = True
            self.permission_status = "authorized"
            self.status_code = 200
            self.error = None
            self.response_preview = ""

    def _fake_preflight(self, *, tenant_base_url: str, probe_path: str = "/", service: str = "core", token_override=None):
        return _FakePreflightResult(service=service)

    monkeypatch.setattr("foundry.api.routes.ui.CelonisGateway.preflight", _fake_preflight)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_resp = api_client.post(
            "/onboarding/celonis-setup/create-client",
            data={
                "name": "Wizard Client",
                "tenant_url": "https://tenant.celonis.cloud",
                "sensitivity_level": "medium",
            },
            follow_redirects=False,
        )
        assert create_resp.status_code == 303
        location = create_resp.headers["location"]
        assert "client_id=" in location
        client_id = location.split("client_id=", 1)[1].split("&", 1)[0]

        save_conn_resp = api_client.post(
            "/onboarding/celonis-setup/save-connection",
            data={
                "client_id": client_id,
                "tenant_base_url": "https://tenant.celonis.cloud",
            },
            follow_redirects=False,
        )
        assert save_conn_resp.status_code == 303

        save_token_resp = api_client.post(
            "/onboarding/celonis-setup/save-token",
            data={
                "client_id": client_id,
                "token_value": "secret-token",
            },
            follow_redirects=False,
        )
        assert save_token_resp.status_code == 303

        preflight_resp = api_client.post(
            "/onboarding/celonis-setup/run-preflight",
            data={"client_id": client_id},
            follow_redirects=False,
        )
        assert preflight_resp.status_code == 303
        assert "ok=" in preflight_resp.headers["location"]

        final_page = api_client.get(f"/onboarding/celonis-setup?client_id={client_id}")
        assert final_page.status_code == 200
        assert "Setup complete. You can start extractions now." in final_page.text
        assert "Open Snapshot History" in final_page.text

    with Session(db_module.engine) as session:
        client = session.exec(select(Client).where(Client.name == "Wizard Client")).first()
        assert client is not None
        connection = session.exec(select(CelonisConnection).where(CelonisConnection.client_id == client.id)).first()
        assert connection is not None and connection.is_active

    # Validate token presence using org/person directly to avoid model coupling.
    with Session(db_module.engine) as session:
        person = session.exec(select(Person).where(Person.email == "wizard-ui@example.com")).first()
        assert person is not None
        saved_tokens = session.exec(select(CelonisUserToken).where(CelonisUserToken.person_id == person.id)).all()
        assert len(saved_tokens) == 1


def test_setup_wizard_marks_partial_preflight_as_usable(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_actor()
    auth_token = create_access_token(person_id, organization_id)

    class _FakePreflightResult:
        def __init__(self, service: str):
            self.service = service
            self.probe_path = "/"
            self.probe_url = "https://tenant.celonis.cloud/"
            self.has_token = True
            self.request_attempted = True
            self.reachable = True
            self.authenticated = service == "data-integration"
            self.permission_status = "authorized" if service == "data-integration" else "forbidden"
            self.status_code = 200 if service == "data-integration" else 403
            self.error = None
            self.response_preview = ""

    def _fake_preflight(self, *, tenant_base_url: str, probe_path: str = "/", service: str = "core", token_override=None):
        return _FakePreflightResult(service=service)

    monkeypatch.setattr("foundry.api.routes.ui.CelonisGateway.preflight", _fake_preflight)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_resp = api_client.post(
            "/onboarding/celonis-setup/create-client",
            data={
                "name": "Wizard Partial Client",
                "tenant_url": "https://tenant.celonis.cloud",
                "sensitivity_level": "medium",
            },
            follow_redirects=False,
        )
        assert create_resp.status_code == 303
        client_id = create_resp.headers["location"].split("client_id=", 1)[1].split("&", 1)[0]

        save_conn_resp = api_client.post(
            "/onboarding/celonis-setup/save-connection",
            data={
                "client_id": client_id,
                "tenant_base_url": "https://tenant.celonis.cloud",
            },
            follow_redirects=False,
        )
        assert save_conn_resp.status_code == 303

        save_token_resp = api_client.post(
            "/onboarding/celonis-setup/save-token",
            data={
                "client_id": client_id,
                "token_value": "secret-token",
            },
            follow_redirects=False,
        )
        assert save_token_resp.status_code == 303

        preflight_resp = api_client.post(
            "/onboarding/celonis-setup/run-preflight",
            data={"client_id": client_id},
            follow_redirects=False,
        )
        assert preflight_resp.status_code == 303
        assert "ok=" in preflight_resp.headers["location"]
        assert "limited+scope" in preflight_resp.headers["location"]

        final_page = api_client.get(f"/onboarding/celonis-setup?client_id={client_id}")
        assert final_page.status_code == 200
        assert "Setup usable with limited scope." in final_page.text
        assert "Authorized services: 1/5" in final_page.text


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_setup_wizard_page_renders()
