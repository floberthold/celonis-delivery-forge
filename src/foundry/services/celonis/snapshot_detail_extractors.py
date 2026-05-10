"""Family-specific asset detail extraction with dependency crawl.

This module provides deep extraction of asset families (ANALYSIS/VIEW, KM, ACTION_FLOW, etc.)
by attempting to fetch detailed information from tenant-specific endpoints and crawling
references and dependencies.
"""

from __future__ import annotations

import json
from typing import Any

from foundry.integrations.celonis_import import CelonisGateway


_FAMILY_ENDPOINTS = {
    "ANALYSIS": (
        "/studio/api/analyses/{id}",
        "/studio/api/packages/{package_id}/analyses/{id}",
    ),
    "VIEW": (
        "/studio/api/views/{id}",
        "/studio/api/packages/{package_id}/views/{id}",
    ),
    "KNOWLEDGE_MODEL": (
        "/knowledge-model/api/knowledge-models/{id}",
        "/semantic-layer/api/knowledge-models/{id}",
    ),
    "ACTION_FLOW": (
        "/action-engine/api/action-flows/{id}",
        "/studio/api/packages/{package_id}/action-flows/{id}",
    ),
    "ANNOTATION_BUILDER": (
        "/studio/api/annotation-builders/{id}",
    ),
    "KPI": (
        "/studio/api/kpis/{id}",
        "/studio/api/packages/{package_id}/kpis/{id}",
    ),
}


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _extract_references_from_content(content: dict[str, Any]) -> dict[str, list[str]]:
    """Scan asset content for references to other assets/tables/columns."""
    refs: dict[str, list[str]] = {
        "assets": [],
        "tables": [],
        "columns": [],
        "views": [],
        "kpis": [],
        "pools": [],
    }
    
    def scan(node: Any, depth: int = 0) -> None:
        if depth > 20:  # Prevent deep recursion
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_lower = key.lower()
                if isinstance(value, str):
                    # Look for ID-like references
                    if key_lower in {"id", "assetid", "asset_id", "viewid", "view_id", "kpiid", "kpi_id"}:
                        refs["assets"].append(value.strip())
                    elif key_lower in {"table", "tablename", "table_name", "sourcetable"}:
                        refs["tables"].append(value.strip())
                    elif key_lower in {"column", "columnname", "column_name", "field"}:
                        refs["columns"].append(value.strip())
                elif isinstance(value, (dict, list)):
                    scan(value, depth + 1)
        elif isinstance(node, list):
            for item in node:
                scan(item, depth + 1)
    
    scan(content)
    # Deduplicate and filter empty values
    for key in refs:
        refs[key] = sorted(set(v for v in refs[key] if v.strip()))
    return refs


def fetch_asset_detail_by_family(
    gw: CelonisGateway,
    base_url: str,
    asset_type: str,
    asset_id: str,
    *,
    package_id: str | None = None,
    token_override: str | None = None,
) -> dict[str, Any]:
    """Fetch detailed information for an asset based on its family/type.
    
    Returns a dict with:
    - detail: The fetched detail payload (or empty dict if not found)
    - source_endpoint: Which endpoint returned data
    - references: Extracted references (assets, tables, columns, etc.)
    - error: Error message if fetch failed
    """
    result: dict[str, Any] = {
        "detail": {},
        "source_endpoint": None,
        "references": {
            "assets": [],
            "tables": [],
            "columns": [],
            "views": [],
            "kpis": [],
            "pools": [],
        },
        "error": None,
    }
    
    endpoints = _FAMILY_ENDPOINTS.get(asset_type, ())
    if not endpoints:
        result["error"] = f"No detail endpoints defined for family {asset_type}"
        return result
    
    # Try each endpoint, substituting package_id and asset_id
    for endpoint_template in endpoints:
        endpoint = endpoint_template.replace("{id}", asset_id)
        if "{package_id}" in endpoint:
            if not package_id:
                continue
            endpoint = endpoint.replace("{package_id}", package_id)
        
        extract_kwargs: dict[str, Any] = {}
        if token_override:
            extract_kwargs["token_override"] = token_override
        
        try:
            api_result = gw.extract_full(
                tenant_base_url=base_url,
                source_path=endpoint,
                **extract_kwargs,
            )
            
            if api_result.ok and api_result.body:
                try:
                    payload = json.loads(api_result.body)
                    if isinstance(payload, dict):
                        result["detail"] = payload
                        result["source_endpoint"] = endpoint
                        result["references"] = _extract_references_from_content(payload)
                        return result
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as e:
            result["error"] = str(e)
            continue
    
    if not result["detail"]:
        result["error"] = f"Could not fetch detail from {len(endpoints)} endpoint(s)"
    
    return result


def crawl_asset_dependencies(
    gw: CelonisGateway,
    base_url: str,
    seed_refs: list[str],
    *,
    token_override: str | None = None,
    max_depth: int = 2,
    max_nodes: int = 30,
) -> list[dict[str, Any]]:
    """Crawl asset dependencies starting from a set of reference IDs.
    
    Attempts to fetch detail for each referenced ID and extract further references,
    building a dependency graph up to max_depth levels.
    """
    visited: set[str] = set()
    dependencies: list[dict[str, Any]] = []
    queue: list[tuple[str, int]] = [(ref, 0) for ref in seed_refs if ref]
    
    while queue and len(dependencies) < max_nodes:
        ref_id, depth = queue.pop(0)
        if ref_id in visited or depth >= max_depth:
            continue
        visited.add(ref_id)
        
        # Try to fetch detail for this reference
        detail = fetch_asset_detail_by_family(
            gw,
            base_url,
            "ANALYSIS",  # Generic fallback; could be smarter
            ref_id,
            token_override=token_override,
        )
        
        if detail.get("detail"):
            dependencies.append({
                "id": ref_id,
                "type": "unknown",
                "detail": detail["detail"],
                "references": detail["references"],
                "source_endpoint": detail["source_endpoint"],
                "depth": depth,
            })
            
            # Add new references to queue
            for nested_ref in detail["references"].get("assets", []):
                if nested_ref not in visited:
                    queue.append((nested_ref, depth + 1))
    
    return dependencies
