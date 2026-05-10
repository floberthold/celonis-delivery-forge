"""Tests for client and project-level Celonis tokens."""

from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from foundry import db as db_module
from foundry.api.main import app
from foundry.models import (
    CelonisClientToken,
    CelonisProjectToken,
    CelonisUserToken,
    Client,
    Organization,
    OrganizationMembership,
    Person,
    Project,
)
from foundry.security import create_access_token

def _reset_db():
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_test_data():
    """Seed organization, people, clients, and projects."""
    with Session(db_module.engine) as session:
        # Create org
        org = Organization(name="Test Org", slug="test-org")
        session.add(org)
        session.flush()

        # Create people
        admin = Person(
            email="admin@test.org",
            name="Admin",
            hashed_password="hashed",
        )
        member = Person(
            email="member@test.org",
            name="Member",
            hashed_password="hashed",
        )
        session.add_all([admin, member])
        session.flush()

        # Create memberships
        admin_mem = OrganizationMembership(
            organization_id=org.id,
            person_id=admin.id,
            role="admin",
        )
        member_mem = OrganizationMembership(
            organization_id=org.id,
            person_id=member.id,
            role="member",
        )
        session.add_all([admin_mem, member_mem])
        session.flush()

        # Create clients
        roboyo = Client(
            organization_id=org.id,
            name="Roboyo Sandbox",
            tenant_url="https://roboyo.celonis.cloud",
        )
        carlo = Client(
            organization_id=org.id,
            name="Carlo Gavazzi",
            tenant_url="https://carlo.celonis.cloud",
        )
        session.add_all([roboyo, carlo])
        session.flush()

        # Create projects
        proj1 = Project(
            organization_id=org.id,
            name="Roboyo Project 1",
            client_id=roboyo.id,
            status="active",
        )
        proj2 = Project(
            organization_id=org.id,
            name="Carlo Project 1",
            client_id=carlo.id,
            status="active",
        )
        session.add_all([proj1, proj2])
        session.flush()

        session.commit()
        return {
            "org_id": str(org.id),
            "admin_id": str(admin.id),
            "member_id": str(member.id),
            "roboyo_id": str(roboyo.id),
            "carlo_id": str(carlo.id),
            "proj1_id": str(proj1.id),
            "proj2_id": str(proj2.id),
        }


def test_token_resolution_hierarchy():
    """Test that tokens are resolved in correct priority: project > client > user."""
    _reset_db()
    data = _seed_test_data()

    with Session(db_module.engine) as session:
        org_id = UUID(data["org_id"])
        person_id = UUID(data["admin_id"])
        client_id = UUID(data["roboyo_id"])
        project_id = UUID(data["proj1_id"])

        # Import after DB is initialized
        from foundry.api.routes.ui import _resolve_celonis_token_value

        # Initially no token
        token = _resolve_celonis_token_value(session, org_id, person_id, client_id, project_id)
        assert token is None

        # Create user-level token
        user_token = CelonisUserToken(
            organization_id=org_id,
            person_id=person_id,
            token_value="user-token-123",
        )
        session.add(user_token)
        session.commit()

        # Should resolve to user token
        token = _resolve_celonis_token_value(session, org_id, person_id, client_id, project_id)
        assert token == "user-token-123"

        # Add client-level token (should override)
        client_token = CelonisClientToken(
            organization_id=org_id,
            client_id=client_id,
            token_value="client-token-456",
        )
        session.add(client_token)
        session.commit()

        token = _resolve_celonis_token_value(session, org_id, person_id, client_id, project_id)
        assert token == "client-token-456"

        # Add project-level token (should override all)
        project_token = CelonisProjectToken(
            organization_id=org_id,
            project_id=project_id,
            token_value="project-token-789",
        )
        session.add(project_token)
        session.commit()

        token = _resolve_celonis_token_value(session, org_id, person_id, client_id, project_id)
        assert token == "project-token-789"

        # If project is not provided, should resolve to client
        token = _resolve_celonis_token_value(session, org_id, person_id, client_id)
        assert token == "client-token-456"

        # If both client and project not provided, should resolve to user
        token = _resolve_celonis_token_value(session, org_id, person_id)
        assert token == "user-token-123"


