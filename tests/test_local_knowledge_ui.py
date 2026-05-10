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


def test_local_knowledge_ui_shows_webui_not_running(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id = _seed_user()
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui as ui_module

    monkeypatch.setattr(ui_module, "LocalKnowledgeGateway", DummyGateway)

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
