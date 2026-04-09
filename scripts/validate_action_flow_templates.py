from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / "developer" / "action_flow_templates"
SCHEMA_PATH = LIB_ROOT / "schema" / "action-flow-template.schema.json"
CATALOG_PATH = LIB_ROOT / "catalog" / "template-catalog.json"
SPECS_DIR = LIB_ROOT / "specs"
PLAYBOOKS_DIR = LIB_ROOT / "playbooks"

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "template_id",
    "title",
    "category",
    "risk_level",
    "description",
    "ownership",
    "trigger",
    "inputs",
    "steps",
    "error_policy",
    "observability",
}

ALLOWED_CATEGORIES = {
    "alerts_escalation",
    "sync_propagation",
    "recommendation_human_loop",
    "ai_assisted_triage",
}

ALLOWED_RISK = {"low", "medium", "high"}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_template(path: Path, errors: list[str]) -> dict | None:
    try:
        payload = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        _fail(errors, f"{path.name}: invalid JSON ({exc})")
        return None

    missing = sorted(REQUIRED_TOP_LEVEL - set(payload.keys()))
    if missing:
        _fail(errors, f"{path.name}: missing keys: {', '.join(missing)}")

    template_id = payload.get("template_id")
    if not isinstance(template_id, str) or not template_id:
        _fail(errors, f"{path.name}: template_id must be a non-empty string")

    if payload.get("category") not in ALLOWED_CATEGORIES:
        _fail(errors, f"{path.name}: category must be one of {sorted(ALLOWED_CATEGORIES)}")

    if payload.get("risk_level") not in ALLOWED_RISK:
        _fail(errors, f"{path.name}: risk_level must be one of {sorted(ALLOWED_RISK)}")

    steps = payload.get("steps")
    if not isinstance(steps, list) or len(steps) < 2:
        _fail(errors, f"{path.name}: steps must contain at least two entries")

    return payload


def main() -> int:
    errors: list[str] = []

    if not SCHEMA_PATH.exists():
        _fail(errors, f"Missing schema file: {SCHEMA_PATH}")

    if not CATALOG_PATH.exists():
        _fail(errors, f"Missing catalog file: {CATALOG_PATH}")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    catalog = _load_json(CATALOG_PATH)
    template_ids = catalog.get("templates", [])
    if not isinstance(template_ids, list) or not template_ids:
        _fail(errors, "Catalog templates must be a non-empty list")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    seen_ids: set[str] = set()
    for template_id in template_ids:
        if not isinstance(template_id, str) or not template_id:
            _fail(errors, f"Invalid template id in catalog: {template_id!r}")
            continue

        if template_id in seen_ids:
            _fail(errors, f"Duplicate template id in catalog: {template_id}")
        seen_ids.add(template_id)

        spec_path = SPECS_DIR / f"{template_id}.json"
        playbook_path = PLAYBOOKS_DIR / f"{template_id}.md"

        if not spec_path.exists():
            _fail(errors, f"Missing spec file for {template_id}: {spec_path}")
            continue

        if not playbook_path.exists():
            _fail(errors, f"Missing playbook file for {template_id}: {playbook_path}")

        payload = _validate_template(spec_path, errors)
        if payload is None:
            continue

        if payload.get("template_id") != template_id:
            _fail(
                errors,
                f"{spec_path.name}: template_id mismatch (expected {template_id}, got {payload.get('template_id')})",
            )

    for spec_path in sorted(SPECS_DIR.glob("*.json")):
        try:
            spec = _load_json(spec_path)
            template_id = spec.get("template_id")
        except Exception:  # noqa: BLE001
            continue

        if isinstance(template_id, str) and template_id not in seen_ids:
            _fail(errors, f"Spec is not listed in catalog: {spec_path.name}")

    if errors:
        print("Action-flow template validation failed.")
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print(f"Validated {len(template_ids)} action-flow templates successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
