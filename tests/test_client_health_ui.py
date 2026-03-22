# ruff: noqa: E402

import os
import re
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_client_health_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    CelonisConnection,
    CelonisUserToken,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
)
from foundry.security import create_access_token, hash_password

engine = db_module.engine


DB_FILE = Path("tmp_client_health_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_client_health_data() -> tuple[str, str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="client-health-ui@example.com",
            name="Client Health UI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Health UI Org", slug="health-ui-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.owner,
        )
        session.add(membership)

        alpha_client = Client(
            organization_id=organization.id,
            name="Alpha Health UI Client",
            tenant_url="https://alpha-health-ui-client.celonis.cloud",
        )
        beta_client = Client(
            organization_id=organization.id,
            name="Beta Health UI Client",
            tenant_url="https://beta-health-ui-client.celonis.cloud",
        )
        session.add(alpha_client)
        session.add(beta_client)
        session.commit()
        session.refresh(alpha_client)
        session.refresh(beta_client)

        alpha_project_1 = Project(
            organization_id=organization.id,
            name="A-Health UI Project 1",
            client_id=alpha_client.id,
        )
        alpha_project_2 = Project(
            organization_id=organization.id,
            name="A-Health UI Project 2",
            client_id=alpha_client.id,
        )
        beta_project_1 = Project(
            organization_id=organization.id,
            name="B-Health UI Project 1",
            client_id=beta_client.id,
        )
        session.add(alpha_project_1)
        session.add(alpha_project_2)
        session.add(beta_project_1)
        session.commit()

        return str(person.id), str(organization.id), str(alpha_client.id), str(beta_client.id)


def _project_id_by_name(name: str) -> str:
    with Session(engine) as session:
        row = session.exec(select(Project).where(Project.name == name)).first()
        assert row is not None
        return str(row.id)


def _add_active_celonis_connection(organization_id: str, client_id: str) -> None:
    with Session(engine) as session:
        session.add(
            CelonisConnection(
                organization_id=UUID(organization_id),
                client_id=UUID(client_id),
                tenant_base_url="https://tenant.celonis.cloud",
                is_active=True,
            )
        )
        session.commit()


def test_client_health_ui_renders_tabs_and_toggle_controls() -> None:
    _reset_db()
    person_id, organization_id, _, _ = _seed_client_health_data()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.get("/client-health-ui")
        assert response.status_code == 200

        html = response.text

        # Core page content
        assert "Global Client Health" in html
        assert "PM View" in html
        assert "Dev View" in html
        assert "/client-health-ui/create-client" in html
        assert "Create Client" in html
        assert "name=\"tenant_url\"" in html
        assert "name=\"sensitivity_level\"" in html

        # New smoke-test controls for grouped rows
        assert "Collapse all" in html
        assert "Expand all" in html
        assert "class=\"client-toggle\"" in html
        assert "class=\"project-row\"" in html
        assert "class=\"client-summary-row\"" in html
        assert "Portfolio summary" in html

        # Dev-specific metrics expected on the page
        assert "Workflow Runs (7d)" in html
        assert "Data Pipeline" in html
        assert "No active Celonis connection" in html
        assert "Project Overview: A-Health UI Project 1" in html
        assert "/client-health-ui/projects/" in html
        assert "Save Links" in html
        assert "Save/Clear Token" in html
        assert "Download Metrics" in html


def test_client_health_ui_groups_project_rows_under_each_client_summary() -> None:
    _reset_db()
    person_id, organization_id, alpha_client_id, beta_client_id = _seed_client_health_data()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.get("/client-health-ui")
        assert response.status_code == 200

        html = response.text
        pm_start = html.index('<div id="pm-view"')
        pm_end = html.index('<div id="dev-view"')
        pm_html = html[pm_start:pm_end]

        row_pattern = re.compile(
            r'<tr class="(?P<row_class>client-summary-row|project-row)"[^>]*data-row-kind="(?P<kind>[^"]+)"[^>]*data-client-id="(?P<client_id>[^"]+)"',
            re.DOTALL,
        )
        row_sequence = [(match.group("kind"), match.group("client_id")) for match in row_pattern.finditer(pm_html)]

        assert row_sequence == [
            ("client-summary", alpha_client_id),
            ("project", alpha_client_id),
            ("project", alpha_client_id),
            ("client-summary", beta_client_id),
            ("project", beta_client_id),
        ]

        assert "(2 projects)" in pm_html
        assert "(1 projects)" in pm_html


