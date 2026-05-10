from __future__ import annotations

import json

from tests.e2e.helpers import append_bug, prepare_run


def test_e2e_helpers_write_metadata_and_bug_ledger(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FORGE_E2E_ARTIFACTS_DIR", str(tmp_path))
    metadata, run_dir = prepare_run("helpers-smoke", browser="chromium")
    metadata_path = run_dir / "run_metadata.json"

    assert metadata_path.exists()
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == metadata.run_id
    assert payload["journey_id"] == "helpers-smoke"

    bug_path = append_bug(
        run_dir,
        severity="P2",
        expected_behavior="Expected behavior",
        observed_behavior="Observed behavior",
        route="/test-route",
        evidence=["example.png"],
    )
    assert bug_path.exists()

    bug_payload = json.loads(bug_path.read_text(encoding="utf-8"))
    assert len(bug_payload["bugs"]) == 1
    assert bug_payload["bugs"][0]["severity"] == "P2"
