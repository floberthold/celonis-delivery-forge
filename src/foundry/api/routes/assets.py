from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from foundry.api.deps import CurrentActor, get_current_actor_with_org
from foundry.db import get_session
from foundry.models import Asset, AssetMembership, Client, EntityType, MembershipRole, Project
from foundry.schemas import AssetCreate
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=Asset)
def create_asset(
    payload: AssetCreate,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    project = session.get(Project, payload.project_id)
    if not project or project.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Project not found")

    client = session.get(Client, payload.client_id)
    if not client or client.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Client not found")

    if project.client_id != client.id:
        raise HTTPException(status_code=400, detail="Project does not belong to the specified client")

    asset = Asset(
        organization_id=current_actor.organization.id,
        **payload.model_dump(),
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    log_created(
        session,
        entity_type=EntityType.asset,
        entity_id=asset.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"project_id": str(asset.project_id), "client_id": str(asset.client_id)},
    )
    return asset


@router.get("/", response_model=list[Asset])
def list_assets(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    stmt = select(Asset).where(Asset.organization_id == current_actor.organization.id)
    return list(session.exec(stmt).all())


@router.post("/{asset_id}/membership", response_model=AssetMembership)
def add_asset_member(
    asset_id: UUID,
    person_id: UUID,
    member_role: MembershipRole,
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    asset = session.get(Asset, asset_id)
    if not asset or asset.organization_id != current_actor.organization.id:
        raise HTTPException(status_code=404, detail="Asset not found")

    membership = AssetMembership(
        asset_id=asset_id,
        person_id=person_id,
        member_role=member_role,
        from_ts=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    log_created(
        session,
        entity_type=EntityType.membership,
        entity_id=membership.id,
        actor_id=current_actor.person.id,
        organization_id=current_actor.organization.id,
        metadata={"asset_id": str(asset_id), "person_id": str(person_id), "role": member_role.value},
    )
    return membership


@router.get("/matrix")
def asset_matrix(
    session: Session = Depends(get_session),
    current_actor: CurrentActor = Depends(get_current_actor_with_org),
):
    rows = session.exec(
        select(AssetMembership, Asset).where(
            AssetMembership.asset_id == Asset.id,
            Asset.organization_id == current_actor.organization.id,
        )
    ).all()
    return [
        {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "asset_type": asset.type,
            "member_person_id": membership.person_id,
            "member_role": membership.member_role,
            "from_ts": membership.from_ts,
            "to_ts": membership.to_ts,
        }
        for membership, asset in rows
    ]

