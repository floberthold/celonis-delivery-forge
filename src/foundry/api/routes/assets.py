from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.models import Asset, AssetMembership, EntityType, MembershipRole, Person
from foundry.schemas import AssetCreate
from foundry.services.activity_log import log_created

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=Asset)
def create_asset(
    payload: AssetCreate,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    asset = Asset(**payload.model_dump())
    session.add(asset)
    session.commit()
    session.refresh(asset)
    log_created(
        session,
        entity_type=EntityType.asset,
        entity_id=asset.id,
        actor_id=current_person.id,
        metadata={"project_id": str(asset.project_id), "client_id": str(asset.client_id)},
    )
    return asset


@router.get("/", response_model=list[Asset])
def list_assets(session: Session = Depends(get_session)):
    return list(session.exec(select(Asset)).all())


@router.post("/{asset_id}/membership", response_model=AssetMembership)
def add_asset_member(
    asset_id: UUID,
    person_id: UUID,
    member_role: MembershipRole,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    membership = AssetMembership(
        asset_id=asset_id,
        person_id=person_id,
        member_role=member_role,
        from_ts=datetime.utcnow(),
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    log_created(
        session,
        entity_type=EntityType.membership,
        entity_id=membership.id,
        actor_id=current_person.id,
        metadata={"asset_id": str(asset_id), "person_id": str(person_id), "role": member_role.value},
    )
    return membership


@router.get("/matrix")
def asset_matrix(session: Session = Depends(get_session)):
    rows = session.exec(
        select(AssetMembership, Asset).where(AssetMembership.asset_id == Asset.id)
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
