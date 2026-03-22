import os
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
import subprocess

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_snapshots_api_test.db")

from foundry.api.main import app
from foundry.db import engine
from foundry.models import (
    CelonisSnapshot,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    SnapshotChangeType,
    SnapshotDataModel,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotRunStatus,
    SnapshotTask,
)
from foundry.security import create_access_token, hash_password


DB_FILE = Path("tmp_snapshots_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_snapshot_data() -> dict[str, str]:
    with Session(engine) as session:
        person_a = Person(
            email="snapshots-api-a@example.com",
            name="Snapshots API Tester A",
            hashed_password=hash_password("secret"),
        )
        person_b = Person(
            email="snapshots-api-b@example.com",
            name="Snapshots API Tester B",
            hashed_password=hash_password("secret"),
        )
        session.add(person_a)
        session.add(person_b)
        session.commit()
        session.refresh(person_a)
        session.refresh(person_b)

        org_a = Organization(name="Snapshots Org A", slug="snapshots-org-a")
        org_b = Organization(name="Snapshots Org B", slug="snapshots-org-b")
        session.add(org_a)
        session.add(org_b)
        session.commit()
        session.refresh(org_a)
        session.refresh(org_b)

        session.add(
            OrganizationMembership(
                organization_id=org_a.id,
                person_id=person_a.id,
                role=OrganizationRole.owner,
            )
        )
        session.add(
            OrganizationMembership(
                organization_id=org_b.id,
                person_id=person_b.id,
                role=OrganizationRole.owner,
            )
        )

        client_a = Client(
            organization_id=org_a.id,
            name="Snapshots Client A",
            tenant_url="https://snapshots-a.celonis.cloud",
        )
        session.add(client_a)
        session.commit()
        session.refresh(client_a)

        now = datetime.utcnow()
        prev_snapshot = CelonisSnapshot(
            client_id=client_a.id,
            triggered_by=person_a.id,
            status=SnapshotRunStatus.completed,
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=2) + timedelta(minutes=2),
            created_at=now - timedelta(hours=2),
        )
        current_snapshot = CelonisSnapshot(
            client_id=client_a.id,
            triggered_by=person_a.id,
            status=SnapshotRunStatus.completed,
            started_at=now - timedelta(hours=1),
            finished_at=now - timedelta(hours=1) + timedelta(minutes=2),
            created_at=now - timedelta(hours=1),
        )
        session.add(prev_snapshot)
        session.add(current_snapshot)
        session.commit()
        session.refresh(prev_snapshot)
        session.refresh(current_snapshot)

        session.add(
            SnapshotPackage(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-1",
                name="Package One",
                key="pkg-1",
                change_type=SnapshotChangeType.unchanged,
                raw_json={"id": "pkg-1", "name": "Package One", "version": 1},
            )
        )
        session.add(
            SnapshotPackage(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-2",
                name="Package Two",
                key="pkg-2",
                change_type=SnapshotChangeType.unchanged,
                raw_json={"id": "pkg-2", "name": "Package Two", "version": 1},
            )
        )
        session.add(
            SnapshotTask(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-1",
                task_id="task-1",
                name="Task One",
                task_type="kpi",
                content_hash="hash-task-1-v1",
                raw_json={"id": "task-1", "dataModelId": "dm-1", "knowledgeModelId": "km-1"},
            )
        )
        session.add(
            SnapshotTask(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-2",
                task_id="task-2",
                name="Task Two",
                task_type="kpi",
                content_hash="hash-task-2-v1",
                raw_json={"id": "task-2"},
            )
        )
        session.add(
            SnapshotDataModel(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                data_model_id="dm-1",
                name="Data Model One",
                raw_json={"id": "dm-1", "version": 1},
            )
        )
        session.add(
            SnapshotKnowledgeModel(
                snapshot_id=prev_snapshot.id,
                client_id=client_a.id,
                km_id="km-1",
                name="Knowledge Model One",
                raw_json={"id": "km-1", "version": 1},
            )
        )

        session.add(
            SnapshotPackage(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-1",
                name="Package One",
                key="pkg-1",
                change_type=SnapshotChangeType.modified,
                raw_json={"id": "pkg-1", "name": "Package One", "version": 2},
            )
        )
        session.add(
            SnapshotPackage(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-3",
                name="Package Three",
                key="pkg-3",
                change_type=SnapshotChangeType.added,
                raw_json={"id": "pkg-3", "name": "Package Three", "version": 1},
            )
        )
        session.add(
            SnapshotTask(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-1",
                task_id="task-1",
                name="Task One",
                task_type="kpi",
                content_hash="hash-task-1-v2",
                raw_json={"id": "task-1", "dataModelId": "dm-1", "knowledgeModelId": "km-1"},
            )
        )
        session.add(
            SnapshotTask(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                package_id="pkg-3",
                task_id="task-3",
                name="Task Three",
                task_type="kpi",
                content_hash="hash-task-3-v1",
                raw_json={"id": "task-3"},
            )
        )
        session.add(
            SnapshotDataModel(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                data_model_id="dm-1",
                name="Data Model One",
                raw_json={"id": "dm-1", "version": 2},
            )
        )
        session.add(
            SnapshotKnowledgeModel(
                snapshot_id=current_snapshot.id,
                client_id=client_a.id,
                km_id="km-1",
                name="Knowledge Model One",
                raw_json={"id": "km-1", "version": 1},
            )
        )

        session.commit()

        return {
            "person_a_id": str(person_a.id),
            "org_a_id": str(org_a.id),
            "person_b_id": str(person_b.id),
            "org_b_id": str(org_b.id),
            "client_a_id": str(client_a.id),
            "current_snapshot_id": str(current_snapshot.id),
            "prev_snapshot_id": str(prev_snapshot.id),
        }


