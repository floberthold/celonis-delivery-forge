import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_celonis_user_token_api_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.integrations.celonis_import import CelonisPreflightHttpResult
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


DB_FILE = Path("tmp_celonis_user_token_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_actor_org_client_connection() -> tuple[str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="celonis-user-token-api@example.com",
            name="Celonis User Token API Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Celonis User Token Org", slug="celonis-user-token-org")
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
            name="Celonis User Token Client",
            tenant_url="https://user-token-client.celonis.cloud",
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


def test_celonis_user_token_crud_status_endpoints() -> None:
    _reset_db()
    person_id, organization_id, _ = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        initial = api_client.get("/celonis/user-token")
        assert initial.status_code == 200
        assert initial.json()["token_configured"] is False

        save = api_client.put("/celonis/user-token", json={"token_value": " user-tok-123 "})
        assert save.status_code == 200
        assert save.json()["token_configured"] is True
        assert save.json()["updated_at"]

        configured = api_client.get("/celonis/user-token")
        assert configured.status_code == 200
        assert configured.json()["token_configured"] is True

        clear = api_client.delete("/celonis/user-token")
        assert clear.status_code == 200
        assert clear.json()["token_configured"] is False

    with Session(engine) as session:
        row = session.exec(
            select(CelonisUserToken).where(
                CelonisUserToken.organization_id == UUID(organization_id),
                CelonisUserToken.person_id == UUID(person_id),
            )
        ).first()
        assert row is None


def test_celonis_preflight_prefers_user_token_override(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    class _SettingsStub:
        celonis_api_token = "global-fallback-token"
        celonis_timeout_seconds = 20

    observed_token_overrides: list[str | None] = []

    def _patched_preflight(
        self,
        *,
        tenant_base_url: str,
        probe_path: str = "/",
        service: str = "core",
        token_override: str | None = None,
    ):
        observed_token_overrides.append(token_override)
        return CelonisPreflightHttpResult(
            service=service,
            probe_path=probe_path,
            probe_url=f"{tenant_base_url}{probe_path}",
            has_token=True,
            request_attempted=True,
            reachable=True,
            authenticated=True,
            permission_status="authorized",
            status_code=200,
            error=None,
            response_preview="{}",
        )

    monkeypatch.setattr("foundry.api.routes.celonis.get_settings", lambda: _SettingsStub())
    monkeypatch.setattr("foundry.integrations.celonis_import.CelonisGateway.preflight", _patched_preflight)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        # No user token configured yet: request should rely on gateway default token behavior.
        first = api_client.get(f"/celonis/connections/{client_id}/preflight")
        assert first.status_code == 200

        save = api_client.put("/celonis/user-token", json={"token_value": "delegated-user-token"})
        assert save.status_code == 200

        second = api_client.get(f"/celonis/connections/{client_id}/preflight")
        assert second.status_code == 200

    assert observed_token_overrides[0] is None
    assert observed_token_overrides[1] == "delegated-user-token"
