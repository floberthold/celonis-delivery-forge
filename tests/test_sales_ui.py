# ruff: noqa: E402

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_sales_ui_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person, TryCelonisDemo
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_sales_ui_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(db_module.engine)
    SQLModel.metadata.create_all(db_module.engine)


def _seed_actor() -> tuple[UUID, UUID]:
    with Session(db_module.engine) as session:
        person = Person(
            email="sales-ui@example.com",
            name="Sales UI Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Sales Org", slug="sales-org")
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

        return person.id, organization.id


def test_sales_ui_renders_stored_demo_rows() -> None:
    _reset_db()
    person_id, organization_id = _seed_actor()
    auth_token = create_access_token(str(person_id), str(organization_id))

    with Session(db_module.engine) as session:
        now = datetime.now(UTC).replace(tzinfo=None)
        session.add(
            TryCelonisDemo(
                organization_id=organization_id,
                title="FY27 - Shopfloor - Manufacturing (EN)",
                slug="fy27-shopfloor-manufacturing-en",
                summary="Manufacturing operations demo for shopfloor orchestration.",
                source_url="https://partners.try.celonis.cloud/try/ui/demo-portal/ui",
                catalog_url="https://partners.try.celonis.cloud/try/ui/demo-portal/ui",
                source_kind="manifest",
                industries_json=["manufacturing"],
                tags_json=["execution-app"],
                image_urls_json=[],
                evidence_json=[],
                confidence_score=0.91,
                last_synced_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.get("/sales-ui")
        assert response.status_code == 200
        assert "TryCelonis Demo Overview" in response.text
        assert "FY27 - Shopfloor - Manufacturing (EN)" in response.text
        assert "Open original source" in response.text
        assert "Sync TryCelonis Demos" in response.text


def test_sales_ui_sync_imports_manifest_rows() -> None:
    _reset_db()
    person_id, organization_id = _seed_actor()
    auth_token = create_access_token(str(person_id), str(organization_id))

    manifest_path = Path("tmp_trycelonis_manifest.json")
    manifest_path.write_text(
        json.dumps(
            {
                "catalog_url": "https://partners.try.celonis.cloud/try/ui/demo-portal/ui",
                "generated_at": "2026-03-22T12:00:00+00:00",
                "demos": [
                    {
                        "name": "FY27 - Customer Journey - Telco (EN)",
                        "slug": "fy27-customer-journey-telco-en",
                        "source_url": "https://partners.try.celonis.cloud/try/ui/demo-portal/ui",
                        "summary": "Telco journey demo for sales qualification.",
                        "industries": ["telecommunications"],
                        "tags": ["dashboard"],
                        "image_urls": [],
                        "evidence": [
                            {
                                "page_url": "https://partners.try.celonis.cloud/try/ui/demo-portal/ui",
                                "title": "FY27 - Customer Journey - Telco (EN)",
                                "summary": "Telco journey demo for sales qualification.",
                                "image_urls": [],
                            }
                        ],
                        "confidence": 0.88,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        with TestClient(app) as api_client:
            api_client.cookies.set("foundry_access_token", auth_token)

            response = api_client.post(
                "/sales-ui/trycelonis-sync",
                data={
                    "catalog_url": "",
                    "manifest_path": str(manifest_path),
                },
                follow_redirects=False,
            )
            assert response.status_code == 303
            assert response.headers["location"].startswith("/sales-ui?ok=")

        with Session(db_module.engine) as session:
            rows = session.exec(
                select(TryCelonisDemo).where(TryCelonisDemo.organization_id == organization_id)
            ).all()
            assert len(rows) == 1
            assert rows[0].title == "FY27 - Customer Journey - Telco (EN)"
            assert rows[0].tags_json == ["dashboard"]
            assert rows[0].source_kind == "manifest"
    finally:
        if manifest_path.exists():
            manifest_path.unlink()


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_sales_ui_renders_stored_demo_rows()
    test_sales_ui_sync_imports_manifest_rows()