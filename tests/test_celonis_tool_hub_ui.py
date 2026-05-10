# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_tool_hub_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import CelonisConnection, CelonisDeploymentRequest, CelonisDeploymentStatus, Client, Organization, OrganizationMembership, OrganizationRole, Person, Project
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_celonis_tool_hub_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_tool_hub_data() -> tuple[str, str]:
    with Session(db_module.engine) as session:
        person = Person(email="tool-hub-ui@example.com", name="Tool Hub UI Tester", hashed_password=hash_password("secret"))
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Tool Hub Org", slug="tool-hub-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        session.add(OrganizationMembership(organization_id=organization.id, person_id=person.id, role=OrganizationRole.owner))

        client = Client(organization_id=organization.id, name="Tool Hub Client", tenant_url="https://tool-hub-client.celonis.cloud")
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(organization_id=organization.id, client_id=client.id, name="Tool Hub Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        session.add(CelonisConnection(organization_id=organization.id, client_id=client.id, tenant_base_url="https://team.eu-1.celonis.cloud", is_active=True))
        session.add(
            CelonisDeploymentRequest(
                organization_id=organization.id,
                project_id=project.id,
                client_id=client.id,
                created_by=person.id,
                status=CelonisDeploymentStatus.approved,
                target_package_key="demo-package",
                target_package_name="Demo Package",
                preflight_passed=True,
                permission_diff_acknowledged=True,
            )
        )
        session.commit()

        return str(person.id), str(organization.id)


def test_celonis_tool_hub_ui_renders() -> None:
    _reset_db()
    person_id, organization_id = _seed_tool_hub_data()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/celonis-tool-hub-ui")
        assert response.status_code == 200
        assert "Celonis Tool Hub" in response.text
        assert "Run Tool" in response.text
        assert "Approved Deployments" in response.text
        assert "studio_publish_package_tool" in response.text
        assert 'href="/celonis-tool-hub-ui" class="secondary-nav-link is-active"' in response.text


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass