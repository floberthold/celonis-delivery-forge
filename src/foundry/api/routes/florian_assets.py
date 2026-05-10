from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.schemas import FlorianScriptRegisterOut, FlorianScriptProjectOut
from foundry.services.delivery.florian_script_seed import register_florian_script_assets
from foundry.settings import get_settings

router = APIRouter(prefix="/florian-assets", tags=["florian-assets"])


@router.post("/register", response_model=FlorianScriptRegisterOut)
def register_florian_assets(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    settings = get_settings()
    root_dir = Path(settings.florian_shared_dir)
    try:
        result = register_florian_script_assets(
            session,
            actor_id=current_actor.person.id,
            root_dir=root_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FlorianScriptRegisterOut(
        organization_id=result.organization_id,
        client_id=result.client_id,
        project_count=len(result.project_results),
        asset_count=result.asset_count,
        projects=[
            FlorianScriptProjectOut(
                folder=row.folder,
                project_id=row.project_id,
                source_id=row.source_id,
                assets_registered=row.assets_registered,
                scripts_discovered=row.scripts_discovered,
            )
            for row in result.project_results
        ],
    )