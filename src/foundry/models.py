from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Text
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


class OrganizationRole(str, Enum):
    owner = "owner"
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


class KpiStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    deprecated = "deprecated"


class EntityType(str, Enum):
    organization = "organization"
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
    delivery_file = "delivery_file"
    gitlab_repo = "gitlab_repo"
    gitlab_pipeline_run = "gitlab_pipeline_run"
    kpi_definition = "kpi_definition"
    kpi_version = "kpi_version"
    use_case = "use_case"
    use_case_roadmap_item = "use_case_roadmap_item"
    forum_insight = "forum_insight"
    asset_source = "asset_source"
    asset_snapshot = "asset_snapshot"
    ingest_run = "ingest_run"
    ingest_finding = "ingest_finding"
    celonis_snapshot = "celonis_snapshot"
    kpi_book_entry = "kpi_book_entry"
    agent = "agent"
    quest = "quest"
    quest_assignment = "quest_assignment"
    quest_feedback = "quest_feedback"
    task_dependency = "task_dependency"
    celonis_deployment_request = "celonis_deployment_request"


class AssetSourceKind(str, Enum):
    code_drop = "code_drop"
    pullable_repo = "pullable_repo"
    mirrored_repo = "mirrored_repo"
    celonis_marketplace = "celonis_marketplace"


class IngestRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


class IngestFindingSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class UseCaseMaturity(str, Enum):
    idea = "idea"
    pilot = "pilot"
    validated = "validated"
    scaled = "scaled"


class RoadmapItemStatus(str, Enum):
    planned = "planned"
    in_discovery = "in_discovery"
    in_build = "in_build"
    in_review = "in_review"
    released = "released"
    blocked = "blocked"


class ForumInsightStatus(str, Enum):
    discovered = "discovered"
    triaged = "triaged"
    planned = "planned"
    in_progress = "in_progress"
    validated = "validated"
    archived = "archived"


class TodoStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class TodoPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TodoDocumentSource(str, Enum):
    url = "url"
    file = "file"


class TemplateStorageType(str, Enum):
    sharepoint = "sharepoint"
    onedrive = "onedrive"
    uploaded_pptx = "uploaded_pptx"


class TemplateScope(str, Enum):
    global_scope = "global_scope"
    client_scope = "client_scope"


class LibraryType(str, Enum):
    template = "template"
    document = "document"


class FileSource(str, Enum):
    uploaded = "uploaded"
    sharepoint_doc = "sharepoint_doc"
    onedrive_doc = "onedrive_doc"
    external_link = "external_link"


class AgentStatus(str, Enum):
    idle = "idle"
    active = "active"
    paused = "paused"
    offline = "offline"


class QuestStatus(str, Enum):
    draft = "draft"
    suggested = "suggested"
    accepted = "accepted"
    active = "active"
    blocked = "blocked"
    done = "done"
    archived = "archived"


class QuestSource(str, Enum):
    user_authored = "user_authored"
    agent_suggested = "agent_suggested"
    policy_generated = "policy_generated"


class QuestPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class QuestFeedbackType(str, Enum):
    accepted = "accepted"
    edited = "edited"
    replaced = "replaced"
    rejected = "rejected"
    paused = "paused"


class TaskDependencyType(str, Enum):
    blocks = "blocks"


