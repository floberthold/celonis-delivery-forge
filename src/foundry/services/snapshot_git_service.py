from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, select

from foundry.models import (
    AssetSnapshot,
    AssetSource,
    CelonisSnapshot,
    Client,
    SnapshotDataModel,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotPackageDefinition,
    SnapshotTask,
    SnapshotTaskDetail,
)
from foundry.services.snapshot_export_service import (
    build_snapshot_delta_report,
    build_snapshot_replay_plan,
)


def _slugify(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "snapshot"


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _run_git(repo_dir: Path, *args: str, env: dict[str, str] | None = None) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if process.returncode != 0:
        stderr = process.stderr.strip()
        stdout = process.stdout.strip()
        raise RuntimeError(stderr or stdout or f"git {' '.join(args)} failed")
    return process.stdout.strip()


def _ensure_git_available() -> None:
    process = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("git is required to materialize snapshot history")


def _ensure_repo(repo_dir: Path) -> str:
    _ensure_git_available()
    repo_dir.mkdir(parents=True, exist_ok=True)
    git_dir = repo_dir / ".git"

    if not git_dir.exists():
        _run_git(repo_dir, "init")

    _run_git(repo_dir, "config", "user.name", "Celonis Delivery Forge")
    _run_git(repo_dir, "config", "user.email", "foundry@local")

    try:
        branch = _run_git(repo_dir, "symbolic-ref", "--short", "HEAD")
    except RuntimeError:
        branch = "main"
        _run_git(repo_dir, "checkout", "--orphan", branch)
    if not branch:
        branch = "main"
        _run_git(repo_dir, "checkout", "-B", branch)
    return branch


def _clear_worktree(repo_dir: Path) -> None:
    for child in repo_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _copy_tree(source_dir: Path, destination_dir: Path) -> None:
    for path in sorted(source_dir.rglob("*")):
        relative_path = path.relative_to(source_dir)
        target_path = destination_dir / relative_path
        if path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_path)


def _repo_result(
    *,
    repo_dir: Path,
    branch: str,
    commit_sha: str,
    created_commit: bool,
    commit_message: str,
    snapshot_id: UUID,
    target_type: str,
    target_id: UUID,
) -> dict[str, object]:
    return {
        "snapshot_id": str(snapshot_id),
        "target_type": target_type,
        "target_id": str(target_id),
        "repo_path": str(repo_dir),
        "branch": branch,
        "commit_sha": commit_sha,
        "created_commit": created_commit,
        "commit_message": commit_message,
        "committed_at": datetime.utcnow().isoformat(),
    }


def _commit_repo(repo_dir: Path, *, commit_message: str, commit_dt: datetime) -> tuple[str, bool]:
    _run_git(repo_dir, "add", "-A")
    status = _run_git(repo_dir, "status", "--porcelain")
    if not status.strip():
        commit_sha = _run_git(repo_dir, "rev-parse", "HEAD")
        return commit_sha, False

    env = os.environ.copy()
    git_date = commit_dt.replace(microsecond=0).isoformat() + "Z"
    env["GIT_AUTHOR_DATE"] = git_date
    env["GIT_COMMITTER_DATE"] = git_date
    _run_git(repo_dir, "commit", "-m", commit_message, env=env)
    commit_sha = _run_git(repo_dir, "rev-parse", "HEAD")
    return commit_sha, True


