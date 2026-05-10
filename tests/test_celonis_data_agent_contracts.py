from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from foundry.services.celonis.celonis_contracts import CelonisDataAgentInvocationContract
from foundry.services.celonis.celonis_data_agent_service import (
    CelonisDataAgentError,
    _request_json,
    get_data_agent_tool_definition,
    invoke_data_agent_tool,
)
from foundry.settings import get_settings


def test_invocation_contract_activity_metadata_contains_core_fields() -> None:
    contract = CelonisDataAgentInvocationContract(
        request_id="req-123",
        organization_id=uuid4(),
        client_id=uuid4(),
        tenant_base_url="https://team.eu-1.celonis.cloud",
        tool_key="query_data_model_sql_tool",
        inputs={"data_model_id": "dm-1", "limit": 10},
        actor_person_id=uuid4(),
        quest_id=uuid4(),
        deployment_request_id=uuid4(),
    )

    metadata = contract.to_activity_metadata(
        input_keys=["data_model_id", "sql", "limit"],
        read_only=True,
        requires_user_token=True,
        requires_approved_deployment=False,
        capability_group="analysis",
    )

    assert metadata["request_id"] == "req-123"
    assert metadata["tool_key"] == "query_data_model_sql_tool"
    assert metadata["input_keys"] == ["data_model_id", "sql", "limit"]
    assert metadata["read_only"] is True
    assert metadata["requires_user_token"] is True
    assert metadata["requires_approved_deployment"] is False
    assert metadata["capability_group"] == "analysis"
    assert metadata["data_model_id"] == "dm-1"
    assert metadata["limit"] == 10
    assert metadata["ok"] is True


def test_tool_definition_marks_write_tool_as_approval_bound() -> None:
    definition = get_data_agent_tool_definition("studio_publish_package_tool")
    assert definition is not None
    assert definition.read_only is False
    assert definition.requires_approved_deployment is True
    assert definition.requires_user_token is True


def test_data_agent_invoke_requires_delegated_token() -> None:
    settings = get_settings()

    with pytest.raises(CelonisDataAgentError, match="delegated Celonis user token"):
        invoke_data_agent_tool(
            settings,
            tenant_base_url="https://team.eu-1.celonis.cloud",
            token_override="",
            tool_key="list_pools_tool",
            inputs={},
        )


def test_query_tool_rejects_non_read_only_sql() -> None:
    settings = get_settings()

    with pytest.raises(CelonisDataAgentError, match="Only SELECT or WITH queries are allowed"):
        invoke_data_agent_tool(
            settings,
            tenant_base_url="https://team.eu-1.celonis.cloud",
            token_override="delegated-token",
            tool_key="query_data_model_sql_tool",
            inputs={
                "data_model_id": "dm-1",
                "sql": "DELETE FROM table_x",
            },
        )


def test_celonis_preflight_maps_gateway_result(monkeypatch) -> None:
    settings = get_settings()

    def _patched_preflight(self, *, tenant_base_url: str, service: str, token_override: str):
        return SimpleNamespace(
            service=service,
            probe_path="/integration/api/pools",
            probe_url=f"{tenant_base_url}/integration/api/pools",
            has_token=True,
            reachable=True,
            authenticated=True,
            permission_status="authorized",
            status_code=200,
            error=None,
            response_preview="{}",
        )

    monkeypatch.setattr("foundry.services.celonis.celonis_data_agent_service.CelonisGateway.preflight", _patched_preflight)

    payload = invoke_data_agent_tool(
        settings,
        tenant_base_url="https://team.eu-1.celonis.cloud",
        token_override="delegated-token",
        tool_key="celonis_preflight",
        inputs={},
    )

    assert payload["ok"] is True
    assert payload["service"] == "data-integration"
    assert payload["permission_status"] == "authorized"
    assert payload["status_code"] == 200


def test_list_pools_tool_falls_back_to_next_endpoint(monkeypatch) -> None:
    settings = get_settings()
    called_paths: list[str] = []

    def _patched_request_json(
        settings,
        *,
        method: str,
        tenant_base_url: str,
        path: str,
        token_override: str,
        params=None,
        payload=None,
    ):
        called_paths.append(path)
        if path.endswith("/integration/api/pools"):
            raise CelonisDataAgentError("timeout")
        return {"pools": [{"id": "pool-1", "name": "Main Pool"}]}

    monkeypatch.setattr("foundry.services.celonis.celonis_data_agent_service._request_json", _patched_request_json)

    payload = invoke_data_agent_tool(
        settings,
        tenant_base_url="https://team.eu-1.celonis.cloud",
        token_override="delegated-token",
        tool_key="list_pools_tool",
        inputs={},
    )

    assert payload["count"] == 1
    assert payload["endpoint"] == "/integration/api/v1/pools"
    assert called_paths == ["/integration/api/pools", "/integration/api/v1/pools"]


def test_list_pools_tool_raises_when_all_endpoints_fail(monkeypatch) -> None:
    settings = get_settings()

    def _always_fail(*args, **kwargs):
        raise CelonisDataAgentError("rate limited")

    monkeypatch.setattr("foundry.services.celonis.celonis_data_agent_service._request_json", _always_fail)

    with pytest.raises(CelonisDataAgentError, match="rate limited"):
        invoke_data_agent_tool(
            settings,
            tenant_base_url="https://team.eu-1.celonis.cloud",
            token_override="delegated-token",
            tool_key="list_pools_tool",
            inputs={},
        )


def test_request_json_maps_timeout_to_celonis_data_agent_error(monkeypatch) -> None:
    settings = get_settings()

    class _TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def request(self, *args, **kwargs):
            raise httpx.ReadTimeout("request timed out")

    monkeypatch.setattr("foundry.services.celonis.celonis_data_agent_service.httpx.Client", _TimeoutClient)

    with pytest.raises(CelonisDataAgentError, match="timeout"):
        _request_json(
            settings,
            method="GET",
            tenant_base_url="https://team.eu-1.celonis.cloud",
            path="/integration/api/pools",
            token_override="delegated-token",
        )


def test_request_json_maps_429_to_rate_limited_error(monkeypatch) -> None:
    settings = get_settings()

    class _Response:
        status_code = 429
        text = "Too many requests"
        content = b'{"error":"rate_limit"}'

        @staticmethod
        def json():
            return {"error": "rate_limit"}

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def request(self, *args, **kwargs):
            return _Response()

    monkeypatch.setattr("foundry.services.celonis.celonis_data_agent_service.httpx.Client", _Client)

    with pytest.raises(CelonisDataAgentError, match="rate limited"):
        _request_json(
            settings,
            method="GET",
            tenant_base_url="https://team.eu-1.celonis.cloud",
            path="/integration/api/pools",
            token_override="delegated-token",
        )
