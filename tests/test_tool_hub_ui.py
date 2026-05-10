# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_tool_hub_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password

engine = db_module.engine


DB_FILE = Path("tmp_tool_hub_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_test_user() -> tuple[str, str]:
    with Session(engine) as session:
        person = Person(
            email="tool-hub-user@example.com",
            name="Tool Hub User",
            hashed_password=hash_password("tool-hub-password-1"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Tool Hub Test Org", slug="tool-hub-test-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.member,
        )
        session.add(membership)
        session.commit()

        return str(person.id), str(organization.id)


def test_tool_hub_ui_renders() -> None:
    """Test that /celonis-tool-hub-ui renders correctly."""
    _reset_db()
    person_id, organization_id = _seed_test_user()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/celonis-tool-hub-ui")
        
        # Should succeed with auth
        assert response.status_code == 200
        
        # Should contain expected elements (at least one of these)
        assert any([
            "Tool Hub Command Center" in response.text,
            "Tool Hub" in response.text,
            "tool-hub" in response.text.lower(),
            "Available Tools" in response.text,
            "No tools found" in response.text,
        ]), f"Expected tool hub content not found. Response contains: {response.text[:500]}"


def test_tool_hub_ui_requires_auth() -> None:
    """Test that /celonis-tool-hub-ui requires authentication."""
    _reset_db()
    
    with TestClient(app) as api_client:
        response = api_client.get("/celonis-tool-hub-ui", follow_redirects=False)
        
        # Should return 401 Unauthorized without auth
        assert response.status_code in [307, 401, 302], f"Expected auth redirect, got {response.status_code}"


if __name__ == "__main__":
    test_tool_hub_ui_renders()
    test_tool_hub_ui_requires_auth()
    print("✓ All tests passed!")
    
    # Cleanup
    if DB_FILE.exists():
        DB_FILE.unlink()
