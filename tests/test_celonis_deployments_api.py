# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_deployments_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    ActivityLog,
    CelonisDeploymentStatus,
    Client,
    EntityType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_celonis_deployments_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_org_client_project(email: str, slug: str) -> tuple[str, str, str, str]:
    with Session(db_module.engine) as session:
        person = Person(email=email, name=email, hashed_password=hash_password("secret"))
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name=f"Org {slug}", slug=slug)
        session.add(organization)
        session.commit()
        session.refresh(organization)

        session.add(OrganizationMembership(organization_id=organization.id, person_id=person.id, role=OrganizationRole.owner))
        session.commit()

        client = Client(organization_id=organization.id, name=f"Client {slug}", tenant_url="https://deployments-client.celonis.cloud")
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(organization_id=organization.id, client_id=client.id, name=f"Project {slug}")
        session.add(project)
        session.commit()
        session.refresh(project)

        return str(person.id), str(organization.id), str(client.id), str(project.id)


def _add_member(organization_id: str, email: str) -> str:
    with Session(db_module.engine) as session:
        person = Person(email=email, name=email, hashed_password=hash_password("secret"))
        session.add(person)
        session.commit()
        session.refresh(person)

        session.add(
            OrganizationMembership(
                organization_id=UUID(organization_id),
                person_id=person.id,
                role=OrganizationRole.member,
            )
        )
        session.commit()
        return str(person.id)


def test_celonis_deployments_api_lifecycle() -> None:
    _reset_db()
    person_id, organization_id, client_id, project_id = _seed_org_client_project(
        "deployments-api@example.com",
        "deployments-api-org",
    )
    auth_token = create_access_token(person_id, organization_id)
    reviewer_id = _add_member(organization_id, "deployments-reviewer@example.com")
    reviewer_auth_token = create_access_token(reviewer_id, organization_id)

    with Session(db_module.engine) as session:
        session.add(
            ActivityLog(
                organization_id=UUID(organization_id),
                entity_type=EntityType.celonis_connection,
                entity_id=UUID(client_id),
                actor_id=UUID(person_id),
                action="celonis_connection.preflight",
                metadata_json={
                    "client_id": client_id,
                    "run_id": "run-123",
                    "permission_status": "authorized",
                },
            )
        )
        session.commit()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_response = api_client.post(
            "/celonis/deployments/",
            json={
                "client_id": client_id,
                "project_id": project_id,
                "target_space_name": "prod-space",
                "target_package_key": "demo-package",
                "preflight_run_id": "run-123",
            },
        )
        assert create_response.status_code == 200, create_response.text
        create_payload = create_response.json()
        assert create_payload["status"] == CelonisDeploymentStatus.draft
        assert create_payload["preflight_passed"] is True
        deployment_request_id = create_payload["id"]

        ack_response = api_client.post(f"/celonis/deployments/{deployment_request_id}/acknowledge-diff")
        assert ack_response.status_code == 200
        assert ack_response.json()["permission_diff_acknowledged"] is True

        submit_without_reviewer = api_client.post(f"/celonis/deployments/{deployment_request_id}/submit-for-approval")
        assert submit_without_reviewer.status_code == 400
        assert "reviewer" in submit_without_reviewer.json()["detail"].lower()

        assign_response = api_client.post(
            f"/celonis/deployments/{deployment_request_id}/assign-reviewer",
            json={"reviewer_id": reviewer_id},
        )
        assert assign_response.status_code == 200
        assert assign_response.json()["reviewer_id"] == reviewer_id

        submit_response = api_client.post(f"/celonis/deployments/{deployment_request_id}/submit-for-approval")
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == CelonisDeploymentStatus.awaiting_approval

        queue_response = api_client.get(f"/celonis/deployments/queue?reviewer_id={reviewer_id}&include_unassigned=false")
        assert queue_response.status_code == 200
        queue_payload = queue_response.json()
        assert len(queue_payload) == 1
        assert queue_payload[0]["id"] == deployment_request_id

        decision_by_creator = api_client.post(
            f"/celonis/deployments/{deployment_request_id}/decision",
            json={"decision": "approved", "reviewer_note": "creator must fail"},
        )
        assert decision_by_creator.status_code == 400
        assert "assigned reviewer" in decision_by_creator.json()["detail"].lower()

    with TestClient(app) as reviewer_client:
        reviewer_client.cookies.set("foundry_access_token", reviewer_auth_token)
        approve_response = reviewer_client.post(
            f"/celonis/deployments/{deployment_request_id}/decision",
            json={"decision": "approved", "reviewer_note": "looks good"},
        )
        assert approve_response.status_code == 200
        approve_payload = approve_response.json()
        assert approve_payload["status"] == CelonisDeploymentStatus.approved
        assert approve_payload["reviewer_id"] == reviewer_id

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        history_response = api_client.get(f"/celonis/deployments/{deployment_request_id}/history")
        assert history_response.status_code == 200
        history_payload = history_response.json()
        actions = [event["action"] for event in history_payload]
        assert "celonis_deployment_request.created" in actions
        assert "celonis_deployment_request.diff_acknowledged" in actions
        assert "celonis_deployment_request.reviewer_assigned" in actions
        assert "celonis_deployment_request.submitted_for_approval" in actions
        assert "celonis_deployment_request.approved" in actions


