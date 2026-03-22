# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_celonis_marketplace_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    Asset,
    AssetSource,
    AssetSourceKind,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
)
from foundry.security import create_access_token, hash_password
from foundry.settings import get_settings

engine = db_module.engine


DB_FILE = Path("tmp_celonis_marketplace_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_person() -> tuple[str, str]:
    with Session(engine) as session:
        person = Person(
            email="celonis-marketplace-tester@example.com",
            name="Celonis Marketplace Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="API Test Org", slug="api-test-org")
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


def test_register_celonis_marketplace_creates_projects_sources_and_assets(tmp_path: Path) -> None:
    _reset_db()

    person_id, organization_id = _seed_person()
    auth_token = create_access_token(person_id, organization_id)

    shared_root = tmp_path / "Code from Celonis"
    dm_project = shared_root / "dm-load-optimization"
    kpi_project = shared_root / "KPI_Resolver"

    dm_project.mkdir(parents=True, exist_ok=True)
    kpi_project.mkdir(parents=True, exist_ok=True)

    (dm_project / "README.md").write_text("# DM\n", encoding="utf-8")
    (dm_project / "script_DM1_create_report.ipynb").write_text("{}", encoding="utf-8")
    (dm_project / "tool.py").write_text("print('dm')\n", encoding="utf-8")

    (kpi_project / "KPI_Resolver.ipynb").write_text("{}", encoding="utf-8")
    (kpi_project / "requirements.txt").write_text("pycelonis\n", encoding="utf-8")

    os.environ["FORGE_CELONIS_SHARED_DIR"] = str(shared_root)
    get_settings.cache_clear()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post("/celonis-marketplace/register")
        assert response.status_code == 200, response.text
        payload = response.json()

        assert payload["project_count"] == 2
        assert payload["asset_count"] >= 5
        assert len(payload["projects"]) == 2

        # Calling register again should be idempotent for existing assets.
        second_response = api_client.post("/celonis-marketplace/register")
        assert second_response.status_code == 200, second_response.text
        second_payload = second_response.json()
        assert second_payload["asset_count"] == 0

        shared_org_id = UUID(payload["organization_id"])

    with Session(engine) as session:
        shared_org = session.get(Organization, shared_org_id)
        assert shared_org is not None
        assert shared_org.slug == "celonis-shared"

        shared_client = session.exec(
            select(Client).where(Client.organization_id == shared_org.id)
        ).first()
        assert shared_client is not None

        projects = session.exec(
            select(Project).where(Project.organization_id == shared_org.id)
        ).all()
        assert len(projects) == 2

        sources = session.exec(
            select(AssetSource).where(
                AssetSource.organization_id == shared_org.id,
                AssetSource.kind == AssetSourceKind.celonis_marketplace,
            )
        ).all()
        assert len(sources) == 2

        assets = session.exec(
            select(Asset).where(Asset.organization_id == shared_org.id)
        ).all()
        assert len(assets) >= 5


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
