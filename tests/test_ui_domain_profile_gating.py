# ruff: noqa: E402

import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

DB_FILE = Path("tmp_ui_domain_profile_gating_test.db")
ROLLOUT_FILE = Path("tmp_ui_domain_profile_gating_config.json")

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_ui_domain_profile_gating_test.db"

import foundry.db as db_module


db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password
from foundry.settings import get_settings


@pytest.fixture(autouse=True)
def _isolate_rollout_env(monkeypatch):
    monkeypatch.setenv("FORGE_UI_ROLLOUT_CONFIG_PATH", str(ROLLOUT_FILE))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _cleanup_files() -> None:
    for path in (
        DB_FILE,
        DB_FILE.with_name(f"{DB_FILE.name}-journal"),
        DB_FILE.with_name(f"{DB_FILE.name}-wal"),
        DB_FILE.with_name(f"{DB_FILE.name}-shm"),
        ROLLOUT_FILE,
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except PermissionError:
            continue


def _write_rollout_config() -> None:
    payload = {
        "default_profile": "pilot-core",
        "profiles": {
            "pilot-core": {"enabled_domains": ["core-platform"]},
            "pilot-core-plus-knowledge": {
                "enabled_domains": ["core-platform", "knowledge-hub"]
            },
            "full": {"enabled_domains": ["*"]},
        },
        "org_profile_overrides": {
            "knowledge-org": "pilot-core-plus-knowledge"
        },
    }
    ROLLOUT_FILE.write_text(json.dumps(payload), encoding="utf-8")
    get_settings.cache_clear()


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_user(org_slug: str) -> tuple[str, str]:
    with Session(db_module.engine) as session:
        person = Person(
            email=f"{org_slug}@example.com",
            name=f"{org_slug} User",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name=f"{org_slug} Org", slug=org_slug)
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
        session.commit()

        return str(person.id), str(organization.id)


def test_celonis_tool_hub_ui_redirects_when_celonis_domain_disabled() -> None:
    _cleanup_files()
    _write_rollout_config()
    _reset_db()
    person_id, organization_id = _seed_user("pilot-core-org")
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/celonis-tool-hub-ui", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/dashboard?err=Feature+domain")


def test_local_knowledge_ui_redirects_when_knowledge_domain_disabled() -> None:
    _cleanup_files()
    _write_rollout_config()
    _reset_db()
    person_id, organization_id = _seed_user("pilot-core-org")
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/local-knowledge-ui", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/dashboard?err=Feature+domain")


def test_local_knowledge_ui_is_accessible_for_org_override_profile(monkeypatch) -> None:
    _cleanup_files()
    _write_rollout_config()
    _reset_db()
    person_id, organization_id = _seed_user("knowledge-org")
    auth_token = create_access_token(person_id, organization_id)

    import foundry.api.routes.ui as ui_module

    class DummyGateway:
        def __init__(self, settings) -> None:
            self.settings = settings

        def health(self) -> dict:
            return {"status": "ok", "document_count": 2, "ollama_available": True}

        def corpus(self) -> dict:
            return {"total_documents": 2, "by_corpus": {"wiki": 2}}

    monkeypatch.setattr(ui_module, "LocalKnowledgeGateway", DummyGateway)

    def _raise_connect_error(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(ui_module.httpx, "get", _raise_connect_error)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/local-knowledge-ui")

    assert response.status_code == 200
    assert "Local Knowledge Hub" in response.text


def teardown_module(_: object) -> None:
    get_settings.cache_clear()
    _cleanup_files()