def test_snapshot_delta_and_replay_plan_endpoints() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        delta_response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/delta")
        assert delta_response.status_code == 200, delta_response.text
        delta_payload = delta_response.json()

        assert delta_payload["snapshot_id"] == seed["current_snapshot_id"]
        assert delta_payload["previous_snapshot_id"] == seed["prev_snapshot_id"]
        assert delta_payload["assets"]["packages"]["counts"] == {
            "added": 1,
            "removed": 1,
            "modified": 1,
            "unchanged": 0,
        }
        assert delta_payload["assets"]["tasks"]["counts"] == {
            "added": 1,
            "removed": 1,
            "modified": 1,
            "unchanged": 0,
        }

        replay_response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/replay-plan")
        assert replay_response.status_code == 200, replay_response.text
        replay_payload = replay_response.json()

        assert replay_payload["snapshot_id"] == seed["current_snapshot_id"]
        assert replay_payload["dry_run"] is True
        assert replay_payload["summary"]["steps_total"] > 0

        step_pairs = {(row["action"], row["asset_type"], row.get("asset_id")) for row in replay_payload["steps"]}
        assert ("upsert", "package", "pkg-3") in step_pairs
        assert ("delete", "package", "pkg-2") in step_pairs
        assert ("upsert", "task", "task-3") in step_pairs
        assert ("delete", "task", "task-2") in step_pairs


def test_snapshot_export_endpoint_includes_delta_and_relationship_graph(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        export_response = api_client.post(f"/snapshots/{seed['current_snapshot_id']}/export")
        assert export_response.status_code == 200, export_response.text
        export_payload = export_response.json()

        assert export_payload["snapshot_id"] == seed["current_snapshot_id"]
        assert export_payload["delta_counts"]["packages"] == {
            "added": 1,
            "removed": 1,
            "modified": 1,
            "unchanged": 0,
        }
        assert export_payload["delta_counts"]["tasks"] == {
            "added": 1,
            "removed": 1,
            "modified": 1,
            "unchanged": 0,
        }
        assert export_payload["relationship_graph"]["nodes"] >= 6
        assert export_payload["relationship_graph"]["edges"] >= 3

        export_dir = Path(export_payload["export_dir"])
        docs_dir = Path(export_payload["docs_path"])
        bundle_path = Path(export_payload["bundle_path"])

        assert export_dir.exists()
        assert docs_dir.exists()
        assert bundle_path.exists()
        assert (export_dir / "data" / "delta.json").exists()
        assert (export_dir / "data" / "relationships.json").exists()
        assert (docs_dir / "relationships.md").exists()


def test_snapshot_export_download_returns_zip_response(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/export/download")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/zip"
        assert response.headers["content-disposition"] == (
            f'attachment; filename="snapshot_{seed["current_snapshot_id"]}.zip"'
        )
        assert response.content.startswith(b"PK")


def test_snapshot_git_history_endpoint_materializes_commit(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post(f"/snapshots/{seed['current_snapshot_id']}/git-history")
        assert response.status_code == 200, response.text
        payload = response.json()

        repo_path = Path(payload["repo_path"])
        assert payload["snapshot_id"] == seed["current_snapshot_id"]
        assert payload["target_type"] == "celonis_client"
        assert repo_path.exists()
        assert (repo_path / ".git").exists()
        assert (repo_path / ".forge" / "snapshot.json").exists()
        assert (repo_path / "reports" / "delta.json").exists()
        assert payload["commit_sha"]


def test_snapshot_delta_and_replay_plan_org_scope_enforced() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token_other_org = create_access_token(seed["person_b_id"], seed["org_b_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token_other_org)

        delta_response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/delta")
        assert delta_response.status_code == 404
        assert "Snapshot not found" in delta_response.text

        replay_response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/replay-plan")
        assert replay_response.status_code == 404
        assert "Snapshot not found" in replay_response.text


def test_trigger_snapshot_returns_400_without_active_connection() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        response = api_client.post(
            "/snapshots/trigger",
            json={"client_id": seed["client_a_id"]},
        )
        assert response.status_code == 400
        assert "No active Celonis connection" in response.text


def test_trigger_snapshot_passes_organization_scope_to_service(monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])
    captured: dict[str, str] = {}

    def _patched_run_snapshot(session, *, client_id, triggered_by, organization_id=None):
        captured["client_id"] = str(client_id)
        captured["triggered_by"] = str(triggered_by)
        captured["organization_id"] = str(organization_id) if organization_id else ""
        return session.get(CelonisSnapshot, UUID(seed["current_snapshot_id"]))

    monkeypatch.setattr("foundry.api.routes.snapshots.run_snapshot", _patched_run_snapshot)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/snapshots/trigger",
            json={"client_id": seed["client_a_id"]},
        )
        assert response.status_code == 202, response.text

    assert captured["client_id"] == seed["client_a_id"]
    assert captured["triggered_by"] == seed["person_a_id"]
    assert captured["organization_id"] == seed["org_a_id"]
