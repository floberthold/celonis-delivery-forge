# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_user_token_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.integrations.celonis_import import CelonisPreflightHttpResult
from foundry.models import (
    ActivityLog,
    CelonisConnection,
    CelonisDeploymentRequest,
    CelonisDeploymentStatus,
    CelonisUserToken,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Quest,
    QuestPriority,
    QuestSource,
    QuestStatus,
)
from foundry.security import create_access_token, hash_password

engine = db_module.engine


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


def test_celonis_data_agent_tool_catalog_reflects_token_status() -> None:
    _reset_db()
    person_id, organization_id, _ = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        initial = api_client.get("/celonis/data-agent/tools")
        assert initial.status_code == 200, initial.text
        initial_payload = initial.json()
        assert initial_payload["tool_count"] == 13
        assert initial_payload["token_configured"] is False

        tool_keys = {tool["key"] for tool in initial_payload["tools"]}
        assert tool_keys == {
            "celonis_preflight",
            "get_data_model_load_info_tool",
            "list_data_models_tool",
            "list_jobs_tool",
            "list_pools_tool",
            "list_transformations_tool",
            "list_tables_tool",
            "list_pool_tables_tool",
            "list_data_model_table_row_counts_tool",
            "query_data_model_sql_tool",
            "studio_create_analysis_tool",
            "studio_set_view_component_tool",
            "studio_publish_package_tool",
        }
        assert all(
            tool["read_only"] is True
            for tool in initial_payload["tools"]
            if tool["key"] not in {
                "studio_create_analysis_tool",
                "studio_set_view_component_tool",
                "studio_publish_package_tool",
            }
        )
        write_tools = [
            tool
            for tool in initial_payload["tools"]
            if tool["key"] in {
                "studio_create_analysis_tool",
                "studio_set_view_component_tool",
                "studio_publish_package_tool",
            }
        ]
        assert len(write_tools) == 3
        assert all(tool["read_only"] is False for tool in write_tools)
        assert all(tool["requires_approved_deployment"] is True for tool in write_tools)
        assert all(tool["capability_group"] == "studio_write" for tool in write_tools)
        assert all(tool["requires_user_token"] is True for tool in initial_payload["tools"])

        save = api_client.put("/celonis/user-token", json={"token_value": "delegated-user-token"})
        assert save.status_code == 200

        configured = api_client.get("/celonis/data-agent/tools")
        assert configured.status_code == 200, configured.text
        configured_payload = configured.json()
        assert configured_payload["tool_count"] == 13
        assert configured_payload["token_configured"] is True


def test_celonis_data_agent_invoke_requires_delegated_token() -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post(
            "/celonis/data-agent/tools/list_pools_tool/invoke",
            json={"client_id": client_id, "inputs": {}},
        )
        assert response.status_code == 400
        assert "Delegated Celonis user token required" in response.text


