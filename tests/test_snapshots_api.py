# ruff: noqa: E402

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_snapshots_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    Asset,
    CelonisConnection,
    CelonisSnapshot,
    CelonisUserToken,
    Client,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
    SnapshotApp,
    SnapshotChangeType,
    SnapshotDataModel,
    SnapshotDataPool,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotRunStatus,
    SnapshotSpace,
    SnapshotTask,
    SnapshotTransformation,
)
from foundry.security import create_access_token, hash_password

engine = db_module.engine


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
        lambda: SimpleNamespace(uploads_dir=str(tmp_path), generated_dir=str(tmp_path)),
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
        mirror_dir = Path(export_payload["mirror_dir"])
        docs_dir = Path(export_payload["docs_path"])
        bundle_path = Path(export_payload["bundle_path"])

        assert export_dir.exists()
        assert mirror_dir.exists()
        assert docs_dir.exists()
        assert bundle_path.exists()
        assert (export_dir / "data" / "delta.json").exists()
        assert (export_dir / "data" / "relationships.json").exists()
        assert (docs_dir / "relationships.md").exists()
        assert (mirror_dir / "tenant-manifest.json").exists()
        assert (mirror_dir / "Studio" / "Spaces").exists()
        assert (mirror_dir / "Apps" / "apps-manifest.json").exists()
        assert (mirror_dir / "Data Integration" / "data-integration-manifest.json").exists()


def test_snapshot_export_download_returns_zip_response(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path), generated_dir=str(tmp_path)),
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


def test_snapshot_coverage_endpoint_returns_statuses() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    _seed_extended_snapshot_data(seed)
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/coverage")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["snapshot_id"] == seed["current_snapshot_id"]
    assert "statuses" in payload
    assert "families" in payload
    family_keys = {row["key"] for row in payload["families"]}
    assert "packages" in family_keys
    assert "package_assets" in family_keys
    assert "knowledge_models" in family_keys


def test_snapshot_coverage_download_returns_json_attachment() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    _seed_extended_snapshot_data(seed)
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/coverage/download")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == (
        f'attachment; filename="snapshot_{seed["current_snapshot_id"]}_coverage.json"'
    )
    payload = response.json()
    assert payload["snapshot_id"] == seed["current_snapshot_id"]


def test_snapshot_ui_export_redirects_by_default(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.ui.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/snapshots-ui/{seed['client_a_id']}/{seed['current_snapshot_id']}/export",
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert "/snapshots-ui/" in response.headers["location"]
    assert "/detail" in response.headers["location"]
    assert "ok=" in response.headers["location"]


def test_snapshot_ui_export_returns_json_in_json_mode(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.ui.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/snapshots-ui/{seed['client_a_id']}/{seed['current_snapshot_id']}/export?response_mode=json",
            headers={"Accept": "application/json"},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["snapshot_id"] == seed["current_snapshot_id"]
    assert "Export bundle created" in payload["message"]
    assert payload["result"]["bundle_path"]


def test_snapshot_detail_ui_shows_compare_and_drilldown_sections() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get(
            f"/snapshots-ui/{seed['client_a_id']}/{seed['current_snapshot_id']}/detail?tab=hierarchy"
        )

    assert response.status_code == 200, response.text
    assert "Compare Snapshots" in response.text
    assert "Hierarchy" in response.text
    assert "Git-Style Diff" in response.text
    assert "Filter spaces, packages, assets, or types" in response.text


def test_snapshot_create_app_asset_from_task_creates_dependency_assets() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with Session(engine) as session:
        project = Project(
            organization_id=UUID(seed["org_a_id"]),
            client_id=UUID(seed["client_a_id"]),
            name="Snapshot Dependency Project",
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        project_id = str(project.id)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/snapshots-ui/{seed['client_a_id']}/{seed['current_snapshot_id']}/create-app-asset",
            data={
                "source_kind": "task",
                "source_id": "task-1",
                "source_name": "Task One",
                "project_id": project_id,
                "task_type": "kpi",
                "tab": "deep_packages",
                "compare_to": seed["prev_snapshot_id"],
            },
            follow_redirects=False,
        )

    assert response.status_code == 303, response.text
    assert "ok=" in response.headers["location"]

    with Session(engine) as session:
        assets = session.exec(
            select(Asset).where(Asset.project_id == UUID(project_id))
        ).all()

    identifiers = {row.asset_identifier for row in assets}
    assert f"snapshot:{seed['current_snapshot_id']}:task:task-1" in identifiers
    assert f"snapshot:{seed['current_snapshot_id']}:data_model:dm-1" in identifiers
    assert f"snapshot:{seed['current_snapshot_id']}:knowledge_model:km-1" in identifiers


def test_snapshot_git_history_endpoint_materializes_commit(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path), generated_dir=str(tmp_path)),
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


def test_snapshot_git_history_preserves_previous_assets_and_writes_redactions(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path), generated_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        first_response = api_client.post(f"/snapshots/{seed['prev_snapshot_id']}/git-history")
        assert first_response.status_code == 200, first_response.text
        first_payload = first_response.json()
        repo_path = Path(first_payload["repo_path"])

        previous_package_file = repo_path / "packages" / "package-two" / "pkg-2" / "package.json"
        previous_task_file = repo_path / "packages" / "package-two" / "pkg-2" / "tasks" / "task-2.json"
        assert previous_package_file.exists()
        assert previous_task_file.exists()

        second_response = api_client.post(f"/snapshots/{seed['current_snapshot_id']}/git-history")
        assert second_response.status_code == 200, second_response.text
        second_payload = second_response.json()
        assert Path(second_payload["repo_path"]) == repo_path

        assert previous_package_file.exists(), "Historical package file should remain after access loss"
        assert previous_task_file.exists(), "Historical task file should remain after access loss"

        redactions_file = repo_path / "reports" / "redactions.json"
        assert redactions_file.exists()
        redactions_payload = json.loads(redactions_file.read_text(encoding="utf-8"))
        removed_packages = redactions_payload["removed_assets"].get("packages", [])
        removed_tasks = redactions_payload["removed_assets"].get("tasks", [])
        assert any(row.get("id") == "pkg-2" for row in removed_packages)
        assert any(row.get("id") == "task-2" for row in removed_tasks)


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


def test_trigger_snapshot_ui_uses_saved_user_token(monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])
    captured: dict[str, str] = {}

    with Session(engine) as session:
        session.add(
            CelonisConnection(
                organization_id=UUID(seed["org_a_id"]),
                client_id=UUID(seed["client_a_id"]),
                tenant_base_url="https://tenant.celonis.cloud",
                is_active=True,
            )
        )
        session.add(
            CelonisUserToken(
                organization_id=UUID(seed["org_a_id"]),
                person_id=UUID(seed["person_a_id"]),
                token_value="user-token-abc",
            )
        )
        session.commit()

    def _patched_run_snapshot(session, *, client_id, triggered_by, organization_id=None, token_override=None):
        captured["client_id"] = str(client_id)
        captured["triggered_by"] = str(triggered_by)
        captured["organization_id"] = str(organization_id) if organization_id else ""
        captured["token_override"] = token_override or ""
        return session.get(CelonisSnapshot, UUID(seed["current_snapshot_id"]))

    monkeypatch.setattr("foundry.services.snapshot_service.run_snapshot", _patched_run_snapshot)

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            f"/snapshots-ui/{seed['client_a_id']}/trigger",
            follow_redirects=False,
        )

    assert response.status_code == 303, response.text
    assert "ok=" in response.headers["location"]
    assert captured["client_id"] == seed["client_a_id"]
    assert captured["triggered_by"] == seed["person_a_id"]
    assert captured["organization_id"] == seed["org_a_id"]
    assert captured["token_override"] == "user-token-abc"


# ---------------------------------------------------------------------------
# Extended artifact-type coverage tests
# ---------------------------------------------------------------------------

