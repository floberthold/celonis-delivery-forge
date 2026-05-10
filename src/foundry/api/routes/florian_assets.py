from pathlib import Path
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.services.delivery.florian_script_seed import register_florian_script_assets
from foundry.settings import get_settings

router = APIRouter(prefix="/florian-assets", tags=["florian-assets"])


class FlorianScriptProjectOut(BaseModel):
    folder: str
    project_id: str
    source_id: str
    assets_registered: int
    scripts_discovered: int


class FlorianScriptRegisterOut(BaseModel):
    organization_id: str
    client_id: str
    project_count: int
    asset_count: int
    projects: list[FlorianScriptProjectOut]


@router.post("/register", response_model=FlorianScriptRegisterOut)
def register_florian_assets(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    configured_root = getattr(settings, "florian_shared_dir", "") or os.getenv(
        "FORGE_FLORIAN_SHARED_DIR",
        "./external resources/Code by Florian",
    )
    root_dir = Path(configured_root)
    try:
        result = register_florian_script_assets(
            session,
            actor_id=current_actor.person.id,
            root_dir=root_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FlorianScriptRegisterOut(
        organization_id=str(result.organization_id),
        client_id=str(result.client_id),
        project_count=len(result.project_results),
        asset_count=result.asset_count,
        projects=[
            FlorianScriptProjectOut(
                folder=row.folder,
                project_id=str(row.project_id),
                source_id=str(row.source_id),
                assets_registered=row.assets_registered,
                scripts_discovered=row.scripts_discovered,
            )
            for row in result.project_results
        ],
    )