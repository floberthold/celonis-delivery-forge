# API Contracts

This page defines how to use shared request and response contracts for routes and service boundaries.

## Shared Contract Module

Use [src/foundry/contracts.py](../../src/foundry/contracts.py) for shared DTOs:

- ApiErrorDetail
- ApiErrorResponse
- HealthResponse
- TenancyContext
- MCPToolInvocation
- MCPToolResponse

## Error Contract Usage

Use a stable error payload with three required fields:

- error_code
- message
- request_id

Route pattern:

```python
from fastapi import HTTPException
from foundry.contracts import build_error_detail
from foundry.error_codes import RESOURCE_NOT_FOUND

request_id = "..."
raise HTTPException(
    status_code=404,
    detail=build_error_detail(
        error_code=RESOURCE_NOT_FOUND,
        message="Resource not found",
        request_id=request_id,
    ).model_dump(),
)
```

## Error Code Catalog

Use centralized constants from [src/foundry/error_codes.py](../../src/foundry/error_codes.py).

Guidelines:

1. Reuse an existing constant when semantics already match.
2. Add new constants in `foundry.error_codes` when introducing a new contract-visible error.
3. Keep string values stable after release to avoid breaking client handling.

## Health Response Contract

Use `HealthResponse` for machine-readable health semantics:

- status: one of healthy, degraded, unhealthy
- version: app version string
- timestamp: UTC timestamp
- components: per-component status map

Example:

```python
from datetime import datetime, timezone
from foundry.contracts import HealthResponse

payload = HealthResponse(
    status="healthy",
    version="1.0.0",
    timestamp=datetime.now(timezone.utc),
    components={"api": "healthy", "tool_hub": "degraded"},
)
```

## Migration Notes

When touching legacy routes:

1. Replace ad-hoc error dictionaries with `build_error_detail(...).model_dump()`.
2. Replace inline error code strings with constants from `foundry.error_codes`.
3. Add or update route tests to assert `error_code` and `request_id` fields.