def _seed_extended_snapshot_data(seed: dict[str, str]) -> None:
    """Add spaces, apps, data pools, and transformations to the current snapshot."""
    with Session(engine) as session:
        snapshot_id = UUID(seed["current_snapshot_id"])
        client_id = UUID(seed["client_a_id"])

        session.add(SnapshotSpace(
            snapshot_id=snapshot_id, client_id=client_id,
            space_id="space-1", name="Space One",
            change_type=SnapshotChangeType.unchanged, raw_json={"id": "space-1"},
        ))
        session.add(SnapshotApp(
            snapshot_id=snapshot_id, client_id=client_id,
            app_id="app-1", name="App One",
            space_id="space-1", space_name="Space One", package_key="pkg-1",
            change_type=SnapshotChangeType.added, raw_json={"id": "app-1", "spaceId": "space-1"},
        ))
        session.add(SnapshotDataPool(
            snapshot_id=snapshot_id, client_id=client_id,
            pool_id="pool-1", name="Pool One",
            change_type=SnapshotChangeType.unchanged, raw_json={"id": "pool-1"},
        ))
        session.add(SnapshotTransformation(
            snapshot_id=snapshot_id, client_id=client_id,
            transformation_id="tf-1", name="Transformation One",
            pool_id="pool-1", pool_name="Pool One",
            change_type=SnapshotChangeType.added, raw_json={"id": "tf-1", "poolId": "pool-1"},
        ))
        session.commit()


def test_delta_includes_new_artifact_types() -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    _seed_extended_snapshot_data(seed)
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        delta_response = api_client.get(f"/snapshots/{seed['current_snapshot_id']}/delta")
        assert delta_response.status_code == 200, delta_response.text
        assets = delta_response.json()["assets"]

    assert "spaces" in assets, "delta must include spaces"
    assert "apps" in assets, "delta must include apps"
    assert "data_pools" in assets, "delta must include data_pools"
    assert "transformations" in assets, "delta must include transformations"

    # app-1 and tf-1 only appear in current snapshot → should be added
    assert assets["apps"]["counts"]["added"] >= 1
    assert assets["transformations"]["counts"]["added"] >= 1


