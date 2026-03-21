import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_use_case_api_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import Client, Organization, OrganizationMembership, OrganizationRole, Person, Project
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_use_case_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_person_client_project() -> tuple[str, str, str]:
    with Session(engine) as session:
        person = Person(
            email="usecase-tester@example.com",
            name="Use Case Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Use Case Test Org", slug="use-case-test-org")
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
            name="Acme Corp",
            tenant_url="https://acme.celonis.cloud",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=organization.id,
            name="Acme O2C",
            client_id=client.id,
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        return str(person.id), str(client.id), str(organization.id)


def _create_use_case(api_client: TestClient, payload: dict) -> None:
    response = api_client.post("/use-cases/", json=payload)
    assert response.status_code == 200, response.text


def test_use_case_scoped_views_and_redaction() -> None:
    _reset_db()

    person_id, client_id, organization_id = _seed_person_client_project()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        _create_use_case(
            api_client,
            {
                "title": "Internal + client + benchmark",
                "summary": "Comprehensive use case",
                "problem_statement": "Reduce invoice cycle time",
                "industry": "Manufacturing",
                "process_domain": "O2C",
                "owner_person_id": person_id,
                "client_id": client_id,
                "maturity": "validated",
                "tags_json": ["o2c", "automation"],
                "api_dependencies_json": ["knowledge model api", "subscription api"],
                "is_anonymized_ready": True,
                "is_client_view_enabled": True,
                "is_industry_benchmark_eligible": True,
            },
        )

        _create_use_case(
            api_client,
            {
                "title": "Anonymized only",
                "summary": "Public-safe use case",
                "problem_statement": "Suppress sensitive fields",
                "industry": "Manufacturing",
                "process_domain": "P2P",
                "owner_person_id": person_id,
                "maturity": "pilot",
                "tags_json": ["p2p"],
                "api_dependencies_json": ["knowledge model api"],
                "is_anonymized_ready": True,
                "is_client_view_enabled": False,
                "is_industry_benchmark_eligible": False,
            },
        )

        _create_use_case(
            api_client,
            {
                "title": "Internal only",
                "summary": "Not exposed externally",
                "problem_statement": "Internal context",
                "industry": "Retail",
                "process_domain": "O2C",
                "owner_person_id": person_id,
                "maturity": "idea",
                "tags_json": ["internal"],
                "api_dependencies_json": ["ai agent api"],
                "is_anonymized_ready": False,
                "is_client_view_enabled": False,
                "is_industry_benchmark_eligible": False,
            },
        )

        internal_view = api_client.get("/use-cases/views/internal")
        assert internal_view.status_code == 200
        assert len(internal_view.json()) == 3

        anonymized_view = api_client.get("/use-cases/views/anonymized")
        assert anonymized_view.status_code == 200
        anonymized_rows = anonymized_view.json()
        assert len(anonymized_rows) == 2
        assert all(row["client_id"] is None for row in anonymized_rows)
        assert all(row["owner_person_id"] is None for row in anonymized_rows)
        assert all(row["problem_statement"] is None for row in anonymized_rows)

        client_view = api_client.get(f"/use-cases/views/client/{client_id}")
        assert client_view.status_code == 200
        client_rows = client_view.json()
        assert len(client_rows) == 1
        assert client_rows[0]["client_id"] == client_id
        assert client_rows[0]["title"] == "Internal + client + benchmark"

        benchmark_view = api_client.get("/use-cases/views/industry-benchmark")
        assert benchmark_view.status_code == 200
        benchmark_rows = benchmark_view.json()
        assert len(benchmark_rows) == 1
        assert benchmark_rows[0]["title"] == "Internal + client + benchmark"
        assert benchmark_rows[0]["client_id"] is None
        assert benchmark_rows[0]["owner_person_id"] is None
        assert benchmark_rows[0]["problem_statement"] is None



def test_industry_benchmark_summary_rollup() -> None:
    _reset_db()

    person_id, client_id, organization_id = _seed_person_client_project()
    auth_token = create_access_token(person_id, organization_id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        _create_use_case(
            api_client,
            {
                "title": "Manufacturing O2C A",
                "summary": "First benchmark item",
                "industry": "Manufacturing",
                "process_domain": "O2C",
                "client_id": client_id,
                "maturity": "validated",
                "tags_json": ["o2c", "automation"],
                "api_dependencies_json": ["knowledge model api"],
                "is_industry_benchmark_eligible": True,
            },
        )

        _create_use_case(
            api_client,
            {
                "title": "Manufacturing O2C B",
                "summary": "Second benchmark item",
                "industry": "Manufacturing",
                "process_domain": "O2C",
                "owner_person_id": person_id,
                "maturity": "validated",
                "tags_json": ["o2c", "predictive"],
                "api_dependencies_json": ["knowledge model api", "subscription api"],
                "is_industry_benchmark_eligible": True,
            },
        )

        _create_use_case(
            api_client,
            {
                "title": "Retail P2P",
                "summary": "Different benchmark bucket",
                "industry": "Retail",
                "process_domain": "P2P",
                "owner_person_id": person_id,
                "maturity": "pilot",
                "tags_json": ["p2p"],
                "api_dependencies_json": ["ai agent api"],
                "is_industry_benchmark_eligible": True,
            },
        )

        _create_use_case(
            api_client,
            {
                "title": "Not eligible",
                "summary": "Should not appear in summary",
                "industry": "Retail",
                "process_domain": "P2P",
                "owner_person_id": person_id,
                "maturity": "pilot",
                "tags_json": ["internal-only"],
                "api_dependencies_json": ["ai agent api"],
                "is_industry_benchmark_eligible": False,
            },
        )

        summary_response = api_client.get("/use-cases/views/industry-benchmark/summary")
        assert summary_response.status_code == 200
        payload = summary_response.json()

        assert payload["total_use_cases"] == 3
        assert payload["bucket_count"] == 2
        assert payload["buckets"][0]["industry"] == "Manufacturing"
        assert payload["buckets"][0]["process_domain"] == "O2C"
        assert payload["buckets"][0]["maturity"] == "validated"
        assert payload["buckets"][0]["use_case_count"] == 2
        assert "o2c" in payload["top_tags"]
        assert "knowledge model api" in payload["top_api_dependencies"]

        filtered_summary_response = api_client.get(
            "/use-cases/views/industry-benchmark/summary",
            params={"industry": "Retail", "process_domain": "P2P"},
        )
        assert filtered_summary_response.status_code == 200
        filtered_payload = filtered_summary_response.json()
        assert filtered_payload["total_use_cases"] == 1
        assert filtered_payload["bucket_count"] == 1
        assert filtered_payload["buckets"][0]["industry"] == "Retail"

