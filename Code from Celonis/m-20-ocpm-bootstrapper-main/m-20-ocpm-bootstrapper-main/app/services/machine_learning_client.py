import logging
import typing
import uuid
from abc import ABC
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr
from python_core_internal_client import AsyncClient, PythonCoreBaseEnum, PythonCoreBaseModel, PythonCoreDatetime

logger = logging.getLogger("python_core_internal_client.machine_learning")

JsonNode = Any


class ExecutionPattern(PythonCoreBaseEnum):
    HOURLY = "HOURLY"
    X_HOURLY = "X_HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class ImageType(PythonCoreBaseEnum):
    JUPYTER = "JUPYTER"
    VSCODE = "VSCODE"
    STREAMLIT = "STREAMLIT"


class JobExecutionSource(PythonCoreBaseEnum):
    API = "API"
    KNOWLEDGE_MODEL = "KNOWLEDGE_MODEL"
    DATA_MODEL_RELOAD = "DATA_MODEL_RELOAD"
    SKILL_UPDATE = "SKILL_UPDATE"


class JobExecutionStatus(PythonCoreBaseEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class JobExecutionStatusTransport(PythonCoreBaseEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class LogLevel(PythonCoreBaseEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MonthPattern(PythonCoreBaseEnum):
    SPECIFIC_DAY = "SPECIFIC_DAY"
    LAST_DAY = "LAST_DAY"


class NotebookExecutionSource(PythonCoreBaseEnum):
    SCHEDULING = "SCHEDULING"
    API = "API"
    KNOWLEDGE_MODEL = "KNOWLEDGE_MODEL"
    DATA_MODEL_RELOAD = "DATA_MODEL_RELOAD"
    SKILL_UPDATE = "SKILL_UPDATE"


class NotebookExecutionStatus(PythonCoreBaseEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    NOTEBOOK_ERROR = "NOTEBOOK_ERROR"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELED = "CANCELED"
    RESOURCES_ERROR = "RESOURCES_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class TimeUnitTransport(PythonCoreBaseEnum):
    MINUTES = "MINUTES"
    HOURS = "HOURS"


class ApplicationKeyTransport(PythonCoreBaseModel):
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    last_used_at: Optional["PythonCoreDatetime"] = Field(None, alias="lastUsedAt")
    name: Optional["str"] = Field(None, alias="name")
    original_id: Optional["str"] = Field(None, alias="originalId")
    team_role: Optional["int"] = Field(None, alias="teamRole")


class ExceptionReference(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")
    reference: Optional["str"] = Field(None, alias="reference")
    short_message: Optional["str"] = Field(None, alias="shortMessage")


class FrontendHandledBackendError(PythonCoreBaseModel):
    error_information: Optional["Any"] = Field(None, alias="errorInformation")
    frontend_error_key: Optional["str"] = Field(None, alias="frontendErrorKey")


class ImageTransport(PythonCoreBaseModel):
    home_path: Optional["str"] = Field(None, alias="homePath")
    id: Optional["str"] = Field(None, alias="id")
    image_key: Optional["str"] = Field(None, alias="imageKey")
    image_type: Optional["ImageType"] = Field(None, alias="imageType")
    image_url: Optional["str"] = Field(None, alias="imageUrl")
    name: Optional["str"] = Field(None, alias="name")
    visible_in_dropdown: Optional["bool"] = Field(None, alias="visibleInDropdown")


class JobConfigTransport(PythonCoreBaseModel):
    application_key_id: Optional["str"] = Field(None, alias="applicationKeyId")
    id: Optional["str"] = Field(None, alias="id")


class JobExecution(PythonCoreBaseModel):
    completed: Optional["PythonCoreDatetime"] = Field(None, alias="completed")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    id: Optional["str"] = Field(None, alias="id")
    image: Optional["str"] = Field(None, alias="image")
    input: Optional["str"] = Field(None, alias="input")
    job_execution_source: Optional["JobExecutionSource"] = Field(None, alias="jobExecutionSource")
    job_execution_source_id: Optional["str"] = Field(None, alias="jobExecutionSourceId")
    job_id: Optional["str"] = Field(None, alias="jobId")
    optional_tenant_id: Optional["str"] = Field(None, alias="optionalTenantId")
    started: Optional["PythonCoreDatetime"] = Field(None, alias="started")
    status: Optional["JobExecutionStatus"] = Field(None, alias="status")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    timeout: Optional["int"] = Field(None, alias="timeout")


class JobExecutionGroup(PythonCoreBaseModel):
    job_name: Optional["str"] = Field(None, alias="jobName")
    last_job_execution_id: Optional["str"] = Field(None, alias="lastJobExecutionId")
    last_job_execution_started_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastJobExecutionStartedDate")
    last_job_execution_status: Optional["JobExecutionStatus"] = Field(None, alias="lastJobExecutionStatus")


class JobExecutionTransport(PythonCoreBaseModel):
    completed: Optional["PythonCoreDatetime"] = Field(None, alias="completed")
    error_message: Optional["str"] = Field(None, alias="errorMessage")
    id: Optional["str"] = Field(None, alias="id")
    job_execution_source: Optional["str"] = Field(None, alias="jobExecutionSource")
    job_id: Optional["str"] = Field(None, alias="jobId")
    params: Optional["JsonNode"] = Field(None, alias="params")
    started: Optional["PythonCoreDatetime"] = Field(None, alias="started")
    status: Optional["JobExecutionStatusTransport"] = Field(None, alias="status")


class NotebookAccessInformationTransport(PythonCoreBaseModel):
    app_key: Optional["str"] = Field(None, alias="appKey")
    cpu_cores_limit: Optional["str"] = Field(None, alias="cpuCoresLimit")
    disk_usage_limit: Optional["str"] = Field(None, alias="diskUsageLimit")
    exec_commands: Optional["List[Optional[str]]"] = Field(None, alias="execCommands")
    gpu_cores_limit: Optional["str"] = Field(None, alias="gpuCoresLimit")
    image_type: Optional["str"] = Field(None, alias="imageType")
    image_url: Optional["str"] = Field(None, alias="imageUrl")
    instance_type: Optional["str"] = Field(None, alias="instanceType")
    kubernetes: Optional["bool"] = Field(None, alias="kubernetes")
    machine_id: Optional["str"] = Field(None, alias="machineId")
    memory_limit: Optional["str"] = Field(None, alias="memoryLimit")
    migration: Optional["bool"] = Field(None, alias="migration")
    public_address: Optional["str"] = Field(None, alias="publicAddress")
    puppet_id: Optional["str"] = Field(None, alias="puppetId")
    token: Optional["str"] = Field(None, alias="token")
    volume_driver: Optional["str"] = Field(None, alias="volumeDriver")
    with_plan: Optional["bool"] = Field(None, alias="withPlan")


class NotebookExecutionLogTransport(PythonCoreBaseModel):
    log_level: Optional["str"] = Field(None, alias="logLevel")
    message: Optional["str"] = Field(None, alias="message")
    notebook_execution_id: Optional["str"] = Field(None, alias="notebookExecutionId")
    timestamp: Optional["PythonCoreDatetime"] = Field(None, alias="timestamp")


class NotebookExecutionRequestApiModel(PythonCoreBaseModel):
    execution_file_name: Optional["str"] = Field(None, alias="executionFileName")
    notebook_id: Optional["str"] = Field(None, alias="notebookId")
    params: Optional["JsonNode"] = Field(None, alias="params")


class NotebookRequestApiModel(PythonCoreBaseModel):
    agreement: Optional["bool"] = Field(None, alias="agreement")
    image_id: Optional["str"] = Field(None, alias="imageId")
    name: Optional["str"] = Field(None, alias="name")
    notebook_resources: Optional["NotebookResourcesTransport"] = Field(None, alias="notebookResources")


class NotebookResourcesRequestApiModel(PythonCoreBaseModel):
    cpu: Optional["int"] = Field(None, alias="cpu")
    gpu: Optional["int"] = Field(None, alias="gpu")
    memory: Optional["int"] = Field(None, alias="memory")
    storage: Optional["int"] = Field(None, alias="storage")


class NotebookResourcesTransport(PythonCoreBaseModel):
    cpu: Optional["int"] = Field(None, alias="cpu")
    gpu: Optional["int"] = Field(None, alias="gpu")
    memory: Optional["int"] = Field(None, alias="memory")
    storage: Optional["int"] = Field(None, alias="storage")


class NotebookTransport(PythonCoreBaseModel):
    agreement: Optional["bool"] = Field(None, alias="agreement")
    app_key: Optional["str"] = Field(None, alias="appKey")
    available_storage_in_mb: Optional["int"] = Field(None, alias="availableStorageInMb")
    home_path: Optional["str"] = Field(None, alias="homePath")
    id: Optional["str"] = Field(None, alias="id")
    image_id: Optional["str"] = Field(None, alias="imageId")
    image_key: Optional["str"] = Field(None, alias="imageKey")
    image_type: Optional["ImageType"] = Field(None, alias="imageType")
    last_access_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastAccessDate")
    log_retention_days: Optional["int"] = Field(None, alias="logRetentionDays")
    machine_id: Optional["str"] = Field(None, alias="machineId")
    memory_size_id: Optional["str"] = Field(None, alias="memorySizeId")
    mlflow_id: Optional["str"] = Field(None, alias="mlflowId")
    name: Optional["str"] = Field(None, alias="name")
    notebook_resources: Optional["NotebookResourcesTransport"] = Field(None, alias="notebookResources")
    object_id: Optional["str"] = Field(None, alias="objectId")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    productive: Optional["bool"] = Field(None, alias="productive")
    status: Optional["str"] = Field(None, alias="status")
    stopped: Optional["bool"] = Field(None, alias="stopped")
    url: Optional["str"] = Field(None, alias="url")
    version_id: Optional["str"] = Field(None, alias="versionId")
    workspace_id: Optional["str"] = Field(None, alias="workspaceId")


class NotebookTreeItem(PythonCoreBaseModel):
    children: Optional["List[Optional[NotebookTreeItem]]"] = Field(None, alias="children")
    content: Optional["Any"] = Field(None, alias="content")
    directory: Optional["bool"] = Field(None, alias="directory")
    name: Optional["str"] = Field(None, alias="name")
    notebook: Optional["bool"] = Field(None, alias="notebook")
    path: Optional["str"] = Field(None, alias="path")
    type_: Optional["str"] = Field(None, alias="type")


class NotebookVersionTransport(PythonCoreBaseModel):
    created_date: Optional["PythonCoreDatetime"] = Field(None, alias="createdDate")
    id: Optional["str"] = Field(None, alias="id")
    image_id: Optional["str"] = Field(None, alias="imageId")
    image_key: Optional["str"] = Field(None, alias="imageKey")
    latest: Optional["bool"] = Field(None, alias="latest")
    release_notes: Optional["str"] = Field(None, alias="releaseNotes")
    version_code: Optional["str"] = Field(None, alias="versionCode")
    warning: Optional["str"] = Field(None, alias="warning")
    warning_code: Optional["str"] = Field(None, alias="warningCode")


class PageJobExecutionTransport(PythonCoreBaseModel):
    content: Optional["List[Optional[JobExecutionTransport]]"] = Field(None, alias="content")
    empty: Optional["bool"] = Field(None, alias="empty")
    first: Optional["bool"] = Field(None, alias="first")
    last: Optional["bool"] = Field(None, alias="last")
    page_number: Optional["int"] = Field(None, alias="pageNumber")
    page_size: Optional["int"] = Field(None, alias="pageSize")
    total_count: Optional["int"] = Field(None, alias="totalCount")
    total_pages: Optional["int"] = Field(None, alias="totalPages")


class SchedulingConfig(PythonCoreBaseModel):
    custom_cron: Optional["str"] = Field(None, alias="customCron")
    day: Optional["int"] = Field(None, alias="day")
    enabled: Optional["bool"] = Field(None, alias="enabled")
    every_x_hours: Optional["int"] = Field(None, alias="everyXHours")
    execution_pattern: Optional["ExecutionPattern"] = Field(None, alias="executionPattern")
    last_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionDate")
    minute: Optional["int"] = Field(None, alias="minute")
    month_pattern: Optional["MonthPattern"] = Field(None, alias="monthPattern")
    next_execution_date: Optional["PythonCoreDatetime"] = Field(None, alias="nextExecutionDate")
    time: Optional["str"] = Field(None, alias="time")
    timezone_id: Optional["str"] = Field(None, alias="timezoneId")
    week_days: Optional["List[Optional[int]]"] = Field(None, alias="weekDays")


class SchedulingRequestApiModel(PythonCoreBaseModel):
    execute_file: Optional["str"] = Field(None, alias="executeFile")
    name: Optional["str"] = Field(None, alias="name")
    notebook_id: Optional["str"] = Field(None, alias="notebookId")
    scheduling_config: Optional["SchedulingConfig"] = Field(None, alias="schedulingConfig")


class SchedulingTransport(PythonCoreBaseModel):
    execute_file: Optional["str"] = Field(None, alias="executeFile")
    id: Optional["str"] = Field(None, alias="id")
    last_notebook_execution_id: Optional["str"] = Field(None, alias="lastNotebookExecutionId")
    last_notebook_execution_status: Optional["NotebookExecutionStatus"] = Field(
        None, alias="lastNotebookExecutionStatus"
    )
    max_retries: Optional["int"] = Field(None, alias="maxRetries")
    name: Optional["str"] = Field(None, alias="name")
    notebook_id: Optional["str"] = Field(None, alias="notebookId")
    notebook_name: Optional["str"] = Field(None, alias="notebookName")
    notebook_stopped: Optional["bool"] = Field(None, alias="notebookStopped")
    object_id: Optional["str"] = Field(None, alias="objectId")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    scheduling_config: Optional["SchedulingConfig"] = Field(None, alias="schedulingConfig")
    time_unit: Optional["TimeUnitTransport"] = Field(None, alias="timeUnit")
    timeout: Optional["int"] = Field(None, alias="timeout")


class TriggeredExecutionGroupTransport(PythonCoreBaseModel):
    execution_file_name: Optional["str"] = Field(None, alias="executionFileName")
    id: Optional["str"] = Field(None, alias="id")
    last_execution_id: Optional["str"] = Field(None, alias="lastExecutionId")
    last_execution_started_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastExecutionStartedDate")
    last_execution_status: Optional["NotebookExecutionStatus"] = Field(None, alias="lastExecutionStatus")
    notebook_id: Optional["str"] = Field(None, alias="notebookId")
    notebook_name: Optional["str"] = Field(None, alias="notebookName")


ApplicationKeyTransport.model_rebuild()
ExceptionReference.model_rebuild()
FrontendHandledBackendError.model_rebuild()
ImageTransport.model_rebuild()
JobConfigTransport.model_rebuild()
JobExecution.model_rebuild()
JobExecutionGroup.model_rebuild()
JobExecutionTransport.model_rebuild()
NotebookAccessInformationTransport.model_rebuild()
NotebookExecutionLogTransport.model_rebuild()
NotebookExecutionRequestApiModel.model_rebuild()
NotebookRequestApiModel.model_rebuild()
NotebookResourcesRequestApiModel.model_rebuild()
NotebookResourcesTransport.model_rebuild()
NotebookTransport.model_rebuild()
NotebookTreeItem.model_rebuild()
NotebookVersionTransport.model_rebuild()
PageJobExecutionTransport.model_rebuild()
SchedulingConfig.model_rebuild()
SchedulingRequestApiModel.model_rebuild()
SchedulingTransport.model_rebuild()
TriggeredExecutionGroupTransport.model_rebuild()


class MachineLearningClientBase(ABC):
    client: AsyncClient

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.client = AsyncClient(base_url=base_url, **kwargs)

    async def post_api_executions(self, request_body: NotebookExecutionRequestApiModel, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/executions", request_body=request_body, **kwargs)

    async def get_api_executions_triggered_groups(
        self, **kwargs: Any
    ) -> List[Optional[TriggeredExecutionGroupTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/executions/triggered-groups",
            parse_json=True,
            type_=List[Optional[TriggeredExecutionGroupTransport]],
            **kwargs,
        )

    async def get_api_executions_triggered_groups_id(self, id: str, **kwargs: Any) -> TriggeredExecutionGroupTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/executions/triggered-groups/{id}",
            parse_json=True,
            type_=TriggeredExecutionGroupTransport,
            **kwargs,
        )

    async def get_api_executions_triggered_id(
        self,
        id: str,
        page_index: Optional["int"] = None,
        limit: Optional["int"] = None,
        started_order: Optional["str"] = None,
        execution_sources: Optional["List[Optional[NotebookExecutionSource]]"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if page_index is not None:
            if isinstance(page_index, PythonCoreBaseModel):
                params.update(page_index.json_dict(by_alias=True))
            elif isinstance(page_index, dict):
                params.update(page_index)
            else:
                params["pageIndex"] = page_index
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if started_order is not None:
            if isinstance(started_order, PythonCoreBaseModel):
                params.update(started_order.json_dict(by_alias=True))
            elif isinstance(started_order, dict):
                params.update(started_order)
            else:
                params["startedOrder"] = started_order
        if execution_sources is not None:
            if isinstance(execution_sources, PythonCoreBaseModel):
                params.update(execution_sources.json_dict(by_alias=True))
            elif isinstance(execution_sources, dict):
                params.update(execution_sources)
            else:
                params["executionSources"] = execution_sources
        return await self.client.request(method="GET", url=f"/api/executions/triggered/{id}", params=params, **kwargs)

    async def get_api_executions_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/api/executions/{id}", **kwargs)

    async def get_api_executions_id_logs(
        self, id: str, log_levels: Optional["List[Optional[LogLevel]]"] = None, **kwargs: Any
    ) -> List[Optional[NotebookExecutionLogTransport]]:
        params: Dict[str, Any] = {}
        if log_levels is not None:
            if isinstance(log_levels, PythonCoreBaseModel):
                params.update(log_levels.json_dict(by_alias=True))
            elif isinstance(log_levels, dict):
                params.update(log_levels)
            else:
                params["logLevels"] = log_levels
        return await self.client.request(
            method="GET",
            url=f"/api/executions/{id}/logs",
            params=params,
            parse_json=True,
            type_=List[Optional[NotebookExecutionLogTransport]],
            **kwargs,
        )

    async def put_api_executions_id_stop(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="PUT", url=f"/api/executions/{id}/stop", **kwargs)

    async def get_api_jobs_executions_groups(self, **kwargs: Any) -> List[Optional[JobExecutionGroup]]:
        return await self.client.request(
            method="GET",
            url=f"/api/jobs/executions/groups",
            parse_json=True,
            type_=List[Optional[JobExecutionGroup]],
            **kwargs,
        )

    async def get_api_jobs_executions_id(self, id: str, **kwargs: Any) -> JobExecution:
        return await self.client.request(
            method="GET", url=f"/api/jobs/executions/{id}", parse_json=True, type_=JobExecution, **kwargs
        )

    async def post_api_jobs_executions_id_stop(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/jobs/executions/{id}/stop", **kwargs)

    async def get_api_jobs_job_id_executions(
        self,
        job_id: str,
        page_index: Optional["int"] = None,
        limit: Optional["int"] = None,
        started_order: Optional["str"] = None,
        execution_sources: Optional["List[Optional[JobExecutionSource]]"] = None,
        **kwargs: Any,
    ) -> PageJobExecutionTransport:
        params: Dict[str, Any] = {}
        if page_index is not None:
            if isinstance(page_index, PythonCoreBaseModel):
                params.update(page_index.json_dict(by_alias=True))
            elif isinstance(page_index, dict):
                params.update(page_index)
            else:
                params["pageIndex"] = page_index
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if started_order is not None:
            if isinstance(started_order, PythonCoreBaseModel):
                params.update(started_order.json_dict(by_alias=True))
            elif isinstance(started_order, dict):
                params.update(started_order)
            else:
                params["startedOrder"] = started_order
        if execution_sources is not None:
            if isinstance(execution_sources, PythonCoreBaseModel):
                params.update(execution_sources.json_dict(by_alias=True))
            elif isinstance(execution_sources, dict):
                params.update(execution_sources)
            else:
                params["executionSources"] = execution_sources
        return await self.client.request(
            method="GET",
            url=f"/api/jobs/{job_id}/executions",
            params=params,
            parse_json=True,
            type_=PageJobExecutionTransport,
            **kwargs,
        )

    async def post_api_jobs_job_id_executions(self, job_id: str, request_body: JsonNode, **kwargs: Any) -> JobExecution:
        return await self.client.request(
            method="POST",
            url=f"/api/jobs/{job_id}/executions",
            request_body=request_body,
            parse_json=True,
            type_=JobExecution,
            **kwargs,
        )

    async def get_api_notebooks(self, **kwargs: Any) -> List[Optional[NotebookTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/notebooks", parse_json=True, type_=List[Optional[NotebookTransport]], **kwargs
        )

    async def post_api_notebooks(self, request_body: NotebookRequestApiModel, **kwargs: Any) -> NotebookTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/notebooks",
            request_body=request_body,
            parse_json=True,
            type_=NotebookTransport,
            **kwargs,
        )

    async def get_api_notebooks_limit_reached(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/limit/reached", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_notebooks_machine_learning_images(self, **kwargs: Any) -> List[Optional[ImageTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/machine-learning-images",
            parse_json=True,
            type_=List[Optional[ImageTransport]],
            **kwargs,
        )

    async def get_api_notebooks_memory_sizes(self, **kwargs: Any) -> List[Optional[str]]:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/memory-sizes", parse_json=True, type_=List[Optional[str]], **kwargs
        )

    async def get_api_notebooks_node(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/node", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_notebooks_node_machine_id(self, machine_id: str, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/node/{machine_id}", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_notebooks_versions(self, **kwargs: Any) -> List[Optional[NotebookVersionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/versions",
            parse_json=True,
            type_=List[Optional[NotebookVersionTransport]],
            **kwargs,
        )

    async def get_api_notebooks_id(self, id: str, **kwargs: Any) -> NotebookTransport:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/{id}", parse_json=True, type_=NotebookTransport, **kwargs
        )

    async def put_api_notebooks_id(
        self, id: str, request_body: NotebookRequestApiModel, **kwargs: Any
    ) -> NotebookTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/notebooks/{id}",
            request_body=request_body,
            parse_json=True,
            type_=NotebookTransport,
            **kwargs,
        )

    async def delete_api_notebooks_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/notebooks/{id}", **kwargs)

    async def get_api_notebooks_id_access_info(self, id: str, **kwargs: Any) -> NotebookAccessInformationTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/{id}/access-info",
            parse_json=True,
            type_=NotebookAccessInformationTransport,
            **kwargs,
        )

    async def get_api_notebooks_id_app_key(self, id: str, **kwargs: Any) -> ApplicationKeyTransport:
        return await self.client.request(
            method="GET", url=f"/api/notebooks/{id}/app-key", parse_json=True, type_=ApplicationKeyTransport, **kwargs
        )

    async def put_api_notebooks_id_app_key(self, id: str, app_key: Optional["str"] = None, **kwargs: Any) -> None:
        params: Dict[str, Any] = {}
        if app_key is not None:
            if isinstance(app_key, PythonCoreBaseModel):
                params.update(app_key.json_dict(by_alias=True))
            elif isinstance(app_key, dict):
                params.update(app_key)
            else:
                params["appKey"] = app_key
        return await self.client.request(method="PUT", url=f"/api/notebooks/{id}/app-key", params=params, **kwargs)

    async def put_api_notebooks_id_assign_mlflow(
        self, id: str, mlflow_id: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if mlflow_id is not None:
            if isinstance(mlflow_id, PythonCoreBaseModel):
                params.update(mlflow_id.json_dict(by_alias=True))
            elif isinstance(mlflow_id, dict):
                params.update(mlflow_id)
            else:
                params["mlflowId"] = mlflow_id
        return await self.client.request(
            method="PUT", url=f"/api/notebooks/{id}/assign-mlflow", params=params, **kwargs
        )

    async def get_api_notebooks_id_content(
        self, id: str, path: Optional["str"] = None, **kwargs: Any
    ) -> NotebookTreeItem:
        params: Dict[str, Any] = {}
        if path is not None:
            if isinstance(path, PythonCoreBaseModel):
                params.update(path.json_dict(by_alias=True))
            elif isinstance(path, dict):
                params.update(path)
            else:
                params["path"] = path
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/{id}/content",
            params=params,
            parse_json=True,
            type_=NotebookTreeItem,
            **kwargs,
        )

    async def put_api_notebooks_id_move(
        self, id: str, workspace_id: Optional["str"] = None, **kwargs: Any
    ) -> NotebookTransport:
        params: Dict[str, Any] = {}
        if workspace_id is not None:
            if isinstance(workspace_id, PythonCoreBaseModel):
                params.update(workspace_id.json_dict(by_alias=True))
            elif isinstance(workspace_id, dict):
                params.update(workspace_id)
            else:
                params["workspaceId"] = workspace_id
        return await self.client.request(
            method="PUT",
            url=f"/api/notebooks/{id}/move",
            params=params,
            parse_json=True,
            type_=NotebookTransport,
            **kwargs,
        )

    async def put_api_notebooks_id_probe(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="PUT", url=f"/api/notebooks/{id}/probe", **kwargs)

    async def get_api_notebooks_id_resources(self, id: str, **kwargs: Any) -> NotebookResourcesTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/{id}/resources",
            parse_json=True,
            type_=NotebookResourcesTransport,
            **kwargs,
        )

    async def put_api_notebooks_id_resources(
        self, id: str, request_body: NotebookResourcesRequestApiModel, **kwargs: Any
    ) -> NotebookResourcesTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/notebooks/{id}/resources",
            request_body=request_body,
            parse_json=True,
            type_=NotebookResourcesTransport,
            **kwargs,
        )

    async def put_api_notebooks_id_upgrade(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="PUT", url=f"/api/notebooks/{id}/upgrade", **kwargs)

    async def get_api_notebooks_id_versions_latest(
        self, id: str, **kwargs: Any
    ) -> List[Optional[NotebookVersionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/notebooks/{id}/versions/latest",
            parse_json=True,
            type_=List[Optional[NotebookVersionTransport]],
            **kwargs,
        )

    async def get_api_scheduling(self, **kwargs: Any) -> List[Optional[SchedulingTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/scheduling", parse_json=True, type_=List[Optional[SchedulingTransport]], **kwargs
        )

    async def post_api_scheduling(self, request_body: SchedulingRequestApiModel, **kwargs: Any) -> SchedulingTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/scheduling",
            request_body=request_body,
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def get_api_scheduling_id(self, id: str, **kwargs: Any) -> SchedulingTransport:
        return await self.client.request(
            method="GET", url=f"/api/scheduling/{id}", parse_json=True, type_=SchedulingTransport, **kwargs
        )

    async def put_api_scheduling_id(
        self, id: str, request_body: SchedulingRequestApiModel, **kwargs: Any
    ) -> SchedulingTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/scheduling/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def delete_api_scheduling_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/scheduling/{id}", **kwargs)

    async def put_api_scheduling_id_change_status(
        self, id: str, status: Optional["bool"] = None, **kwargs: Any
    ) -> SchedulingTransport:
        params: Dict[str, Any] = {}
        if status is not None:
            if isinstance(status, PythonCoreBaseModel):
                params.update(status.json_dict(by_alias=True))
            elif isinstance(status, dict):
                params.update(status)
            else:
                params["status"] = status
        return await self.client.request(
            method="PUT",
            url=f"/api/scheduling/{id}/change-status",
            params=params,
            parse_json=True,
            type_=SchedulingTransport,
            **kwargs,
        )

    async def get_api_scheduling_id_executions(
        self,
        id: str,
        page_index: Optional["int"] = None,
        limit: Optional["int"] = None,
        started_order: Optional["str"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if page_index is not None:
            if isinstance(page_index, PythonCoreBaseModel):
                params.update(page_index.json_dict(by_alias=True))
            elif isinstance(page_index, dict):
                params.update(page_index)
            else:
                params["pageIndex"] = page_index
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if started_order is not None:
            if isinstance(started_order, PythonCoreBaseModel):
                params.update(started_order.json_dict(by_alias=True))
            elif isinstance(started_order, dict):
                params.update(started_order)
            else:
                params["startedOrder"] = started_order
        return await self.client.request(method="GET", url=f"/api/scheduling/{id}/executions", params=params, **kwargs)

    async def post_api_scheduling_id_run(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/scheduling/{id}/run", **kwargs)


class MachineLearningClient(MachineLearningClientBase):
    async def get_api_internal_jobs_id(
        self, id: str, enable_job: Optional["bool"] = None, **kwargs: Any
    ) -> JobConfigTransport:
        params: Dict[str, Any] = {}
        if enable_job is not None:
            if isinstance(enable_job, PythonCoreBaseModel):
                params.update(enable_job.json_dict(by_alias=True))
            elif isinstance(enable_job, dict):
                params.update(enable_job)
            else:
                params["enableJob"] = enable_job
        return await self.client.request(
            method="GET",
            url=f"/api/internal/jobs/{id}",
            params=params,
            parse_json=True,
            type_=JobConfigTransport,
            **kwargs,
        )

    async def post_api_internal_jobs_id_application_key(
        self, id: str, request_body: ApplicationKeyTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/jobs/{id}/application-key", request_body=request_body, **kwargs
        )

    pass


class MachineLearningExternalClient(MachineLearningClientBase):
    pass