def test_client_health_ui_create_client_form_creates_client_and_redirects() -> None:
    _reset_db()
    person_id, organization_id, _, _ = _seed_client_health_data()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post(
            "/client-health-ui/create-client",
            data={
                "name": "Gamma Health UI Client",
                "tenant_url": "https://gamma-health-ui-client.celonis.cloud",
                "sensitivity_level": "high",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers.get("location", "").startswith("/client-health-ui?ok=")

        dashboard_response = api_client.get("/client-health-ui")
        assert dashboard_response.status_code == 200
        assert "Gamma Health UI Client" in dashboard_response.text


def test_client_health_ui_updates_project_celonis_links() -> None:
    _reset_db()
    person_id, organization_id, _, _ = _seed_client_health_data()
    project_id = _project_id_by_name("A-Health UI Project 1")
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/client-health-ui/projects/{project_id}/celonis-links",
            data={
                "celonis_package_url": "package.celonis.cloud/my-package",
                "celonis_app_url": "https://apps.celonis.cloud/my-app",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/client-health-ui?ok=")

    with Session(engine) as session:
        project = session.get(Project, UUID(project_id))
        assert project is not None
        assert project.celonis_package_url == "https://package.celonis.cloud/my-package"
        assert project.celonis_app_url == "https://apps.celonis.cloud/my-app"


def test_client_health_ui_saves_and_clears_user_token() -> None:
    _reset_db()
    person_id, organization_id, _, _ = _seed_client_health_data()
    project_id = _project_id_by_name("A-Health UI Project 1")
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        save_response = api_client.post(
            f"/client-health-ui/projects/{project_id}/celonis-token",
            data={"token_value": "tok-123"},
            follow_redirects=False,
        )
        assert save_response.status_code == 303

        clear_response = api_client.post(
            f"/client-health-ui/projects/{project_id}/celonis-token",
            data={"token_value": ""},
            follow_redirects=False,
        )
        assert clear_response.status_code == 303

    with Session(engine) as session:
        token_row = session.exec(
            select(CelonisUserToken).where(
                CelonisUserToken.organization_id == UUID(organization_id),
                CelonisUserToken.person_id == UUID(person_id),
            )
        ).first()
        assert token_row is None


def test_client_health_ui_uptime_check_uses_project_connection(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, alpha_client_id, _ = _seed_client_health_data()
    project_id = _project_id_by_name("A-Health UI Project 1")
    _add_active_celonis_connection(organization_id, alpha_client_id)
    auth_token = create_access_token(person_id, organization_id)

    def _fake_preflight(self, *, tenant_base_url: str, probe_path: str = "/", service: str = "core", token_override: str | None = None):
        from foundry.integrations.celonis_import import CelonisPreflightHttpResult

        return CelonisPreflightHttpResult(
            service=service,
            probe_path=probe_path,
            probe_url=f"{tenant_base_url}{probe_path}",
            has_token=bool(token_override),
            request_attempted=True,
            reachable=True,
            authenticated=True,
            permission_status="authorized",
            status_code=200,
            error=None,
            response_preview="{}",
        )

    monkeypatch.setattr("foundry.api.routes.ui.CelonisGateway.preflight", _fake_preflight)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/client-health-ui/projects/{project_id}/celonis-uptime",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/client-health-ui?ok=")


def test_client_health_ui_metrics_download_returns_attachment(monkeypatch) -> None:
    _reset_db()
    person_id, organization_id, alpha_client_id, _ = _seed_client_health_data()
    project_id = _project_id_by_name("A-Health UI Project 1")
    _add_active_celonis_connection(organization_id, alpha_client_id)
    auth_token = create_access_token(person_id, organization_id)

    def _fake_extract_full(self, *, tenant_base_url: str, source_path: str, token_override: str | None = None):
        from foundry.integrations.celonis_import import CelonisHttpFullResult

        return CelonisHttpFullResult(
            action="extract_full",
            url=f"{tenant_base_url}{source_path}",
            status_code=200,
            ok=True,
            body='{"status":"ok"}',
        )

    monkeypatch.setattr("foundry.api.routes.ui.CelonisGateway.extract_full", _fake_extract_full)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/client-health-ui/projects/{project_id}/celonis-metrics-download",
            data={"metrics_path": "/apps/api/packages"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        assert "attachment; filename=" in response.headers.get("content-disposition", "")
        assert response.text == '{"status":"ok"}'


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_client_health_ui_renders_tabs_and_toggle_controls()
