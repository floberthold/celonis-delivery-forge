from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from foundry.models import (
    ArtifactType,
    AssetSourceKind,
    AssetStatus,
    AssetType,
    DecisionType,
    FileSource,
    ForumInsightStatus,
    IngestFindingSeverity,
    IngestRunStatus,
    KpiStatus,
    LibraryType,
    MembershipRole,
    OrganizationRole,
    ProjectStatus,
    ReviewStatus,
    RoadmapItemStatus,
    QuestFeedbackType,
    QuestPriority,
    QuestSource,
    QuestStatus,
    SensitivityLevel,
    SnapshotChangeType,
    SnapshotRunStatus,
    TodoPriority,
    TodoStatus,
    UseCaseMaturity,
    TemplateScope,
    TemplateStorageType,
)


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationMembershipOut(BaseModel):
    id: UUID
    organization_id: UUID
    person_id: UUID
    role: OrganizationRole
    joined_at: datetime

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    name: str
    tenant_url: str
    sensitivity_level: SensitivityLevel = SensitivityLevel.medium
    salesforce_url: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    client_id: UUID
    status: ProjectStatus = ProjectStatus.planned
    salesforce_url: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus


class ProjectAssign(BaseModel):
    person_id: UUID
    role: MembershipRole = MembershipRole.contributor


class TemplateLibraryCreate(BaseModel):
    name: str
    scope: TemplateScope = TemplateScope.global_scope
    library_type: LibraryType = LibraryType.template
    client_id: Optional[UUID] = None
    base_url: Optional[str] = None


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


class DeliveryFileLinkCreate(BaseModel):
    name: str
    description: Optional[str] = None
    file_source: FileSource
    external_url: Optional[str] = None
    library_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class DeliveryFileUploadCreate(BaseModel):
    name: str
    description: Optional[str] = None
    library_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


class DeliveryFileOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    file_source: FileSource
    external_url: Optional[str]
    library_id: Optional[UUID]
    stored_filename: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    client_id: Optional[UUID]
    project_id: Optional[UUID]
    uploaded_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class FileViewerUrlResponse(BaseModel):
    viewer_url: Optional[str] = None
    viewer_type: Optional[str] = None
    download_url: str


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


class AssetSourceCreate(BaseModel):
    organization_id: Optional[UUID] = None
    name: str
    kind: AssetSourceKind
    provider: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class AssetSourceUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[AssetSourceKind] = None
    provider: Optional[str] = None
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class AssetSourceOut(BaseModel):
    id: UUID
    organization_id: Optional[UUID]
    name: str
    kind: AssetSourceKind
    provider: Optional[str]
    repo_url: Optional[str]
    default_branch: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetSnapshotCreate(BaseModel):
    version_label: str
    source_ref: Optional[str] = None
    manifest_path: Optional[str] = None
    summary_json: dict = Field(default_factory=dict)


class AssetSnapshotOut(BaseModel):
    id: UUID
    asset_source_id: UUID
    version_label: str
    source_ref: Optional[str]
    manifest_path: Optional[str]
    summary_json: dict
    received_at: datetime

    class Config:
        from_attributes = True


class IngestRunCreate(BaseModel):
    asset_source_id: UUID
    asset_snapshot_id: Optional[UUID] = None
    status: IngestRunStatus = IngestRunStatus.queued
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    notes: Optional[str] = None
    metrics_json: dict = Field(default_factory=dict)


class IngestRunUpdate(BaseModel):
    status: Optional[IngestRunStatus] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    notes: Optional[str] = None
    metrics_json: Optional[dict] = None


class IngestRunOut(BaseModel):
    id: UUID
    asset_source_id: UUID
    asset_snapshot_id: Optional[UUID]
    status: IngestRunStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    triggered_by: UUID
    notes: Optional[str]
    metrics_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class IngestFindingCreate(BaseModel):
    severity: IngestFindingSeverity = IngestFindingSeverity.warning
    finding_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    is_blocking: bool = False
    metadata_json: dict = Field(default_factory=dict)


class IngestFindingOut(BaseModel):
    id: UUID
    ingest_run_id: UUID
    severity: IngestFindingSeverity
    finding_type: str
    message: str
    file_path: Optional[str]
    line_number: Optional[int]
    is_blocking: bool
    metadata_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class CodeDropIngestRequest(BaseModel):
    asset_source_id: UUID
    drop_path: str
    version_label: Optional[str] = None
    source_ref: Optional[str] = None
    notes: Optional[str] = None


