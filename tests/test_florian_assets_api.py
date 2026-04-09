# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_florian_assets_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    Asset,
    AssetSnapshot,
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


DB_FILE = Path("tmp_florian_assets_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_person() -> tuple[str, str]:
    with Session(engine) as session:
        person = Person(
            email="florian-assets-tester@example.com",
            name="Florian Assets Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="API Test Org", slug="api-test-org-florian")
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


def test_register_florian_assets_creates_sources_assets_and_snapshots(tmp_path: Path) -> None:
    _reset_db()

    person_id, organization_id = _seed_person()
    auth_token = create_access_token(person_id, organization_id)

    root = tmp_path / "external resources" / "Code by Florian"
    tools_repo = root / "pyCelonis-tools"
    fuchs_repo = root / "pyCelonis%20-%20for%20Fuchs"
    migration_repo = root / "pyCelonis%20-%20OCPM%20migration%20tool"

    (tools_repo / "scripts" / "extractors" / "studio").mkdir(parents=True, exist_ok=True)
    (fuchs_repo / "Automations" / "Automations").mkdir(parents=True, exist_ok=True)
    (migration_repo / "app" / "services").mkdir(parents=True, exist_ok=True)

    (tools_repo / "local_scripts.py").write_text(
        "def build_celonis_url():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (tools_repo / "scripts" / "extractors" / "studio" / "views.py").write_text(
        "def extract_views():\n    return []\n",
        encoding="utf-8",
    )
    (fuchs_repo / "Automations" / "Automations" / "scripts.py").write_text(
        "def combine_data():\n    return []\n",
        encoding="utf-8",
    )
    (migration_repo / "app" / "services" / "team_client.py").write_text(
        "class TeamClient:\n    pass\n",
        encoding="utf-8",
    )

    os.environ["FORGE_FLORIAN_SHARED_DIR"] = str(root)
    get_settings.cache_clear()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post("/florian-assets/register")
        assert response.status_code == 200, response.text
        payload = response.json()

        assert payload["project_count"] == 3
        assert payload["asset_count"] == 4
        assert len(payload["projects"]) == 3
        assert all(project["scripts_discovered"] >= 1 for project in payload["projects"])

        second_response = api_client.post("/florian-assets/register")
        assert second_response.status_code == 200, second_response.text
        second_payload = second_response.json()
        assert second_payload["asset_count"] == 0

        shared_org_id = UUID(payload["organization_id"])

    with Session(engine) as session:
        shared_org = session.get(Organization, shared_org_id)
        assert shared_org is not None
        assert shared_org.slug == "florian-shared"

        shared_client = session.exec(
            select(Client).where(Client.organization_id == shared_org.id)
        ).first()
        assert shared_client is not None

        projects = session.exec(
            select(Project).where(Project.organization_id == shared_org.id)
        ).all()
        assert len(projects) == 3

        sources = session.exec(
            select(AssetSource).where(
                AssetSource.organization_id == shared_org.id,
                AssetSource.kind == AssetSourceKind.mirrored_repo,
            )
        ).all()
        assert len(sources) == 3

        assets = session.exec(
            select(Asset).where(Asset.organization_id == shared_org.id)
        ).all()
        assert len(assets) == 4
        assert {row.asset_identifier for row in assets} == {
            "Florian/pyCelonis-tools/local_scripts.py",
            "Florian/pyCelonis-tools/scripts/extractors/studio/views.py",
            "Florian/pyCelonis%20-%20for%20Fuchs/Automations/Automations/scripts.py",
            "Florian/pyCelonis%20-%20OCPM%20migration%20tool/app/services/team_client.py",
        }

        snapshots = session.exec(
            select(AssetSnapshot)
        ).all()
        assert len(snapshots) == 3
        assert all(row.summary_json.get("script_count", 0) >= 1 for row in snapshots)


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass