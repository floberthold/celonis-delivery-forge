# ruff: noqa: E402

import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_token_admin_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    ActivityLog,
    CelonisUserToken,
    Client,
    EntityType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_celonis_token_admin_ui_test.db")


def _cleanup_db_file() -> None:
    for path in (
        DB_FILE,
        DB_FILE.with_name(f"{DB_FILE.name}-journal"),
        DB_FILE.with_name(f"{DB_FILE.name}-wal"),
        DB_FILE.with_name(f"{DB_FILE.name}-shm"),
    ):
        try:
            path.unlink()
        except (FileNotFoundError, PermissionError):
            continue


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


@pytest.fixture(autouse=True)
def _isolate_celonis_token_admin_test_engine():
    previous_url = db_module._active_database_url
    _cleanup_db_file()
    db_module._set_engine("sqlite:///./tmp_celonis_token_admin_ui_test.db")
    yield
    db_module.engine.dispose()
    db_module._set_engine(previous_url)
    _cleanup_db_file()


def _seed_admin_and_member_with_token() -> tuple[str, str, str, str]:
    with Session(db_module.engine) as session:
        admin = Person(
            email="token-admin@example.com",
            name="Token Admin",
            hashed_password=hash_password("admin-secret"),
        )
        member = Person(
            email="token-member@example.com",
            name="Token Member",
            hashed_password=hash_password("member-secret"),
        )
        session.add(admin)
        session.add(member)
        session.commit()
        session.refresh(admin)
        session.refresh(member)

        organization = Organization(name="Token Admin Org", slug="token-admin-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        session.add(
            OrganizationMembership(
                organization_id=organization.id,
                person_id=admin.id,
                role=OrganizationRole.owner,
            )
        )
        session.add(
            OrganizationMembership(
                organization_id=organization.id,
                person_id=member.id,
                role=OrganizationRole.member,
            )
        )

        client = Client(
            organization_id=organization.id,
            name="Token Admin Client",
            tenant_url="https://token-admin-client.celonis.cloud",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=organization.id,
            client_id=client.id,
            name="Token Project Alpha",
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        token = CelonisUserToken(
            organization_id=organization.id,
            person_id=member.id,
            token_value="member-token-123456",
        )
        session.add(token)

        now = datetime.utcnow()
        session.add(
            ActivityLog(
                entity_type=EntityType.project,
                entity_id=project.id,
                actor_id=member.id,
                organization_id=organization.id,
                action="project.celonis_token.updated",
                timestamp=now - timedelta(minutes=2),
                metadata_json={
                    "token_present": True,
                    "scope": "project",
                },
            )
        )
        session.add(
            ActivityLog(
                entity_type=EntityType.celonis_connection,
                entity_id=organization.id,
                actor_id=member.id,
                organization_id=organization.id,
                action="celonis_connection.preflight",
                timestamp=now,
                metadata_json={
                    "service": "core",
                    "permission_status": "authorized",
                    "run_id": "run-1",
                },
            )
        )
        session.add(
            ActivityLog(
                entity_type=EntityType.celonis_connection,
                entity_id=organization.id,
                actor_id=member.id,
                organization_id=organization.id,
                action="celonis_connection.preflight",
                timestamp=now - timedelta(minutes=1),
                metadata_json={
                    "service": "packages",
                    "permission_status": "forbidden",
                    "run_id": "run-1",
                },
            )
        )

        session.commit()
        return str(admin.id), str(organization.id), str(member.id), str(token.id)


def test_celonis_token_admin_ui_shows_tokens_and_system_access() -> None:
    _reset_db()
    admin_id, organization_id, _, _ = _seed_admin_and_member_with_token()
    auth_token = create_access_token(admin_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/celonis-token-admin-ui")

    assert response.status_code == 200
    assert "Token Member" in response.text
    assert "person+organization" in response.text
    assert "Token Project Alpha" in response.text
    assert "project" in response.text
    assert "core" in response.text
    assert "packages (forbidden)" in response.text


def test_celonis_token_admin_ui_create_update_delete_flow() -> None:
    _reset_db()
    admin_id, organization_id, member_id, token_id = _seed_admin_and_member_with_token()
    auth_token = create_access_token(admin_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_response = api_client.post(
            "/celonis-token-admin-ui/create",
            data={"person_id": admin_id, "token_value": "admin-token-abc"},
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        assert create_response.headers["location"].startswith("/celonis-token-admin-ui?")

        update_response = api_client.post(
            "/celonis-token-admin-ui/update",
            data={"token_id": token_id, "token_value": "member-token-updated"},
            follow_redirects=False,
        )
        assert update_response.status_code == 303
        assert update_response.headers["location"].startswith("/celonis-token-admin-ui?")

        delete_response = api_client.post(
            "/celonis-token-admin-ui/delete",
            data={"token_id": token_id},
            follow_redirects=False,
        )
        assert delete_response.status_code == 303
        assert delete_response.headers["location"].startswith("/celonis-token-admin-ui?")

    with Session(db_module.engine) as session:
        admin_token = session.exec(
            select(CelonisUserToken).where(
                CelonisUserToken.organization_id == UUID(organization_id),
                CelonisUserToken.person_id == UUID(admin_id),
            )
        ).first()
        assert admin_token is not None

        member_token = session.exec(
            select(CelonisUserToken).where(
                CelonisUserToken.organization_id == UUID(organization_id),
                CelonisUserToken.person_id == UUID(member_id),
            )
        ).first()
        assert member_token is None


if __name__ == "__main__":
    if DB_FILE.exists():
            try:
                DB_FILE.unlink()
            except PermissionError:
                pass
    test_celonis_token_admin_ui_shows_tokens_and_system_access()
    test_celonis_token_admin_ui_create_update_delete_flow()
