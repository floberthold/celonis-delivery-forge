# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Keep this test isolated from developer-local databases.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_foundry_admin_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    Asset,
    AssetStatus,
    AssetType,
    Client,
    GlobalRole,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_foundry_admin_ui_test.db")
engine = db_module.engine


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_fixture() -> tuple[str, str, str, str]:
    with Session(engine) as session:
        org_a = Organization(name="Roboyo Main Org", slug="roboyo-main-org")
        org_b = Organization(name="Testing Admin Org", slug="testing-admin-org")
        session.add(org_a)
        session.add(org_b)
        session.commit()
        session.refresh(org_a)
        session.refresh(org_b)

        admin = Person(
            email="foundry-admin@example.com",
            name="Foundry Admin",
            hashed_password=hash_password("secret"),
            role_global=GlobalRole.admin,
        )
        member = Person(
            email="foundry-member@example.com",
            name="Foundry Member",
            hashed_password=hash_password("secret"),
            role_global=GlobalRole.member,
        )
        session.add(admin)
        session.add(member)
        session.commit()
        session.refresh(admin)
        session.refresh(member)

        session.add(
            OrganizationMembership(
                organization_id=org_a.id,
                person_id=admin.id,
                role=OrganizationRole.owner,
            )
        )
        session.add(
            OrganizationMembership(
                organization_id=org_b.id,
                person_id=member.id,
                role=OrganizationRole.member,
            )
        )

        client = Client(
            organization_id=org_b.id,
            name="Testing Client",
            tenant_url="https://tenant.example.local",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=org_b.id,
            name="Testing Project",
            client_id=client.id,
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        session.add(
            Asset(
                organization_id=org_b.id,
                project_id=project.id,
                client_id=client.id,
                type=AssetType.kpi,
                name="Testing KPI",
                status=AssetStatus.draft,
            )
        )
        session.commit()

        return str(admin.id), str(org_a.id), str(member.id), str(org_b.id)


def test_foundry_admin_ui_is_accessible_for_global_admin() -> None:
    _reset_db()
    admin_person_id, admin_org_id, _, _ = _seed_fixture()
    auth_token = create_access_token(admin_person_id, admin_org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/foundry-admin-ui")

    assert response.status_code == 200
    assert "Foundry Admin Console" in response.text
    assert "Roboyo Main Org" in response.text
    assert "Testing Admin Org" in response.text
    assert "Testing Client" in response.text
    assert "Testing Project" in response.text


def test_foundry_admin_ui_redirects_non_admin_users() -> None:
    _reset_db()
    _, _, member_person_id, member_org_id = _seed_fixture()
    auth_token = create_access_token(member_person_id, member_org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get("/foundry-admin-ui", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/dashboard?err=Global+admin+access+required")


def test_nav_shows_foundry_admin_link_for_global_admin_only() -> None:
    _reset_db()
    admin_person_id, admin_org_id, member_person_id, member_org_id = _seed_fixture()

    with TestClient(app) as api_client:
        admin_token = create_access_token(admin_person_id, admin_org_id)
        api_client.cookies.set("foundry_access_token", admin_token)
        admin_response = api_client.get("/dashboard")
        assert admin_response.status_code == 200
        assert "Foundry Admin" in admin_response.text

    with TestClient(app) as api_client:
        member_token = create_access_token(member_person_id, member_org_id)
        api_client.cookies.set("foundry_access_token", member_token)
        member_response = api_client.get("/dashboard")
        assert member_response.status_code == 200
        assert "Foundry Admin" not in member_response.text


def test_foundry_admin_can_create_user_with_initial_membership() -> None:
    _reset_db()
    admin_person_id, admin_org_id, _, _ = _seed_fixture()
    admin_org_id_uuid = UUID(admin_org_id)
    auth_token = create_access_token(admin_person_id, admin_org_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/foundry-admin-ui/users/create",
            data={
                "name": "Cross Org User",
                "email": "cross-org-user@example.com",
                "password": "TopSecret123!",
                "confirm_password": "TopSecret123!",
                "role_global": "member",
                "organization_id": admin_org_id,
                "org_role": "member",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/foundry-admin-ui?ok=")

    with Session(engine) as session:
        person = session.exec(select(Person).where(Person.email == "cross-org-user@example.com")).first()
        assert person is not None
        membership = session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.person_id == person.id,
                OrganizationMembership.organization_id == admin_org_id_uuid,
            )
        ).first()
        assert membership is not None
        assert membership.role == OrganizationRole.member


def test_foundry_admin_can_update_user_and_membership_role() -> None:
    _reset_db()
    admin_person_id, admin_org_id, member_person_id, member_org_id = _seed_fixture()
    member_person_id_uuid = UUID(member_person_id)
    member_org_id_uuid = UUID(member_org_id)
    auth_token = create_access_token(admin_person_id, admin_org_id)

    with Session(engine) as session:
        membership = session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.person_id == member_person_id_uuid,
                OrganizationMembership.organization_id == member_org_id_uuid,
            )
        ).first()
        assert membership is not None
        membership_id_value = membership.id
        membership_id = str(membership_id_value)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        update_user_response = api_client.post(
            "/foundry-admin-ui/users/update",
            data={
                "person_id": member_person_id,
                "name": "Updated Member",
                "email": "updated-member@example.com",
                "role_global": "admin",
                "password": "",
                "confirm_password": "",
            },
            follow_redirects=False,
        )
        update_membership_response = api_client.post(
            "/foundry-admin-ui/memberships/update",
            data={"membership_id": membership_id, "role": "admin"},
            follow_redirects=False,
        )

    assert update_user_response.status_code == 303
    assert update_user_response.headers["location"].startswith("/foundry-admin-ui?ok=")
    assert update_membership_response.status_code == 303
    assert update_membership_response.headers["location"].startswith("/foundry-admin-ui?ok=")

    with Session(engine) as session:
        member = session.exec(select(Person).where(Person.email == "updated-member@example.com")).first()
        assert member is not None
        assert member.name == "Updated Member"
        assert member.email == "updated-member@example.com"
        assert member.role_global == GlobalRole.admin

        membership = session.exec(
            select(OrganizationMembership).where(OrganizationMembership.id == membership_id_value)
        ).first()
        assert membership is not None
        assert membership.role == OrganizationRole.admin


def test_foundry_admin_cannot_remove_last_org_owner_or_admin() -> None:
    _reset_db()
    admin_person_id, admin_org_id, _, _ = _seed_fixture()
    admin_org_id_uuid = UUID(admin_org_id)
    auth_token = create_access_token(admin_person_id, admin_org_id)

    with Session(engine) as session:
        owner_membership = session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == admin_org_id_uuid,
                OrganizationMembership.role == OrganizationRole.owner,
            )
        ).first()
        assert owner_membership is not None
        owner_membership_id = str(owner_membership.id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/foundry-admin-ui/memberships/delete",
            data={"membership_id": owner_membership_id},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/foundry-admin-ui?err=Cannot+remove+the+last+owner%2Fadmin")


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
