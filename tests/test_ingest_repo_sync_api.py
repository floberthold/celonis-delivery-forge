import json
import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_ingest_repo_sync_api_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_ingest_repo_sync_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_person() -> tuple[str, str]:
    with Session(engine) as session:
        person = Person(
            email="ingest-repo-sync-tester@example.com",
            name="Ingest Repo Sync Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Ingest Test Org", slug="ingest-test-org")
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


def test_repo_sync_execute_persists_provenance(tmp_path: Path) -> None:
    _reset_db()

    person_id, organization_id = _seed_person()
    auth_token = create_access_token(person_id, organization_id)

    repo_root = tmp_path / "sample-repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "README.md").write_text("# Sample Repo\n", encoding="utf-8")
    (repo_root / "src").mkdir(parents=True, exist_ok=True)
    (repo_root / "src" / "module.py").write_text("print('ok')\n", encoding="utf-8")

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        source_response = api_client.post(
            "/ingest/sources",
            json={
                "name": "Sample Pullable Repo",
                "kind": "pullable_repo",
                "provider": "github",
                "repo_url": "https://github.com/example/sample-repo",
                "default_branch": "main",
                "notes": "repo sync test",
                "is_active": True,
            },
        )
        assert source_response.status_code == 200, source_response.text
        source_id = source_response.json()["id"]

        execute_response = api_client.post(
            "/ingest/repo-sync/execute",
            json={
                "asset_source_id": source_id,
                "local_repo_path": str(repo_root),
                "branch": "feature/intake",
                "tag": "v1.2.3",
                "commit_sha": "abc123def4567890",
                "version_label": "sync-2026-03-21",
                "notes": "test repo sync execution",
            },
        )

        assert execute_response.status_code == 200, execute_response.text
        payload = execute_response.json()

        snapshot = payload["snapshot"]
        run = payload["run"]
        findings = payload["findings"]

        assert snapshot["version_label"] == "sync-2026-03-21"
        assert snapshot["source_ref"] == "abc123def4567890"
        assert snapshot["summary_json"]["ingest_mode"] == "repo_sync"
        assert snapshot["summary_json"]["provenance"]["branch"] == "feature/intake"
        assert snapshot["summary_json"]["provenance"]["tag"] == "v1.2.3"
        assert snapshot["summary_json"]["provenance"]["commit_sha"] == "abc123def4567890"
        assert snapshot["summary_json"]["provenance"]["provider"] == "github"
        assert snapshot["summary_json"]["provenance"]["repo_url"] == "https://github.com/example/sample-repo"

        assert run["asset_source_id"] == source_id
        assert run["asset_snapshot_id"] == snapshot["id"]
        assert run["status"] in {"completed", "failed"}
        assert run["metrics_json"]["files_scanned"] == 2

        assert isinstance(findings, list)

        manifest_path = Path(snapshot["manifest_path"])
        assert manifest_path.exists()

        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_payload["asset_source_id"] == source_id
        assert manifest_payload["snapshot_id"] == snapshot["id"]
        assert "README.md" in manifest_payload["files"]
        assert "src/module.py" in manifest_payload["files"]
        assert manifest_payload["summary"]["ingest_mode"] == "repo_sync"
