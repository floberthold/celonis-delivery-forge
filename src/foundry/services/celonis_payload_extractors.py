"""Utilities to enrich Celonis payloads with normalized extraction metadata.

This module reuses the extraction concepts from the external pyCelonis-tools
scripts while keeping runtime dependencies lightweight (no pandas/pycelonis).
"""

from __future__ import annotations

import json
import re
from typing import Any

# Matches quoted and unquoted table.column expressions in PQL snippets.
_PQL_COLUMN_PATTERNS = (
    re.compile(r'"([^"\\]+)"\s*\.\s*"([^"\\]+)"'),
    re.compile(r"\b([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\b"),
)

_PQL_HINT_KEYS = (
    "pql",
    "query",
    "formula",
    "formulaQuery",
    "eventLog",
)


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _find_component_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    direct_keys = ("components", "viewComponents", "nodes")
    for key in direct_keys:
        rows = _safe_list(payload.get(key))
        candidates = [row for row in rows if isinstance(row, dict) and row.get("type")]
        if candidates:
            return candidates

    stack: list[Any] = [payload]
    discovered: list[dict[str, Any]] = []
    while stack and len(discovered) < 300:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("type") and (node.get("settings") is not None or node.get("dataSources") is not None):
                discovered.append(node)
            for value in node.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    stack.append(item)
    return discovered


def _extract_view_component_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for component in _find_component_candidates(payload):
        component_id = str(component.get("id") or component.get("key") or "")
        component_type = str(component.get("type") or "unknown")
        settings = _safe_dict(component.get("settings"))

        data_sources = _safe_list(settings.get("dataSources"))
        for source in data_sources:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("id") or "")
            source_name = str(source.get("displayName") or source.get("name") or source_id)
            for attribute in _safe_list(source.get("attributes")):
                if not isinstance(attribute, dict):
                    continue
                rows.append(
                    {
                        "view_component_id": component_id,
                        "view_component_type": component_type,
                        "data_source_id": source_id,
                        "data_source_name": source_name,
                        "attribute_id": str(attribute.get("id") or ""),
                        "attribute_name": str(attribute.get("displayName") or attribute.get("name") or ""),
                        "attribute_pql": str(attribute.get("pql") or ""),
                    }
                )

        event_logs = _safe_list(settings.get("eventLogs"))
        for event_log in event_logs:
            if not isinstance(event_log, dict):
                continue
            event_ref = str(event_log.get("eventLog") or event_log.get("id") or "")
            rows.append(
                {
                    "view_component_id": component_id,
                    "view_component_type": component_type,
                    "data_source_id": "eventLogs",
                    "data_source_name": "eventLogs",
                    "attribute_id": str(event_log.get("id") or event_ref),
                    "attribute_name": event_ref,
                    "attribute_pql": event_ref,
                }
            )

    return rows


def _scan_for_pql_snippets(payload: Any, *, max_items: int = 500) -> list[str]:
    snippets: list[str] = []
    stack: list[Any] = [payload]

    while stack and len(snippets) < max_items:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    stack.append(value)
                    continue
                if isinstance(value, str):
                    key_lower = key.lower()
                    if key_lower in _PQL_HINT_KEYS or key_lower.endswith("pql") or key_lower.endswith("query"):
                        snippet = value.strip()
                        if snippet:
                            snippets.append(snippet)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    return snippets


def _extract_tables_and_columns(snippets: list[str]) -> tuple[list[str], list[str]]:
    tables: set[str] = set()
    columns: set[str] = set()

    for snippet in snippets:
        for pattern in _PQL_COLUMN_PATTERNS:
            for match in pattern.finditer(snippet):
                if len(match.groups()) != 2:
                    continue
                table = match.group(1).strip()
                column = match.group(2).strip()
                if not table or not column:
                    continue
                tables.add(table)
                columns.add(f"{table}.{column}")

    return sorted(tables), sorted(columns)


def _extract_km_content(payload: dict[str, Any]) -> str:
    serialized = payload.get("serialized_content")
    if isinstance(serialized, str) and serialized.strip():
        return serialized

    content = payload.get("serializedContent")
    if isinstance(content, str) and content.strip():
        return content

    nested = _safe_dict(payload.get("content"))
    serialized_nested = nested.get("serialized_content") or nested.get("serializedContent")
    if isinstance(serialized_nested, str) and serialized_nested.strip():
        return serialized_nested

    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def enrich_task_payload(task_payload: dict[str, Any], *, task_type: str | None = None) -> dict[str, Any]:
    """Attach normalized extraction metadata to a package asset/task payload."""
    payload = dict(task_payload)
    existing = _safe_dict(payload.get("_forge_extract"))

    view_rows = _extract_view_component_rows(payload)
    snippets = _scan_for_pql_snippets(payload)
    snippets.extend(
        row.get("attribute_pql", "") for row in view_rows if row.get("attribute_pql")
    )
    snippets = sorted({snippet for snippet in snippets if isinstance(snippet, str) and snippet.strip()})
    tables, columns = _extract_tables_and_columns(snippets)

    metadata = {
        **existing,
        "source": "pycelonis_tools_port",
        "task_type": task_type or payload.get("type") or payload.get("assetType") or "unknown",
        "view_component_rows": view_rows,
        "pql_snippets": snippets[:200],
        "pql_tables": tables,
        "pql_columns": columns,
    }
    payload["_forge_extract"] = metadata
    return payload


def enrich_knowledge_model_payload(km_payload: dict[str, Any]) -> dict[str, Any]:
    """Attach normalized extraction metadata to a knowledge model payload."""
    payload = dict(km_payload)
    existing = _safe_dict(payload.get("_forge_extract"))

    km_content = _extract_km_content(payload)
    snippets = _scan_for_pql_snippets(payload)
    snippets.append(km_content)
    snippets = sorted({snippet for snippet in snippets if isinstance(snippet, str) and snippet.strip()})
    tables, columns = _extract_tables_and_columns(snippets)

    metadata = {
        **existing,
        "source": "pycelonis_tools_port",
        "pql_tables": tables,
        "pql_columns": columns,
        "pql_snippets": snippets[:200],
    }
    payload["_forge_extract"] = metadata
    return payload
