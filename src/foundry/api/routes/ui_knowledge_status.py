from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.services.feature_rollout import enabled_domains_for_org
from foundry.services.local_knowledge_control import LocalKnowledgeControlService
from foundry.settings import get_settings

router = APIRouter(tags=["ui"])


def _knowledge_hub_enabled(current_actor: CurrentActor) -> bool:
    settings = get_settings()
    domains = enabled_domains_for_org(settings.ui_rollout_config_path, current_actor.organization.slug)
    return "*" in domains or "knowledge-hub" in domains


@router.get("/local-knowledge-ui/status")
def local_knowledge_run_status(
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    if not _knowledge_hub_enabled(current_actor):
        return JSONResponse(status_code=403, content={"detail": "knowledge-hub domain disabled"})

    controller = LocalKnowledgeControlService(get_settings())
    payload: dict[str, Any] = {
        "run_state": controller.get_run_state(),
        "run_log_tail": controller.get_log_tail(limit=120),
        "recent_changes": controller.list_recent_file_changes(limit=80),
    }
    return JSONResponse(content=payload)