def test_celonis_deployments_api_list_is_org_scoped() -> None:
    _reset_db()
    person_id, organization_id, client_id, project_id = _seed_org_client_project(
        "deployments-scope@example.com",
        "deployments-scope-org",
    )
    other_person_id, other_org_id, other_client_id, other_project_id = _seed_org_client_project(
        "deployments-scope-other@example.com",
        "deployments-scope-other-org",
    )
    auth_token = create_access_token(person_id, organization_id)
    other_auth_token = create_access_token(other_person_id, other_org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        create_first = api_client.post(
            "/celonis/deployments/",
            json={"client_id": client_id, "project_id": project_id},
        )
        assert create_first.status_code == 200

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", other_auth_token)
        create_other = api_client.post(
            "/celonis/deployments/",
            json={"client_id": other_client_id, "project_id": other_project_id},
        )
        assert create_other.status_code == 200

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/celonis/deployments/")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["client_id"] == client_id


def test_celonis_deployment_queue_and_history_are_org_scoped() -> None:
    _reset_db()
    person_id, organization_id, client_id, project_id = _seed_org_client_project(
        "deployments-queue@example.com",
        "deployments-queue-org",
    )
    other_person_id, other_org_id, other_client_id, other_project_id = _seed_org_client_project(
        "deployments-queue-other@example.com",
        "deployments-queue-other-org",
    )
    reviewer_id = _add_member(organization_id, "deployments-queue-reviewer@example.com")

    auth_token = create_access_token(person_id, organization_id)
    other_auth_token = create_access_token(other_person_id, other_org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        create_response = api_client.post(
            "/celonis/deployments/",
            json={"client_id": client_id, "project_id": project_id},
        )
        deployment_id = create_response.json()["id"]
        api_client.post(f"/celonis/deployments/{deployment_id}/assign-reviewer", json={"reviewer_id": reviewer_id})

    with TestClient(app) as other_client:
        other_client.cookies.set("foundry_access_token", other_auth_token)
        create_other = other_client.post(
            "/celonis/deployments/",
            json={"client_id": other_client_id, "project_id": other_project_id},
        )
        assert create_other.status_code == 200

        other_queue = other_client.get("/celonis/deployments/queue")
        assert other_queue.status_code == 200
        assert all(item["client_id"] == other_client_id for item in other_queue.json())

        hidden_history = other_client.get(f"/celonis/deployments/{deployment_id}/history")
        assert hidden_history.status_code == 404


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass