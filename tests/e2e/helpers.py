from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DEFAULT_ARTIFACTS_ROOT = Path(".orchestration/test-runs")


@dataclass
class E2ERunMetadata:
    run_id: str
    journey_id: str
    browser: str
    started_at_utc: str
    status: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_run(journey_id: str, browser: str = "chromium") -> tuple[E2ERunMetadata, Path]:
    run_id = uuid4().hex
    metadata = E2ERunMetadata(
        run_id=run_id,
        journey_id=journey_id,
        browser=browser,
        started_at_utc=_utc_now(),
        status="started",
    )
    artifacts_root = Path(os.getenv("FORGE_E2E_ARTIFACTS_DIR", str(DEFAULT_ARTIFACTS_ROOT)))
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_metadata(run_dir, metadata)
    return metadata, run_dir


def write_metadata(run_dir: Path, metadata: E2ERunMetadata) -> Path:
    metadata_path = run_dir / "run_metadata.json"
    metadata_path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    return metadata_path


def append_bug(
    run_dir: Path,
    *,
    severity: str,
    expected_behavior: str,
    observed_behavior: str,
    route: str,
    evidence: list[str] | None = None,
) -> Path:
    bug_path = run_dir / "bug_ledger.json"
    if bug_path.exists():
        payload = json.loads(bug_path.read_text(encoding="utf-8"))
        bugs = payload.get("bugs", [])
    else:
        bugs = []

    bugs.append(
        {
            "id": f"BUG-{len(bugs) + 1:04d}",
            "severity": severity,
            "expected_behavior": expected_behavior,
            "observed_behavior": observed_behavior,
            "route": route,
            "evidence": evidence or [],
            "recorded_at_utc": _utc_now(),
        }
    )
    bug_payload = {"bugs": bugs}
    bug_path.write_text(json.dumps(bug_payload, indent=2), encoding="utf-8")
    return bug_path
