from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CelonisDataAgentToolDefinition:
    key: str
    display_name: str
    description: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    read_only: bool = True
    requires_user_token: bool = True
    source: str = "external_mcp"


_TOOL_DEFINITIONS: tuple[CelonisDataAgentToolDefinition, ...] = (
    CelonisDataAgentToolDefinition(
        key="celonis_preflight",
        display_name="Tenant Preflight",
        description="Validate the delegated user token and tenant reachability before running other data-agent tools.",
        required_inputs=("user_token",),
    ),
    CelonisDataAgentToolDefinition(
        key="list_data_models_tool",
        display_name="List Data Models",
        description="List available Celonis data models for the active tenant.",
        required_inputs=("user_token",),
    ),
    CelonisDataAgentToolDefinition(
        key="list_pools_tool",
        display_name="List Data Pools",
        description="List available Celonis data pools for the active tenant.",
        required_inputs=("user_token",),
    ),
    CelonisDataAgentToolDefinition(
        key="list_tables_tool",
        display_name="List Data Model Tables",
        description="List tables and table metadata for a specific data model.",
        required_inputs=("user_token", "data_model_id"),
        optional_inputs=("page", "page_size"),
    ),
    CelonisDataAgentToolDefinition(
        key="list_pool_tables_tool",
        display_name="List Pool Tables",
        description="List tables and table metadata for a specific data pool.",
        required_inputs=("user_token", "pool_id"),
        optional_inputs=("page", "page_size"),
    ),
    CelonisDataAgentToolDefinition(
        key="list_data_model_table_row_counts_tool",
        display_name="List Table Row Counts",
        description="Inspect the latest data-model load metadata and return per-table row counts.",
        required_inputs=("user_token", "pool_id", "data_model_id"),
        optional_inputs=("include_zero",),
    ),
    CelonisDataAgentToolDefinition(
        key="query_data_model_sql_tool",
        display_name="Query Data Model SQL",
        description="Run a guarded read-only SQL query against a Celonis data model.",
        required_inputs=("user_token", "data_model_id", "sql"),
        optional_inputs=("limit",),
    ),
)


def list_data_agent_tools() -> list[CelonisDataAgentToolDefinition]:
    return list(_TOOL_DEFINITIONS)