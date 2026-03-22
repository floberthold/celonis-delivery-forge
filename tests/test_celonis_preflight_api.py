# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_preflight_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.integrations.celonis_import import CelonisGateway, CelonisPreflightHttpResult
from foundry.models import (
    CelonisConnection,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_celonis_preflight_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_actor_org_client_connection() -> tuple[str, str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email="celonis-preflight-api@example.com",
            name="Celonis Preflight API Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Celonis Test Org", slug="celonis-test-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.owner,
        )
        session.add(membership)

        client = Client(
            organization_id=organization.id,
            name="Celonis API Client",
            tenant_url="https://api-client.celonis.cloud",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        connection = CelonisConnection(
            organization_id=organization.id,
            client_id=client.id,
            tenant_base_url="https://team.eu-1.celonis.cloud",
            is_active=True,
        )
        session.add(connection)
        session.commit()

        return str(person.id), str(organization.id), str(client.id)


def _fake_preflight(service: str) -> CelonisPreflightHttpResult:
    if service == "core":
        return CelonisPreflightHttpResult(
            service="core",
            probe_path="/",
            probe_url="https://team.eu-1.celonis.cloud/",
            has_token=True,
            request_attempted=True,
            reachable=True,
            authenticated=True,
            permission_status="authorized",
            status_code=200,
            error=None,
            response_preview="{}",
        )
    return CelonisPreflightHttpResult(
        service="studio",
        probe_path="/studio/api/spaces",
        probe_url="https://team.eu-1.celonis.cloud/studio/api/spaces",
        has_token=True,
        request_attempted=True,
        reachable=True,
        authenticated=False,
        permission_status="forbidden",
        status_code=403,
        error=None,
        response_preview="{}",
    )


def test_celonis_preflight_batch_and_history(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    def _patched_preflight(self, *, tenant_base_url: str, probe_path: str = "/", service: str = "core"):
        return _fake_preflight(service)

    monkeypatch.setattr("foundry.integrations.celonis_import.CelonisGateway.preflight", _patched_preflight)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        batch_response = api_client.post(
            f"/celonis/connections/{client_id}/preflight/batch",
            params={"services": "core,studio"},
        )
        assert batch_response.status_code == 200, batch_response.text
        payload = batch_response.json()
        assert payload["client_id"] == client_id
        assert payload["total"] == 2
        assert payload["authorized_count"] == 1
        assert payload["issue_count"] == 1
        assert payload["run_id"]
        assert len(payload["results"]) == 2

        by_service = {row["service"]: row for row in payload["results"]}
        assert by_service["core"]["permission_status"] == "authorized"
        assert by_service["studio"]["permission_status"] == "forbidden"

        history_response = api_client.get(
            f"/celonis/connections/{client_id}/preflight/history",
            params={"limit": 10},
        )
        assert history_response.status_code == 200, history_response.text
        history_rows = history_response.json()
        assert len(history_rows) == 2
        history_services = {row["service"] for row in history_rows}
        assert history_services == {"core", "studio"}
        assert all(row["run_id"] == payload["run_id"] for row in history_rows)


def test_celonis_preflight_batch_invalid_service_returns_400() -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post(
            f"/celonis/connections/{client_id}/preflight/batch",
            params={"services": "core,not-a-real-service"},
        )
        assert response.status_code == 400
        assert "Invalid service values" in response.text


def test_celonis_preflight_history_limit_bounds() -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        low = api_client.get(
            f"/celonis/connections/{client_id}/preflight/history",
            params={"limit": 0},
        )
        assert low.status_code == 400

        high = api_client.get(
            f"/celonis/connections/{client_id}/preflight/history",
            params={"limit": 201},
        )
        assert high.status_code == 400


def test_gateway_permission_status_maps_redirect_codes() -> None:
    assert CelonisGateway._permission_status(301) == "redirect-to-login"
    assert CelonisGateway._permission_status(302) == "redirect-to-login"


def test_gateway_classifies_login_html_as_redirect_to_login() -> None:
    class _FakeResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {"content-type": "text/html"}
            self.url = "https://team.eu-1.celonis.cloud/login"
            self.text = "<html><body>Sign in</body></html>"

    status = CelonisGateway._classify_preflight_response(_FakeResponse())
    assert status == "redirect-to-login"