def test_celonis_data_agent_invoke_logs_connection_and_quest(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with Session(engine) as session:
        quest = Quest(
            organization_id=UUID(organization_id),
            title="Investigate pool health",
            description="Check Celonis Data Integration pools",
            status=QuestStatus.active,
            source=QuestSource.agent_suggested,
            priority=QuestPriority.high,
            owner_person_id=UUID(person_id),
            created_by=UUID(person_id),
            client_id=UUID(client_id),
        )
        session.add(quest)
        session.commit()
        session.refresh(quest)
        quest_id = str(quest.id)

    observed: dict[str, object] = {}

    def _patched_invoke(settings, *, tenant_base_url: str, token_override: str, tool_key: str, inputs: dict):
        observed["tenant_base_url"] = tenant_base_url
        observed["token_override"] = token_override
        observed["tool_key"] = tool_key
        observed["inputs"] = dict(inputs)
        return {"count": 1, "items": [{"id": "pool-1", "name": "Main Pool"}]}

    monkeypatch.setattr("foundry.api.routes.celonis.invoke_data_agent_tool", _patched_invoke)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        save = api_client.put("/celonis/user-token", json={"token_value": "delegated-user-token"})
        assert save.status_code == 200

        response = api_client.post(
            "/celonis/data-agent/tools/list_pools_tool/invoke",
            json={
                "client_id": client_id,
                "quest_id": quest_id,
                "inputs": {},
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["tool_key"] == "list_pools_tool"
        assert payload["ok"] is True
        assert payload["token_configured"] is True
        assert payload["quest_id"] == quest_id
        assert payload["data"]["count"] == 1
        assert observed == {
            "tenant_base_url": "https://team.eu-1.celonis.cloud",
            "token_override": "delegated-user-token",
            "tool_key": "list_pools_tool",
            "inputs": {},
        }

    with Session(engine) as session:
        connection_logs = session.exec(
            select(ActivityLog).where(ActivityLog.action == "celonis_data_agent.tool_invoked")
        ).all()
        quest_logs = session.exec(
            select(ActivityLog).where(ActivityLog.action == "quest.celonis_data_agent_tool_invoked")
        ).all()

        assert len(connection_logs) == 1
        assert len(quest_logs) == 1
        assert connection_logs[0].metadata_json["client_id"] == client_id
        assert connection_logs[0].metadata_json["tool_key"] == "list_pools_tool"
        assert connection_logs[0].metadata_json["quest_id"] == quest_id
        assert quest_logs[0].entity_id == UUID(quest_id)


def test_celonis_studio_write_tool_requires_approved_deployment_request() -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        save = api_client.put("/celonis/user-token", json={"token_value": "delegated-user-token"})
        assert save.status_code == 200

        response = api_client.post(
            "/celonis/data-agent/tools/studio_publish_package_tool/invoke",
            json={
                "client_id": client_id,
                "inputs": {
                    "package_key": "demo-package",
                },
            },
        )
        assert response.status_code == 400
        assert "deployment_request_id" in response.text


def test_celonis_studio_write_tool_uses_approved_deployment_request(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, client_id = _seed_actor_org_client_connection()
    auth_token = create_access_token(person_id, organization_id)

    with Session(engine) as session:
        deployment_request = CelonisDeploymentRequest(
            organization_id=UUID(organization_id),
            project_id=uuid4(),
            client_id=UUID(client_id),
            created_by=UUID(person_id),
            status=CelonisDeploymentStatus.approved,
            target_package_key="demo-package",
            target_package_name="Demo Package",
            target_space_name="Demo Space",
            preflight_passed=True,
            permission_diff_acknowledged=True,
        )
        session.add(deployment_request)
        session.commit()
        session.refresh(deployment_request)
        deployment_request_id = str(deployment_request.id)

    observed: dict[str, object] = {}

    def _patched_invoke(settings, *, tenant_base_url: str, token_override: str, tool_key: str, inputs: dict):
        observed["tenant_base_url"] = tenant_base_url
        observed["token_override"] = token_override
        observed["tool_key"] = tool_key
        observed["inputs"] = dict(inputs)
        return {"endpoint": "/package-manager/api/packages/demo-package/activate", "result": {"ok": True}}

    monkeypatch.setattr("foundry.api.routes.celonis.invoke_data_agent_tool", _patched_invoke)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        save = api_client.put("/celonis/user-token", json={"token_value": "delegated-user-token"})
        assert save.status_code == 200

        response = api_client.post(
            "/celonis/data-agent/tools/studio_publish_package_tool/invoke",
            json={
                "client_id": client_id,
                "inputs": {
                    "deployment_request_id": deployment_request_id,
                    "package_key": "demo-package",
                },
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["tool_key"] == "studio_publish_package_tool"
        assert payload["ok"] is True
        assert payload["data"]["result"]["ok"] is True
        assert observed == {
            "tenant_base_url": "https://team.eu-1.celonis.cloud",
            "token_override": "delegated-user-token",
            "tool_key": "studio_publish_package_tool",
            "inputs": {
                "deployment_request_id": deployment_request_id,
                "package_key": "demo-package",
            },
        }

    with Session(engine) as session:
        deploy_logs = session.exec(
            select(ActivityLog).where(ActivityLog.action == "celonis_deployment_request.studio_write_tool_invoked")
        ).all()
        assert len(deploy_logs) == 1
        assert deploy_logs[0].entity_id == UUID(deployment_request_id)
        assert deploy_logs[0].metadata_json["tool_key"] == "studio_publish_package_tool"
        assert deploy_logs[0].metadata_json["requires_approved_deployment"] is True