def test_celonis_token_admin_ui_display():
    """Test that token admin UI displays all token types."""
    _reset_db()
    data = _seed_test_data()

    with Session(db_module.engine) as session:
        org_id = UUID(data["org_id"])
        admin_id = UUID(data["admin_id"])
        roboyo_id = UUID(data["roboyo_id"])
        proj1_id = UUID(data["proj1_id"])

        # Create tokens of each type
        user_token = CelonisUserToken(
            organization_id=org_id,
            person_id=admin_id,
            token_value="user-token-abc",
            token_name="My Admin Token",
        )
        client_token = CelonisClientToken(
            organization_id=org_id,
            client_id=roboyo_id,
            token_value="client-token-def",
            token_name="Roboyo Token",
        )
        project_token = CelonisProjectToken(
            organization_id=org_id,
            project_id=proj1_id,
            token_value="project-token-ghi",
            token_name="Project Dev",
        )
        session.add_all([user_token, client_token, project_token])
        session.commit()

    auth_token = create_access_token(data["admin_id"], data["org_id"])

    with TestClient(app) as client:
        client.cookies.set("foundry_access_token", auth_token)
        response = client.get("/celonis-token-admin-ui")

    assert response.status_code == 200
    assert "Roboyo Sandbox" in response.text  # client token entity
    assert "Roboyo Project 1" in response.text  # project token entity
    assert "Roboyo Token" in response.text  # client token name
    assert "Project Dev" in response.text  # project token name
    assert "Admin" in response.text  # user token entity (person name)


def test_create_client_token():
    """Test creating a client-level token via API."""
    _reset_db()
    data = _seed_test_data()

    auth_token = create_access_token(data["admin_id"], data["org_id"])

    with TestClient(app) as client:
        client.cookies.set("foundry_access_token", auth_token)
        response = client.post(
            "/celonis-token-admin-ui/create",
            data={
                "token_type": "client",
                "person_id": data["roboyo_id"],  # client ID reused in form field
                "token_value": "new-client-tok-123",
                "token_name": "Roboyo Production",
            },
            follow_redirects=False,
        )

    # Should redirect with success message
    assert response.status_code == 303
    assert "ok" in response.headers["location"]

    # Verify token was created
    with Session(db_module.engine) as session:
        org_id = UUID(data["org_id"])
        client_id = UUID(data["roboyo_id"])
        token = session.exec(
            select(CelonisClientToken).where(
                CelonisClientToken.organization_id == org_id,
                CelonisClientToken.client_id == client_id,
            )
        ).first()
        assert token is not None
        assert token.token_value == "new-client-tok-123"
        assert token.token_name == "Roboyo Production"


def test_create_project_token():
    """Test creating a project-level token via API."""
    _reset_db()
    data = _seed_test_data()

    auth_token = create_access_token(data["admin_id"], data["org_id"])

    with TestClient(app) as client:
        client.cookies.set("foundry_access_token", auth_token)
        response = client.post(
            "/celonis-token-admin-ui/create",
            data={
                "token_type": "project",
                "person_id": data["proj1_id"],  # project ID reused in form field
                "token_value": "new-proj-tok-456",
                "token_name": "Project Dev Token",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "ok" in response.headers["location"]

    # Verify token was created
    with Session(db_module.engine) as session:
        org_id = UUID(data["org_id"])
        project_id = UUID(data["proj1_id"])
        token = session.exec(
            select(CelonisProjectToken).where(
                CelonisProjectToken.organization_id == org_id,
                CelonisProjectToken.project_id == project_id,
            )
        ).first()
        assert token is not None
        assert token.token_value == "new-proj-tok-456"
        assert token.token_name == "Project Dev Token"


def test_delete_token():
    """Test deleting tokens via API."""
    _reset_db()
    data = _seed_test_data()

    org_id = UUID(data["org_id"])
    roboyo_id = UUID(data["roboyo_id"])

    # Create a client token
    with Session(db_module.engine) as session:
        token = CelonisClientToken(
            organization_id=org_id,
            client_id=roboyo_id,
            token_value="token-to-delete",
        )
        session.add(token)
        session.commit()
        token_id = token.id

    auth_token = create_access_token(data["admin_id"], data["org_id"])

    with TestClient(app) as client:
        client.cookies.set("foundry_access_token", auth_token)
        response = client.post(
            "/celonis-token-admin-ui/delete",
            data={"token_id": str(token_id)},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "ok" in response.headers["location"]

    # Verify token was deleted
    with Session(db_module.engine) as session:
        token = session.get(CelonisClientToken, token_id)
        assert token is None


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_token_resolution_hierarchy()
    test_celonis_token_admin_ui_display()
    test_create_client_token()
    test_create_project_token()
    test_delete_token()
    print("All tests passed!")
