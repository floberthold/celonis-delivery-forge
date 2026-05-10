from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = REPO_ROOT / "config" / "service_domain_mapping.json"
SERVICES_DIR = REPO_ROOT / "src" / "foundry" / "services"


def _load_mapping() -> dict:
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


def test_service_domain_mapping_lists_all_service_modules_once() -> None:
    mapping = _load_mapping()
    domains = mapping.get("domains", {})

    mapped_files: list[str] = []
    for files in domains.values():
        mapped_files.extend(files)

    expected_files = sorted(
        {
            path.name
            for path in SERVICES_DIR.rglob("*.py")
            if path.name != "__init__.py"
        }
    )

    assert sorted(mapped_files) == expected_files
    assert len(mapped_files) == len(set(mapped_files))


def test_service_domain_mapping_declares_expected_domains() -> None:
    mapping = _load_mapping()
    domains = mapping.get("domains", {})

    assert set(domains.keys()) == {
        "platform",
        "delivery",
        "celonis",
        "knowledge",
        "integrations",
        "orchestration",
        "shared",
    }