class RepoSyncIngestRequest(BaseModel):
    asset_source_id: UUID
    local_repo_path: str
    branch: Optional[str] = None
    tag: Optional[str] = None
    commit_sha: Optional[str] = None
    version_label: Optional[str] = None
    notes: Optional[str] = None


class CodeDropIngestResult(BaseModel):
    snapshot: AssetSnapshotOut
    run: IngestRunOut
    findings: list[IngestFindingOut]


class CelonisPreflightResult(BaseModel):
    client_id: UUID
    service: str
    probe_path: str
    probe_url: str
    has_token: bool
    request_attempted: bool
    reachable: bool
    authenticated: bool
    permission_status: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_preview: str = ""


class CelonisPreflightBatchResult(BaseModel):
    client_id: UUID
    run_id: str
    timestamp: datetime
    total: int
    authorized_count: int
    issue_count: int
    results: list[CelonisPreflightResult]


class CelonisPreflightHistoryItem(BaseModel):
    timestamp: datetime
    actor_id: UUID
    service: str
    probe_path: str
    probe_url: str
    has_token: bool
    reachable: bool
    authenticated: bool
    permission_status: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    run_id: Optional[str] = None


class GitLabRepoCreate(BaseModel):
    project_id: UUID
    name: str
    repo_path: str
    token_override: Optional[str] = None
    default_branch: str = "main"
    webhook_secret: Optional[str] = None


class GitLabRepoUpdate(BaseModel):
    name: Optional[str] = None
    repo_path: Optional[str] = None
    token_override: Optional[str] = None
    default_branch: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None


class GitLabTriggerRequest(BaseModel):
    ref: Optional[str] = None
    variables: dict = Field(default_factory=dict)


class GitLabRepoOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    repo_path: str
    token_override: Optional[str]
    default_branch: str
    webhook_secret: Optional[str]
    is_active: bool
    created_by: UUID
    created_at: datetime


class GitLabPipelineRunOut(BaseModel):
    id: UUID
    repo_id: UUID
    pipeline_id: int
    ref: str
    status: str
    triggered_by: Optional[UUID]
    triggered_at: datetime
    web_url: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class UseCaseCreate(BaseModel):
    title: str
    summary: str
    problem_statement: Optional[str] = None
    industry: Optional[str] = None
    process_domain: Optional[str] = None
    owner_person_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    maturity: UseCaseMaturity = UseCaseMaturity.idea
    tags_json: list[str] = Field(default_factory=list)
    api_dependencies_json: list[str] = Field(default_factory=list)
    is_anonymized_ready: bool = False
    is_client_view_enabled: bool = False
    is_industry_benchmark_eligible: bool = False


class UseCaseUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    problem_statement: Optional[str] = None
    industry: Optional[str] = None
    process_domain: Optional[str] = None
    owner_person_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    maturity: Optional[UseCaseMaturity] = None
    tags_json: Optional[list[str]] = None
    api_dependencies_json: Optional[list[str]] = None
    is_anonymized_ready: Optional[bool] = None
    is_client_view_enabled: Optional[bool] = None
    is_industry_benchmark_eligible: Optional[bool] = None


class UseCaseOut(BaseModel):
    id: UUID
    title: str
    summary: str
    problem_statement: Optional[str]
    industry: Optional[str]
    process_domain: Optional[str]
    owner_person_id: Optional[UUID]
    client_id: Optional[UUID]
    project_id: Optional[UUID]
    maturity: UseCaseMaturity
    tags_json: list[str]
    api_dependencies_json: list[str]
    is_anonymized_ready: bool
    is_client_view_enabled: bool
    is_industry_benchmark_eligible: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UseCaseViewOut(BaseModel):
    id: UUID
    title: str
    summary: str
    problem_statement: Optional[str]
    industry: Optional[str]
    process_domain: Optional[str]
    maturity: UseCaseMaturity
    tags_json: list[str]
    api_dependencies_json: list[str]
    owner_person_id: Optional[UUID]
    client_id: Optional[UUID]
    project_id: Optional[UUID]
    view_mode: Literal["internal", "anonymized", "client", "industry_benchmark"]
    created_at: datetime
    updated_at: datetime


class UseCaseIndustryBenchmarkBucketOut(BaseModel):
    industry: str
    process_domain: str
    maturity: UseCaseMaturity
    use_case_count: int


class UseCaseIndustryBenchmarkSummaryOut(BaseModel):
    total_use_cases: int
    bucket_count: int
    buckets: list[UseCaseIndustryBenchmarkBucketOut]
    top_tags: list[str]
    top_api_dependencies: list[str]


