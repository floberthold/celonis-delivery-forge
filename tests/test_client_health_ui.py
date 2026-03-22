import os
import re
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_client_health_ui_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import Client, Organization, OrganizationMembership, OrganizationRole, Person, Project
from foundry.security import create_access_token, hash_password


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


if __name__ == "__main__":
    if DB_FILE.exists():
        DB_FILE.unlink()
    test_client_health_ui_renders_tabs_and_toggle_controls()
