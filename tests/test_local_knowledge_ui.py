# ruff: noqa: E402

import os
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_local_knowledge_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_local_knowledge_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_user() -> tuple[str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email="local-knowledge-ui@example.com",
            name="Local Knowledge UI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Local Knowledge Org", slug="local-knowledge-org")
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


class DummyGateway:
    def __init__(self, settings) -> None:
        self.settings = settings

    def health(self) -> dict:
        return {"status": "ok", "document_count": 9995, "ollama_available": True}

    def corpus(self) -> dict:
        return {"total_documents": 9995, "by_corpus": {"wiki": 1, "raw": 4994, "source": 5000}}


class DummyControlService:
    def __init__(self, settings) -> None:
        self.settings = settings

    def get_run_state(self) -> dict:
        return {
            "run_id": "run-123",
            "status": "running",
            "stage": "ingest",
            "started_at": "2026-05-10T10:00:00+00:00",
            "finished_at": None,
            "latest_line": "Analyzing source note",
            "line_count": 7,
            "auto_approve": False,
        }

    def get_log_tail(self, limit: int = 120) -> list[str]:
        return ["line-1", "line-2"]

    def list_source_files(self, limit: int = 250) -> list[dict]:
        return [
            {
                "path": "raw/OneNote/fuchs.md",
                "size_bytes": 120,
                "modified_at": "2026-05-10T09:00:00+00:00",
            }
        ]

    def list_recent_file_changes(self, limit: int = 250) -> dict:
        return {
            "baseline": "2026-05-10T08:00:00+00:00",
            "items": [
                {
                    "path": "wiki/Fuchs.md",
                    "family": "wiki",
                    "modified_at": "2026-05-10T09:30:00+00:00",
                }
            ],
        }

    def start_run(self, *, auto_approve: bool) -> dict:
        return {
            "run_id": "run-started",
            "status": "running",
            "line_count": 0,
            "auto_approve": auto_approve,
        }


def test_local_knowledge_ui_shows_webui_not_running(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui as ui_module

    monkeypatch.setattr(ui_module, "LocalKnowledgeGateway", DummyGateway)
    monkeypatch.setattr(ui_module, "LocalKnowledgeControlService", DummyControlService)

    def _raise_connect_error(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(ui_module.httpx, "get", _raise_connect_error)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/local-knowledge-ui")

    assert response.status_code == 200
    assert "Local Knowledge Hub" in response.text
    assert "Gateway Status" in response.text
    assert "Open WebUI" in response.text
    assert "Not Running" in response.text
    assert ".\\scripts\\start_open_webui_local_knowledge.ps1" in response.text
    assert "9995" in response.text
    assert "Run Control" in response.text
    assert "Source Files" in response.text
    assert "Recent File Changes" in response.text
    assert "run-123" in response.text


def test_local_knowledge_ui_run_trigger_redirects_with_ok(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui as ui_module

    monkeypatch.setattr(ui_module, "LocalKnowledgeControlService", DummyControlService)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/local-knowledge-ui/run",
            data={"auto_approve": "on"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "/local-knowledge-ui?ok=" in response.headers["location"]


def test_local_knowledge_ui_status_returns_json_payload(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui_knowledge_status as status_module

    monkeypatch.setattr(status_module, "LocalKnowledgeControlService", DummyControlService)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/local-knowledge-ui/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_state"]["run_id"] == "run-123"
    assert payload["run_log_tail"] == ["line-1", "line-2"]
    assert payload["recent_changes"]["items"][0]["family"] == "wiki"


def test_local_knowledge_ui_status_returns_403_when_domain_disabled(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui_knowledge_status as status_module

    monkeypatch.setattr(status_module, "_knowledge_hub_enabled", lambda current_actor: False)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/local-knowledge-ui/status")

    assert response.status_code == 403
    assert response.json()["detail"] == "knowledge-hub domain disabled"