class Client(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    name: str
    tenant_url: str
    sensitivity_level: SensitivityLevel = Field(default=SensitivityLevel.medium)
    salesforce_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Person(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str
    role_global: GlobalRole = Field(default=GlobalRole.member)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Organization(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    slug: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationMembership(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(index=True, foreign_key="organization.id")
    person_id: UUID = Field(index=True, foreign_key="person.id")
    role: OrganizationRole = Field(default=OrganizationRole.member)
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class Project(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    name: str
    client_id: UUID = Field(index=True, foreign_key="client.id")
    status: ProjectStatus = Field(default=ProjectStatus.planned)
    salesforce_url: Optional[str] = None
    celonis_package_url: Optional[str] = None
    celonis_app_url: Optional[str] = None
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
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
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
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    entity_type: EntityType
    entity_id: UUID
    action: str
    actor_id: UUID = Field(index=True, foreign_key="person.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Todo(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    title: str
    description: Optional[str] = None
    long_description_markdown: Optional[str] = Field(default=None, sa_column=Column(Text))
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


class Agent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    role_label: Optional[str] = None
    status: AgentStatus = Field(default=AgentStatus.idle, index=True)
    capability_summary_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    is_system_agent: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentCapability(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(index=True, foreign_key="agent.id")
    skill: str = Field(index=True)
    confidence_score: int = 50
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Quest(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: QuestStatus = Field(default=QuestStatus.draft, index=True)
    source: QuestSource = Field(default=QuestSource.user_authored, index=True)
    priority: QuestPriority = Field(default=QuestPriority.medium, index=True)
    owner_person_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    suggested_by_agent_id: Optional[UUID] = Field(default=None, index=True, foreign_key="agent.id")
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    project_id: Optional[UUID] = Field(default=None, index=True, foreign_key="project.id")
    linked_todo_id: Optional[UUID] = Field(default=None, index=True, foreign_key="todo.id")
    due_at: Optional[datetime] = Field(default=None, index=True)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuestObjective(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quest_id: UUID = Field(index=True, foreign_key="quest.id")
    title: str
    details: Optional[str] = Field(default=None, sa_column=Column(Text))
    sort_order: int = 0
    is_done: bool = Field(default=False, index=True)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuestAssignment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quest_id: UUID = Field(index=True, foreign_key="quest.id")
    agent_id: Optional[UUID] = Field(default=None, index=True, foreign_key="agent.id")
    assignee_person_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    role: Optional[str] = None
    state: str = Field(default="assigned", index=True)
    assigned_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


class QuestFeedback(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quest_id: UUID = Field(index=True, foreign_key="quest.id")
    actor_id: UUID = Field(index=True, foreign_key="person.id")
    feedback_type: QuestFeedbackType = Field(index=True)
    note: Optional[str] = Field(default=None, sa_column=Column(Text))
    metadata_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class TaskDependency(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    blocker_todo_id: UUID = Field(index=True, foreign_key="todo.id")
    dependent_todo_id: UUID = Field(index=True, foreign_key="todo.id")
    dependency_type: TaskDependencyType = Field(default=TaskDependencyType.blocks, index=True)
    note: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class TodoComment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    todo_id: UUID = Field(index=True, foreign_key="todo.id")
    author_id: UUID = Field(index=True, foreign_key="person.id")
    content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TodoTag(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    todo_id: UUID = Field(index=True, foreign_key="todo.id")
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TodoLink(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    todo_id: UUID = Field(index=True, foreign_key="todo.id")
    label: Optional[str] = None
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TodoDocument(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    todo_id: UUID = Field(index=True, foreign_key="todo.id")
    source_type: TodoDocumentSource = Field(default=TodoDocumentSource.url)
    title: str
    url: Optional[str] = None
    storage_path: Optional[str] = None
    original_filename: Optional[str] = None
    uploaded_by: UUID = Field(index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CelonisConnection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    client_id: UUID = Field(index=True, foreign_key="client.id", unique=True)
    tenant_base_url: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CelonisUserToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(index=True, foreign_key="organization.id")
    person_id: UUID = Field(index=True, foreign_key="person.id")
    token_value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CelonisDeploymentStatus(str, Enum):
    draft = "draft"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    cancelled = "cancelled"


class CelonisDeploymentRequest(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(index=True, foreign_key="organization.id")
    project_id: UUID = Field(index=True, foreign_key="project.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    created_by: UUID = Field(index=True, foreign_key="person.id")
    status: CelonisDeploymentStatus = Field(default=CelonisDeploymentStatus.draft, index=True)
    target_space_name: Optional[str] = None
    target_package_key: Optional[str] = None
    target_package_name: Optional[str] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    preflight_run_id: Optional[str] = None
    preflight_passed: bool = False
    permission_diff_acknowledged: bool = False
    permission_diff_acknowledged_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    reviewer_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    reviewer_decision: Optional[str] = None
    reviewer_note: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GitLabRepo(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(index=True, foreign_key="project.id")
    name: str
    repo_path: str
    token_override: Optional[str] = None
    default_branch: str = Field(default="main")
    webhook_secret: Optional[str] = None
    is_active: bool = True
    created_by: UUID = Field(index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GitLabPipelineRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    repo_id: UUID = Field(index=True, foreign_key="gitlabrepo.id")
    pipeline_id: int = Field(index=True)
    ref: str
    status: str = Field(default="pending", index=True)
    triggered_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    web_url: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UseCase(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True)
    summary: str = Field(sa_column=Column(Text, nullable=False))
    problem_statement: Optional[str] = Field(default=None, sa_column=Column(Text))
    industry: Optional[str] = Field(default=None, index=True)
    process_domain: Optional[str] = Field(default=None, index=True)
    owner_person_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    project_id: Optional[UUID] = Field(default=None, index=True, foreign_key="project.id")
    maturity: UseCaseMaturity = Field(default=UseCaseMaturity.idea, index=True)
    tags_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    api_dependencies_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_anonymized_ready: bool = False
    is_client_view_enabled: bool = False
    is_industry_benchmark_eligible: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UseCaseRoadmapItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    initiative: str
    phase: str = Field(index=True)
    owner_person_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    target_month: Optional[str] = Field(default=None, index=True)
    status: RoadmapItemStatus = Field(default=RoadmapItemStatus.planned, index=True)
    percent_complete: int = Field(default=0)
    blockers: Optional[str] = Field(default=None, sa_column=Column(Text))
    last_update_note: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ForumInsight(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    topic: str = Field(index=True)
    source_url: str = Field(index=True)
    thread_title: str
    problem_summary: str = Field(sa_column=Column(Text, nullable=False))
    proposed_action: Optional[str] = Field(default=None, sa_column=Column(Text))
    impact_score: int = 3
    confidence_score: int = 3
    status: ForumInsightStatus = Field(default=ForumInsightStatus.discovered, index=True)
    owner_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    reviewer_id: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    target_week: Optional[str] = Field(default=None, index=True)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_reviewed_at: Optional[datetime] = None
    created_by: UUID = Field(index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TemplateLibrary(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    name: str
    scope: TemplateScope = Field(default=TemplateScope.global_scope)
    library_type: LibraryType = Field(default=LibraryType.template)
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    base_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Template(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
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
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
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


class DeliveryFile(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    file_source: FileSource
    external_url: Optional[str] = None
    library_id: Optional[UUID] = Field(default=None, index=True, foreign_key="templatelibrary.id")
    stored_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    client_id: Optional[UUID] = Field(default=None, index=True, foreign_key="client.id")
    project_id: Optional[UUID] = Field(default=None, index=True, foreign_key="project.id")
    uploaded_by: Optional[UUID] = Field(default=None, index=True, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssetSource(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organization.id")
    name: str = Field(index=True)
    kind: AssetSourceKind = Field(index=True)
    provider: Optional[str] = Field(default=None, index=True)
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AssetSnapshot(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_source_id: UUID = Field(index=True, foreign_key="assetsource.id")
    version_label: str
    source_ref: Optional[str] = None
    manifest_path: Optional[str] = None
    summary_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    received_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class IngestRun(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_source_id: UUID = Field(index=True, foreign_key="assetsource.id")
    asset_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="assetsnapshot.id")
    status: IngestRunStatus = Field(default=IngestRunStatus.queued, index=True)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    triggered_by: UUID = Field(index=True, foreign_key="person.id")
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    metrics_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class IngestFinding(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ingest_run_id: UUID = Field(index=True, foreign_key="ingestrun.id")
    severity: IngestFindingSeverity = Field(default=IngestFindingSeverity.warning, index=True)
    finding_type: str = Field(index=True)
    message: str = Field(sa_column=Column(Text, nullable=False))
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    is_blocking: bool = Field(default=False, index=True)
    metadata_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class KpiDefinition(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(index=True, foreign_key="project.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    name: str
    description: Optional[str] = None
    pql_formula: Optional[str] = None
    data_model: Optional[str] = None
    celonis_url: Optional[str] = None
    asset_identifier: Optional[str] = None
    status: KpiStatus = Field(default=KpiStatus.draft)
    owner_id: Optional[UUID] = Field(default=None, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class KpiVersion(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    kpi_id: UUID = Field(index=True, foreign_key="kpidefinition.id")
    version: int = 1
    pql_formula: Optional[str] = None
    change_note: Optional[str] = None
    author_id: Optional[UUID] = Field(default=None, foreign_key="person.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Celonis Snapshot Engine
# ---------------------------------------------------------------------------

class SnapshotRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class SnapshotChangeType(str, Enum):
    added = "added"
    modified = "modified"
    removed = "removed"
    unchanged = "unchanged"


class CelonisSnapshot(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(index=True, foreign_key="client.id")
    triggered_by: UUID = Field(index=True, foreign_key="person.id")
    status: SnapshotRunStatus = Field(default=SnapshotRunStatus.pending, index=True)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    summary_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class SnapshotPackage(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    package_id: str = Field(index=True)
    name: str
    key: Optional[str] = None
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotTask(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    package_id: Optional[str] = Field(default=None, index=True)
    task_id: str = Field(index=True)
    name: str
    task_type: Optional[str] = None
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    pql_formula: Optional[str] = Field(default=None, sa_column=Column(Text))
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    content_hash: Optional[str] = None
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotDataModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    data_model_id: str = Field(index=True)
    name: str
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotJob(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    job_id: str = Field(index=True)
    name: str
    pool_id: Optional[str] = None
    pool_name: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotKnowledgeModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    km_id: str = Field(index=True)
    name: str
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotSpace(SQLModel, table=True):
    """Celonis Studio space (container for packages and apps)."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    space_id: str = Field(index=True)
    name: str
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotApp(SQLModel, table=True):
    """Celonis App Framework app."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    app_id: str = Field(index=True)
    name: str
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    package_key: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotDataPool(SQLModel, table=True):
    """Celonis Data Integration pool (groups connections and data jobs)."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    pool_id: str = Field(index=True)
    name: str
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SnapshotTransformation(SQLModel, table=True):
    """Celonis Data Integration transformation (SQL/PQL transform inside a pool)."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(index=True, foreign_key="celonissnapshot.id")
    client_id: UUID = Field(index=True, foreign_key="client.id")
    transformation_id: str = Field(index=True)
    name: str
    pool_id: Optional[str] = Field(default=None, index=True)
    pool_name: Optional[str] = None
    change_type: SnapshotChangeType = Field(default=SnapshotChangeType.unchanged)
    raw_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KpiBookEntry(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: UUID = Field(index=True, foreign_key="client.id")
    snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="celonissnapshot.id")
    snapshot_task_id: Optional[UUID] = Field(default=None, index=True, foreign_key="snapshottask.id")
    saved_by: UUID = Field(index=True, foreign_key="person.id")
    name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    pql_formula: Optional[str] = Field(default=None, sa_column=Column(Text))
    package_name: Optional[str] = None
    task_type: Optional[str] = None
    is_shared: bool = Field(default=False, index=True)
    tags_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
