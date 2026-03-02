from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from foundry.db import get_session
from foundry.models import Asset, AssetMembership, MembershipRole
from foundry.schemas import AssetCreate

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=Asset)
def create_asset(payload: AssetCreate, session: Session = Depends(get_session)):
    asset = Asset(**payload.model_dump())
    session.add(asset)
    session.commit()
    session.refresh(asset)
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
