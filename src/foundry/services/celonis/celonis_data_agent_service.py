from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import httpx

from foundry.integrations.celonis_import import CelonisGateway
from foundry.settings import Settings


@dataclass(frozen=True)
class CelonisDataAgentToolDefinition:
    key: str
    display_name: str
    description: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    read_only: bool = True
    requires_user_token: bool = True
    requires_approved_deployment: bool = False
    capability_group: str = "data_integration"
    source: str = "external_mcp"


class CelonisDataAgentError(ValueError):
    pass


_TOOL_DEFINITIONS: tuple[CelonisDataAgentToolDefinition, ...] = (
    CelonisDataAgentToolDefinition(
        key="celonis_preflight",
        display_name="Tenant Preflight",
        description="Validate the delegated user token and tenant reachability before running other data-agent tools.",
        required_inputs=("user_token",),
        capability_group="governance",
    ),
    CelonisDataAgentToolDefinition(
        key="list_data_models_tool",
        display_name="List Data Models",
        description="List available Celonis data models for the active tenant.",
        required_inputs=("user_token",),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="list_pools_tool",
        display_name="List Data Pools",
        description="List available Celonis data pools for the active tenant.",
        required_inputs=("user_token",),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="list_tables_tool",
        display_name="List Data Model Tables",
        description="List tables and table metadata for a specific data model.",
        required_inputs=("user_token", "data_model_id"),
        optional_inputs=("page", "page_size"),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="list_pool_tables_tool",
        display_name="List Pool Tables",
        description="List tables and table metadata for a specific data pool.",
        required_inputs=("user_token", "pool_id"),
        optional_inputs=("page", "page_size"),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="list_data_model_table_row_counts_tool",
        display_name="List Table Row Counts",
        description="Inspect the latest data-model load metadata and return per-table row counts.",
        required_inputs=("user_token", "pool_id", "data_model_id"),
        optional_inputs=("include_zero",),
        capability_group="analysis",
    ),
    CelonisDataAgentToolDefinition(
        key="query_data_model_sql_tool",
        display_name="Query Data Model SQL",
        description="Run a guarded read-only SQL query against a Celonis data model.",
        required_inputs=("user_token", "data_model_id", "sql"),
        optional_inputs=("limit",),
        capability_group="analysis",
    ),
    CelonisDataAgentToolDefinition(
        key="list_jobs_tool",
        display_name="List Jobs",
        description="List available Celonis Data Integration jobs.",
        required_inputs=("user_token",),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="list_transformations_tool",
        display_name="List Transformations",
        description="List Celonis transformations globally or for a specific pool.",
        required_inputs=("user_token",),
        optional_inputs=("pool_id",),
        capability_group="data_integration",
    ),
    CelonisDataAgentToolDefinition(
        key="get_data_model_load_info_tool",
        display_name="Get Load Info",
        description="Read the latest load-info metadata for a data model inside a pool.",
        required_inputs=("user_token", "pool_id", "data_model_id"),
        capability_group="analysis",
    ),
    CelonisDataAgentToolDefinition(
        key="studio_create_analysis_tool",
        display_name="Create Studio Analysis",
        description="Create a Studio analysis asset inside an approved target package.",
        required_inputs=("user_token", "deployment_request_id", "package_key", "analysis_name", "payload"),
        read_only=False,
        requires_approved_deployment=True,
        capability_group="studio_write",
    ),
    CelonisDataAgentToolDefinition(
        key="studio_set_view_component_tool",
        display_name="Set Studio View Component",
        description="Update a Studio analysis or view asset component inside an approved package.",
        required_inputs=("user_token", "deployment_request_id", "package_key", "asset_id", "payload"),
        optional_inputs=("method",),
        read_only=False,
        requires_approved_deployment=True,
        capability_group="studio_write",
    ),
    CelonisDataAgentToolDefinition(
        key="studio_publish_package_tool",
        display_name="Publish Studio Package",
        description="Publish or activate an approved Studio package after governance checks pass.",
        required_inputs=("user_token", "deployment_request_id", "package_key"),
        optional_inputs=("payload",),
        read_only=False,
        requires_approved_deployment=True,
        capability_group="studio_write",
    ),
)


_TOOL_MAP = {tool.key: tool for tool in _TOOL_DEFINITIONS}

_LIST_FALLBACK_KEYS = (
    "items",
    "results",
    "value",
    "content",
)

_FORBIDDEN_SQL_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "merge",
    "grant",
    "revoke",
    "commit",
    "rollback",
    "execute",
    "exec",
    "call",
}


def _truncate_text(value: str, *, limit: int = 300) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]


