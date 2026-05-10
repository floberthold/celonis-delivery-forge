from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from foundry.schemas import ToolHubCatalogOut, ToolHubCatalogToolOut

router = APIRouter(prefix="/tool-hub", tags=["tool-hub"])


def _catalog_path() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / ".orchestration" / "tool-hub" / "catalog.json"


@router.get("/catalog", response_model=ToolHubCatalogOut)
def get_tool_hub_catalog() -> ToolHubCatalogOut:
    path = _catalog_path()
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Tool hub catalog not found. Run START.ps1 -Mode dry-run or start first.",
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Tool hub catalog is not valid JSON") from exc

    raw_tools = payload.get("tools") if isinstance(payload, dict) else None
    rows = raw_tools if isinstance(raw_tools, list) else []

    tools: list[ToolHubCatalogToolOut] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        tools.append(
            ToolHubCatalogToolOut(
                id=str(row.get("id") or ""),
                display_name=str(row.get("display_name") or ""),
                repo_path=str(row.get("repo_path") or ""),
                absolute_repo_path=str(row.get("absolute_repo_path") or ""),
                domain=str(row.get("domain") or "unassigned"),
                activation_phase=int(row.get("activation_phase") or 1),
                shell=str(row.get("shell") or ""),
                command=None if row.get("command") is None else str(row.get("command")),
                enabled=bool(row.get("enabled", False)),
                startable=bool(row.get("startable", False)),
                source=str(row.get("source") or "registry"),
                notes=str(row.get("notes") or ""),
                health_probe=row.get("health_probe") if isinstance(row.get("health_probe"), dict) else {},
            )
        )

    return ToolHubCatalogOut(
        catalog_exists=True,
        catalog_path=str(path),
        generated_at_utc=str(payload.get("generated_at_utc") or "") if isinstance(payload, dict) else "",
        mode=str(payload.get("mode") or "") if isinstance(payload, dict) else "",
        include_auto_discovered=bool(payload.get("include_auto_discovered", False)) if isinstance(payload, dict) else False,
        tool_count=len(tools),
        tools=tools,
    )
