# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_assets_ui_florian_import_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Asset, Client, Organization, OrganizationMembership, OrganizationRole, Person, Project
from foundry.security import create_access_token, hash_password
from foundry.settings import get_settings

engine = db_module.engine


DB_FILE = Path("tmp_assets_ui_florian_import_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_actor_with_project() -> tuple[str, str, str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="assets-ui-florian@example.com",
            name="Assets UI Florian",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Assets UI Org", slug="assets-ui-org")
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

        client = Client(
            organization_id=organization.id,
            name="Roboyo Sandbox",
            tenant_url="https://tenant.example",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=organization.id,
            client_id=client.id,
            name="AI Demand Forecast App",
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        return str(person.id), str(organization.id), str(client.id), str(project.id), create_access_token(str(person.id), str(organization.id))


def test_assets_ui_imports_florian_scripts_into_current_org(tmp_path: Path) -> None:
    _reset_db()

    person_id, organization_id, client_id, project_id, auth_token = _seed_actor_with_project()
    assert person_id
    assert organization_id

    root = tmp_path / "external resources" / "Code by Florian"
    tools_repo = root / "pyCelonis-tools"
    (tools_repo / "scripts" / "extractors" / "studio").mkdir(parents=True, exist_ok=True)
    (tools_repo / "local_scripts.py").write_text(
        "def build_celonis_url():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (tools_repo / "scripts" / "extractors" / "studio" / "views.py").write_text(
        "def extract_views():\n    return []\n",
        encoding="utf-8",
    )

    os.environ["FORGE_FLORIAN_SHARED_DIR"] = str(root)
    get_settings.cache_clear()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post("/florian-assets/register")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["project_count"] >= 1
        assert payload["asset_count"] >= 2

    with Session(engine) as session:
        rows = session.exec(select(Asset)).all()
        assert len(rows) >= 2


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass