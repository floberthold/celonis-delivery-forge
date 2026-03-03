from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ProjectStatus(str, Enum):
    planned = "planned"
    active = "active"
    closed = "closed"


class SensitivityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class GlobalRole(str, Enum):
    admin = "admin"
    member = "member"


class MembershipRole(str, Enum):
    lead = "lead"
    reviewer = "reviewer"
    contributor = "contributor"


class AssetType(str, Enum):
    data_model = "data_model"
    kpi = "kpi"
    view = "view"
    action_flow = "action_flow"
    extractor = "extractor"
    ml_job = "ml_job"
    other = "other"


class ReviewStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    changes_requested = "changes_requested"
    closed = "closed"


class AssetStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    deprecated = "deprecated"


class DecisionType(str, Enum):
    approve = "approve"
    request_changes = "request_changes"


class ArtifactType(str, Enum):
    pql = "pql"
    sql = "sql"
    json = "json"
    markdown = "markdown"
    other = "other"


class EntityType(str, Enum):
    client = "client"
    project = "project"
    person = "person"
    membership = "membership"
    asset = "asset"
    review = "review"
    todo = "todo"
    celonis_connection = "celonis_connection"
    template = "template"
    template_instantiation = "template_instantiation"


class TodoStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class TodoPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TemplateStorageType(str, Enum):
    sharepoint = "sharepoint"
    onedrive = "onedrive"
    uploaded_pptx = "uploaded_pptx"


class TemplateScope(str, Enum):
    global_scope = "global_scope"
    client_scope = "client_scope"


class Client(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    tenant_url: str
    sensitivity_level: SensitivityLevel = Field(default=SensitivityLevel.medium)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str
    role_global: GlobalRole = Field(default=GlobalRole.member)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Project(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    client_id: UUID = Field(index=True, foreign_key="client.id")
    status: ProjectStatus = Field(default=ProjectStatus.planned)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectMembership(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(index=True, foreign_key="project.id")
    person_id: UUID = Field(index=True, foreign_key="person.id")
    role: MembershipRole = Field(default=MembershipRole.contributor)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None


class Asset(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(index=True, foreign_key="project.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    type: AssetType
    name: str
    asset_identifier: Optional[str] = None
    celonis_url: Optional[str] = None
    status: AssetStatus = Field(default=AssetStatus.draft)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssetMembership(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(index=True, foreign_key="asset.id")
    person_id: UUID = Field(index=True, foreign_key="person.id")
    member_role: MembershipRole = Field(default=MembershipRole.contributor)
    from_ts: datetime = Field(default_factory=datetime.utcnow)
    to_ts: Optional[datetime] = None


class ReviewRequest(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(index=True, foreign_key="asset.id")
    project_id: UUID = Field(index=True, foreign_key="project.id")
    author_id: UUID = Field(index=True, foreign_key="person.id")
    reviewer_id: UUID = Field(index=True, foreign_key="person.id")
    change_summary: str
    status: ReviewStatus = Field(default=ReviewStatus.draft)
    snippet_worthy: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None


class ReviewArtifact(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    review_request_id: UUID = Field(index=True, foreign_key="reviewrequest.id")
    type: ArtifactType = Field(default=ArtifactType.other)
    content: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewComment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    review_request_id: UUID = Field(index=True, foreign_key="reviewrequest.id")
    author_id: UUID = Field(index=True, foreign_key="person.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewDecision(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    review_request_id: UUID = Field(index=True, foreign_key="reviewrequest.id")
    reviewer_id: UUID = Field(index=True, foreign_key="person.id")
    decision: DecisionType
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    entity_type: EntityType
    entity_id: UUID
    action: str
    actor_id: UUID = Field(index=True, foreign_key="person.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Todo(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    description: Optional[str] = None
    status: TodoStatus = Field(default=TodoStatus.open, index=True)
    priority: TodoPriority = Field(default=TodoPriority.medium)
    due_at: Optional[datetime] = Field(default=None, index=True)
    assignee_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    created_by: UUID = Field(index=True, foreign_key="person.id")
    person_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    project_id: Optional[UUID] = Field(default=None, index=True, foreign_key="project.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class CelonisConnection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(index=True, foreign_key="client.id", unique=True)
    tenant_base_url: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TemplateLibrary(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    scope: TemplateScope = Field(default=TemplateScope.global_scope)
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Template(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    library_id: UUID = Field(index=True, foreign_key="templatelibrary.id")
    title: str
    category: str
    description: Optional[str] = None
    storage_type: TemplateStorageType
    storage_url: str
    prefill_schema_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    requires_review: bool = Field(default=True)
    is_active: bool = Field(default=True)
    created_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TemplateInstantiation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(index=True, foreign_key="template.id")
    project_id: UUID = Field(index=True, foreign_key="project.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    author_id: UUID = Field(index=True, foreign_key="person.id")
    reviewer_id: UUID = Field(index=True, foreign_key="person.id")
    generated_url: str
    prefill_data_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    asset_id: Optional[UUID] = Field(default=None, index=True, foreign_key="asset.id")
    review_request_id: Optional[UUID] = Field(default=None, index=True, foreign_key="reviewrequest.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