def test_export_includes_new_artifact_jsonl_files(tmp_path, monkeypatch) -> None:
    _reset_db()
    seed = _seed_snapshot_data()
    _seed_extended_snapshot_data(seed)
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    monkeypatch.setattr(
        "foundry.api.routes.snapshots.get_settings",
        lambda: SimpleNamespace(uploads_dir=str(tmp_path), generated_dir=str(tmp_path)),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        export_response = api_client.post(f"/snapshots/{seed['current_snapshot_id']}/export")
        assert export_response.status_code == 200, export_response.text
        export_payload = export_response.json()

    data_dir = Path(export_payload["export_dir"]) / "data"
    assert (data_dir / "spaces.jsonl").exists(), "spaces.jsonl must be emitted"
    assert (data_dir / "apps.jsonl").exists(), "apps.jsonl must be emitted"
    assert (data_dir / "data_pools.jsonl").exists(), "data_pools.jsonl must be emitted"
    assert (data_dir / "transformations.jsonl").exists(), "transformations.jsonl must be emitted"

    # Verify counts in manifest
    counts = export_payload["asset_counts"]
    assert counts["spaces"] >= 1
    assert counts["apps"] >= 1
    assert counts["data_pools"] >= 1
    assert counts["transformations"] >= 1


def test_snapshot_run_captures_all_artifact_types(tmp_path, monkeypatch) -> None:
    """Verify run_snapshot calls all extractor functions and stores new entity types."""
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    # Provide fake Celonis API responses for all artifact endpoints
    from foundry.integrations.celonis_import import CelonisHttpFullResult

    def _fake_extract_full(self, *, tenant_base_url: str, source_path: str) -> CelonisHttpFullResult:
        responses: dict[str, list] = {
            "/package-manager/api/spaces": [{"id": "s-1", "name": "Space 1"}],
            "/package-manager/api/packages": [{"id": "p-1", "key": "p-1", "name": "Package 1"}],
            "/package-manager/api/packages/p-1/assets": [
                {"id": "t-1", "name": "KPI 1", "type": "KPI"},
                {"id": "t-2", "name": "Action Flow 1", "type": "ACTION_FLOW"},
                {"id": "t-3", "name": "View 1", "type": "ANALYSIS"},
            ],
            "/process-mining/api/data-models": [{"id": "dm-1", "name": "DM 1"}],
            "/integration/api/v1/jobs": [{"id": "j-1", "name": "Job 1"}],
            "/knowledge-model/api/knowledge-models": [{"id": "km-1", "name": "KM 1"}],
            "/apps/api/packages": [{"id": "a-1", "name": "App 1", "key": "a-1"}],
            "/integration/api/pools": [{"id": "pool-1", "name": "Pool 1"}],
            "/integration/api/v1/transformations": [{"id": "tf-1", "name": "TF 1", "poolId": "pool-1"}],
        }
        body = responses.get(source_path)
        if body is not None:
            import json
            return CelonisHttpFullResult(
                action="extract_full", url=source_path, status_code=200, ok=True,
                body=json.dumps(body),
            )
        return CelonisHttpFullResult(
            action="extract_full", url=source_path, status_code=404, ok=False, body=None,
        )

    # Patch the gateway method and settings, then also add a live CelonisConnection
    from foundry.models import CelonisConnection
    with Session(engine) as session:
        conn = CelonisConnection(
            organization_id=UUID(seed["org_a_id"]),
            client_id=UUID(seed["client_a_id"]),
            tenant_base_url="https://fake.celonis.cloud",
            is_active=True,
        )
        session.add(conn)
        session.commit()

    monkeypatch.setattr(
        "foundry.services.snapshot_service.CelonisGateway.extract_full",
        _fake_extract_full,
    )
    monkeypatch.setattr(
        "foundry.services.snapshot_service.get_settings",
        lambda: SimpleNamespace(
            celonis_api_token="tok",
            celonis_timeout_seconds=10,
            uploads_dir=str(tmp_path),
        ),
    )
    # stub export so it doesn't fail without a real ZipFile
    monkeypatch.setattr(
        "foundry.services.snapshot_export_service.build_snapshot_export",
        lambda *a, **kw: {
            "bundle_path": "", "docs_path": "", "generated_at": datetime.utcnow(),
            "delta_counts": {}, "relationship_graph": {},
        },
    )
    monkeypatch.setattr(
        "foundry.services.snapshot_service.materialize_celonis_snapshot_git_history",
        lambda *a, **kw: {},
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.post(
            "/snapshots/trigger",
            json={"client_id": seed["client_a_id"]},
        )
        assert response.status_code == 202, response.text
        payload = response.json()
        summary = payload["summary_json"]

    assert summary.get("spaces", 0) >= 1, "spaces must be counted in summary"
    assert summary.get("packages", 0) >= 1, "packages must be counted in summary"
    assert summary.get("data_models", 0) >= 1, "data_models must be counted in summary"
    assert summary.get("jobs", 0) >= 1, "jobs must be counted in summary"
    assert summary.get("knowledge_models", 0) >= 1, "knowledge_models must be counted in summary"
    assert summary.get("apps", 0) >= 1, "apps must be counted in summary"
    assert summary.get("data_pools", 0) >= 1, "data_pools must be counted in summary"
    assert summary.get("transformations", 0) >= 1, "transformations must be counted in summary"

    # Verify package tasks with different asset types (KPI, ACTION_FLOW, ANALYSIS) are stored
    with Session(engine) as session:
        tasks = session.exec(
            select(SnapshotTask).where(SnapshotTask.client_id == UUID(seed["client_a_id"]))
        ).all()
        task_types = {t.task_type for t in tasks}
    assert "KPI" in task_types, "KPI task_type must be stored"
    assert "ACTION_FLOW" in task_types, "ACTION_FLOW task_type must be stored"
    assert "ANALYSIS" in task_types, "ANALYSIS task_type must be stored"

    # Coverage stats must show at least one endpoint_with_data per family
    coverage = summary.get("coverage", {})
    for family in ("spaces", "packages", "data_models", "jobs", "knowledge_models", "apps", "data_pools"):
        assert coverage.get(family, {}).get("endpoints_with_data", 0) >= 1, (
            f"{family}: expected endpoints_with_data >= 1"
        )


def test_extract_items_hal_envelope() -> None:
    """_extract_items must unwrap HAL _embedded envelopes."""
    from foundry.services.snapshot_service import _extract_items

    payload = {"_embedded": {"spaces": [{"id": "s-1", "name": "S1"}, {"id": "s-2", "name": "S2"}]}}
    result = _extract_items(payload, ("spaces", "data"))
    assert len(result) == 2
    assert result[0]["id"] == "s-1"


def test_extract_items_non_json_envelope_keys() -> None:
    """_extract_items must handle lesser-known envelope keys like 'entities' and 'responseObject'."""
    from foundry.services.snapshot_service import _extract_items

    for key in ("entities", "records", "responseObject", "responseData", "payload"):
        payload = {key: [{"id": "x-1"}]}
        result = _extract_items(payload, ())
        assert result == [{"id": "x-1"}], f"Failed for envelope key '{key}'"


def test_fetch_endpoint_items_handles_json_decode_error(monkeypatch) -> None:
    """_fetch_endpoint_items must not raise on HTML/non-JSON response bodies."""
    from foundry.services.snapshot_service import _fetch_endpoint_items
    from foundry.integrations.celonis_import import CelonisGateway, CelonisHttpFullResult

    def _fake_extract_full(self, *, tenant_base_url, source_path, **kwargs):
        return CelonisHttpFullResult(
            action="extract_full",
            url=source_path,
            status_code=200,
            ok=True,
            body="<html><body>Login</body></html>",
        )

    monkeypatch.setattr(CelonisGateway, "extract_full", _fake_extract_full)
    from types import SimpleNamespace
    gw = CelonisGateway(SimpleNamespace(celonis_api_token="tok", celonis_timeout_seconds=5))
    items, had_items, ep_log = _fetch_endpoint_items(
        gw, "https://fake.celonis.cloud", "/studio/api/spaces", list_keys=("spaces",)
    )
    assert items == []
    assert had_items is False
    assert any("not valid JSON" in (entry.get("error") or "") for entry in ep_log)


def test_preflight_endpoint_returns_diagnostics(monkeypatch) -> None:
    """GET /snapshots/preflight/{client_id} returns per-endpoint probe results."""
    _reset_db()
    seed = _seed_snapshot_data()
    auth_token = create_access_token(seed["person_a_id"], seed["org_a_id"])

    from foundry.models import CelonisConnection
    with Session(engine) as session:
        conn = CelonisConnection(
            organization_id=UUID(seed["org_a_id"]),
            client_id=UUID(seed["client_a_id"]),
            tenant_base_url="https://fake.celonis.cloud",
            is_active=True,
        )
        session.add(conn)
        session.commit()

    from foundry.integrations.celonis_import import CelonisGateway, CelonisHttpFullResult
    import json as _json

    def _fake_extract_full(self, *, tenant_base_url, source_path, **kwargs):
        if "/package-manager/api/spaces" in source_path:
            return CelonisHttpFullResult(
                action="extract_full", url=source_path, status_code=200, ok=True,
                body=_json.dumps([{"id": "s-1", "name": "Space 1"}]),
            )
        return CelonisHttpFullResult(
            action="extract_full", url=source_path, status_code=404, ok=False, body=None,
        )

    monkeypatch.setattr(CelonisGateway, "extract_full", _fake_extract_full)
    monkeypatch.setattr(
        "foundry.services.snapshot_service.get_settings",
        lambda: SimpleNamespace(celonis_api_token="tok", celonis_timeout_seconds=5),
    )

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)
        response = api_client.get(f"/snapshots/preflight/{seed['client_a_id']}")

    assert response.status_code == 200
    data = response.json()
    assert "families" in data
    assert "spaces" in data["families"]
    spaces_results = data["families"]["spaces"]
    assert any(r.get("ok") for r in spaces_results), "At least one spaces probe should succeed"
    assert any(r.get("items_detected", 0) >= 1 for r in spaces_results)

