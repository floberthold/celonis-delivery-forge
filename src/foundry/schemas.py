from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from foundry.models import (
    ArtifactType,
    AssetStatus,
    AssetType,
    DecisionType,
    MembershipRole,
    ProjectStatus,
    ReviewStatus,
    SensitivityLevel,
)


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class ClientCreate(BaseModel):
    name: str
    tenant_url: str
    sensitivity_level: SensitivityLevel = SensitivityLevel.medium


class ProjectCreate(BaseModel):
    name: str
    client_id: UUID
    status: ProjectStatus = ProjectStatus.planned


class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus


class ProjectAssign(BaseModel):
    person_id: UUID
    role: MembershipRole = MembershipRole.contributor


class AssetCreate(BaseModel):
    project_id: UUID
    client_id: UUID
    type: AssetType
    name: str
    asset_identifier: Optional[str] = None
    celonis_url: Optional[str] = None


class AssetStatusUpdate(BaseModel):
    status: AssetStatus


class ReviewRequestCreate(BaseModel):
    asset_id: UUID
    project_id: UUID
    author_id: UUID
    reviewer_id: UUID
    change_summary: str


class ReviewDecisionCreate(BaseModel):
    review_id: UUID
    reviewer_id: UUID
    decision: DecisionType
    note: Optional[str] = None
    snippet_worthy: bool = False


class ReviewCommentCreate(BaseModel):
    review_id: UUID
    author_id: UUID
    content: str


class ReviewArtifactCreate(BaseModel):
    review_id: UUID
    type: ArtifactType = ArtifactType.other
    content: str


class ReviewRequestOut(BaseModel):
    id: UUID
    asset_id: UUID
    project_id: UUID
    author_id: UUID
    reviewer_id: UUID
    change_summary: str
    status: ReviewStatus
    snippet_worthy: bool
    created_at: datetime
    submitted_at: Optional[datetime]
    decision_at: Optional[datetime]

    class Config:
        from_attributes = True
