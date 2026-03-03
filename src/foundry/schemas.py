from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from foundry.models import (
    ArtifactType,
    AssetStatus,
    AssetType,
    DecisionType,
    MembershipRole,
    ProjectStatus,
    ReviewStatus,
    SensitivityLevel,
    TodoPriority,
    TodoStatus,
    TemplateScope,
    TemplateStorageType,
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


class TemplateLibraryCreate(BaseModel):
    name: str
    scope: TemplateScope = TemplateScope.global_scope
    client_id: Optional[UUID] = None


class TemplateCreate(BaseModel):
    library_id: UUID
    title: str
    category: str
    description: Optional[str] = None
    storage_type: TemplateStorageType
    storage_url: str
    prefill_schema_json: dict = Field(default_factory=dict)
    requires_review: bool = True
    is_active: bool = True
    created_by: UUID


class TemplateInstantiateCreate(BaseModel):
    project_id: UUID
    client_id: UUID
    author_id: UUID
    reviewer_id: UUID


class TemplateOut(BaseModel):
    id: UUID
    library_id: UUID
    title: str
    category: str
    description: Optional[str]
    storage_type: TemplateStorageType
    storage_url: str
    prefill_schema_json: dict
    requires_review: bool
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateInstantiationOut(BaseModel):
    id: UUID
    template_id: UUID
    project_id: UUID
    client_id: UUID
    author_id: UUID
    reviewer_id: UUID
    generated_url: str
    prefill_data_json: dict
    asset_id: Optional[UUID]
    review_request_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


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


class CelonisConnectionUpsert(BaseModel):
    client_id: UUID
    tenant_base_url: str
    is_active: bool = True


class CelonisConnectionOut(BaseModel):
    id: UUID
    client_id: UUID
    tenant_base_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CelonisExtractRequest(BaseModel):
    client_id: UUID
    source_path: str = "/process-mining/api/teams"


class CelonisImportRequest(BaseModel):
    client_id: UUID
    target_path: str = "/process-mining/api/teams"
    payload: dict = Field(default_factory=dict)


class CelonisActionResult(BaseModel):
    client_id: UUID
    action: str
    url: str
    status_code: int
    ok: bool
    response_preview: str


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.medium
    due_at: Optional[datetime] = None
    assignee_id: Optional[UUID] = None
    created_by: UUID
    person_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_at: Optional[datetime] = None
    assignee_id: Optional[UUID] = None


class TodoOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: TodoStatus
    priority: TodoPriority
    due_at: Optional[datetime]
    assignee_id: Optional[UUID]
    created_by: UUID
    person_id: Optional[UUID]
    client_id: Optional[UUID]
    project_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
