# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_extract_import_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

engine = db_module.engine

from foundry.api.main import app
from foundry.models import ActivityLog, CelonisConnection, Client, Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_celonis_extract_import_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_actor_org_client_connection() -> tuple[str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="celonis-extract-import-api@example.com",
            name="Celonis Extract Import API Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Celonis Extract Import Org", slug="celonis-extract-import-org")
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

        client = Client(
            organization_id=organization.id,
            name="Celonis Extract Import Client",
            tenant_url="https://extract-import-client.celonis.cloud",
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


def test_celonis_extract_logs_request_and_accepts_org_boundary(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    observed: dict[str, object] = {}

    def _patched_extract(self, *, tenant_base_url: str, source_path: str, token_override: str | None = None):
        observed["tenant_base_url"] = tenant_base_url
        observed["source_path"] = source_path
        observed["token_override"] = token_override
        return type(
            "_Result",
            (),
            {
                "action": "extract",
                "url": f"{tenant_base_url}{source_path}",
                "status_code": 200,
                "ok": True,
                "response_preview": "ok",
            },
        )()

    monkeypatch.setattr("foundry.integrations.celonis_import.CelonisGateway.extract", _patched_extract)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/celonis/extract",
            json={
                "client_id": client_id,
                "organization_id": organization_id,
                "source_path": "/process-mining/api/teams",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["client_id"] == client_id
        assert payload["request_id"]
        assert payload["action"] == "extract"
        assert payload["status_code"] == 200
        assert payload["ok"] is True
        assert observed == {
            "tenant_base_url": "https://team.eu-1.celonis.cloud",
            "source_path": "/process-mining/api/teams",
            "token_override": None,
        }

    with Session(engine) as session:
        logs = session.exec(select(ActivityLog).where(ActivityLog.action == "celonis.extract")).all()
        assert len(logs) == 1
        assert logs[0].metadata_json["request_id"] == payload["request_id"]
        assert logs[0].metadata_json["client_id"] == client_id
        assert logs[0].metadata_json["source_path"] == "/process-mining/api/teams"


def test_celonis_import_rejects_cross_organization_boundary() -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)
    other_organization_id = str(uuid4())

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/celonis/import",
            json={
                "client_id": client_id,
                "organization_id": other_organization_id,
                "target_path": "/process-mining/api/teams",
                "payload": {},
            },
        )
        assert response.status_code == 400
        assert "organization_id does not match" in response.text


def test_celonis_import_logs_request(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    observed: dict[str, object] = {}

    def _patched_import(self, *, tenant_base_url: str, target_path: str, payload: dict, token_override: str | None = None):
        observed["tenant_base_url"] = tenant_base_url
        observed["target_path"] = target_path
        observed["payload"] = dict(payload)
        observed["token_override"] = token_override
        return type(
            "_Result",
            (),
            {
                "action": "import",
                "url": f"{tenant_base_url}{target_path}",
                "status_code": 201,
                "ok": True,
                "response_preview": "created",
            },
        )()

    monkeypatch.setattr("foundry.integrations.celonis_import.CelonisGateway.import_data", _patched_import)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/celonis/import",
            json={
                "client_id": client_id,
                "organization_id": organization_id,
                "target_path": "/process-mining/api/teams",
                "payload": {"hello": "world"},
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["client_id"] == client_id
        assert payload["request_id"]
        assert payload["action"] == "import"
        assert payload["status_code"] == 201
        assert observed == {
            "tenant_base_url": "https://team.eu-1.celonis.cloud",
            "target_path": "/process-mining/api/teams",
            "payload": {"hello": "world"},
            "token_override": None,
        }

    with Session(engine) as session:
        logs = session.exec(select(ActivityLog).where(ActivityLog.action == "celonis.import")).all()
        assert len(logs) == 1
        assert logs[0].metadata_json["request_id"] == payload["request_id"]
        assert logs[0].metadata_json["target_path"] == "/process-mining/api/teams"


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