def _write_celonis_snapshot_tree(repo_dir: Path, snapshot: CelonisSnapshot, session: Session) -> None:
    package_rows = session.exec(
        select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot.id)
    ).all()
    task_rows = session.exec(
        select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot.id)
    ).all()
    task_detail_rows = session.exec(
        select(SnapshotTaskDetail).where(SnapshotTaskDetail.snapshot_id == snapshot.id)
    ).all()
    package_definition_rows = session.exec(
        select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == snapshot.id)
    ).all()
    data_model_rows = session.exec(
        select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == snapshot.id)
    ).all()
    job_rows = session.exec(
        select(SnapshotJob).where(SnapshotJob.snapshot_id == snapshot.id)
    ).all()
    km_rows = session.exec(
        select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == snapshot.id)
    ).all()

    task_rows_by_package: dict[str, list[SnapshotTask]] = {}
    for task in task_rows:
        package_key = task.package_id or "unassigned"
        task_rows_by_package.setdefault(package_key, []).append(task)

    _json_dump(
        repo_dir / ".forge" / "snapshot.json",
        {
            "snapshot_id": str(snapshot.id),
            "client_id": str(snapshot.client_id),
            "triggered_by": str(snapshot.triggered_by),
            "status": snapshot.status.value,
            "started_at": snapshot.started_at,
            "finished_at": snapshot.finished_at,
            "created_at": snapshot.created_at,
            "summary_json": snapshot.summary_json,
        },
    )
    delta_report = build_snapshot_delta_report(session, snapshot_id=snapshot.id)
    _json_dump(repo_dir / "reports" / "delta.json", delta_report)
    _json_dump(repo_dir / "reports" / "replay-plan.json", build_snapshot_replay_plan(session, snapshot_id=snapshot.id))

    removed_by_family: dict[str, list[dict[str, str]]] = {}
    for family, payload in delta_report.get("assets", {}).items():
        removed_items = payload.get("removed", [])
        if isinstance(removed_items, list) and removed_items:
            removed_by_family[family] = removed_items
    _json_dump(
        repo_dir / "reports" / "redactions.json",
        {
            "snapshot_id": str(snapshot.id),
            "recorded_at": datetime.utcnow().isoformat(),
            "removed_assets": removed_by_family,
        },
    )

    for package in package_rows:
        package_dir = repo_dir / "packages" / _slugify(package.name) / package.package_id
        _json_dump(package_dir / "package.json", package.raw_json)
        _json_dump(
            package_dir / ".forge-meta.json",
            {
                "package_id": package.package_id,
                "name": package.name,
                "key": package.key,
                "space_id": package.space_id,
                "space_name": package.space_name,
                "change_type": package.change_type.value,
            },
        )
        for task in sorted(task_rows_by_package.get(package.package_id, []), key=lambda row: row.task_id):
            task_dir = package_dir / "tasks"
            _json_dump(task_dir / f"{task.task_id}.json", task.raw_json)

        package_definitions = [row for row in package_definition_rows if row.package_id == package.package_id]
        for definition in sorted(package_definitions, key=lambda row: (row.definition_id, row.id)):
            definition_name = definition.definition_id or "studio.config.yaml"
            definition_dir = package_dir / "definitions"
            definition_dir.mkdir(parents=True, exist_ok=True)
            (definition_dir / definition_name).write_text(definition.raw_yaml or "", encoding="utf-8")
            _json_dump(
                definition_dir / f"{definition_name}.parsed.json",
                {
                    "package_id": definition.package_id,
                    "package_key": definition.package_key,
                    "definition_id": definition_name,
                    "source_endpoint": definition.source_endpoint,
                    "parse_error": definition.parse_error,
                    "change_type": definition.change_type.value,
                    "content_hash": definition.content_hash,
                    "parsed_json": definition.parsed_json,
                },
            )

    for task in sorted(task_rows_by_package.get("unassigned", []), key=lambda row: row.task_id):
        _json_dump(repo_dir / "tasks" / f"{task.task_id}.json", task.raw_json)

    detail_by_task: dict[str, SnapshotTaskDetail] = {}
    for row in task_detail_rows:
        detail_by_task[row.task_id] = row

    for task in task_rows:
        detail = detail_by_task.get(task.task_id)
        if detail is None:
            continue
        _json_dump(
            repo_dir / "task-details" / f"{task.task_id}.json",
            {
                "task_id": task.task_id,
                "package_id": detail.package_id,
                "task_type": detail.task_type,
                "source_endpoint": detail.source_endpoint,
                "error_message": detail.error_message,
                "detail": detail.detail_json,
                "references": detail.references_json,
                "dependencies": detail.dependencies_json,
            },
        )

    for data_model in data_model_rows:
        _json_dump(repo_dir / "data-models" / f"{data_model.data_model_id}.json", data_model.raw_json)
    for job in job_rows:
        _json_dump(repo_dir / "jobs" / f"{job.job_id}.json", job.raw_json)
    for knowledge_model in km_rows:
        _json_dump(repo_dir / "knowledge-models" / f"{knowledge_model.km_id}.json", knowledge_model.raw_json)