class UseCaseRoadmapItemCreate(BaseModel):
    initiative: str
    phase: str
    owner_person_id: Optional[UUID] = None
    target_month: Optional[str] = None
    status: RoadmapItemStatus = RoadmapItemStatus.planned
    percent_complete: int = 0
    blockers: Optional[str] = None
    last_update_note: Optional[str] = None


class UseCaseRoadmapItemUpdate(BaseModel):
    initiative: Optional[str] = None
    phase: Optional[str] = None
    owner_person_id: Optional[UUID] = None
    target_month: Optional[str] = None
    status: Optional[RoadmapItemStatus] = None
    percent_complete: Optional[int] = None
    blockers: Optional[str] = None
    last_update_note: Optional[str] = None


class UseCaseRoadmapItemOut(BaseModel):
    id: UUID
    initiative: str
    phase: str
    owner_person_id: Optional[UUID]
    target_month: Optional[str]
    status: RoadmapItemStatus
    percent_complete: int
    blockers: Optional[str]
    last_update_note: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    long_description_markdown: Optional[str] = None
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
    long_description_markdown: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_at: Optional[datetime] = None
    assignee_id: Optional[UUID] = None


class TodoOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    long_description_markdown: Optional[str]
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


class QuestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: QuestStatus = QuestStatus.suggested
    source: QuestSource = QuestSource.user_authored
    priority: QuestPriority = QuestPriority.medium
    owner_person_id: Optional[UUID] = None
    suggested_by_agent_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    linked_todo_id: Optional[UUID] = None
    due_at: Optional[datetime] = None


class QuestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[QuestStatus] = None
    priority: Optional[QuestPriority] = None
    owner_person_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    due_at: Optional[datetime] = None


class QuestReprioritize(BaseModel):
    priority: QuestPriority


class QuestReplace(BaseModel):
    title: str
    description: Optional[str] = None
    priority: QuestPriority = QuestPriority.medium


class QuestOut(BaseModel):
    id: UUID
    organization_id: Optional[UUID]
    title: str
    description: Optional[str]
    status: QuestStatus
    source: QuestSource
    priority: QuestPriority
    owner_person_id: Optional[UUID]
    suggested_by_agent_id: Optional[UUID]
    client_id: Optional[UUID]
    project_id: Optional[UUID]
    linked_todo_id: Optional[UUID]
    due_at: Optional[datetime]
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestFeedbackCreate(BaseModel):
    feedback_type: QuestFeedbackType
    note: Optional[str] = None
    metadata_json: dict = Field(default_factory=dict)


class QuestObjectiveCreate(BaseModel):
    title: str
    details: Optional[str] = None
    sort_order: Optional[int] = None


class QuestObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    sort_order: Optional[int] = None
    is_done: Optional[bool] = None


class QuestObjectiveOut(BaseModel):
    id: UUID
    quest_id: UUID
    title: str
    details: Optional[str]
    sort_order: int
    is_done: bool
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestAssignmentCreate(BaseModel):
    agent_id: Optional[UUID] = None
    assignee_person_id: Optional[UUID] = None
    role: Optional[str] = None
    state: str = "assigned"


class QuestAssignmentUpdate(BaseModel):
    role: Optional[str] = None
    state: Optional[str] = None


class QuestAssignmentOut(BaseModel):
    id: UUID
    quest_id: UUID
    agent_id: Optional[UUID]
    assignee_person_id: Optional[UUID]
    role: Optional[str]
    state: str
    assigned_by: Optional[UUID]
    assigned_at: datetime

    class Config:
        from_attributes = True


class ForumInsightCreate(BaseModel):
    topic: str
    source_url: str
    thread_title: str
    problem_summary: str
    proposed_action: Optional[str] = None
    impact_score: int = Field(default=3, ge=1, le=5)
    confidence_score: int = Field(default=3, ge=1, le=5)
    owner_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    target_week: Optional[str] = None
    created_by: UUID


class ForumInsightUpdate(BaseModel):
    status: Optional[ForumInsightStatus] = None
    topic: Optional[str] = None
    thread_title: Optional[str] = None
    problem_summary: Optional[str] = None
    proposed_action: Optional[str] = None
    impact_score: Optional[int] = Field(default=None, ge=1, le=5)
    confidence_score: Optional[int] = Field(default=None, ge=1, le=5)
    owner_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    target_week: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    actor_id: UUID