def _strip_sql_comments(sql: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    no_line = re.sub(r"--.*?$", "", no_block, flags=re.M)
    return no_line.strip()


def _validate_read_only_sql(sql: str) -> str:
    cleaned = _strip_sql_comments(sql)
    if not cleaned:
        raise CelonisDataAgentError("sql is empty")

    segments = [segment.strip() for segment in cleaned.split(";") if segment.strip()]
    if len(segments) != 1:
        raise CelonisDataAgentError("Only one SQL statement is allowed")

    statement = segments[0]
    lowered = statement.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise CelonisDataAgentError("Only SELECT or WITH queries are allowed")

    tokenized = re.findall(r"[a-zA-Z_]+", lowered)
    blocked = sorted(_FORBIDDEN_SQL_KEYWORDS.intersection(tokenized))
    if blocked:
        raise CelonisDataAgentError(f"Query contains blocked keyword(s): {', '.join(blocked)}")
    return statement


def _extract_items(payload: Any, list_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in (*list_keys, *_LIST_FALLBACK_KEYS):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _request_json(
    settings: Settings,
    *,
    method: str,
    tenant_base_url: str,
    path: str,
    token_override: str,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    gateway = CelonisGateway(settings)
    normalized_base = gateway._normalize_base_url(tenant_base_url)
    normalized_path = gateway._normalize_path(path)
    url = f"{normalized_base}{normalized_path}"
    try:
        with httpx.Client(timeout=settings.celonis_timeout_seconds) as client:
            response = client.request(
                method,
                url,
                headers=gateway._headers(token_override),
                params=params,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise CelonisDataAgentError(
            f"Celonis API timeout for {method} {normalized_path}"
        ) from exc
    except httpx.RequestError as exc:
        raise CelonisDataAgentError(
            f"Celonis API request failed for {method} {normalized_path}: {exc}"
        ) from exc

    if response.status_code >= 400:
        response_preview = _truncate_text(response.text)
        if response.status_code == 429:
            raise CelonisDataAgentError(
                f"Celonis API rate limited ({response.status_code}) for {method} {normalized_path}: {response_preview}"
            )
        if response.status_code >= 500:
            raise CelonisDataAgentError(
                f"Celonis API upstream unavailable ({response.status_code}) for {method} {normalized_path}: {response_preview}"
            )
        raise CelonisDataAgentError(
            f"Celonis API call failed ({response.status_code}) for {method} {normalized_path}: {response_preview}"
        )
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise CelonisDataAgentError(f"Invalid JSON response for {method} {normalized_path}") from exc


def _call_first_collection_endpoint(
    settings: Settings,
    *,
    tenant_base_url: str,
    token_override: str,
    endpoints: tuple[str, ...],
    list_keys: tuple[str, ...],
    params: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    last_error: Exception | None = None
    for endpoint in endpoints:
        try:
            payload = _request_json(
                settings,
                method="GET",
                tenant_base_url=tenant_base_url,
                path=endpoint,
                token_override=token_override,
                params=params,
            )
            return _extract_items(payload, list_keys), endpoint
        except Exception as exc:
            last_error = exc
            continue
    raise CelonisDataAgentError(str(last_error or "No working Celonis endpoint found"))


def _require_string(inputs: dict[str, Any], key: str) -> str:
    value = inputs.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CelonisDataAgentError(f"'{key}' is required")
    return value.strip()


def _optional_positive_int(inputs: dict[str, Any], key: str, *, default: int, minimum: int = 1, maximum: int = 1000) -> int:
    value = inputs.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CelonisDataAgentError(f"'{key}' must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise CelonisDataAgentError(f"'{key}' must be between {minimum} and {maximum}")
    return parsed


def _optional_bool(inputs: dict[str, Any], key: str, *, default: bool) -> bool:
    value = inputs.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise CelonisDataAgentError(f"'{key}' must be a boolean")


def _paginate(rows: list[dict[str, Any]], *, page: int, page_size: int) -> list[dict[str, Any]]:
    start = (page - 1) * page_size
    end = start + page_size
    return rows[start:end]


def _require_dict(inputs: dict[str, Any], key: str) -> dict[str, Any]:
    value = inputs.get(key)
    if not isinstance(value, dict):
        raise CelonisDataAgentError(f"'{key}' must be an object")
    return value


def _request_first_json(
    settings: Settings,
    *,
    method: str,
    tenant_base_url: str,
    token_override: str,
    endpoints: tuple[str, ...],
    payload: dict[str, Any] | None = None,
) -> tuple[Any, str]:
    last_error: Exception | None = None
    for endpoint in endpoints:
        try:
            result = _request_json(
                settings,
                method=method,
                tenant_base_url=tenant_base_url,
                path=endpoint,
                token_override=token_override,
                payload=payload,
            )
            return result, endpoint
        except Exception as exc:
            last_error = exc
            continue
    raise CelonisDataAgentError(str(last_error or "No working Celonis endpoint found"))


def get_data_agent_tool_definition(tool_key: str) -> CelonisDataAgentToolDefinition | None:
    return _TOOL_MAP.get(tool_key)


def invoke_data_agent_tool(
    settings: Settings,
    *,
    tenant_base_url: str,
    token_override: str,
    tool_key: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    if not token_override.strip():
        raise CelonisDataAgentError("A delegated Celonis user token is required")

    if tool_key == "celonis_preflight":
        result = CelonisGateway(settings).preflight(
            tenant_base_url=tenant_base_url,
            service="data-integration",
            token_override=token_override,
        )
        return {
            "ok": result.permission_status == "authorized",
            "service": result.service,
            "probe_path": result.probe_path,
            "probe_url": result.probe_url,
            "has_token": result.has_token,
            "reachable": result.reachable,
            "authenticated": result.authenticated,
            "permission_status": result.permission_status,
            "status_code": result.status_code,
            "error": result.error,
            "response_preview": result.response_preview,
        }

    if tool_key == "list_data_models_tool":
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=("/integration/api/data-models", "/integration/api/v1/data-models", "/process-analytics/api/data-models"),
            list_keys=("dataModels", "data"),
        )
        return {"count": len(items), "items": items, "endpoint": endpoint}

    if tool_key == "list_pools_tool":
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=("/integration/api/pools", "/integration/api/v1/pools"),
            list_keys=("pools", "data"),
        )
        return {"count": len(items), "items": items, "endpoint": endpoint}

    if tool_key == "list_tables_tool":
        data_model_id = _require_string(inputs, "data_model_id")
        page = _optional_positive_int(inputs, "page", default=1)
        page_size = _optional_positive_int(inputs, "page_size", default=100, maximum=1000)
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=(
                f"/integration/api/data-models/{data_model_id}/tables",
                f"/integration/api/v1/data-models/{data_model_id}/tables",
                f"/process-analytics/api/data-models/{data_model_id}/tables",
            ),
            list_keys=("tables", "data"),
            params={"page": page, "pageSize": page_size},
        )
        return {
            "count": len(items),
            "items": items,
            "page": page,
            "page_size": page_size,
            "data_model_id": data_model_id,
            "endpoint": endpoint,
        }

    if tool_key == "list_pool_tables_tool":
        pool_id = _require_string(inputs, "pool_id")
        page = _optional_positive_int(inputs, "page", default=1)
        page_size = _optional_positive_int(inputs, "page_size", default=100, maximum=1000)
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=(f"/integration/api/pools/{pool_id}/tables", f"/integration/api/v1/pools/{pool_id}/tables"),
            list_keys=("tables", "data"),
        )
        paged_items = _paginate(items, page=page, page_size=page_size)
        return {
            "count": len(paged_items),
            "total_count": len(items),
            "items": paged_items,
            "page": page,
            "page_size": page_size,
            "pool_id": pool_id,
            "endpoint": endpoint,
        }

    if tool_key in {"list_data_model_table_row_counts_tool", "get_data_model_load_info_tool"}:
        pool_id = _require_string(inputs, "pool_id")
        data_model_id = _require_string(inputs, "data_model_id")
        payload = _request_json(
            settings,
            method="GET",
            tenant_base_url=tenant_base_url,
            path=f"/integration/api/pools/{pool_id}/data-models/{data_model_id}/load-history/load-info-sync",
            token_override=token_override,
        )
        if tool_key == "get_data_model_load_info_tool":
            return {
                "pool_id": pool_id,
                "data_model_id": data_model_id,
                "payload": payload,
            }

        include_zero = _optional_bool(inputs, "include_zero", default=True)
        load_info = payload.get("loadInfo") if isinstance(payload, dict) else {}
        live_data_model = load_info.get("liveDataModel") if isinstance(load_info, dict) else {}
        table_loads = live_data_model.get("tableLoads") if isinstance(live_data_model, dict) else []
        items: list[dict[str, Any]] = []
        if isinstance(table_loads, list):
            for row in table_loads:
                if not isinstance(row, dict):
                    continue
                row_count_raw = row.get("tableRowCount", 0)
                try:
                    row_count = int(row_count_raw or 0)
                except (TypeError, ValueError):
                    row_count = 0
                if not include_zero and row_count == 0:
                    continue
                items.append(
                    {
                        "table_name": row.get("tableName"),
                        "row_count": row_count,
                        "contains_data": row_count > 0,
                    }
                )
        items.sort(key=lambda item: (item.get("table_name") or "").lower())
        return {
            "pool_id": pool_id,
            "data_model_id": data_model_id,
            "data_model_name": live_data_model.get("dataModelName") if isinstance(live_data_model, dict) else None,
            "last_load": live_data_model.get("lastLoad") if isinstance(live_data_model, dict) else None,
            "count": len(items),
            "non_zero_count": sum(1 for item in items if item["row_count"] > 0),
            "zero_count": sum(1 for item in items if item["row_count"] == 0),
            "items": items,
        }

    if tool_key == "query_data_model_sql_tool":
        data_model_id = _require_string(inputs, "data_model_id")
        sql = _validate_read_only_sql(_require_string(inputs, "sql"))
        limit = _optional_positive_int(inputs, "limit", default=1000, maximum=5000)
        path = settings.celonis_sql_query_path_template.format(data_model_id=data_model_id)
        payload = _request_json(
            settings,
            method="POST",
            tenant_base_url=tenant_base_url,
            path=path,
            token_override=token_override,
            payload={"query": sql, "limit": limit},
        )
        return {
            "data_model_id": data_model_id,
            "limit": limit,
            "result": payload if isinstance(payload, dict) else {"rows": payload},
        }

    if tool_key == "list_jobs_tool":
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=("/integration/api/v1/jobs", "/integration/api/jobs"),
            list_keys=("jobs", "data"),
        )
        return {"count": len(items), "items": items, "endpoint": endpoint}

    if tool_key == "list_transformations_tool":
        pool_id = inputs.get("pool_id")
        if pool_id is not None and (not isinstance(pool_id, str) or not pool_id.strip()):
            raise CelonisDataAgentError("'pool_id' must be a non-empty string when provided")
        normalized_pool_id = pool_id.strip() if isinstance(pool_id, str) else None
        endpoints = (
            f"/integration/api/v1/pools/{normalized_pool_id}/transformations",
            f"/integration/api/pools/{normalized_pool_id}/transformations",
        ) if normalized_pool_id else (
            "/integration/api/v1/transformations",
            "/integration/api/transformations",
        )
        items, endpoint = _call_first_collection_endpoint(
            settings,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=endpoints,
            list_keys=("transformations", "data"),
        )
        result = {"count": len(items), "items": items, "endpoint": endpoint}
        if normalized_pool_id:
            result["pool_id"] = normalized_pool_id
        return result

    if tool_key == "studio_create_analysis_tool":
        package_key = _require_string(inputs, "package_key")
        analysis_name = _require_string(inputs, "analysis_name")
        payload = _require_dict(inputs, "payload")
        request_payload = {
            "name": analysis_name,
            "type": payload.get("type") or "analysis",
            **payload,
        }
        result, endpoint = _request_first_json(
            settings,
            method="POST",
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=(
                f"/package-manager/api/packages/{package_key}/assets",
                f"/studio/api/packages/{package_key}/assets",
            ),
            payload=request_payload,
        )
        return {
            "package_key": package_key,
            "analysis_name": analysis_name,
            "endpoint": endpoint,
            "result": result if isinstance(result, dict) else {"value": result},
        }

    if tool_key == "studio_set_view_component_tool":
        package_key = _require_string(inputs, "package_key")
        asset_id = _require_string(inputs, "asset_id")
        payload = _require_dict(inputs, "payload")
        method = str(inputs.get("method") or "PUT").strip().upper()
        if method not in {"PUT", "PATCH", "POST"}:
            raise CelonisDataAgentError("'method' must be PUT, PATCH, or POST")
        result, endpoint = _request_first_json(
            settings,
            method=method,
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=(
                f"/package-manager/api/packages/{package_key}/assets/{asset_id}",
                f"/studio/api/packages/{package_key}/assets/{asset_id}",
            ),
            payload=payload,
        )
        return {
            "package_key": package_key,
            "asset_id": asset_id,
            "method": method,
            "endpoint": endpoint,
            "result": result if isinstance(result, dict) else {"value": result},
        }

    if tool_key == "studio_publish_package_tool":
        package_key = _require_string(inputs, "package_key")
        payload = inputs.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise CelonisDataAgentError("'payload' must be an object when provided")
        result, endpoint = _request_first_json(
            settings,
            method="POST",
            tenant_base_url=tenant_base_url,
            token_override=token_override,
            endpoints=(
                f"/package-manager/api/packages/{package_key}/activate",
                f"/package-manager/api/packages/{package_key}/publish",
            ),
            payload=payload,
        )
        return {
            "package_key": package_key,
            "endpoint": endpoint,
            "result": result if isinstance(result, dict) else {"value": result},
        }

    raise CelonisDataAgentError(f"Unsupported tool: {tool_key}")


def list_data_agent_tools() -> list[CelonisDataAgentToolDefinition]:
    return list(_TOOL_DEFINITIONS)