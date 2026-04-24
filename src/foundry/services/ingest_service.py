import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlmodel import Session

from foundry.models import (
    AssetSnapshot,
    AssetSource,
    IngestFinding,
    IngestFindingSeverity,
    IngestRun,
    IngestRunStatus,
)
from foundry.services.snapshot_git_service import (
    archive_asset_snapshot_payload,
    materialize_asset_snapshot_git_history,
)

_TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
}

_SECRET_PATTERNS = [
    (
        "hardcoded-secret",
        re.compile(r"(?i)(api[_-]?token|secret|password|app[_-]?key)\\s*[:=]\\s*['\"]?[A-Za-z0-9_\\-]{8,}"),
        IngestFindingSeverity.critical,
        True,
    ),
    (
        "aws-access-key",
        re.compile(r"\\bAKIA[0-9A-Z]{16}\\b"),
        IngestFindingSeverity.critical,
        True,
    ),
]


def _looks_text_file(path: Path) -> bool:
    if path.suffix.lower() in _TEXT_EXTENSIONS:
        return True
    return path.stat().st_size <= 512 * 1024


def _scan_file_for_findings(path: Path, relative_path: str) -> list[tuple[dict, bool]]:
    findings: list[tuple[dict, bool]] = []

    if path.suffix.lower() in {".pyc", ".pyo"}:
        findings.append(
            (
                {
                    "severity": IngestFindingSeverity.warning,
                    "finding_type": "compiled-artifact",
                    "message": "Compiled artifact detected in code drop",
                    "file_path": relative_path,
                    "line_number": None,
                    "is_blocking": False,
                    "metadata_json": {"extension": path.suffix.lower()},
                },
                False,
            )
        )

    if not _looks_text_file(path):
        return findings

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    lines = content.splitlines()
    for line_number, line in enumerate(lines, start=1):
        for finding_type, pattern, severity, is_blocking in _SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(
                    (
                        {
                            "severity": severity,
                            "finding_type": finding_type,
                            "message": "Potential hardcoded credential detected",
                            "file_path": relative_path,
                            "line_number": line_number,
                            "is_blocking": is_blocking,
                            "metadata_json": {"excerpt": line.strip()[:120]},
                        },
                        is_blocking,
                    )
                )

    return findings


def execute_code_drop_ingest(
    *,
    session: Session,
    source: AssetSource,
    drop_path: str,
    triggered_by: UUID,
    generated_dir: str,
    version_label: str | None = None,
    source_ref: str | None = None,
    notes: str | None = None,
    ingest_mode: str = "code_drop",
    extra_summary: dict | None = None,
) -> tuple[AssetSnapshot, IngestRun, list[IngestFinding]]:
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    root = Path(drop_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("drop_path must point to an existing directory")

    files = sorted([path for path in root.rglob("*") if path.is_file()])
    extension_counts = Counter(path.suffix.lower() or "<none>" for path in files)
    total_bytes = sum(path.stat().st_size for path in files)

    rel_paths = [path.relative_to(root).as_posix() for path in files]
    manifest_hash = hashlib.sha256("\n".join(rel_paths).encode("utf-8")).hexdigest()

    summary_json = {
        "ingest_mode": ingest_mode,
        "root_path": str(root),
        "total_files": len(files),
        "total_bytes": total_bytes,
        "extension_counts": dict(extension_counts.most_common(20)),
        "manifest_sha256": manifest_hash,
    }
    if extra_summary:
        summary_json.update(extra_summary)

    snapshot = AssetSnapshot(
        asset_source_id=source.id,
        version_label=version_label or now_utc().strftime("drop-%Y%m%d-%H%M%S"),
        source_ref=source_ref,
        summary_json=summary_json,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    manifests_dir = Path(generated_dir).resolve() / "ingest_manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"{snapshot.id}.json"
    manifest_payload = {
        "snapshot_id": str(snapshot.id),
        "asset_source_id": str(source.id),
        "created_at": now_utc().isoformat(),
        "root_path": str(root),
        "files": rel_paths,
        "summary": summary_json,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    snapshot.manifest_path = str(manifest_path)
    updated_summary = dict(snapshot.summary_json)
    updated_summary["archived_payload_path"] = archive_asset_snapshot_payload(
        snapshot_id=snapshot.id,
        drop_path=str(root),
        generated_dir=generated_dir,
    )

    try:
        updated_summary["git_history"] = materialize_asset_snapshot_git_history(
            session,
            snapshot_id=snapshot.id,
            base_output_dir=Path(generated_dir).resolve() / "git_history",
        )
    except Exception as exc:
        updated_summary["git_history_error"] = str(exc)

    snapshot.summary_json = updated_summary

    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    run = IngestRun(
        asset_source_id=source.id,
        asset_snapshot_id=snapshot.id,
        status=IngestRunStatus.running,
        started_at=now_utc(),
        triggered_by=triggered_by,
        notes=notes,
        metrics_json={
            "files_scanned": len(files),
            "total_bytes": total_bytes,
        },
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    created_findings: list[IngestFinding] = []
    blocking_count = 0

    for path in files:
        relative_path = path.relative_to(root).as_posix()
        findings = _scan_file_for_findings(path, relative_path)
        for finding_payload, is_blocking in findings:
            finding = IngestFinding(ingest_run_id=run.id, **finding_payload)
            session.add(finding)
            created_findings.append(finding)
            if is_blocking:
                blocking_count += 1

    session.commit()
    for finding in created_findings:
        session.refresh(finding)

    run.finished_at = now_utc()
    run.status = IngestRunStatus.failed if blocking_count > 0 else IngestRunStatus.completed
    run.metrics_json = {
        **run.metrics_json,
        "findings_total": len(created_findings),
        "findings_blocking": blocking_count,
    }
    session.add(run)
    session.commit()
    session.refresh(run)

    return snapshot, run, created_findings


def execute_repo_sync_ingest(
    *,
    session: Session,
    source: AssetSource,
    local_repo_path: str,
    triggered_by: UUID,
    generated_dir: str,
    branch: str | None = None,
    tag: str | None = None,
    commit_sha: str | None = None,
    version_label: str | None = None,
    notes: str | None = None,
) -> tuple[AssetSnapshot, IngestRun, list[IngestFinding]]:
    selected_branch = branch or source.default_branch
    source_ref = commit_sha or tag or selected_branch

    provenance = {
        "provenance": {
            "branch": selected_branch,
            "tag": tag,
            "commit_sha": commit_sha,
            "repo_url": source.repo_url,
            "provider": source.provider,
        }
    }

    return execute_code_drop_ingest(
        session=session,
        source=source,
        drop_path=local_repo_path,
        triggered_by=triggered_by,
        generated_dir=generated_dir,
        version_label=version_label,
        source_ref=source_ref,
        notes=notes,
        ingest_mode="repo_sync",
        extra_summary=provenance,
    )
