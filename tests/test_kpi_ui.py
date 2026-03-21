import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_kpi_ui_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import Client, KpiDefinition, KpiStatus, KpiVersion, Organization, OrganizationMembership, OrganizationRole, Person, Project
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_kpi_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_person_client_project() -> tuple[str, str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="kpi-tester@example.com",
            name="KPI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="KPI Test Org", slug="kpi-test-org")
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

        client = Client(
            organization_id=organization.id,
            name="KPI Test Client",
            tenant_url="https://kpi-test.celonis.cloud",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=organization.id,
            name="KPI Test Project",
            client_id=client.id,
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        return str(person.id), str(client.id), str(project.id), str(organization.id)


def test_kpi_ui_create_update_version_status_delete_flow() -> None:
    _reset_db()

    person_id, client_id, project_id, organization_id = _seed_person_client_project()
    auth_token = create_access_token(person_id, organization_id=organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        list_page = api_client.get("/kpis-ui")
        assert list_page.status_code == 200
        assert "KPI Editor" in list_page.text

        create_response = api_client.post(
            "/kpis-ui/create",
            data={
                "name": "Cycle Time KPI",
                "description": "Initial KPI",
                "project_id": project_id,
                "client_id": client_id,
                "pql_formula": "SUM(1)",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        location = create_response.headers["location"]
        assert "/kpis-ui/" in location

        kpi_id = UUID(location.split("/kpis-ui/")[1].split("?")[0])

        save_metadata_response = api_client.post(
            f"/kpis-ui/{kpi_id}/save",
            data={
                "name": "Cycle Time KPI v2",
                "description": "Updated KPI",
                "data_model": "AP_DM",
                "celonis_url": "example.celonis.cloud/kpi",
                "asset_identifier": "KPI-001",
                "owner_id": person_id,
            },
            follow_redirects=False,
        )
        assert save_metadata_response.status_code == 303

        save_formula_response = api_client.post(
            f"/kpis-ui/{kpi_id}/save-formula",
            data={
                "pql_formula": "SUM(2)",
                "change_note": "Update formula",
            },
            follow_redirects=False,
        )
        assert save_formula_response.status_code == 303

        update_status_response = api_client.post(
            f"/kpis-ui/{kpi_id}/status",
            data={"status": "approved"},
            follow_redirects=False,
        )
        assert update_status_response.status_code == 303

        detail_page = api_client.get(f"/kpis-ui/{kpi_id}")
        assert detail_page.status_code == 200
        assert "Cycle Time KPI v2" in detail_page.text
        assert "Version History" in detail_page.text
        assert "approved" in detail_page.text

        with Session(engine) as session:
            kpi = session.get(KpiDefinition, kpi_id)
            assert kpi is not None
            assert kpi.status == KpiStatus.approved
            versions = session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all()
            assert len(versions) == 1
            assert versions[0].version == 1
            assert versions[0].pql_formula == "SUM(2)"

        delete_response = api_client.post(
            f"/kpis-ui/{kpi_id}/delete",
            follow_redirects=False,
        )
        assert delete_response.status_code == 303

        with Session(engine) as session:
            remaining_kpi = session.get(KpiDefinition, kpi_id)
            remaining_versions = session.exec(select(KpiVersion).where(KpiVersion.kpi_id == kpi_id)).all()
            assert remaining_kpi is None
            assert len(remaining_versions) == 0
