from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ApiErrorDetail(BaseModel):
    error_code: str
    message: str
    request_id: str


class ApiErrorResponse(BaseModel):
    detail: ApiErrorDetail


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    components: dict[str, str] = Field(default_factory=dict)


class TenancyContext(BaseModel):
    organization_id: UUID
    user_id: UUID
    request_id: str
    enabled_domains: list[str] = Field(default_factory=list)


class MCPToolInvocation(BaseModel):
    tool_id: str
    version: str
    timeout_ms: int = Field(ge=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class MCPToolResponse(BaseModel):
    success: bool
    duration_ms: int = Field(ge=0)
    result: dict[str, Any] | None = None
    error: str | None = None
    fallback: dict[str, Any] | None = None


def build_error_detail(*, error_code: str, message: str, request_id: str) -> ApiErrorDetail:
    return ApiErrorDetail(error_code=error_code, message=message, request_id=request_id)
