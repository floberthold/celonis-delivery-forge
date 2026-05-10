from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from foundry.contracts import (
    MCPToolInvocation,
    MCPToolResponse,
    TenancyContext,
    build_error_detail,
    HealthResponse,
)


def test_build_error_detail_contains_required_fields() -> None:
    payload = build_error_detail(
        error_code="TEST_ERROR",
        message="Something failed",
        request_id="req-123",
    )

    assert payload.error_code == "TEST_ERROR"
    assert payload.message == "Something failed"
    assert payload.request_id == "req-123"


def test_health_response_supports_component_map() -> None:
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        components={"api": "healthy", "tool_hub": "degraded"},
    )

    assert response.status == "healthy"
    assert response.components["api"] == "healthy"


def test_tenancy_context_requires_org_and_user() -> None:
    context = TenancyContext(
        organization_id=uuid4(),
        user_id=uuid4(),
        request_id="req-456",
        enabled_domains=["core-platform", "celonis-agent"],
    )

    assert context.request_id == "req-456"
    assert "core-platform" in context.enabled_domains


def test_mcp_contracts_capture_invocation_and_response() -> None:
    invocation = MCPToolInvocation(
        tool_id="celonis_preflight",
        version="v1",
        timeout_ms=5000,
        parameters={"tenant": "team-a"},
    )
    response = MCPToolResponse(
        success=True,
        duration_ms=120,
        result={"ok": True},
    )

    assert invocation.tool_id == "celonis_preflight"
    assert invocation.timeout_ms == 5000
    assert response.success is True
    assert response.duration_ms == 120
