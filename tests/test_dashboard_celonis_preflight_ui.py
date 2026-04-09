# ruff: noqa: E402

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_dashboard_celonis_preflight_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.api.routes.ui import _sort_datetime_key
from foundry.models import (
    ActivityLog,
    CelonisConnection,
    Client,
    EntityType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_dashboard_celonis_preflight_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_dashboard_preflight_data() -> tuple[str, str, str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email="dashboard-preflight-ui@example.com",
            name="Dashboard Preflight UI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Dashboard Org", slug="dashboard-org")
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
            name="Dashboard Celonis Client",
            tenant_url="https://dashboard-client.celonis.cloud",
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
        session.refresh(connection)

        session.add(
            ActivityLog(
                organization_id=organization.id,
                entity_type=EntityType.celonis_connection,
                entity_id=connection.id,
                action="celonis_connection.preflight",
                actor_id=person.id,
                metadata_json={
                    "client_id": str(client.id),
                    "service": "core",
                    "probe_path": "/",
                    "probe_url": "https://team.eu-1.celonis.cloud/",
                    "permission_status": "authorized",
                    "status_code": 200,
                    "run_id": "run-abc",
                },
            )
        )
        session.add(
            ActivityLog(
                organization_id=organization.id,
                entity_type=EntityType.celonis_connection,
                entity_id=connection.id,
                action="celonis_connection.preflight",
                actor_id=person.id,
                metadata_json={
                    "client_id": str(client.id),
                    "service": "studio",
                    "probe_path": "/studio/api/spaces",
                    "probe_url": "https://team.eu-1.celonis.cloud/studio/api/spaces",
                    "permission_status": "missing-token",
                    "status_code": None,
                    "run_id": "run-abc",
                },
            )
        )
        session.commit()

        return str(person.id), str(organization.id), str(client.id), str(connection.id)


def test_dashboard_shows_celonis_preflight_history_badges() -> None:
    _reset_db()
    person_id, organization_id, _, _ = _seed_dashboard_preflight_data()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.get("/dashboard")
        assert response.status_code == 200
        assert "Celonis Preflight History" in response.text
        assert "celonis-status-authorized" in response.text
        assert "celonis-status-missing-token" in response.text
        assert "run run-abc" in response.text
        assert "Primary navigation" in response.text
        assert "Operations" in response.text
        assert "Admin" in response.text
        assert "Utility" in response.text
        assert 'href="/dashboard" class="primary-nav-link is-active"' in response.text


def test_sort_datetime_key_handles_mixed_timezone_values() -> None:
    naive = datetime(2026, 3, 22, 10, 0, 0)
    aware = datetime(2026, 3, 22, 10, 0, 1, tzinfo=timezone.utc)

    values = [aware, naive]
    sorted_values = sorted(values, key=_sort_datetime_key, reverse=True)

    assert sorted_values[0] == aware