def materialize_celonis_snapshot_git_history(
    session: Session,
    *,
    snapshot_id: UUID,
    base_output_dir: Path,
) -> dict[str, object]:
    snapshot = session.get(CelonisSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError("Snapshot not found")

    client = session.get(Client, snapshot.client_id)
    client_slug = _slugify(client.name if client else str(snapshot.client_id))
    repo_dir = base_output_dir / "celonis_clients" / f"{client_slug}-{snapshot.client_id}"
    branch = _ensure_repo(repo_dir)
    # Keep previously materialized files to preserve historical assets when access is redacted.
    # Current snapshot content overwrites known files, while missing files remain in history.
    _write_celonis_snapshot_tree(repo_dir, snapshot, session)

    commit_message = f"celonis snapshot {snapshot.created_at:%Y-%m-%d %H:%M:%S}"
    commit_sha, created_commit = _commit_repo(
        repo_dir,
        commit_message=commit_message,
        commit_dt=snapshot.created_at,
    )
    return _repo_result(
        repo_dir=repo_dir,
        branch=branch,
        commit_sha=commit_sha,
        created_commit=created_commit,
        commit_message=commit_message,
        snapshot_id=snapshot.id,
        target_type="celonis_client",
        target_id=snapshot.client_id,
    )


def archive_asset_snapshot_payload(
    *,
    snapshot_id: UUID,
    drop_path: str,
    generated_dir: str,
) -> str:
    source_dir = Path(drop_path).expanduser().resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError("drop_path must point to an existing directory")

    archive_dir = Path(generated_dir).resolve() / "asset_snapshot_payloads" / str(snapshot_id) / "files"
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    _copy_tree(source_dir, archive_dir)
    return str(archive_dir)


def materialize_asset_snapshot_git_history(
    session: Session,
    *,
    snapshot_id: UUID,
    base_output_dir: Path,
) -> dict[str, object]:
    snapshot = session.get(AssetSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError("Asset snapshot not found")

    source = session.get(AssetSource, snapshot.asset_source_id)
    if source is None:
        raise ValueError("Asset source not found")

    archive_path = snapshot.summary_json.get("archived_payload_path")
    if not archive_path:
        manifest_root = snapshot.summary_json.get("root_path")
        if not manifest_root:
            raise ValueError("Snapshot payload is not available for git materialization")
        archive_path = manifest_root

    payload_dir = Path(str(archive_path)).resolve()
    if not payload_dir.exists() or not payload_dir.is_dir():
        raise ValueError("Snapshot payload directory is missing")

    source_slug = _slugify(source.name)
    repo_dir = base_output_dir / "asset_sources" / f"{source_slug}-{source.id}"
    branch = _ensure_repo(repo_dir)
    _clear_worktree(repo_dir)
    _copy_tree(payload_dir, repo_dir)

    manifest_payload = {}
    if snapshot.manifest_path:
        manifest_file = Path(snapshot.manifest_path)
        if manifest_file.exists() and manifest_file.is_file():
            manifest_payload = json.loads(manifest_file.read_text(encoding="utf-8"))

    _json_dump(
        repo_dir / ".forge" / "snapshot.json",
        {
            "snapshot_id": str(snapshot.id),
            "asset_source_id": str(snapshot.asset_source_id),
            "version_label": snapshot.version_label,
            "source_ref": snapshot.source_ref,
            "received_at": snapshot.received_at,
            "summary_json": snapshot.summary_json,
        },
    )
    if manifest_payload:
        _json_dump(repo_dir / ".forge" / "manifest.json", manifest_payload)

    commit_message = f"asset snapshot {snapshot.version_label}"
    commit_sha, created_commit = _commit_repo(
        repo_dir,
        commit_message=commit_message,
        commit_dt=snapshot.received_at,
    )
    return _repo_result(
        repo_dir=repo_dir,
        branch=branch,
        commit_sha=commit_sha,
        created_commit=created_commit,
        commit_message=commit_message,
        snapshot_id=snapshot.id,
        target_type="asset_source",
        target_id=snapshot.asset_source_id,
    )