class ForumInsightOut(BaseModel):
    id: UUID
    topic: str
    source_url: str
    thread_title: str
    problem_summary: str
    proposed_action: Optional[str]
    impact_score: int
    confidence_score: int
    status: ForumInsightStatus
    owner_id: Optional[UUID]
    reviewer_id: Optional[UUID]
    target_week: Optional[str]
    first_seen_at: datetime
    last_reviewed_at: Optional[datetime]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KpiCreate(BaseModel):
    project_id: UUID
    client_id: UUID
    name: str
    description: Optional[str] = None
    pql_formula: Optional[str] = None
    data_model: Optional[str] = None
    celonis_url: Optional[str] = None
    asset_identifier: Optional[str] = None
    owner_id: Optional[UUID] = None


class KpiUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pql_formula: Optional[str] = None
    data_model: Optional[str] = None
    celonis_url: Optional[str] = None
    asset_identifier: Optional[str] = None
    owner_id: Optional[UUID] = None


class KpiStatusUpdate(BaseModel):
    status: KpiStatus


class KpiVersionCreate(BaseModel):
    pql_formula: str
    change_note: Optional[str] = None


class KpiOut(BaseModel):
    id: UUID
    project_id: UUID
    client_id: UUID
    name: str
    description: Optional[str]
    pql_formula: Optional[str]
    data_model: Optional[str]
    celonis_url: Optional[str]
    asset_identifier: Optional[str]
    status: KpiStatus
    owner_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Celonis Snapshot Engine schemas
# ---------------------------------------------------------------------------

class CelonisSnapshotTriggerRequest(BaseModel):
    client_id: UUID


class CelonisSnapshotOut(BaseModel):
    id: UUID
    client_id: UUID
    triggered_by: UUID
    status: SnapshotRunStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    summary_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotPackageOut(BaseModel):
    id: UUID
    snapshot_id: UUID
    client_id: UUID
    package_id: str
    name: str
    key: Optional[str]
    space_id: Optional[str]
    space_name: Optional[str]
    change_type: SnapshotChangeType
    raw_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotTaskOut(BaseModel):
    id: UUID
    snapshot_id: UUID
    client_id: UUID
    package_id: Optional[str]
    task_id: str
    name: str
    task_type: Optional[str]
    description: Optional[str]
    pql_formula: Optional[str]
    change_type: SnapshotChangeType
    content_hash: Optional[str]
    raw_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotDataModelOut(BaseModel):
    id: UUID
    snapshot_id: UUID
    client_id: UUID
    data_model_id: str
    name: str
    space_id: Optional[str]
    space_name: Optional[str]
    change_type: SnapshotChangeType
    raw_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotJobOut(BaseModel):
    id: UUID
    snapshot_id: UUID
    client_id: UUID
    job_id: str
    name: str
    pool_id: Optional[str]
    pool_name: Optional[str]
    change_type: SnapshotChangeType
    raw_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotKnowledgeModelOut(BaseModel):
    id: UUID
    snapshot_id: UUID
    client_id: UUID
    km_id: str
    name: str
    space_id: Optional[str]
    space_name: Optional[str]
    change_type: SnapshotChangeType
    raw_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class KpiBookEntryCreate(BaseModel):
    client_id: UUID
    snapshot_id: Optional[UUID] = None
    snapshot_task_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    pql_formula: Optional[str] = None
    package_name: Optional[str] = None
    task_type: Optional[str] = None
    is_shared: bool = False
    tags_json: list[str] = Field(default_factory=list)


class KpiBookEntryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pql_formula: Optional[str] = None
    package_name: Optional[str] = None
    task_type: Optional[str] = None
    is_shared: Optional[bool] = None
    tags_json: Optional[list[str]] = None


class KpiBookEntryOut(BaseModel):
    id: UUID
    client_id: UUID
    snapshot_id: Optional[UUID]
    snapshot_task_id: Optional[UUID]
    saved_by: UUID
    name: str
    description: Optional[str]
    pql_formula: Optional[str]
    package_name: Optional[str]
    task_type: Optional[str]
    is_shared: bool
    tags_json: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SnapshotExportOut(BaseModel):
    snapshot_id: UUID
    export_dir: str
    bundle_path: str
    docs_path: str
    generated_at: datetime
    asset_counts: dict
    delta_counts: dict | None = None
    relationship_graph: dict | None = None


class SnapshotReplayPlanStepOut(BaseModel):
    order: int
    action: str
    asset_type: str
    asset_id: str | None = None
    name: str | None = None
    reason: str | None = None


class SnapshotReplayPlanOut(BaseModel):
    snapshot_id: UUID
    previous_snapshot_id: UUID | None = None
    generated_at: datetime
    dry_run: bool
    summary: dict
    steps: list[SnapshotReplayPlanStepOut]
