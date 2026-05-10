from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class CelonisDataAgentInvocationContract:
    """Internal contract boundary between API route orchestration and extractor execution."""

    request_id: str
    organization_id: UUID
    client_id: UUID
    tenant_base_url: str
    tool_key: str
    inputs: dict[str, Any]
    actor_person_id: UUID
    quest_id: UUID | None = None
    deployment_request_id: UUID | None = None

    def to_activity_metadata(
        self,
        *,
        input_keys: list[str],
        read_only: bool,
        requires_user_token: bool,
        requires_approved_deployment: bool,
        capability_group: str,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "request_id": self.request_id,
            "organization_id": str(self.organization_id),
            "client_id": str(self.client_id),
            "tool_key": self.tool_key,
            "quest_id": str(self.quest_id) if self.quest_id else None,
            "deployment_request_id": str(self.deployment_request_id) if self.deployment_request_id else None,
            "input_keys": input_keys,
            "requires_user_token": requires_user_token,
            "requires_approved_deployment": requires_approved_deployment,
            "capability_group": capability_group,
            "read_only": read_only,
            "ok": True,
        }
        if "data_model_id" in self.inputs:
            metadata["data_model_id"] = self.inputs.get("data_model_id")
        if "pool_id" in self.inputs:
            metadata["pool_id"] = self.inputs.get("pool_id")
        if "limit" in self.inputs:
            metadata["limit"] = self.inputs.get("limit")
        return metadata
