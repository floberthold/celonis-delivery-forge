import logging
import typing
import uuid
from abc import ABC
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr
from python_core_internal_client import AsyncClient, PythonCoreBaseEnum, PythonCoreBaseModel, PythonCoreDatetime

logger = logging.getLogger("python_core_internal_client.package_manager")

JsonNode = Any


class AppMode(PythonCoreBaseEnum):
    VIEWER = "VIEWER"
    CREATOR = "CREATOR"


class CascadeType(PythonCoreBaseEnum):
    DELETE = "DELETE"


class ContentNodeType(PythonCoreBaseEnum):
    ASSET = "ASSET"
    PACKAGE = "PACKAGE"
    FOLDER = "FOLDER"
    IMAGE = "IMAGE"


class RelationType(PythonCoreBaseEnum):
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"


class CommentType(PythonCoreBaseEnum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class GuideFeature(PythonCoreBaseEnum):
    STUDIO_FIRST_LOOK = "STUDIO_FIRST_LOOK"
    VIEWS_FIRST_LOOK = "VIEWS_FIRST_LOOK"
    PAUTO_STUDIO_ANNOUNCEMENT = "PAUTO_STUDIO_ANNOUNCEMENT"
    VISUAL_EDITOR_ANNOUNCEMENT = "VISUAL_EDITOR_ANNOUNCEMENT"
    TASK_INBOX_FIRST_LOOK = "TASK_INBOX_FIRST_LOOK"
    WIDGET_ADMINISTRATION_FIRST_LOOK = "WIDGET_ADMINISTRATION_FIRST_LOOK"


class AccessControlEntrySubjectType(PythonCoreBaseEnum):
    USER = "USER"
    GROUP = "GROUP"
    APPLICATION = "APPLICATION"


class InsightChangeType(PythonCoreBaseEnum):
    NO_CHANGE_TYPE_SPECIFIED = "NO_CHANGE_TYPE_SPECIFIED"
    COMPONENT_ADDED = "COMPONENT_ADDED"
    COMMENT_ADDED = "COMMENT_ADDED"
    STATUS_UPDATE = "STATUS_UPDATE"


class WidgetModuleType(PythonCoreBaseEnum):
    BOARD = "BOARD"
    ASSET = "ASSET"


class WidgetKind(PythonCoreBaseEnum):
    COMPONENT = "COMPONENT"
    TOOL = "TOOL"
    PAGE = "PAGE"


class WidgetPushType(PythonCoreBaseEnum):
    USER = "USER"
    TEAM = "TEAM"
    CLUSTER = "CLUSTER"


class DataModelLoadStatus(PythonCoreBaseEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    LOST_CONNECTION = "LOST_CONNECTION"
    CANCELED = "CANCELED"
    CANCELLING = "CANCELLING"


class ChangeType(PythonCoreBaseEnum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    CHANGED = "CHANGED"
    RESTORED = "RESTORED"


class ContentNodeInstallationType(PythonCoreBaseEnum):
    COPY = "COPY"
    EXTEND = "EXTEND"


class ColumnType(PythonCoreBaseEnum):
    INTEGER = "INTEGER"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"


class AutoMergeExecutionMode(PythonCoreBaseEnum):
    DISTINCT = "DISTINCT"
    NON_DISTINCT = "NON_DISTINCT"


class CalendarDay(PythonCoreBaseEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class DataModelCalendarType(PythonCoreBaseEnum):
    NONE = "NONE"
    CUSTOM = "CUSTOM"
    FACTORY = "FACTORY"


class ProcessType(PythonCoreBaseEnum):
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    GENERIC = "GENERIC"


class ProcessWorkspaceKpiValidationStatus(PythonCoreBaseEnum):
    VALID = "VALID"
    DIMENSION_ERROR = "DIMENSION_ERROR"
    COMPUTE_ERROR = "COMPUTE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ExceptionReference(PythonCoreBaseModel):
    reference: Optional["str"] = Field(None, alias="reference")
    message: Optional["str"] = Field(None, alias="message")
    short_message: Optional["str"] = Field(None, alias="shortMessage")


class ValidationError(PythonCoreBaseModel):
    attribute: Optional["str"] = Field(None, alias="attribute")
    error: Optional["str"] = Field(None, alias="error")
    error_code: Optional["str"] = Field(None, alias="errorCode")
    additional_info: Optional["str"] = Field(None, alias="additionalInfo")


class ValidationExceptionDescriptor(PythonCoreBaseModel):
    errors: Optional["List[Optional[ValidationError]]"] = Field(None, alias="errors")


class WidgetConfiguration(PythonCoreBaseModel):
    configuration: Optional["str"] = Field(None, alias="configuration")


class SpaceSaveTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    icon_reference: Optional["str"] = Field(None, alias="iconReference")
    object_id: Optional["str"] = Field(None, alias="objectId")


class SpaceTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    icon_reference: Optional["str"] = Field(None, alias="iconReference")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    object_id: Optional["str"] = Field(None, alias="objectId")


class PreferencesTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    object_id: Optional["str"] = Field(None, alias="objectId")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")


class PackageDependencyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    version: Optional["str"] = Field(None, alias="version")
    external: Optional["bool"] = Field(None, alias="external")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    root_node_id: Optional["str"] = Field(None, alias="rootNodeId")
    update_available: Optional["bool"] = Field(None, alias="updateAvailable")
    deleted: Optional["bool"] = Field(None, alias="deleted")


class ChangeHiddenOptions(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    hide: Optional["bool"] = Field(None, alias="hide")


class AssetMetadataTransport(PythonCoreBaseModel):
    used_variables: Optional["List[Optional[VariableDefinition]]"] = Field(None, alias="usedVariables")
    related_assets: Optional["List[Optional[RelatedAsset]]"] = Field(None, alias="relatedAssets")
    asset_usages: Optional["List[Optional[AssetUsage]]"] = Field(None, alias="assetUsages")
    metadata: Optional["JsonNode"] = Field(None, alias="metadata")
    hidden: Optional["bool"] = Field(None, alias="hidden")


class AssetUsage(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    target_objects: Optional["List[Optional[TargetUsageMetadata]]"] = Field(None, alias="targetObjects")


class ContentNodeBaseTransport(PythonCoreBaseModel):
    reference: Optional["str"] = Field(None, alias="reference")
    version: Optional["str"] = Field(None, alias="version")
    external: Optional["bool"] = Field(None, alias="external")


class ContentNodeTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    root_node_key: Optional["str"] = Field(None, alias="rootNodeKey")
    base: Optional["ContentNodeBaseTransport"] = Field(None, alias="base")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    node_type: Optional["ContentNodeType"] = Field(None, alias="nodeType")
    parent_node_key: Optional["str"] = Field(None, alias="parentNodeKey")
    parent_node_id: Optional["str"] = Field(None, alias="parentNodeId")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    serialization_type: Optional["str"] = Field(None, alias="serializationType")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    working_draft_id: Optional["str"] = Field(None, alias="workingDraftId")
    activated_draft_id: Optional["str"] = Field(None, alias="activatedDraftId")
    show_in_viewer_mode: Optional["bool"] = Field(None, alias="showInViewerMode")
    public_available: Optional["bool"] = Field(None, alias="publicAvailable")
    embeddable: Optional["bool"] = Field(None, alias="embeddable")
    root_node_id: Optional["str"] = Field(None, alias="rootNodeId")
    order: Optional["int"] = Field(None, alias="order")
    source: Optional["str"] = Field(None, alias="source")
    asset_metadata_transport: Optional["AssetMetadataTransport"] = Field(None, alias="assetMetadataTransport")
    space_id: Optional["str"] = Field(None, alias="spaceId")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    created_by_id: Optional["str"] = Field(None, alias="createdById")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    created_by_name: Optional["str"] = Field(None, alias="createdByName")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")
    root_with_key: Optional["str"] = Field(None, alias="rootWithKey")
    object_id: Optional["str"] = Field(None, alias="objectId")
    asset: Optional["bool"] = Field(None, alias="asset")
    root: Optional["bool"] = Field(None, alias="root")
    identifier: Optional["str"] = Field(None, alias="identifier")


class RelatedAsset(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    type_: Optional["str"] = Field(None, alias="type")
    relation_type: Optional["RelationType"] = Field(None, alias="relationType")
    cascade_type: Optional["CascadeType"] = Field(None, alias="cascadeType")


class SourceUsageMetadata(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")


class TargetUsageMetadata(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    type_: Optional["str"] = Field(None, alias="type")
    source_objects: Optional["List[Optional[SourceUsageMetadata]]"] = Field(None, alias="sourceObjects")


class VariableDefinition(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    type_: Optional["str"] = Field(None, alias="type")
    description: Optional["str"] = Field(None, alias="description")
    source: Optional["str"] = Field(None, alias="source")
    runtime: Optional["bool"] = Field(None, alias="runtime")
    metadata: Optional["JsonNode"] = Field(None, alias="metadata")


class NodeDraftRenameTransport(PythonCoreBaseModel):
    draft_id: Optional["str"] = Field(None, alias="draftId")
    new_name: Optional["str"] = Field(None, alias="newName")


class NodeDraftTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    node_key: Optional["str"] = Field(None, alias="nodeKey")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    author_email: Optional["str"] = Field(None, alias="authorEmail")
    active: Optional["bool"] = Field(None, alias="active")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    current_version: Optional["str"] = Field(None, alias="currentVersion")
    package_versions: Optional["List[Optional[str]]"] = Field(None, alias="packageVersions")


class SaveContentNodeTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    root_node_key: Optional["str"] = Field(None, alias="rootNodeKey")
    base: Optional["ContentNodeBaseTransport"] = Field(None, alias="base")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    node_type: Optional["ContentNodeType"] = Field(None, alias="nodeType")
    parent_node_key: Optional["str"] = Field(None, alias="parentNodeKey")
    parent_node_id: Optional["str"] = Field(None, alias="parentNodeId")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    serialization_type: Optional["str"] = Field(None, alias="serializationType")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    working_draft_id: Optional["str"] = Field(None, alias="workingDraftId")
    activated_draft_id: Optional["str"] = Field(None, alias="activatedDraftId")
    show_in_viewer_mode: Optional["bool"] = Field(None, alias="showInViewerMode")
    public_available: Optional["bool"] = Field(None, alias="publicAvailable")
    embeddable: Optional["bool"] = Field(None, alias="embeddable")
    root_node_id: Optional["str"] = Field(None, alias="rootNodeId")
    order: Optional["int"] = Field(None, alias="order")
    source: Optional["str"] = Field(None, alias="source")
    asset_metadata_transport: Optional["AssetMetadataTransport"] = Field(None, alias="assetMetadataTransport")
    space_id: Optional["str"] = Field(None, alias="spaceId")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    created_by_id: Optional["str"] = Field(None, alias="createdById")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    created_by_name: Optional["str"] = Field(None, alias="createdByName")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")
    publish: Optional["bool"] = Field(None, alias="publish")
    activate: Optional["bool"] = Field(None, alias="activate")
    version: Optional["str"] = Field(None, alias="version")
    root_with_key: Optional["str"] = Field(None, alias="rootWithKey")
    object_id: Optional["str"] = Field(None, alias="objectId")
    asset: Optional["bool"] = Field(None, alias="asset")
    root: Optional["bool"] = Field(None, alias="root")
    identifier: Optional["str"] = Field(None, alias="identifier")


class NodeSharingConfig(PythonCoreBaseModel):
    embeddable: Optional["bool"] = Field(None, alias="embeddable")
    publicly_available: Optional["bool"] = Field(None, alias="publiclyAvailable")


class NameContentNodeTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    new_name: Optional["str"] = Field(None, alias="newName")


class MoveNodeOptions(PythonCoreBaseModel):
    dropped_below: Optional["bool"] = Field(None, alias="droppedBelow")
    dropped_above: Optional["bool"] = Field(None, alias="droppedAbove")
    delete_source: Optional["bool"] = Field(None, alias="deleteSource")
    overwrite: Optional["bool"] = Field(None, alias="overwrite")


class VariableDefinitionWithValue(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    type_: Optional["str"] = Field(None, alias="type")
    description: Optional["str"] = Field(None, alias="description")
    source: Optional["str"] = Field(None, alias="source")
    runtime: Optional["bool"] = Field(None, alias="runtime")
    metadata: Optional["JsonNode"] = Field(None, alias="metadata")
    value: Optional["Any"] = Field(None, alias="value")


class SaveNodeStorageTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    type_: Optional["str"] = Field(None, alias="type")
    object_id: Optional["str"] = Field(None, alias="objectId")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    name: Optional["str"] = Field(None, alias="name")


class NodeStorageTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    type_: Optional["str"] = Field(None, alias="type")
    object_id: Optional["str"] = Field(None, alias="objectId")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    name: Optional["str"] = Field(None, alias="name")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    created_by_name: Optional["str"] = Field(None, alias="createdByName")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")


class AttachmentTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    object_id: Optional["str"] = Field(None, alias="objectId")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    name: Optional["str"] = Field(None, alias="name")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    created_by_name: Optional["str"] = Field(None, alias="createdByName")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")


class UpdateInsightCommentTransport(PythonCoreBaseModel):
    comment: Optional["str"] = Field(None, alias="comment")


class InsightCommentTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    author: Optional["UserTransport"] = Field(None, alias="author")
    comment: Optional["str"] = Field(None, alias="comment")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    href: Optional["str"] = Field(None, alias="href")
    initiator: Optional["UserTransport"] = Field(None, alias="initiator")
    mentioned_users: Optional["List[Optional[UserTransport]]"] = Field(None, alias="mentionedUsers")
    object_id: Optional["str"] = Field(None, alias="objectId")
    type_: Optional["CommentType"] = Field(None, alias="type")


class UserTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    email: Optional["str"] = Field(None, alias="email")
    name: Optional["str"] = Field(None, alias="name")
    team_name: Optional["str"] = Field(None, alias="teamName")
    team_id: Optional["str"] = Field(None, alias="teamId")
    team_domain: Optional["str"] = Field(None, alias="teamDomain")
    api_token: Optional["str"] = Field(None, alias="apiToken")
    active: Optional["bool"] = Field(None, alias="active")
    token: Optional["str"] = Field(None, alias="token")
    account_created: Optional["bool"] = Field(None, alias="accountCreated")
    current: Optional["bool"] = Field(None, alias="current")
    language: Optional["str"] = Field(None, alias="language")
    avatar_url: Optional["str"] = Field(None, alias="avatarUrl")
    enable_notifications: Optional["bool"] = Field(None, alias="enableNotifications")
    notifications_time: Optional["str"] = Field(None, alias="notificationsTime")
    time_zone: Optional["str"] = Field(None, alias="timeZone")
    role: Optional["int"] = Field(None, alias="role")
    effective_role: Optional["int"] = Field(None, alias="effectiveRole")
    contentstore_admin: Optional["bool"] = Field(None, alias="contentstoreAdmin")
    backend_access: Optional["bool"] = Field(None, alias="backendAccess")
    last_log_in_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastLogInDate")
    is_first_log_in: Optional["bool"] = Field(None, alias="isFirstLogIn")
    is_celonis_user: Optional["bool"] = Field(None, alias="isCelonisUser")
    full_template_access: Optional["bool"] = Field(None, alias="fullTemplateAccess")
    group_ids: Optional["List[Optional[str]]"] = Field(None, alias="groupIds")
    name_and_email: Optional["str"] = Field(None, alias="nameAndEmail")
    name_or_email: Optional["str"] = Field(None, alias="nameOrEmail")
    admin: Optional["bool"] = Field(None, alias="admin")
    analyst: Optional["bool"] = Field(None, alias="analyst")
    member: Optional["bool"] = Field(None, alias="member")


class SaveAttachmentTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    object_id: Optional["str"] = Field(None, alias="objectId")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    name: Optional["str"] = Field(None, alias="name")


class ConnectionVariable(PythonCoreBaseModel):
    connection_id: Optional["str"] = Field(None, alias="connectionId")
    app_name: Optional["str"] = Field(None, alias="appName")


class ConnectionVariableInfo(PythonCoreBaseModel):
    connection_username_map: Optional["Dict[str, Optional[str]]"] = Field(None, alias="connectionUsernameMap")
    app_label_map: Optional["Dict[str, Optional[str]]"] = Field(None, alias="appLabelMap")


class LockTransport(PythonCoreBaseModel):
    object_locked: Optional["bool"] = Field(None, alias="objectLocked")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    expires_at: Optional["PythonCoreDatetime"] = Field(None, alias="expiresAt")
    locked_by: Optional["str"] = Field(None, alias="lockedBy")
    locked_by_user_name: Optional["str"] = Field(None, alias="lockedByUserName")


class AccessControlEntryTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    parent_object_id: Optional["str"] = Field(None, alias="parentObjectId")
    object_description: Optional["str"] = Field(None, alias="objectDescription")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    service_description: Optional["str"] = Field(None, alias="serviceDescription")
    subject_id: Optional["str"] = Field(None, alias="subjectId")
    subject_type: Optional["AccessControlEntrySubjectType"] = Field(None, alias="subjectType")
    subject_description: Optional["str"] = Field(None, alias="subjectDescription")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    auth_entity_id: Optional["str"] = Field(None, alias="authEntityId")


class SpaceDeleteTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class ActivatePackageTransport(PythonCoreBaseModel):
    package_key: Optional["str"] = Field(None, alias="packageKey")
    version: Optional["str"] = Field(None, alias="version")
    publish_message: Optional["str"] = Field(None, alias="publishMessage")
    node_ids_to_exclude: Optional["List[Optional[str]]"] = Field(None, alias="nodeIdsToExclude")


class PackageVersionTransport(PythonCoreBaseModel):
    package_key: Optional["str"] = Field(None, alias="packageKey")
    version: Optional["str"] = Field(None, alias="version")
    root_draft_id: Optional["str"] = Field(None, alias="rootDraftId")


class NodeKeysAndVersion(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    version: Optional["str"] = Field(None, alias="version")
    name: Optional["str"] = Field(None, alias="name")
    space_id: Optional["str"] = Field(None, alias="spaceId")


class PackageDeleteTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")


class ContentNodeCopyTransport(PythonCoreBaseModel):
    node_id: Optional["str"] = Field(None, alias="nodeId")
    node_id_to_replace: Optional["str"] = Field(None, alias="nodeIdToReplace")
    destination_root_id: Optional["str"] = Field(None, alias="destinationRootId")
    destination_root_key: Optional["str"] = Field(None, alias="destinationRootKey")
    node_key: Optional["str"] = Field(None, alias="nodeKey")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    team_domain: Optional["str"] = Field(None, alias="teamDomain")
    destination_space_id: Optional["str"] = Field(None, alias="destinationSpaceId")
    delete_source: Optional["bool"] = Field(None, alias="deleteSource")
    create_new_in_destination_team: Optional["bool"] = Field(None, alias="createNewInDestinationTeam")


class DuplicateContentNodeTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    tenant_id: Optional["str"] = Field(None, alias="tenantId")
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    root_node_key: Optional["str"] = Field(None, alias="rootNodeKey")
    base: Optional["ContentNodeBaseTransport"] = Field(None, alias="base")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    node_type: Optional["ContentNodeType"] = Field(None, alias="nodeType")
    parent_node_key: Optional["str"] = Field(None, alias="parentNodeKey")
    parent_node_id: Optional["str"] = Field(None, alias="parentNodeId")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    serialization_type: Optional["str"] = Field(None, alias="serializationType")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    working_draft_id: Optional["str"] = Field(None, alias="workingDraftId")
    activated_draft_id: Optional["str"] = Field(None, alias="activatedDraftId")
    show_in_viewer_mode: Optional["bool"] = Field(None, alias="showInViewerMode")
    public_available: Optional["bool"] = Field(None, alias="publicAvailable")
    embeddable: Optional["bool"] = Field(None, alias="embeddable")
    root_node_id: Optional["str"] = Field(None, alias="rootNodeId")
    order: Optional["int"] = Field(None, alias="order")
    source: Optional["str"] = Field(None, alias="source")
    asset_metadata_transport: Optional["AssetMetadataTransport"] = Field(None, alias="assetMetadataTransport")
    space_id: Optional["str"] = Field(None, alias="spaceId")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    created_by_id: Optional["str"] = Field(None, alias="createdById")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    created_by_name: Optional["str"] = Field(None, alias="createdByName")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")
    new_name: Optional["str"] = Field(None, alias="newName")
    new_key: Optional["str"] = Field(None, alias="newKey")
    root_with_key: Optional["str"] = Field(None, alias="rootWithKey")
    object_id: Optional["str"] = Field(None, alias="objectId")
    asset: Optional["bool"] = Field(None, alias="asset")
    root: Optional["bool"] = Field(None, alias="root")
    identifier: Optional["str"] = Field(None, alias="identifier")


class VariableAssignment(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    value: Optional["Any"] = Field(None, alias="value")
    type_: Optional["str"] = Field(None, alias="type")


class FrontendLogTransport(PythonCoreBaseModel):
    stacktrace: Optional["str"] = Field(None, alias="stacktrace")
    url: Optional["str"] = Field(None, alias="url")


class WidgetLicensableFeatureTransport(PythonCoreBaseModel):
    widget_id: Optional["str"] = Field(None, alias="widgetId")
    tenant_ids: Optional["List[Optional[str]]"] = Field(None, alias="tenantIds")


class VariablesDefinitionsTransport(PythonCoreBaseModel):
    variable_definitions: Optional["List[Optional[VariableDefinition]]"] = Field(None, alias="variableDefinitions")


class AssignmentRuleAttributeValuesTransport(PythonCoreBaseModel):
    attribute_id_with_record_id: Optional["str"] = Field(None, alias="attributeIdWithRecordId")
    attribute_value: Optional["str"] = Field(None, alias="attributeValue")


class AssignmentRuleAssigneeValueTransport(PythonCoreBaseModel):
    assignee_value: Optional["str"] = Field(None, alias="assigneeValue")


class VariablesAssignmentsTransport(PythonCoreBaseModel):
    variable_assignments: Optional["List[Optional[VariableAssignment]]"] = Field(None, alias="variableAssignments")


class SerializedVariablesAssignmentsTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    serialized_variable_assignments: Optional["str"] = Field(None, alias="serializedVariableAssignments")


class CloneRequestTransport(PythonCoreBaseModel):
    source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="sourceTeams")


class TeamSlimTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    domain: Optional["str"] = Field(None, alias="domain")
    clone_data: Optional["bool"] = Field(None, alias="cloneData")


class CloneResultTransport(PythonCoreBaseModel):
    cloned_source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="clonedSourceTeams")
    failed_source_teams: Optional["List[Optional[TeamSlimTransport]]"] = Field(None, alias="failedSourceTeams")


class EraserLogMessageTransport(PythonCoreBaseModel):
    team_id: Optional["str"] = Field(None, alias="teamId")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    message: Optional["str"] = Field(None, alias="message")


class PermissionsImportTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    subject_id: Optional["str"] = Field(None, alias="subjectId")
    permission_keys: Optional["List[Optional[str]]"] = Field(None, alias="permissionKeys")


class SavePreferenceTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    object_id: Optional["str"] = Field(None, alias="objectId")
    mode: Optional["AppMode"] = Field(None, alias="mode")
    configuration: Optional["str"] = Field(None, alias="configuration")
    shareable: Optional["bool"] = Field(None, alias="shareable")
    user_id: Optional["str"] = Field(None, alias="userId")


class PackageWithVariableAssignments(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    last_publish_date: Optional["PythonCoreDatetime"] = Field(None, alias="lastPublishDate")
    variable_assignments: Optional["List[Optional[VariableAssignment]]"] = Field(None, alias="variableAssignments")


class AppFeature(PythonCoreBaseModel):
    label: Optional["str"] = Field(None, alias="label")
    features: Optional["List[Optional[LicensableFeature]]"] = Field(None, alias="features")


class LicensableFeature(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    enabled: Optional["bool"] = Field(None, alias="enabled")


class NewInsightCommentTransport(PythonCoreBaseModel):
    comment: Optional["str"] = Field(None, alias="comment")


class ChangeNotificationTransport(PythonCoreBaseModel):
    insight_id: Optional["str"] = Field(None, alias="insightID")
    change_type: Optional["InsightChangeType"] = Field(None, alias="changeType")
    change_url: Optional["str"] = Field(None, alias="changeURL")


class Widget(PythonCoreBaseModel):
    widget_id: Optional["str"] = Field(None, alias="widgetId")
    name: Optional["str"] = Field(None, alias="name")
    kind: Optional["WidgetKind"] = Field(None, alias="kind")
    push_type: Optional["WidgetPushType"] = Field(None, alias="pushType")
    module_type: Optional["WidgetModuleType"] = Field(None, alias="moduleType")
    resource: Optional["str"] = Field(None, alias="resource")
    widget_module_id: Optional["str"] = Field(None, alias="widgetModuleId")
    widget_module_key: Optional["str"] = Field(None, alias="widgetModuleKey")
    group: Optional["str"] = Field(None, alias="group")
    icon: Optional["str"] = Field(None, alias="icon")
    source_url: Optional["str"] = Field(None, alias="sourceUrl")
    parent_page: Optional["str"] = Field(None, alias="parentPage")
    description: Optional["str"] = Field(None, alias="description")
    group_page: Optional["bool"] = Field(None, alias="groupPage")
    change_date: Optional["PythonCoreDatetime"] = Field(None, alias="changeDate")
    options: Optional["WidgetOptions"] = Field(None, alias="options")


class WidgetOptions(PythonCoreBaseModel):
    public_mode: Optional["bool"] = Field(None, alias="publicMode")
    show_in_viewer_mode: Optional["bool"] = Field(None, alias="showInViewerMode")
    suggested: Optional["bool"] = Field(None, alias="suggested")
    beta: Optional["bool"] = Field(None, alias="beta")
    hidden_in_nav: Optional["bool"] = Field(None, alias="hiddenInNav")
    embeddable: Optional["bool"] = Field(None, alias="embeddable")
    required_feature_keys: Optional["List[Optional[str]]"] = Field(None, alias="requiredFeatureKeys")


class PermissionOptionTransport(PythonCoreBaseModel):
    permission_key: Optional["str"] = Field(None, alias="permissionKey")
    permission_type: Optional["str"] = Field(None, alias="permissionType")
    requires_analyst: Optional["bool"] = Field(None, alias="requiresAnalyst")
    use: Optional["bool"] = Field(None, alias="use")
    requires_use: Optional["bool"] = Field(None, alias="requiresUse")
    display_name: Optional["str"] = Field(None, alias="displayName")


class PermissionRoleTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    permission_keys: Optional["List[Optional[str]]"] = Field(None, alias="permissionKeys")
    requires_analyst: Optional["bool"] = Field(None, alias="requiresAnalyst")


class PermissionsModelTransport(PythonCoreBaseModel):
    access_restricted: Optional["bool"] = Field(None, alias="accessRestricted")
    service_name: Optional["str"] = Field(None, alias="serviceName")
    roles: Optional["List[Optional[PermissionRoleTransport]]"] = Field(None, alias="roles")
    options: Optional["List[Optional[PermissionOptionTransport]]"] = Field(None, alias="options")


class Feature(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    enabled: Optional["bool"] = Field(None, alias="enabled")


class DataModel(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")


class ProcessWorkspaceDataModelTransport(PythonCoreBaseModel):
    status: Optional["DataModelLoadStatus"] = Field(None, alias="status")
    last_load: Optional["PythonCoreDatetime"] = Field(None, alias="lastLoad")
    data_model: Optional["DataModel"] = Field(None, alias="dataModel")
    loaded: Optional["bool"] = Field(None, alias="loaded")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")


class PackageNameTransport(PythonCoreBaseModel):
    unique_name: Optional["str"] = Field(None, alias="uniqueName")


class PackageHistoryTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    version: Optional["str"] = Field(None, alias="version")
    date: Optional["PythonCoreDatetime"] = Field(None, alias="date")
    active: Optional["bool"] = Field(None, alias="active")
    author_id: Optional["str"] = Field(None, alias="authorId")
    author_name: Optional["str"] = Field(None, alias="authorName")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    publish_message: Optional["str"] = Field(None, alias="publishMessage")


class ModifiedAssetTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    root_node_key: Optional["str"] = Field(None, alias="rootNodeKey")
    name: Optional["str"] = Field(None, alias="name")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    change_type: Optional["ChangeType"] = Field(None, alias="changeType")
    invalid: Optional["bool"] = Field(None, alias="invalid")
    draft_id: Optional["str"] = Field(None, alias="draftId")
    hidden: Optional["bool"] = Field(None, alias="hidden")


class PackageKeysTransport(PythonCoreBaseModel):
    root_key: Optional["str"] = Field(None, alias="rootKey")
    child_keys: Optional["List[Optional[str]]"] = Field(None, alias="childKeys")


class PackagePermissionTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    types_without_permissions: Optional["List[Optional[str]]"] = Field(None, alias="typesWithoutPermissions")


class ContentNodeDependent(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["str"] = Field(None, alias="type")
    created_by: Optional["str"] = Field(None, alias="createdBy")
    updated_by: Optional["str"] = Field(None, alias="updatedBy")
    update_date: Optional["PythonCoreDatetime"] = Field(None, alias="updateDate")
    creation_date: Optional["PythonCoreDatetime"] = Field(None, alias="creationDate")
    deleted_in_team: Optional["bool"] = Field(None, alias="deletedInTeam")


class ContentNodeWithDependents(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    name: Optional["str"] = Field(None, alias="name")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    parent_key: Optional["str"] = Field(None, alias="parentKey")
    root: Optional["bool"] = Field(None, alias="root")
    order: Optional["int"] = Field(None, alias="order")
    parent_node_key: Optional["str"] = Field(None, alias="parentNodeKey")
    change_type: Optional["ChangeType"] = Field(None, alias="changeType")
    node_type: Optional["ContentNodeType"] = Field(None, alias="nodeType")
    dependents: Optional["List[Optional[ContentNodeDependent]]"] = Field(None, alias="dependents")
    installation_type: Optional["ContentNodeInstallationType"] = Field(None, alias="installationType")
    deleted_in_team: Optional["bool"] = Field(None, alias="deletedInTeam")


class VariableUsageTransport(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    nodes: Optional["List[Optional[ContentNodeTransport]]"] = Field(None, alias="nodes")


class AssetExportMetadata(PythonCoreBaseModel):
    hidden: Optional["bool"] = Field(None, alias="hidden")
    metadata: Optional["JsonNode"] = Field(None, alias="metadata")
    related_assets: Optional["List[Optional[RelatedAsset]]"] = Field(None, alias="relatedAssets")


class BaseNodeExportTransport(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    name: Optional["str"] = Field(None, alias="name")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    node_type: Optional["ContentNodeType"] = Field(None, alias="nodeType")
    serialization_type: Optional["str"] = Field(None, alias="serializationType")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    asset_metadata_transport: Optional["AssetExportMetadata"] = Field(None, alias="assetMetadataTransport")
    show_in_viewer_mode: Optional["bool"] = Field(None, alias="showInViewerMode")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    base: Optional["ContentNodeBaseTransport"] = Field(None, alias="base")
    serialized_document: Optional["List[Optional[Any]]"] = Field(None, alias="serializedDocument")


class PermissionsOverviewTransport(PythonCoreBaseModel):
    service_name: Optional["str"] = Field(None, alias="serviceName")
    members_count: Optional["int"] = Field(None, alias="membersCount")
    analysts_count: Optional["int"] = Field(None, alias="analystsCount")
    permissions_size: Optional["int"] = Field(None, alias="permissionsSize")


class AccessControlListTransport(PythonCoreBaseModel):
    object_id: Optional["str"] = Field(None, alias="objectId")
    parent_object_id: Optional["str"] = Field(None, alias="parentObjectId")
    object_description: Optional["str"] = Field(None, alias="objectDescription")
    service_name: Optional["str"] = Field(None, alias="serviceName")


class TeamRootNodeKeysTransport(PythonCoreBaseModel):
    team_id: Optional["str"] = Field(None, alias="teamId")
    root_node_keys: Optional["List[Optional[str]]"] = Field(None, alias="rootNodeKeys")


class PackageSummary(PythonCoreBaseModel):
    store_package_key: Optional["str"] = Field(None, alias="storePackageKey")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    key: Optional["str"] = Field(None, alias="key")
    version: Optional["str"] = Field(None, alias="version")


class PermissionCheckResult(PythonCoreBaseModel):
    has_permissions: Optional["bool"] = Field(None, alias="hasPermissions")


class NodeUsageTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    root_key: Optional["str"] = Field(None, alias="rootKey")
    name: Optional["str"] = Field(None, alias="name")
    asset_type: Optional["str"] = Field(None, alias="assetType")
    source_objects: Optional["List[Optional[SourceUsageMetadata]]"] = Field(None, alias="sourceObjects")


class DocumentTransport(PythonCoreBaseModel):
    key: Optional["str"] = Field(None, alias="key")
    serialized_document: Optional["List[Optional[Any]]"] = Field(None, alias="serializedDocument")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")


class ContentNodeWithRootDetailsTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    key: Optional["str"] = Field(None, alias="key")
    root_node_key: Optional["str"] = Field(None, alias="rootNodeKey")
    name: Optional["str"] = Field(None, alias="name")
    root_name: Optional["str"] = Field(None, alias="rootName")
    root_version: Optional["str"] = Field(None, alias="rootVersion")
    serialized_content: Optional["str"] = Field(None, alias="serializedContent")
    invalid_content: Optional["bool"] = Field(None, alias="invalidContent")
    external: Optional["bool"] = Field(None, alias="external")
    root_with_key: Optional["str"] = Field(None, alias="rootWithKey")


class ComputePoolTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    connected: Optional["bool"] = Field(None, alias="connected")
    object_id: Optional["str"] = Field(None, alias="objectId")


class StudioComputeNodeDescriptor(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    pool_id: Optional["str"] = Field(None, alias="poolId")


class StudioDataModelTransport(PythonCoreBaseModel):
    node: Optional["StudioComputeNodeDescriptor"] = Field(None, alias="node")
    loaded: Optional["bool"] = Field(None, alias="loaded")
    data_pool: Optional["ComputePoolTransport"] = Field(None, alias="dataPool")


class TeamNodesTransport(PythonCoreBaseModel):
    team_id: Optional["str"] = Field(None, alias="teamId")
    nodes: Optional["List[Optional[ContentNodeTransport]]"] = Field(None, alias="nodes")


class DimensionTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    column_name: Optional["str"] = Field(None, alias="columnName")
    column_type: Optional["ColumnType"] = Field(None, alias="columnType")


class ComputeNodeWithStatusDescriptor(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    name: Optional["str"] = Field(None, alias="name")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    loaded: Optional["bool"] = Field(None, alias="loaded")
    object_id: Optional["str"] = Field(None, alias="objectId")


class ComputeNodeDescriptor(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    name: Optional["str"] = Field(None, alias="name")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    object_id: Optional["str"] = Field(None, alias="objectId")


class DataModelColumnTransport(PythonCoreBaseModel):
    name: Optional["str"] = Field(None, alias="name")
    type_: Optional["ColumnType"] = Field(None, alias="type")
    primary_key: Optional["bool"] = Field(None, alias="primaryKey")


class DataModelConfigurationTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    activity_table_id: Optional["str"] = Field(None, alias="activityTableId")
    case_table_id: Optional["str"] = Field(None, alias="caseTableId")
    default_configuration: Optional["bool"] = Field(None, alias="defaultConfiguration")
    case_id_column: Optional["str"] = Field(None, alias="caseIdColumn")
    activity_column: Optional["str"] = Field(None, alias="activityColumn")
    timestamp_column: Optional["str"] = Field(None, alias="timestampColumn")
    sorting_column: Optional["str"] = Field(None, alias="sortingColumn")
    end_timestamp_column: Optional["str"] = Field(None, alias="endTimestampColumn")
    cost_column: Optional["str"] = Field(None, alias="costColumn")
    user_column: Optional["str"] = Field(None, alias="userColumn")
    use_parallel_process: Optional["bool"] = Field(None, alias="useParallelProcess")
    parallel_process_parent_column: Optional["str"] = Field(None, alias="parallelProcessParentColumn")
    parallel_process_child_column: Optional["str"] = Field(None, alias="parallelProcessChildColumn")


class DataModelCustomCalendarEntryTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    day: Optional["CalendarDay"] = Field(None, alias="day")
    working_day: Optional["bool"] = Field(None, alias="workingDay")
    start_time: Optional["int"] = Field(None, alias="startTime")
    end_time: Optional["int"] = Field(None, alias="endTime")


class DataModelCustomCalendarTransport(PythonCoreBaseModel):
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    entries: Optional["List[Optional[DataModelCustomCalendarEntryTransport]]"] = Field(None, alias="entries")


class DataModelFactoryCalendarTransport(PythonCoreBaseModel):
    table_name: Optional["str"] = Field(None, alias="tableName")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")


class DataModelForeignKeyColumnTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    source_column_name: Optional["str"] = Field(None, alias="sourceColumnName")
    target_column_name: Optional["str"] = Field(None, alias="targetColumnName")


class DataModelForeignKeyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    source_table_id: Optional["str"] = Field(None, alias="sourceTableId")
    target_table_id: Optional["str"] = Field(None, alias="targetTableId")
    columns: Optional["List[Optional[DataModelForeignKeyColumnTransport]]"] = Field(None, alias="columns")


class DataModelTableTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    data_model_id: Optional["str"] = Field(None, alias="dataModelId")
    data_source_id: Optional["str"] = Field(None, alias="dataSourceId")
    name: Optional["str"] = Field(None, alias="name")
    alias: Optional["str"] = Field(None, alias="alias")
    columns: Optional["List[Optional[DataModelColumnTransport]]"] = Field(None, alias="columns")
    use_direct_storage: Optional["bool"] = Field(None, alias="useDirectStorage")
    alias_or_name: Optional["str"] = Field(None, alias="aliasOrName")
    primary_keys: Optional["List[Optional[str]]"] = Field(None, alias="primaryKeys")


class DataModelTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    description: Optional["str"] = Field(None, alias="description")
    create_date: Optional["PythonCoreDatetime"] = Field(None, alias="createDate")
    changed_date: Optional["PythonCoreDatetime"] = Field(None, alias="changedDate")
    configuration_skipped: Optional["bool"] = Field(None, alias="configurationSkipped")
    pool_id: Optional["str"] = Field(None, alias="poolId")
    unavailable: Optional["bool"] = Field(None, alias="unavailable")
    editable: Optional["bool"] = Field(None, alias="editable")
    creator_user_id: Optional["str"] = Field(None, alias="creatorUserId")
    tables: Optional["List[Optional[DataModelTableTransport]]"] = Field(None, alias="tables")
    foreign_keys: Optional["List[Optional[DataModelForeignKeyTransport]]"] = Field(None, alias="foreignKeys")
    process_configurations: Optional["List[Optional[DataModelConfigurationTransport]]"] = Field(
        None, alias="processConfigurations"
    )
    data_model_calendar_type: Optional["DataModelCalendarType"] = Field(None, alias="dataModelCalendarType")
    factory_calendar: Optional["DataModelFactoryCalendarTransport"] = Field(None, alias="factoryCalendar")
    custom_calendar: Optional["DataModelCustomCalendarTransport"] = Field(None, alias="customCalendar")
    original_id: Optional["str"] = Field(None, alias="originalId")
    eventlog_automerge_enabled: Optional["bool"] = Field(None, alias="eventlogAutomergeEnabled")
    auto_merge_execution_mode: Optional["AutoMergeExecutionMode"] = Field(None, alias="autoMergeExecutionMode")
    object_id: Optional["str"] = Field(None, alias="objectId")
    event_log_count: Optional["int"] = Field(None, alias="eventLogCount")


class DataModelGraphPositioningTransport(PythonCoreBaseModel):
    editing_mode: Optional["int"] = Field(None, alias="editingMode")
    table_positions: Optional["List[Optional[DataModelTablePosition]]"] = Field(None, alias="tablePositions")


class DataModelTablePosition(PythonCoreBaseModel):
    table_id: Optional["str"] = Field(None, alias="tableId")
    x: Optional["int"] = Field(None, alias="x")
    y: Optional["int"] = Field(None, alias="y")


class DataModelPreviewTransport(PythonCoreBaseModel):
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")
    name: Optional["str"] = Field(None, alias="name")
    id: Optional["str"] = Field(None, alias="id")
    last_loaded: Optional["PythonCoreDatetime"] = Field(None, alias="lastLoaded")
    data_pool_name: Optional["str"] = Field(None, alias="dataPoolName")
    data_pool_id: Optional["str"] = Field(None, alias="dataPoolId")
    case_count: Optional["int"] = Field(None, alias="caseCount")
    kpi_validations: Optional["Dict[str, Optional[ProcessWorkspaceKpiValidationMessage]]"] = Field(
        None, alias="kpiValidations"
    )
    object_id: Optional["str"] = Field(None, alias="objectId")
    uplink: Optional["bool"] = Field(None, alias="uplink")
    demo: Optional["bool"] = Field(None, alias="demo")
    loaded: Optional["bool"] = Field(None, alias="loaded")


class ProcessWorkspaceKpiValidationMessage(PythonCoreBaseModel):
    status: Optional["ProcessWorkspaceKpiValidationStatus"] = Field(None, alias="status")
    pql_errors: Optional["str"] = Field(None, alias="pqlErrors")


ExceptionReference.model_rebuild()
ValidationError.model_rebuild()
ValidationExceptionDescriptor.model_rebuild()
WidgetConfiguration.model_rebuild()
SpaceSaveTransport.model_rebuild()
SpaceTransport.model_rebuild()
PreferencesTransport.model_rebuild()
PackageDependencyTransport.model_rebuild()
ChangeHiddenOptions.model_rebuild()
AssetMetadataTransport.model_rebuild()
AssetUsage.model_rebuild()
ContentNodeBaseTransport.model_rebuild()
ContentNodeTransport.model_rebuild()
RelatedAsset.model_rebuild()
SourceUsageMetadata.model_rebuild()
TargetUsageMetadata.model_rebuild()
VariableDefinition.model_rebuild()
NodeDraftRenameTransport.model_rebuild()
NodeDraftTransport.model_rebuild()
SaveContentNodeTransport.model_rebuild()
NodeSharingConfig.model_rebuild()
NameContentNodeTransport.model_rebuild()
MoveNodeOptions.model_rebuild()
VariableDefinitionWithValue.model_rebuild()
SaveNodeStorageTransport.model_rebuild()
NodeStorageTransport.model_rebuild()
AttachmentTransport.model_rebuild()
UpdateInsightCommentTransport.model_rebuild()
InsightCommentTransport.model_rebuild()
UserTransport.model_rebuild()
SaveAttachmentTransport.model_rebuild()
ConnectionVariable.model_rebuild()
ConnectionVariableInfo.model_rebuild()
LockTransport.model_rebuild()
AccessControlEntryTransport.model_rebuild()
SpaceDeleteTransport.model_rebuild()
ActivatePackageTransport.model_rebuild()
PackageVersionTransport.model_rebuild()
NodeKeysAndVersion.model_rebuild()
PackageDeleteTransport.model_rebuild()
ContentNodeCopyTransport.model_rebuild()
DuplicateContentNodeTransport.model_rebuild()
VariableAssignment.model_rebuild()
FrontendLogTransport.model_rebuild()
WidgetLicensableFeatureTransport.model_rebuild()
VariablesDefinitionsTransport.model_rebuild()
AssignmentRuleAttributeValuesTransport.model_rebuild()
AssignmentRuleAssigneeValueTransport.model_rebuild()
VariablesAssignmentsTransport.model_rebuild()
SerializedVariablesAssignmentsTransport.model_rebuild()
CloneRequestTransport.model_rebuild()
TeamSlimTransport.model_rebuild()
CloneResultTransport.model_rebuild()
EraserLogMessageTransport.model_rebuild()
PermissionsImportTransport.model_rebuild()
SavePreferenceTransport.model_rebuild()
PackageWithVariableAssignments.model_rebuild()
AppFeature.model_rebuild()
LicensableFeature.model_rebuild()
NewInsightCommentTransport.model_rebuild()
ChangeNotificationTransport.model_rebuild()
Widget.model_rebuild()
WidgetOptions.model_rebuild()
PermissionOptionTransport.model_rebuild()
PermissionRoleTransport.model_rebuild()
PermissionsModelTransport.model_rebuild()
Feature.model_rebuild()
DataModel.model_rebuild()
ProcessWorkspaceDataModelTransport.model_rebuild()
PackageNameTransport.model_rebuild()
PackageHistoryTransport.model_rebuild()
ModifiedAssetTransport.model_rebuild()
PackageKeysTransport.model_rebuild()
PackagePermissionTransport.model_rebuild()
ContentNodeDependent.model_rebuild()
ContentNodeWithDependents.model_rebuild()
VariableUsageTransport.model_rebuild()
AssetExportMetadata.model_rebuild()
BaseNodeExportTransport.model_rebuild()
PermissionsOverviewTransport.model_rebuild()
AccessControlListTransport.model_rebuild()
TeamRootNodeKeysTransport.model_rebuild()
PackageSummary.model_rebuild()
PermissionCheckResult.model_rebuild()
NodeUsageTransport.model_rebuild()
DocumentTransport.model_rebuild()
ContentNodeWithRootDetailsTransport.model_rebuild()
ComputePoolTransport.model_rebuild()
StudioComputeNodeDescriptor.model_rebuild()
StudioDataModelTransport.model_rebuild()
TeamNodesTransport.model_rebuild()
DimensionTransport.model_rebuild()
ComputeNodeWithStatusDescriptor.model_rebuild()
ComputeNodeDescriptor.model_rebuild()
DataModelColumnTransport.model_rebuild()
DataModelConfigurationTransport.model_rebuild()
DataModelCustomCalendarEntryTransport.model_rebuild()
DataModelCustomCalendarTransport.model_rebuild()
DataModelFactoryCalendarTransport.model_rebuild()
DataModelForeignKeyColumnTransport.model_rebuild()
DataModelForeignKeyTransport.model_rebuild()
DataModelTableTransport.model_rebuild()
DataModelTransport.model_rebuild()
DataModelGraphPositioningTransport.model_rebuild()
DataModelTablePosition.model_rebuild()
DataModelPreviewTransport.model_rebuild()
ProcessWorkspaceKpiValidationMessage.model_rebuild()


class PackageManagerClientBase(ABC):
    client: AsyncClient

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.client = AsyncClient(base_url=base_url, **kwargs)

    async def get_api_widgets_administration(self, **kwargs: Any) -> WidgetConfiguration:
        return await self.client.request(
            method="GET", url=f"/api/widgets/administration", parse_json=True, type_=WidgetConfiguration, **kwargs
        )

    async def put_api_widgets_administration(self, request_body: str, **kwargs: Any) -> WidgetConfiguration:
        return await self.client.request(
            method="PUT",
            url=f"/api/widgets/administration",
            request_body=request_body,
            parse_json=True,
            type_=WidgetConfiguration,
            **kwargs,
        )

    async def get_api_widgets_administration_user(self, **kwargs: Any) -> WidgetConfiguration:
        return await self.client.request(
            method="GET", url=f"/api/widgets/administration/user", parse_json=True, type_=WidgetConfiguration, **kwargs
        )

    async def put_api_widgets_administration_user(self, request_body: str, **kwargs: Any) -> WidgetConfiguration:
        return await self.client.request(
            method="PUT",
            url=f"/api/widgets/administration/user",
            request_body=request_body,
            parse_json=True,
            type_=WidgetConfiguration,
            **kwargs,
        )

    async def get_api_spaces_id(self, id: str, **kwargs: Any) -> SpaceTransport:
        return await self.client.request(
            method="GET", url=f"/api/spaces/{id}", parse_json=True, type_=SpaceTransport, **kwargs
        )

    async def put_api_spaces_id(self, id: str, request_body: SpaceSaveTransport, **kwargs: Any) -> SpaceTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/spaces/{id}",
            request_body=request_body,
            parse_json=True,
            type_=SpaceTransport,
            **kwargs,
        )

    async def get_api_preferences_id(self, id: str, **kwargs: Any) -> PreferencesTransport:
        return await self.client.request(
            method="GET", url=f"/api/preferences/{id}", parse_json=True, type_=PreferencesTransport, **kwargs
        )

    async def put_api_preferences_id(
        self, id: str, request_body: PreferencesTransport, **kwargs: Any
    ) -> PreferencesTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/preferences/{id}",
            request_body=request_body,
            parse_json=True,
            type_=PreferencesTransport,
            **kwargs,
        )

    async def delete_api_preferences_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/preferences/{id}", **kwargs)

    async def put_api_packages_id_move_space_id(self, id: str, space_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="PUT", url=f"/api/packages/{id}/move/{space_id}", **kwargs)

    async def get_api_package_dependencies_package_id_dependency_by_key_dependency_key(
        self, package_id: str, dependency_key: str, **kwargs: Any
    ) -> List[Optional[ContentNodeWithDependents]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-dependencies/{package_id}/dependency/by-key/{dependency_key}",
            parse_json=True,
            type_=List[Optional[ContentNodeWithDependents]],
            **kwargs,
        )

    async def put_api_package_dependencies_package_id_dependency_by_key_dependency_key(
        self,
        package_id: str,
        dependency_key: str,
        request_body: PackageDependencyTransport,
        duplicate: Optional["bool"] = None,
        **kwargs: Any,
    ) -> PackageDependencyTransport:
        params: Dict[str, Any] = {}
        if duplicate is not None:
            if isinstance(duplicate, PythonCoreBaseModel):
                params.update(duplicate.json_dict(by_alias=True))
            elif isinstance(duplicate, dict):
                params.update(duplicate)
            else:
                params["duplicate"] = duplicate
        return await self.client.request(
            method="PUT",
            url=f"/api/package-dependencies/{package_id}/dependency/by-key/{dependency_key}",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=PackageDependencyTransport,
            **kwargs,
        )

    async def delete_api_package_dependencies_package_id_dependency_by_key_dependency_key(
        self, package_id: str, dependency_key: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/package-dependencies/{package_id}/dependency/by-key/{dependency_key}", **kwargs
        )

    async def put_api_nodes_root_key_visibility(
        self, root_key: str, request_body: List[Optional[ChangeHiddenOptions]], **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/{root_key}/visibility",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_id(self, id: str, draft_id: Optional["str"] = None, **kwargs: Any) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if draft_id is not None:
            if isinstance(draft_id, PythonCoreBaseModel):
                params.update(draft_id.json_dict(by_alias=True))
            elif isinstance(draft_id, dict):
                params.update(draft_id)
            else:
                params["draftId"] = draft_id
        return await self.client.request(
            method="GET", url=f"/api/nodes/{id}", params=params, parse_json=True, type_=ContentNodeTransport, **kwargs
        )

    async def put_api_nodes_id(
        self, id: str, request_body: SaveContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/{id}",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def delete_api_nodes_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/nodes/{id}", **kwargs)

    async def put_api_nodes_id_sharing_config(self, id: str, request_body: NodeSharingConfig, **kwargs: Any) -> None:
        return await self.client.request(
            method="PUT", url=f"/api/nodes/{id}/sharing-config", request_body=request_body, **kwargs
        )

    async def put_api_nodes_id_rename(self, id: str, request_body: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/{id}/rename",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def put_api_nodes_id_name(
        self, id: str, request_body: NameContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/{id}/name",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def put_api_nodes_id_move(
        self, id: str, request_body: MoveNodeOptions, new_parent_id: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if new_parent_id is not None:
            if isinstance(new_parent_id, PythonCoreBaseModel):
                params.update(new_parent_id.json_dict(by_alias=True))
            elif isinstance(new_parent_id, dict):
                params.update(new_parent_id)
            else:
                params["newParentId"] = new_parent_id
        return await self.client.request(
            method="PUT", url=f"/api/nodes/{id}/move", params=params, request_body=request_body, **kwargs
        )

    async def put_api_nodes_id_hidden(
        self, id: str, request_body: ChangeHiddenOptions, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/{id}/hidden",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def put_api_nodes_by_package_key_package_key_variables_key(
        self, package_key: str, key: str, request_body: VariableDefinitionWithValue, **kwargs: Any
    ) -> VariableDefinitionWithValue:
        return await self.client.request(
            method="PUT",
            url=f"/api/nodes/by-package-key/{package_key}/variables/{key}",
            request_body=request_body,
            parse_json=True,
            type_=VariableDefinitionWithValue,
            **kwargs,
        )

    async def delete_api_nodes_by_package_key_package_key_variables_key(
        self, package_key: str, key: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/nodes/by-package-key/{package_key}/variables/{key}", **kwargs
        )

    async def get_api_node_storage_id(
        self, id: str, with_created_by_name: Optional["bool"] = None, **kwargs: Any
    ) -> NodeStorageTransport:
        params: Dict[str, Any] = {}
        if with_created_by_name is not None:
            if isinstance(with_created_by_name, PythonCoreBaseModel):
                params.update(with_created_by_name.json_dict(by_alias=True))
            elif isinstance(with_created_by_name, dict):
                params.update(with_created_by_name)
            else:
                params["withCreatedByName"] = with_created_by_name
        return await self.client.request(
            method="GET",
            url=f"/api/node-storage/{id}",
            params=params,
            parse_json=True,
            type_=NodeStorageTransport,
            **kwargs,
        )

    async def put_api_node_storage_id(
        self, id: str, request_body: SaveNodeStorageTransport, **kwargs: Any
    ) -> NodeStorageTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/node-storage/{id}",
            request_body=request_body,
            parse_json=True,
            type_=NodeStorageTransport,
            **kwargs,
        )

    async def delete_api_node_storage_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/node-storage/{id}", **kwargs)

    async def put_api_insights_insight_id_comments_comment_id(
        self, comment_id: str, insight_id: str, request_body: UpdateInsightCommentTransport, **kwargs: Any
    ) -> InsightCommentTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/insights/{insight_id}/comments/{comment_id}",
            request_body=request_body,
            parse_json=True,
            type_=InsightCommentTransport,
            **kwargs,
        )

    async def delete_api_insights_insight_id_comments_comment_id(
        self, comment_id: str, insight_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/insights/{insight_id}/comments/{comment_id}", **kwargs
        )

    async def get_api_guide(self, feature: Optional["GuideFeature"] = None, **kwargs: Any) -> bool:
        params: Dict[str, Any] = {}
        if feature is not None:
            if isinstance(feature, PythonCoreBaseModel):
                params.update(feature.json_dict(by_alias=True))
            elif isinstance(feature, dict):
                params.update(feature)
            else:
                params["feature"] = feature
        return await self.client.request(
            method="GET", url=f"/api/guide", params=params, parse_json=True, type_=bool, **kwargs
        )

    async def put_api_guide(self, feature: Optional["GuideFeature"] = None, **kwargs: Any) -> None:
        params: Dict[str, Any] = {}
        if feature is not None:
            if isinstance(feature, PythonCoreBaseModel):
                params.update(feature.json_dict(by_alias=True))
            elif isinstance(feature, dict):
                params.update(feature)
            else:
                params["feature"] = feature
        return await self.client.request(method="PUT", url=f"/api/guide", params=params, **kwargs)

    async def get_api_attachments_id(self, id: str, **kwargs: Any) -> AttachmentTransport:
        return await self.client.request(
            method="GET", url=f"/api/attachments/{id}", parse_json=True, type_=AttachmentTransport, **kwargs
        )

    async def put_api_attachments_id(
        self, id: str, request_body: SaveAttachmentTransport, **kwargs: Any
    ) -> AttachmentTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/attachments/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AttachmentTransport,
            **kwargs,
        )

    async def delete_api_attachments_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/attachments/{id}", **kwargs)

    async def post_api_widgets_upload(self, request_body: Dict[str, Any], **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/widgets/upload", request_body=request_body, **kwargs)

    async def post_api_widgets_upload_user(self, request_body: Dict[str, Any], **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/widgets/upload-user", request_body=request_body, **kwargs
        )

    async def post_api_widgets_upload_tenant_independently(self, request_body: Dict[str, Any], **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/widgets/upload-tenant-independently", request_body=request_body, **kwargs
        )

    async def post_api_variables_connections(
        self, request_body: List[Optional[ConnectionVariable]], **kwargs: Any
    ) -> ConnectionVariableInfo:
        return await self.client.request(
            method="POST",
            url=f"/api/variables/connections",
            request_body=request_body,
            parse_json=True,
            type_=ConnectionVariableInfo,
            **kwargs,
        )

    async def get_api_v2_locks(self, object_id: Optional["str"] = None, **kwargs: Any) -> LockTransport:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        return await self.client.request(
            method="GET", url=f"/api/v2/locks", params=params, parse_json=True, type_=LockTransport, **kwargs
        )

    async def post_api_v2_locks(self, object_id: Optional["str"] = None, **kwargs: Any) -> LockTransport:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        return await self.client.request(
            method="POST", url=f"/api/v2/locks", params=params, parse_json=True, type_=LockTransport, **kwargs
        )

    async def post_api_v2_locks_unlock(self, object_id: Optional["str"] = None, **kwargs: Any) -> None:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        return await self.client.request(method="POST", url=f"/api/v2/locks/unlock", params=params, **kwargs)

    async def post_api_v2_locks_renew(self, object_id: Optional["str"] = None, **kwargs: Any) -> LockTransport:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        return await self.client.request(
            method="POST", url=f"/api/v2/locks/renew", params=params, parse_json=True, type_=LockTransport, **kwargs
        )

    async def get_api_spaces(self, **kwargs: Any) -> List[Optional[SpaceTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/spaces", parse_json=True, type_=List[Optional[SpaceTransport]], **kwargs
        )

    async def post_api_spaces(self, request_body: SpaceSaveTransport, **kwargs: Any) -> SpaceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/spaces",
            request_body=request_body,
            parse_json=True,
            type_=SpaceTransport,
            **kwargs,
        )

    async def get_api_spaces_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/spaces/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_spaces_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/spaces/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_spaces_delete_id(self, id: str, request_body: SpaceDeleteTransport, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/spaces/delete/{id}", request_body=request_body, **kwargs
        )

    async def post_api_process_workspace_compute_pools_load_data_model_id(
        self, data_model_id: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/process-workspace/compute-pools/load/{data_model_id}", **kwargs
        )

    async def get_api_preferences(
        self,
        object_id: Optional["str"] = None,
        shareable: Optional["bool"] = None,
        mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[PreferencesTransport]]:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        if shareable is not None:
            if isinstance(shareable, PythonCoreBaseModel):
                params.update(shareable.json_dict(by_alias=True))
            elif isinstance(shareable, dict):
                params.update(shareable)
            else:
                params["shareable"] = shareable
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        return await self.client.request(
            method="GET",
            url=f"/api/preferences",
            params=params,
            parse_json=True,
            type_=List[Optional[PreferencesTransport]],
            **kwargs,
        )

    async def post_api_preferences(self, request_body: PreferencesTransport, **kwargs: Any) -> PreferencesTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/preferences",
            request_body=request_body,
            parse_json=True,
            type_=PreferencesTransport,
            **kwargs,
        )

    async def post_api_packages_key_export(
        self,
        key: str,
        store: Optional["bool"] = None,
        new_key: Optional["str"] = None,
        draft: Optional["bool"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if store is not None:
            if isinstance(store, PythonCoreBaseModel):
                params.update(store.json_dict(by_alias=True))
            elif isinstance(store, dict):
                params.update(store)
            else:
                params["store"] = store
        if new_key is not None:
            if isinstance(new_key, PythonCoreBaseModel):
                params.update(new_key.json_dict(by_alias=True))
            elif isinstance(new_key, dict):
                params.update(new_key)
            else:
                params["newKey"] = new_key
        if draft is not None:
            if isinstance(draft, PythonCoreBaseModel):
                params.update(draft.json_dict(by_alias=True))
            elif isinstance(draft, dict):
                params.update(draft)
            else:
                params["draft"] = draft
        return await self.client.request(method="POST", url=f"/api/packages/{key}/export", params=params, **kwargs)

    async def post_api_packages_key_activate(
        self, key: str, request_body: ActivatePackageTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/packages/{key}/activate", request_body=request_body, **kwargs
        )

    async def post_api_packages_id_load_version(
        self, id: str, request_body: PackageVersionTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/packages/{id}/load-version", request_body=request_body, **kwargs
        )

    async def post_api_packages_install(self, request_body: NodeKeysAndVersion, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/packages/install",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_packages_import(
        self,
        request_body: Dict[str, Any],
        space_id: Optional["str"] = None,
        new_key: Optional["str"] = None,
        overwrite: Optional["bool"] = None,
        **kwargs: Any,
    ) -> None:
        params: Dict[str, Any] = {}
        if space_id is not None:
            if isinstance(space_id, PythonCoreBaseModel):
                params.update(space_id.json_dict(by_alias=True))
            elif isinstance(space_id, dict):
                params.update(space_id)
            else:
                params["spaceId"] = space_id
        if new_key is not None:
            if isinstance(new_key, PythonCoreBaseModel):
                params.update(new_key.json_dict(by_alias=True))
            elif isinstance(new_key, dict):
                params.update(new_key)
            else:
                params["newKey"] = new_key
        if overwrite is not None:
            if isinstance(overwrite, PythonCoreBaseModel):
                params.update(overwrite.json_dict(by_alias=True))
            elif isinstance(overwrite, dict):
                params.update(overwrite)
            else:
                params["overwrite"] = overwrite
        return await self.client.request(
            method="POST", url=f"/api/packages/import", params=params, request_body=request_body, **kwargs
        )

    async def post_api_packages_delete_id(self, id: str, request_body: PackageDeleteTransport, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/packages/delete/{id}", request_body=request_body, **kwargs
        )

    async def get_api_package_nodes_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-nodes/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_package_nodes_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/package-nodes/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_package_dependencies_package_id(
        self, package_id: str, request_body: List[Optional[PackageDependencyTransport]], **kwargs: Any
    ) -> List[Optional[PackageDependencyTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/package-dependencies/{package_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[PackageDependencyTransport]],
            **kwargs,
        )

    async def get_api_nodes(
        self, asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="GET",
            url=f"/api/nodes",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_nodes(self, request_body: SaveContentNodeTransport, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_nodes_node_id_drafts_draft_id_load(
        self, node_id: str, draft_id: str, **kwargs: Any
    ) -> NodeDraftTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/{node_id}/drafts/{draft_id}/load",
            parse_json=True,
            type_=NodeDraftTransport,
            **kwargs,
        )

    async def post_api_nodes_id_copy(
        self, id: str, request_body: ContentNodeCopyTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/{id}/copy",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_nodes_id_checkpoint(
        self, id: str, request_body: SaveContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/{id}/checkpoint",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_nodes_duplicate(
        self, request_body: DuplicateContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/duplicate",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinition]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinition]],
            **kwargs,
        )

    async def post_api_nodes_by_package_key_package_key_variables(
        self, package_key: str, request_body: VariableDefinitionWithValue, **kwargs: Any
    ) -> VariableDefinitionWithValue:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/by-package-key/{package_key}/variables",
            request_body=request_body,
            parse_json=True,
            type_=VariableDefinitionWithValue,
            **kwargs,
        )

    async def post_api_nodes_by_package_key_package_key_variables_key_value(
        self,
        package_key: str,
        key: str,
        request_body: VariableAssignment,
        app_mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> VariableAssignment:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/by-package-key/{package_key}/variables/{key}/value",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=VariableAssignment,
            **kwargs,
        )

    async def delete_api_nodes_by_package_key_package_key_variables_key_value(
        self, package_key: str, key: str, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="DELETE",
            url=f"/api/nodes/by-package-key/{package_key}/variables/{key}/value",
            params=params,
            **kwargs,
        )

    async def post_api_nodes_by_package_key_package_key_variables_key_runtime_value(
        self,
        package_key: str,
        key: str,
        request_body: VariableAssignment,
        app_mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> VariableAssignment:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/by-package-key/{package_key}/variables/{key}/runtime-value",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=VariableAssignment,
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_values(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableAssignment]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableAssignment]],
            **kwargs,
        )

    async def post_api_nodes_by_package_key_package_key_variables_values(
        self,
        package_key: str,
        request_body: List[Optional[VariableAssignment]],
        app_mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[VariableAssignment]]:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/by-package-key/{package_key}/variables/values",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[VariableAssignment]],
            **kwargs,
        )

    async def post_api_nodes_asset_import(
        self, request_body: SaveContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/nodes/asset/import",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_node_storage(
        self,
        object_id: Optional["str"] = None,
        shareable: Optional["bool"] = None,
        mode: Optional["str"] = None,
        type_: Optional["str"] = None,
        with_created_by_name: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[NodeStorageTransport]]:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        if shareable is not None:
            if isinstance(shareable, PythonCoreBaseModel):
                params.update(shareable.json_dict(by_alias=True))
            elif isinstance(shareable, dict):
                params.update(shareable)
            else:
                params["shareable"] = shareable
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if with_created_by_name is not None:
            if isinstance(with_created_by_name, PythonCoreBaseModel):
                params.update(with_created_by_name.json_dict(by_alias=True))
            elif isinstance(with_created_by_name, dict):
                params.update(with_created_by_name)
            else:
                params["withCreatedByName"] = with_created_by_name
        return await self.client.request(
            method="GET",
            url=f"/api/node-storage",
            params=params,
            parse_json=True,
            type_=List[Optional[NodeStorageTransport]],
            **kwargs,
        )

    async def post_api_node_storage(
        self, request_body: SaveNodeStorageTransport, **kwargs: Any
    ) -> NodeStorageTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/node-storage",
            request_body=request_body,
            parse_json=True,
            type_=NodeStorageTransport,
            **kwargs,
        )

    async def post_api_logging_frontend(self, request_body: FrontendLogTransport, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/logging/frontend", request_body=request_body, **kwargs
        )

    async def get_api_locks_object_id(self, object_id: str, **kwargs: Any) -> LockTransport:
        return await self.client.request(
            method="GET", url=f"/api/locks/{object_id}", parse_json=True, type_=LockTransport, **kwargs
        )

    async def post_api_locks_object_id(self, object_id: str, **kwargs: Any) -> LockTransport:
        return await self.client.request(
            method="POST", url=f"/api/locks/{object_id}", parse_json=True, type_=LockTransport, **kwargs
        )

    async def post_api_locks_object_id_unlock(self, object_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="POST", url=f"/api/locks/{object_id}/unlock", **kwargs)

    async def post_api_locks_object_id_renew(self, object_id: str, **kwargs: Any) -> LockTransport:
        return await self.client.request(
            method="POST", url=f"/api/locks/{object_id}/renew", parse_json=True, type_=LockTransport, **kwargs
        )

    async def get_api_insights_insight_id_comments(
        self, insight_id: str, **kwargs: Any
    ) -> List[Optional[InsightCommentTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/insights/{insight_id}/comments",
            parse_json=True,
            type_=List[Optional[InsightCommentTransport]],
            **kwargs,
        )

    async def post_api_insights_insight_id_comments(
        self, insight_id: str, request_body: NewInsightCommentTransport, **kwargs: Any
    ) -> InsightCommentTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/insights/{insight_id}/comments",
            request_body=request_body,
            parse_json=True,
            type_=InsightCommentTransport,
            **kwargs,
        )

    async def post_api_insights_mail_notify(self, request_body: ChangeNotificationTransport, **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/insights/mail/notify", request_body=request_body, **kwargs
        )

    async def get_api_attachments(
        self,
        object_id: Optional["str"] = None,
        shareable: Optional["bool"] = None,
        mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[AttachmentTransport]]:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        if shareable is not None:
            if isinstance(shareable, PythonCoreBaseModel):
                params.update(shareable.json_dict(by_alias=True))
            elif isinstance(shareable, dict):
                params.update(shareable)
            else:
                params["shareable"] = shareable
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        return await self.client.request(
            method="GET",
            url=f"/api/attachments",
            params=params,
            parse_json=True,
            type_=List[Optional[AttachmentTransport]],
            **kwargs,
        )

    async def post_api_attachments(self, request_body: SaveAttachmentTransport, **kwargs: Any) -> AttachmentTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/attachments",
            request_body=request_body,
            parse_json=True,
            type_=AttachmentTransport,
            **kwargs,
        )

    async def get_api_asset_nodes_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/asset-nodes/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_asset_nodes_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/asset-nodes/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_favicon_ico(self, **kwargs: Any) -> None:
        return await self.client.request(method="GET", url=f"/favicon.ico", **kwargs)

    async def get_api_widgets(
        self, type_: Optional["WidgetModuleType"] = None, kind: Optional["WidgetKind"] = None, **kwargs: Any
    ) -> List[Optional[Widget]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if kind is not None:
            if isinstance(kind, PythonCoreBaseModel):
                params.update(kind.json_dict(by_alias=True))
            elif isinstance(kind, dict):
                params.update(kind)
            else:
                params["kind"] = kind
        return await self.client.request(
            method="GET", url=f"/api/widgets", params=params, parse_json=True, type_=List[Optional[Widget]], **kwargs
        )

    async def get_api_spaces_manage_permissions_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/spaces/manage-permissions/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_spaces_manage_permissions_by_team_domain_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/spaces/manage-permissions/by-team-domain/{team_domain}",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_spaces_by_team_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[SpaceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/spaces/by-team/{team_domain}",
            parse_json=True,
            type_=List[Optional[SpaceTransport]],
            **kwargs,
        )

    async def get_api_spaces_by_node_id_node_id(self, node_id: str, **kwargs: Any) -> SpaceTransport:
        return await self.client.request(
            method="GET", url=f"/api/spaces/by-node-id/{node_id}", parse_json=True, type_=SpaceTransport, **kwargs
        )

    async def get_api_public_widgets(
        self, type_: Optional["WidgetModuleType"] = None, kind: Optional["WidgetKind"] = None, **kwargs: Any
    ) -> List[Optional[Widget]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if kind is not None:
            if isinstance(kind, PythonCoreBaseModel):
                params.update(kind.json_dict(by_alias=True))
            elif isinstance(kind, dict):
                params.update(kind)
            else:
                params["kind"] = kind
        return await self.client.request(
            method="GET",
            url=f"/api/public/widgets",
            params=params,
            parse_json=True,
            type_=List[Optional[Widget]],
            **kwargs,
        )

    async def get_api_public_preferences(
        self,
        object_id: Optional["str"] = None,
        shareable: Optional["bool"] = None,
        mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[PreferencesTransport]]:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        if shareable is not None:
            if isinstance(shareable, PythonCoreBaseModel):
                params.update(shareable.json_dict(by_alias=True))
            elif isinstance(shareable, dict):
                params.update(shareable)
            else:
                params["shareable"] = shareable
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        return await self.client.request(
            method="GET",
            url=f"/api/public/preferences",
            params=params,
            parse_json=True,
            type_=List[Optional[PreferencesTransport]],
            **kwargs,
        )

    async def get_api_public_preferences_id(self, id: str, **kwargs: Any) -> PreferencesTransport:
        return await self.client.request(
            method="GET", url=f"/api/public/preferences/{id}", parse_json=True, type_=PreferencesTransport, **kwargs
        )

    async def get_api_public_nodes_node_id_by_package_key_package_key_variables_runtime_definitions_with_values(
        self,
        node_id: str,
        package_key: str,
        type_: Optional["str"] = None,
        app_mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[VariableDefinitionWithValue]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/public/nodes/{node_id}/by-package-key/{package_key}/variables/runtime-definitions-with-values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinitionWithValue]],
            **kwargs,
        )

    async def get_api_public_final_nodes_id(self, id: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="GET", url=f"/api/public/final-nodes/{id}", parse_json=True, type_=ContentNodeTransport, **kwargs
        )

    async def get_api_public_features_global(self, **kwargs: Any) -> List[Optional[Feature]]:
        return await self.client.request(
            method="GET", url=f"/api/public/features/global", parse_json=True, type_=List[Optional[Feature]], **kwargs
        )

    async def get_api_public_authentication_status(self, **kwargs: Any) -> bool:
        return await self.client.request(
            method="GET", url=f"/api/public/authentication/status", parse_json=True, type_=bool, **kwargs
        )

    async def get_api_process_workspace_compute_pools_data_model_id(
        self, data_model_id: str, **kwargs: Any
    ) -> ProcessWorkspaceDataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/process-workspace/compute-pools/{data_model_id}",
            parse_json=True,
            type_=ProcessWorkspaceDataModelTransport,
            **kwargs,
        )

    async def get_api_preferences_latest(
        self,
        object_id: Optional["str"] = None,
        shareable: Optional["bool"] = None,
        mode: Optional["str"] = None,
        **kwargs: Any,
    ) -> PreferencesTransport:
        params: Dict[str, Any] = {}
        if object_id is not None:
            if isinstance(object_id, PythonCoreBaseModel):
                params.update(object_id.json_dict(by_alias=True))
            elif isinstance(object_id, dict):
                params.update(object_id)
            else:
                params["objectId"] = object_id
        if shareable is not None:
            if isinstance(shareable, PythonCoreBaseModel):
                params.update(shareable.json_dict(by_alias=True))
            elif isinstance(shareable, dict):
                params.update(shareable)
            else:
                params["shareable"] = shareable
        if mode is not None:
            if isinstance(mode, PythonCoreBaseModel):
                params.update(mode.json_dict(by_alias=True))
            elif isinstance(mode, dict):
                params.update(mode)
            else:
                params["mode"] = mode
        return await self.client.request(
            method="GET",
            url=f"/api/preferences/latest",
            params=params,
            parse_json=True,
            type_=PreferencesTransport,
            **kwargs,
        )

    async def get_api_packages(self, **kwargs: Any) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/packages", parse_json=True, type_=List[Optional[ContentNodeTransport]], **kwargs
        )

    async def get_api_packages_id_unique_name(
        self, id: str, name: Optional["str"] = None, node_type: Optional["ContentNodeType"] = None, **kwargs: Any
    ) -> PackageNameTransport:
        params: Dict[str, Any] = {}
        if name is not None:
            if isinstance(name, PythonCoreBaseModel):
                params.update(name.json_dict(by_alias=True))
            elif isinstance(name, dict):
                params.update(name)
            else:
                params["name"] = name
        if node_type is not None:
            if isinstance(node_type, PythonCoreBaseModel):
                params.update(node_type.json_dict(by_alias=True))
            elif isinstance(node_type, dict):
                params.update(node_type)
            else:
                params["nodeType"] = node_type
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/unique-name",
            params=params,
            parse_json=True,
            type_=PackageNameTransport,
            **kwargs,
        )

    async def get_api_packages_id_next_version(self, id: str, **kwargs: Any) -> PackageHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/next-version",
            parse_json=True,
            type_=PackageHistoryTransport,
            **kwargs,
        )

    async def get_api_packages_id_modified_assets(
        self, id: str, **kwargs: Any
    ) -> List[Optional[ModifiedAssetTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/modified-assets",
            parse_json=True,
            type_=List[Optional[ModifiedAssetTransport]],
            **kwargs,
        )

    async def get_api_packages_id_latest_version(self, id: str, **kwargs: Any) -> PackageHistoryTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/latest-version",
            parse_json=True,
            type_=PackageHistoryTransport,
            **kwargs,
        )

    async def get_api_packages_id_keys(
        self, id: str, root_key: Optional["str"] = None, **kwargs: Any
    ) -> PackageKeysTransport:
        params: Dict[str, Any] = {}
        if root_key is not None:
            if isinstance(root_key, PythonCoreBaseModel):
                params.update(root_key.json_dict(by_alias=True))
            elif isinstance(root_key, dict):
                params.update(root_key)
            else:
                params["rootKey"] = root_key
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/keys",
            params=params,
            parse_json=True,
            type_=PackageKeysTransport,
            **kwargs,
        )

    async def get_api_packages_id_history(self, id: str, **kwargs: Any) -> List[Optional[PackageHistoryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/packages/{id}/history",
            parse_json=True,
            type_=List[Optional[PackageHistoryTransport]],
            **kwargs,
        )

    async def get_api_packages_id_active(self, id: str, **kwargs: Any) -> PackageHistoryTransport:
        return await self.client.request(
            method="GET", url=f"/api/packages/{id}/active", parse_json=True, type_=PackageHistoryTransport, **kwargs
        )

    async def get_api_packages_name(self, name: Optional["str"] = None, **kwargs: Any) -> PackageNameTransport:
        params: Dict[str, Any] = {}
        if name is not None:
            if isinstance(name, PythonCoreBaseModel):
                params.update(name.json_dict(by_alias=True))
            elif isinstance(name, dict):
                params.update(name)
            else:
                params["name"] = name
        return await self.client.request(
            method="GET",
            url=f"/api/packages/name",
            params=params,
            parse_json=True,
            type_=PackageNameTransport,
            **kwargs,
        )

    async def get_api_packages_install_missing_permissions(
        self, package_key: Optional["str"] = None, version: Optional["str"] = None, **kwargs: Any
    ) -> PackagePermissionTransport:
        params: Dict[str, Any] = {}
        if package_key is not None:
            if isinstance(package_key, PythonCoreBaseModel):
                params.update(package_key.json_dict(by_alias=True))
            elif isinstance(package_key, dict):
                params.update(package_key)
            else:
                params["packageKey"] = package_key
        if version is not None:
            if isinstance(version, PythonCoreBaseModel):
                params.update(version.json_dict(by_alias=True))
            elif isinstance(version, dict):
                params.update(version)
            else:
                params["version"] = version
        return await self.client.request(
            method="GET",
            url=f"/api/packages/install/missing-permissions",
            params=params,
            parse_json=True,
            type_=PackagePermissionTransport,
            **kwargs,
        )

    async def get_api_package_nodes_manage_permissions_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/package-nodes/manage-permissions/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_package_nodes_manage_permissions_by_team_domain_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-nodes/manage-permissions/by-team-domain/{team_domain}",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_package_dependencies_package_id_potential_dependencies(
        self, package_id: str, **kwargs: Any
    ) -> List[Optional[PackageDependencyTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-dependencies/{package_id}/potential-dependencies",
            parse_json=True,
            type_=List[Optional[PackageDependencyTransport]],
            **kwargs,
        )

    async def get_api_package_dependencies_package_id_dependency_by_key_dependency_key_latest_update(
        self, package_id: str, dependency_key: str, **kwargs: Any
    ) -> PackageDependencyTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/package-dependencies/{package_id}/dependency/by-key/{dependency_key}/latest-update",
            parse_json=True,
            type_=PackageDependencyTransport,
            **kwargs,
        )

    async def get_api_package_dependencies_package_id_dependency_by_key_dependency_key_affected_nodes(
        self, package_id: str, dependency_key: str, dependency_new_draft_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeWithDependents]]:
        params: Dict[str, Any] = {}
        if dependency_new_draft_id is not None:
            if isinstance(dependency_new_draft_id, PythonCoreBaseModel):
                params.update(dependency_new_draft_id.json_dict(by_alias=True))
            elif isinstance(dependency_new_draft_id, dict):
                params.update(dependency_new_draft_id)
            else:
                params["dependencyNewDraftId"] = dependency_new_draft_id
        return await self.client.request(
            method="GET",
            url=f"/api/package-dependencies/{package_id}/dependency/by-key/{dependency_key}/affected-nodes",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeWithDependents]],
            **kwargs,
        )

    async def get_api_package_dependencies_package_id_by_root_draft_id_root_draft_id(
        self, package_id: str, root_draft_id: str, **kwargs: Any
    ) -> List[Optional[PackageDependencyTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/package-dependencies/{package_id}/by-root-draft-id/{root_draft_id}",
            parse_json=True,
            type_=List[Optional[PackageDependencyTransport]],
            **kwargs,
        )

    async def get_api_nodes_root_key_node_key(
        self, node_key: str, root_key: str, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="GET", url=f"/api/nodes/{root_key}/{node_key}", parse_json=True, type_=ContentNodeTransport, **kwargs
        )

    async def get_api_nodes_node_id_drafts(
        self, node_id: str, limit: Optional["int"] = None, offset: Optional["int"] = None, **kwargs: Any
    ) -> List[Optional[NodeDraftTransport]]:
        params: Dict[str, Any] = {}
        if limit is not None:
            if isinstance(limit, PythonCoreBaseModel):
                params.update(limit.json_dict(by_alias=True))
            elif isinstance(limit, dict):
                params.update(limit)
            else:
                params["limit"] = limit
        if offset is not None:
            if isinstance(offset, PythonCoreBaseModel):
                params.update(offset.json_dict(by_alias=True))
            elif isinstance(offset, dict):
                params.update(offset)
            else:
                params["offset"] = offset
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/{node_id}/drafts",
            params=params,
            parse_json=True,
            type_=List[Optional[NodeDraftTransport]],
            **kwargs,
        )

    async def get_api_nodes_node_id_drafts_draft_id(
        self, node_id: str, draft_id: str, **kwargs: Any
    ) -> NodeDraftTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/{node_id}/drafts/{draft_id}",
            parse_json=True,
            type_=NodeDraftTransport,
            **kwargs,
        )

    async def get_api_nodes_visible_root_key(
        self, root_key: str, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/visible/{root_key}",
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_tree(
        self, space_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if space_id is not None:
            if isinstance(space_id, PythonCoreBaseModel):
                params.update(space_id.json_dict(by_alias=True))
            elif isinstance(space_id, dict):
                params.update(space_id)
            else:
                params["spaceId"] = space_id
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/tree",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_team_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-team/{team_domain}",
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_root_key_root_key(
        self,
        root_key: str,
        asset_type: Optional["str"] = None,
        node_type: Optional["ContentNodeType"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if node_type is not None:
            if isinstance(node_type, PythonCoreBaseModel):
                params.update(node_type.json_dict(by_alias=True))
            elif isinstance(node_type, dict):
                params.update(node_type)
            else:
                params["nodeType"] = node_type
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-root-key/{root_key}",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_root_id_root_id(
        self, root_id: str, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-root-id/{root_id}",
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_parent_key_parent_key(
        self, parent_key: str, root_key: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if root_key is not None:
            if isinstance(root_key, PythonCoreBaseModel):
                params.update(root_key.json_dict(by_alias=True))
            elif isinstance(root_key, dict):
                params.update(root_key)
            else:
                params["rootKey"] = root_key
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-parent-key/{parent_key}",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_key_usages(
        self, package_key: str, key: str, **kwargs: Any
    ) -> VariableUsageTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/{key}/usages",
            parse_json=True,
            type_=VariableUsageTransport,
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_usages(
        self, package_key: str, **kwargs: Any
    ) -> List[Optional[VariableUsageTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/usages",
            parse_json=True,
            type_=List[Optional[VariableUsageTransport]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_runtime(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinition]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/runtime",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinition]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_runtime_values(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableAssignment]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/runtime-values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableAssignment]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_runtime_definitions_with_values(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinitionWithValue]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/runtime-definitions-with-values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinitionWithValue]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_definitions_with_values(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinitionWithValue]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/definitions-with-values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinitionWithValue]],
            **kwargs,
        )

    async def get_api_nodes_by_package_key_package_key_variables_definition_with_value_by_key_key(
        self, package_key: str, key: str, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> VariableDefinitionWithValue:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/nodes/by-package-key/{package_key}/variables/definition-with-value/by-key/{key}",
            params=params,
            parse_json=True,
            type_=VariableDefinitionWithValue,
            **kwargs,
        )

    async def get_api_nodes_asset_export_key(self, key: str, **kwargs: Any) -> BaseNodeExportTransport:
        return await self.client.request(
            method="GET", url=f"/api/nodes/asset/export/{key}", parse_json=True, type_=BaseNodeExportTransport, **kwargs
        )

    async def get_api_node_by_key_node_key_users_with_permissions(
        self,
        node_key: str,
        permissions_to_filter_by: Optional["List[Optional[str]]"] = None,
        is_draft: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[UserTransport]]:
        params: Dict[str, Any] = {}
        if permissions_to_filter_by is not None:
            if isinstance(permissions_to_filter_by, PythonCoreBaseModel):
                params.update(permissions_to_filter_by.json_dict(by_alias=True))
            elif isinstance(permissions_to_filter_by, dict):
                params.update(permissions_to_filter_by)
            else:
                params["permissionsToFilterBy"] = permissions_to_filter_by
        if is_draft is not None:
            if isinstance(is_draft, PythonCoreBaseModel):
                params.update(is_draft.json_dict(by_alias=True))
            elif isinstance(is_draft, dict):
                params.update(is_draft)
            else:
                params["isDraft"] = is_draft
        return await self.client.request(
            method="GET",
            url=f"/api/node/by-key/{node_key}/users-with-permissions",
            params=params,
            parse_json=True,
            type_=List[Optional[UserTransport]],
            **kwargs,
        )

    async def get_api_final_nodes(
        self, space_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if space_id is not None:
            if isinstance(space_id, PythonCoreBaseModel):
                params.update(space_id.json_dict(by_alias=True))
            elif isinstance(space_id, dict):
                params.update(space_id)
            else:
                params["spaceId"] = space_id
        return await self.client.request(
            method="GET",
            url=f"/api/final-nodes",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_final_nodes_id(
        self, id: str, is_draft: Optional["bool"] = None, **kwargs: Any
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if is_draft is not None:
            if isinstance(is_draft, PythonCoreBaseModel):
                params.update(is_draft.json_dict(by_alias=True))
            elif isinstance(is_draft, dict):
                params.update(is_draft)
            else:
                params["isDraft"] = is_draft
        return await self.client.request(
            method="GET",
            url=f"/api/final-nodes/{id}",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_embedded_final_nodes_id(self, id: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="GET", url=f"/api/embedded/final-nodes/{id}", parse_json=True, type_=ContentNodeTransport, **kwargs
        )

    async def get_api_compute_pools(self, **kwargs: Any) -> List[Optional[ComputePoolTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools",
            parse_json=True,
            type_=List[Optional[ComputePoolTransport]],
            **kwargs,
        )

    async def get_api_compute_pools_nodes_status(
        self, **kwargs: Any
    ) -> List[Optional[ComputeNodeWithStatusDescriptor]]:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/nodes/status",
            parse_json=True,
            type_=List[Optional[ComputeNodeWithStatusDescriptor]],
            **kwargs,
        )

    async def get_api_compute_pools_data_models(self, **kwargs: Any) -> List[Optional[ComputeNodeDescriptor]]:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/data-models",
            parse_json=True,
            type_=List[Optional[ComputeNodeDescriptor]],
            **kwargs,
        )

    async def get_api_compute_pools_data_models_data_model_id(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/data-models/{data_model_id}",
            parse_json=True,
            type_=DataModelTransport,
            **kwargs,
        )

    async def get_api_compute_pools_data_models_data_model_id_graph_positioning(
        self, data_model_id: str, **kwargs: Any
    ) -> DataModelGraphPositioningTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/data-models/{data_model_id}/graph-positioning",
            parse_json=True,
            type_=DataModelGraphPositioningTransport,
            **kwargs,
        )

    async def get_api_compute_pools_data_models_for_process_type_process_type(
        self, process_type: ProcessType, return_invalid_data_models: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[DataModelPreviewTransport]]:
        params: Dict[str, Any] = {}
        if return_invalid_data_models is not None:
            if isinstance(return_invalid_data_models, PythonCoreBaseModel):
                params.update(return_invalid_data_models.json_dict(by_alias=True))
            elif isinstance(return_invalid_data_models, dict):
                params.update(return_invalid_data_models)
            else:
                params["returnInvalidDataModels"] = return_invalid_data_models
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/data-models/for-process-type/{process_type}",
            params=params,
            parse_json=True,
            type_=List[Optional[DataModelPreviewTransport]],
            **kwargs,
        )

    async def get_api_compute_pools_data_models_assigned(
        self, package_key: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[StudioDataModelTransport]]:
        params: Dict[str, Any] = {}
        if package_key is not None:
            if isinstance(package_key, PythonCoreBaseModel):
                params.update(package_key.json_dict(by_alias=True))
            elif isinstance(package_key, dict):
                params.update(package_key)
            else:
                params["packageKey"] = package_key
        return await self.client.request(
            method="GET",
            url=f"/api/compute-pools/data-models/assigned",
            params=params,
            parse_json=True,
            type_=List[Optional[StudioDataModelTransport]],
            **kwargs,
        )

    async def get_api_asset_nodes_manage_permissions_object_id_model(
        self, object_id: str, **kwargs: Any
    ) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/asset-nodes/manage-permissions/{object_id}/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def delete_api_packages_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/packages/{id}", **kwargs)

    async def get_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="GET", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def put_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="PUT", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def post_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="POST", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def delete_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="DELETE", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def options_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="OPTIONS", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def head_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="HEAD", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )

    async def patch_error(self, **kwargs: Any) -> Dict[str, Optional[Any]]:
        return await self.client.request(
            method="PATCH", url=f"/error", parse_json=True, type_=Dict[str, Optional[Any]], **kwargs
        )


class PackageManagerClient(PackageManagerClientBase):
    async def get_api_internal_nodes_id(
        self, id: str, draft_id: Optional["str"] = None, published: Optional["bool"] = None, **kwargs: Any
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if draft_id is not None:
            if isinstance(draft_id, PythonCoreBaseModel):
                params.update(draft_id.json_dict(by_alias=True))
            elif isinstance(draft_id, dict):
                params.update(draft_id)
            else:
                params["draftId"] = draft_id
        if published is not None:
            if isinstance(published, PythonCoreBaseModel):
                params.update(published.json_dict(by_alias=True))
            elif isinstance(published, dict):
                params.update(published)
            else:
                params["published"] = published
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/{id}",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def put_api_internal_nodes_id(
        self, id: str, request_body: SaveContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/internal/nodes/{id}",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def delete_api_internal_nodes_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/nodes/{id}", **kwargs)

    async def put_api_internal_node_storage_id(
        self, id: str, request_body: NodeStorageTransport, **kwargs: Any
    ) -> NodeStorageTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/internal/node-storage/{id}",
            request_body=request_body,
            parse_json=True,
            type_=NodeStorageTransport,
            **kwargs,
        )

    async def put_api_internal_attachments_id(
        self, id: str, request_body: AttachmentTransport, **kwargs: Any
    ) -> AttachmentTransport:
        return await self.client.request(
            method="PUT",
            url=f"/api/internal/attachments/{id}",
            request_body=request_body,
            parse_json=True,
            type_=AttachmentTransport,
            **kwargs,
        )

    async def post_api_internal_widget_blocks_widget_id_enable(
        self, widget_id: str, request_body: List[Optional[str]], **kwargs: Any
    ) -> WidgetLicensableFeatureTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/widget-blocks/{widget_id}/enable",
            request_body=request_body,
            parse_json=True,
            type_=WidgetLicensableFeatureTransport,
            **kwargs,
        )

    async def post_api_internal_widget_blocks_widget_id_enable_for_all(
        self, widget_id: str, **kwargs: Any
    ) -> WidgetLicensableFeatureTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/widget-blocks/{widget_id}/enable-for-all",
            parse_json=True,
            type_=WidgetLicensableFeatureTransport,
            **kwargs,
        )

    async def post_api_internal_widget_blocks_widget_id_disable(
        self, widget_id: str, request_body: List[Optional[str]], **kwargs: Any
    ) -> WidgetLicensableFeatureTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/widget-blocks/{widget_id}/disable",
            request_body=request_body,
            parse_json=True,
            type_=WidgetLicensableFeatureTransport,
            **kwargs,
        )

    async def post_api_internal_widget_blocks_widget_id_disable_for_all(
        self, widget_id: str, **kwargs: Any
    ) -> WidgetLicensableFeatureTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/widget-blocks/{widget_id}/disable-for-all",
            parse_json=True,
            type_=WidgetLicensableFeatureTransport,
            **kwargs,
        )

    async def post_api_internal_variables(
        self, request_body: VariableDefinitionWithValue, package_key: Optional["str"] = None, **kwargs: Any
    ) -> VariableDefinitionWithValue:
        params: Dict[str, Any] = {}
        if package_key is not None:
            if isinstance(package_key, PythonCoreBaseModel):
                params.update(package_key.json_dict(by_alias=True))
            elif isinstance(package_key, dict):
                params.update(package_key)
            else:
                params["packageKey"] = package_key
        return await self.client.request(
            method="POST",
            url=f"/api/internal/variables",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=VariableDefinitionWithValue,
            **kwargs,
        )

    async def post_api_internal_variables_by_content_node_id_content_node_id(
        self, content_node_id: str, request_body: VariablesDefinitionsTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/variables/by-content-node-id/{content_node_id}",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_internal_variables_assignment_rule_by_package_key_package_key_key_value(
        self,
        package_key: str,
        key: str,
        request_body: List[Optional[AssignmentRuleAttributeValuesTransport]],
        **kwargs: Any,
    ) -> AssignmentRuleAssigneeValueTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/variables/assignment-rule/by-package-key/{package_key}/{key}/value",
            request_body=request_body,
            parse_json=True,
            type_=AssignmentRuleAssigneeValueTransport,
            **kwargs,
        )

    async def post_api_internal_variable_assignments_by_content_node_id_content_node_id(
        self, content_node_id: str, request_body: VariablesAssignmentsTransport, **kwargs: Any
    ) -> SerializedVariablesAssignmentsTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/variable-assignments/by-content-node-id/{content_node_id}",
            request_body=request_body,
            parse_json=True,
            type_=SerializedVariablesAssignmentsTransport,
            **kwargs,
        )

    async def post_api_internal_v2_clone(
        self, request_body: CloneRequestTransport, **kwargs: Any
    ) -> CloneResultTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/v2/clone",
            request_body=request_body,
            parse_json=True,
            type_=CloneResultTransport,
            **kwargs,
        )

    async def post_api_internal_teams_team_id_erase(
        self, team_id: str, **kwargs: Any
    ) -> List[Optional[EraserLogMessageTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/teams/{team_id}/erase",
            parse_json=True,
            type_=List[Optional[EraserLogMessageTransport]],
            **kwargs,
        )

    async def get_api_internal_spaces(self, **kwargs: Any) -> List[Optional[SpaceTransport]]:
        return await self.client.request(
            method="GET", url=f"/api/internal/spaces", parse_json=True, type_=List[Optional[SpaceTransport]], **kwargs
        )

    async def post_api_internal_spaces(self, request_body: SpaceSaveTransport, **kwargs: Any) -> SpaceTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/spaces",
            request_body=request_body,
            parse_json=True,
            type_=SpaceTransport,
            **kwargs,
        )

    async def get_api_internal_service_permissions(self, **kwargs: Any) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_service_permissions(
        self, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/service-permissions/",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_secured_permissions_import(
        self, request_body: List[Optional[PermissionsImportTransport]], **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/secured/permissions/import", request_body=request_body, **kwargs
        )

    async def post_api_internal_preferences(
        self, request_body: List[Optional[SavePreferenceTransport]], with_id: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[PreferencesTransport]]:
        params: Dict[str, Any] = {}
        if with_id is not None:
            if isinstance(with_id, PythonCoreBaseModel):
                params.update(with_id.json_dict(by_alias=True))
            elif isinstance(with_id, dict):
                params.update(with_id)
            else:
                params["withId"] = with_id
        return await self.client.request(
            method="POST",
            url=f"/api/internal/preferences",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[PreferencesTransport]],
            **kwargs,
        )

    async def post_api_internal_preferences_update(
        self, request_body: List[Optional[SavePreferenceTransport]], **kwargs: Any
    ) -> List[Optional[PreferencesTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/preferences/update",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[PreferencesTransport]],
            **kwargs,
        )

    async def post_api_internal_preferences_delete(self, request_body: List[Optional[str]], **kwargs: Any) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/preferences/delete", request_body=request_body, **kwargs
        )

    async def post_api_internal_packages_key_activate(
        self, key: str, request_body: ActivatePackageTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/packages/{key}/activate", request_body=request_body, **kwargs
        )

    async def post_api_internal_packages_with_variable_assignments_by_data_model_ids(
        self, request_body: List[Optional[str]], app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PackageWithVariableAssignments]]:
        params: Dict[str, Any] = {}
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="POST",
            url=f"/api/internal/packages/with-variable-assignments/by-data-model-ids",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[PackageWithVariableAssignments]],
            **kwargs,
        )

    async def post_api_internal_packages_import(
        self, request_body: Dict[str, Any], space_id: Optional["str"] = None, key: Optional["str"] = None, **kwargs: Any
    ) -> None:
        params: Dict[str, Any] = {}
        if space_id is not None:
            if isinstance(space_id, PythonCoreBaseModel):
                params.update(space_id.json_dict(by_alias=True))
            elif isinstance(space_id, dict):
                params.update(space_id)
            else:
                params["spaceId"] = space_id
        if key is not None:
            if isinstance(key, PythonCoreBaseModel):
                params.update(key.json_dict(by_alias=True))
            elif isinstance(key, dict):
                params.update(key)
            else:
                params["key"] = key
        return await self.client.request(
            method="POST", url=f"/api/internal/packages/import", params=params, request_body=request_body, **kwargs
        )

    async def get_api_internal_package_nodes_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/package-nodes/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_package_nodes_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/package-nodes/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes(
        self,
        asset_type: Optional["str"] = None,
        without_content: Optional["bool"] = None,
        active: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if without_content is not None:
            if isinstance(without_content, PythonCoreBaseModel):
                params.update(without_content.json_dict(by_alias=True))
            elif isinstance(without_content, dict):
                params.update(without_content)
            else:
                params["withoutContent"] = without_content
        if active is not None:
            if isinstance(active, PythonCoreBaseModel):
                params.update(active.json_dict(by_alias=True))
            elif isinstance(active, dict):
                params.update(active)
            else:
                params["active"] = active
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_nodes(
        self,
        request_body: SaveContentNodeTransport,
        validate_: Optional["bool"] = None,
        with_id: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if validate_ is not None:
            if isinstance(validate_, PythonCoreBaseModel):
                params.update(validate_.json_dict(by_alias=True))
            elif isinstance(validate_, dict):
                params.update(validate_)
            else:
                params["validate"] = validate_
        if with_id is not None:
            if isinstance(with_id, PythonCoreBaseModel):
                params.update(with_id.json_dict(by_alias=True))
            elif isinstance(with_id, dict):
                params.update(with_id)
            else:
                params["withId"] = with_id
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_internal_nodes_id_checkpoint(
        self, id: str, request_body: SaveContentNodeTransport, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/{id}/checkpoint",
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_internal_nodes_id_activate(
        self, id: str, request_body: ActivatePackageTransport, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="POST", url=f"/api/internal/nodes/{id}/activate", request_body=request_body, **kwargs
        )

    async def post_api_internal_nodes_find_by_keys(
        self,
        request_body: List[Optional[str]],
        asset_type: Optional["str"] = None,
        active: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if active is not None:
            if isinstance(active, PythonCoreBaseModel):
                params.update(active.json_dict(by_alias=True))
            elif isinstance(active, dict):
                params.update(active)
            else:
                params["active"] = active
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/find-by-keys",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_nodes_documents(
        self, request_body: Dict[str, Any], root_node_id: Optional["str"] = None, **kwargs: Any
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if root_node_id is not None:
            if isinstance(root_node_id, PythonCoreBaseModel):
                params.update(root_node_id.json_dict(by_alias=True))
            elif isinstance(root_node_id, dict):
                params.update(root_node_id)
            else:
                params["rootNodeId"] = root_node_id
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/documents",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_internal_nodes_documents_batch_by_root_id_root_id(
        self, root_id: str, request_body: Dict[str, Any], **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/documents/batch/by-root-id/{root_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_nodes_by_keys_published(
        self, request_body: List[Optional[str]], asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/by-keys/published",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_nodes_batch_update_by_root_key_root_key(
        self, root_key: str, request_body: List[Optional[ContentNodeTransport]], **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/batch/update/by-root-key/{root_key}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_nodes_batch_by_root_key_root_key(
        self, root_key: str, request_body: List[Optional[ContentNodeTransport]], **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/nodes/batch/by-root-key/{root_key}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_node_storage(
        self, request_body: SaveNodeStorageTransport, **kwargs: Any
    ) -> NodeStorageTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/node-storage",
            request_body=request_body,
            parse_json=True,
            type_=NodeStorageTransport,
            **kwargs,
        )

    async def post_api_internal_final_nodes_find_by_keys(
        self,
        request_body: List[Optional[str]],
        asset_type: Optional["str"] = None,
        draft_mode: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if draft_mode is not None:
            if isinstance(draft_mode, PythonCoreBaseModel):
                params.update(draft_mode.json_dict(by_alias=True))
            elif isinstance(draft_mode, dict):
                params.update(draft_mode)
            else:
                params["draftMode"] = draft_mode
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="POST",
            url=f"/api/internal/final-nodes/find-by-keys",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_final_nodes_by_root_keys(
        self,
        request_body: List[Optional[str]],
        asset_type: Optional["str"] = None,
        draft_mode: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if draft_mode is not None:
            if isinstance(draft_mode, PythonCoreBaseModel):
                params.update(draft_mode.json_dict(by_alias=True))
            elif isinstance(draft_mode, dict):
                params.update(draft_mode)
            else:
                params["draftMode"] = draft_mode
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="POST",
            url=f"/api/internal/final-nodes/by-root-keys",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_final_nodes_by_keys(
        self,
        request_body: List[Optional[str]],
        root_node_key: Optional["str"] = None,
        draft: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if root_node_key is not None:
            if isinstance(root_node_key, PythonCoreBaseModel):
                params.update(root_node_key.json_dict(by_alias=True))
            elif isinstance(root_node_key, dict):
                params.update(root_node_key)
            else:
                params["rootNodeKey"] = root_node_key
        if draft is not None:
            if isinstance(draft, PythonCoreBaseModel):
                params.update(draft.json_dict(by_alias=True))
            elif isinstance(draft, dict):
                params.update(draft)
            else:
                params["draft"] = draft
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="POST",
            url=f"/api/internal/final-nodes/by-keys",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def post_api_internal_final_nodes_build(
        self,
        request_body: ContentNodeTransport,
        should_validate: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if should_validate is not None:
            if isinstance(should_validate, PythonCoreBaseModel):
                params.update(should_validate.json_dict(by_alias=True))
            elif isinstance(should_validate, dict):
                params.update(should_validate)
            else:
                params["shouldValidate"] = should_validate
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="POST",
            url=f"/api/internal/final-nodes/build",
            params=params,
            request_body=request_body,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def post_api_internal_attachments(
        self, request_body: SaveAttachmentTransport, **kwargs: Any
    ) -> AttachmentTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/attachments",
            request_body=request_body,
            parse_json=True,
            type_=AttachmentTransport,
            **kwargs,
        )

    async def get_api_internal_asset_nodes_manage_permissions_object_id(
        self, object_id: str, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/asset-nodes/manage-permissions/{object_id}",
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def post_api_internal_asset_nodes_manage_permissions_object_id(
        self, object_id: str, request_body: List[Optional[AccessControlEntryTransport]], **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/asset-nodes/manage-permissions/{object_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_api_internal_app_features_team_id(self, team_id: str, **kwargs: Any) -> List[Optional[AppFeature]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/app/features/{team_id}",
            parse_json=True,
            type_=List[Optional[AppFeature]],
            **kwargs,
        )

    async def post_api_internal_app_features_team_id(
        self, team_id: str, request_body: List[Optional[AppFeature]], **kwargs: Any
    ) -> List[Optional[AppFeature]]:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/app/features/{team_id}",
            request_body=request_body,
            parse_json=True,
            type_=List[Optional[AppFeature]],
            **kwargs,
        )

    async def delete_api_internal_app_features_team_id(self, team_id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/app/features/{team_id}", **kwargs)

    async def get_api_internal_variables_by_package_key_package_key_variables(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinition]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/internal/variables/by-package-key/{package_key}/variables",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinition]],
            **kwargs,
        )

    async def get_api_internal_variables_by_package_key_package_key_variables_values(
        self, package_key: str, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableAssignment]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/internal/variables/by-package-key/{package_key}/variables/values",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableAssignment]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_overview(self, **kwargs: Any) -> PermissionsOverviewTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/overview",
            parse_json=True,
            type_=PermissionsOverviewTransport,
            **kwargs,
        )

    async def get_api_internal_service_permissions_model(self, **kwargs: Any) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_service_permissions_all(
        self, subject_id: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[AccessControlEntryTransport]]:
        params: Dict[str, Any] = {}
        if subject_id is not None:
            if isinstance(subject_id, PythonCoreBaseModel):
                params.update(subject_id.json_dict(by_alias=True))
            elif isinstance(subject_id, dict):
                params.update(subject_id)
            else:
                params["subjectId"] = subject_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/all",
            params=params,
            parse_json=True,
            type_=List[Optional[AccessControlEntryTransport]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_acl(
        self, **kwargs: Any
    ) -> List[Optional[AccessControlListTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions/acl",
            parse_json=True,
            type_=List[Optional[AccessControlListTransport]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_evaluated_current_user(self, **kwargs: Any) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions-evaluated/current-user",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_internal_service_permissions_evaluated_current_user_team_domain(
        self, team_domain: str, **kwargs: Any
    ) -> List[Optional[str]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/service-permissions-evaluated/current-user/{team_domain}",
            parse_json=True,
            type_=List[Optional[str]],
            **kwargs,
        )

    async def get_api_internal_packages(self, **kwargs: Any) -> List[Optional[ContentNodeTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages",
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_packages_with_variable_assignments(
        self, type_: Optional["str"] = None, app_mode: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[PackageWithVariableAssignments]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if app_mode is not None:
            if isinstance(app_mode, PythonCoreBaseModel):
                params.update(app_mode.json_dict(by_alias=True))
            elif isinstance(app_mode, dict):
                params.update(app_mode)
            else:
                params["appMode"] = app_mode
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages/with-variable-assignments",
            params=params,
            parse_json=True,
            type_=List[Optional[PackageWithVariableAssignments]],
            **kwargs,
        )

    async def get_api_internal_packages_keys(
        self, team_ids: Optional["List[Optional[str]]"] = None, **kwargs: Any
    ) -> List[Optional[TeamRootNodeKeysTransport]]:
        params: Dict[str, Any] = {}
        if team_ids is not None:
            if isinstance(team_ids, PythonCoreBaseModel):
                params.update(team_ids.json_dict(by_alias=True))
            elif isinstance(team_ids, dict):
                params.update(team_ids)
            else:
                params["teamIds"] = team_ids
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages/keys",
            params=params,
            parse_json=True,
            type_=List[Optional[TeamRootNodeKeysTransport]],
            **kwargs,
        )

    async def get_api_internal_packages_installed(self, **kwargs: Any) -> List[Optional[PackageSummary]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages/installed",
            parse_json=True,
            type_=List[Optional[PackageSummary]],
            **kwargs,
        )

    async def get_api_internal_packages_installed_package_key(
        self, package_key: str, **kwargs: Any
    ) -> List[Optional[PackageSummary]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages/installed/{package_key}",
            parse_json=True,
            type_=List[Optional[PackageSummary]],
            **kwargs,
        )

    async def get_api_internal_packages_check_create_permissions(
        self, space_id: Optional["str"] = None, **kwargs: Any
    ) -> PermissionCheckResult:
        params: Dict[str, Any] = {}
        if space_id is not None:
            if isinstance(space_id, PythonCoreBaseModel):
                params.update(space_id.json_dict(by_alias=True))
            elif isinstance(space_id, dict):
                params.update(space_id)
            else:
                params["spaceId"] = space_id
        return await self.client.request(
            method="GET",
            url=f"/api/internal/packages/check-create-permissions",
            params=params,
            parse_json=True,
            type_=PermissionCheckResult,
            **kwargs,
        )

    async def get_api_internal_package_nodes_manage_permissions_model(self, **kwargs: Any) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/package-nodes/manage-permissions/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_nodes_root_key_key_usages(
        self,
        root_key: str,
        key: str,
        target_object_id: Optional["str"] = None,
        target_object_type: Optional["str"] = None,
        **kwargs: Any,
    ) -> List[Optional[NodeUsageTransport]]:
        params: Dict[str, Any] = {}
        if target_object_id is not None:
            if isinstance(target_object_id, PythonCoreBaseModel):
                params.update(target_object_id.json_dict(by_alias=True))
            elif isinstance(target_object_id, dict):
                params.update(target_object_id)
            else:
                params["targetObjectId"] = target_object_id
        if target_object_type is not None:
            if isinstance(target_object_type, PythonCoreBaseModel):
                params.update(target_object_type.json_dict(by_alias=True))
            elif isinstance(target_object_type, dict):
                params.update(target_object_type)
            else:
                params["targetObjectType"] = target_object_type
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/{root_key}/{key}/usages",
            params=params,
            parse_json=True,
            type_=List[Optional[NodeUsageTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_without_content_id(self, id: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/without-content/{id}",
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_nodes_without_content_by_key_key(self, key: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/without-content/by-key/{key}",
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_nodes_documents_id(self, id: str, **kwargs: Any) -> DocumentTransport:
        return await self.client.request(
            method="GET", url=f"/api/internal/nodes/documents/{id}", parse_json=True, type_=DocumentTransport, **kwargs
        )

    async def get_api_internal_nodes_documents_by_key_key(self, key: str, **kwargs: Any) -> DocumentTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/documents/by-key/{key}",
            parse_json=True,
            type_=DocumentTransport,
            **kwargs,
        )

    async def get_api_internal_nodes_by_root_key_root_key(
        self,
        root_key: str,
        asset_type: Optional["str"] = None,
        active: Optional["bool"] = None,
        without_content: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if active is not None:
            if isinstance(active, PythonCoreBaseModel):
                params.update(active.json_dict(by_alias=True))
            elif isinstance(active, dict):
                params.update(active)
            else:
                params["active"] = active
        if without_content is not None:
            if isinstance(without_content, PythonCoreBaseModel):
                params.update(without_content.json_dict(by_alias=True))
            elif isinstance(without_content, dict):
                params.update(without_content)
            else:
                params["withoutContent"] = without_content
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/by-root-key/{root_key}",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_by_root_id_root_id(
        self,
        root_id: str,
        asset_type: Optional["str"] = None,
        active: Optional["bool"] = None,
        without_content: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if active is not None:
            if isinstance(active, PythonCoreBaseModel):
                params.update(active.json_dict(by_alias=True))
            elif isinstance(active, dict):
                params.update(active)
            else:
                params["active"] = active
        if without_content is not None:
            if isinstance(without_content, PythonCoreBaseModel):
                params.update(without_content.json_dict(by_alias=True))
            elif isinstance(without_content, dict):
                params.update(without_content)
            else:
                params["withoutContent"] = without_content
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/by-root-id/{root_id}",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_by_key_key(self, key: str, **kwargs: Any) -> ContentNodeTransport:
        return await self.client.request(
            method="GET", url=f"/api/internal/nodes/by-key/{key}", parse_json=True, type_=ContentNodeTransport, **kwargs
        )

    async def get_api_internal_nodes_by_key_key_variables(
        self, key: str, type_: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[VariableDefinition]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/by-key/{key}/variables",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableDefinition]],
            **kwargs,
        )

    async def get_api_internal_nodes_by_key_key_variables_assignments(
        self, key: str, type_: Optional["str"] = None, published: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[VariableAssignment]]:
        params: Dict[str, Any] = {}
        if type_ is not None:
            if isinstance(type_, PythonCoreBaseModel):
                params.update(type_.json_dict(by_alias=True))
            elif isinstance(type_, dict):
                params.update(type_)
            else:
                params["type"] = type_
        if published is not None:
            if isinstance(published, PythonCoreBaseModel):
                params.update(published.json_dict(by_alias=True))
            elif isinstance(published, dict):
                params.update(published)
            else:
                params["published"] = published
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/by-key/{key}/variables-assignments",
            params=params,
            parse_json=True,
            type_=List[Optional[VariableAssignment]],
            **kwargs,
        )

    async def get_api_internal_nodes_by_key_key_drafts_draft_id(
        self, key: str, draft_id: str, **kwargs: Any
    ) -> ContentNodeTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/by-key/{key}/drafts/{draft_id}",
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_nodes_bases_by_root_key(
        self, root_key: Optional["str"] = None, asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if root_key is not None:
            if isinstance(root_key, PythonCoreBaseModel):
                params.update(root_key.json_dict(by_alias=True))
            elif isinstance(root_key, dict):
                params.update(root_key)
            else:
                params["rootKey"] = root_key
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/bases/by-root-key",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_bases_with_root_details_external_by_root_key(
        self, root_key: Optional["str"] = None, asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeWithRootDetailsTransport]]:
        params: Dict[str, Any] = {}
        if root_key is not None:
            if isinstance(root_key, PythonCoreBaseModel):
                params.update(root_key.json_dict(by_alias=True))
            elif isinstance(root_key, dict):
                params.update(root_key)
            else:
                params["rootKey"] = root_key
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/bases-with-root-details/external/by-root-key",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeWithRootDetailsTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_bases_with_root_details_by_root_key(
        self, root_key: Optional["str"] = None, asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[ContentNodeWithRootDetailsTransport]]:
        params: Dict[str, Any] = {}
        if root_key is not None:
            if isinstance(root_key, PythonCoreBaseModel):
                params.update(root_key.json_dict(by_alias=True))
            elif isinstance(root_key, dict):
                params.update(root_key)
            else:
                params["rootKey"] = root_key
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/bases-with-root-details/by-root-key",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeWithRootDetailsTransport]],
            **kwargs,
        )

    async def get_api_internal_nodes_assigned_data_models_by_root_key_root_key(
        self, root_key: str, **kwargs: Any
    ) -> List[Optional[StudioDataModelTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/nodes/assigned-data-models/by-root-key/{root_key}",
            parse_json=True,
            type_=List[Optional[StudioDataModelTransport]],
            **kwargs,
        )

    async def get_api_internal_node_by_key_node_key_users_with_permissions(
        self,
        node_key: str,
        permissions_to_filter_by: Optional["List[Optional[str]]"] = None,
        is_draft: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[UserTransport]]:
        params: Dict[str, Any] = {}
        if permissions_to_filter_by is not None:
            if isinstance(permissions_to_filter_by, PythonCoreBaseModel):
                params.update(permissions_to_filter_by.json_dict(by_alias=True))
            elif isinstance(permissions_to_filter_by, dict):
                params.update(permissions_to_filter_by)
            else:
                params["permissionsToFilterBy"] = permissions_to_filter_by
        if is_draft is not None:
            if isinstance(is_draft, PythonCoreBaseModel):
                params.update(is_draft.json_dict(by_alias=True))
            elif isinstance(is_draft, dict):
                params.update(is_draft)
            else:
                params["isDraft"] = is_draft
        return await self.client.request(
            method="GET",
            url=f"/api/internal/node/by-key/{node_key}/users-with-permissions",
            params=params,
            parse_json=True,
            type_=List[Optional[UserTransport]],
            **kwargs,
        )

    async def get_api_internal_final_nodes(
        self,
        asset_type: Optional["str"] = None,
        draft_mode: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if draft_mode is not None:
            if isinstance(draft_mode, PythonCoreBaseModel):
                params.update(draft_mode.json_dict(by_alias=True))
            elif isinstance(draft_mode, dict):
                params.update(draft_mode)
            else:
                params["draftMode"] = draft_mode
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_final_nodes_id(
        self,
        id: str,
        version: Optional["str"] = None,
        draft: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if version is not None:
            if isinstance(version, PythonCoreBaseModel):
                params.update(version.json_dict(by_alias=True))
            elif isinstance(version, dict):
                params.update(version)
            else:
                params["version"] = version
        if draft is not None:
            if isinstance(draft, PythonCoreBaseModel):
                params.update(draft.json_dict(by_alias=True))
            elif isinstance(draft, dict):
                params.update(draft)
            else:
                params["draft"] = draft
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/{id}",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_draft_by_key_key_with_options(
        self,
        key: str,
        with_variable_replacement: Optional["bool"] = None,
        with_resolved_scopes: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        if with_resolved_scopes is not None:
            if isinstance(with_resolved_scopes, PythonCoreBaseModel):
                params.update(with_resolved_scopes.json_dict(by_alias=True))
            elif isinstance(with_resolved_scopes, dict):
                params.update(with_resolved_scopes)
            else:
                params["withResolvedScopes"] = with_resolved_scopes
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/draft/by-key/{key}/with-options",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_documents_id(
        self, id: str, is_draft: Optional["bool"] = None, **kwargs: Any
    ) -> DocumentTransport:
        params: Dict[str, Any] = {}
        if is_draft is not None:
            if isinstance(is_draft, PythonCoreBaseModel):
                params.update(is_draft.json_dict(by_alias=True))
            elif isinstance(is_draft, dict):
                params.update(is_draft)
            else:
                params["isDraft"] = is_draft
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/documents/{id}",
            params=params,
            parse_json=True,
            type_=DocumentTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_documents_by_key_key(
        self, key: str, is_draft: Optional["bool"] = None, **kwargs: Any
    ) -> DocumentTransport:
        params: Dict[str, Any] = {}
        if is_draft is not None:
            if isinstance(is_draft, PythonCoreBaseModel):
                params.update(is_draft.json_dict(by_alias=True))
            elif isinstance(is_draft, dict):
                params.update(is_draft)
            else:
                params["isDraft"] = is_draft
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/documents/by-key/{key}",
            params=params,
            parse_json=True,
            type_=DocumentTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_by_root_key_key(
        self,
        key: str,
        asset_type: Optional["str"] = None,
        draft_mode: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[ContentNodeTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if draft_mode is not None:
            if isinstance(draft_mode, PythonCoreBaseModel):
                params.update(draft_mode.json_dict(by_alias=True))
            elif isinstance(draft_mode, dict):
                params.update(draft_mode)
            else:
                params["draftMode"] = draft_mode
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/by-root-key/{key}",
            params=params,
            parse_json=True,
            type_=List[Optional[ContentNodeTransport]],
            **kwargs,
        )

    async def get_api_internal_final_nodes_by_key_key(
        self,
        key: str,
        version: Optional["str"] = None,
        draft: Optional["bool"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if version is not None:
            if isinstance(version, PythonCoreBaseModel):
                params.update(version.json_dict(by_alias=True))
            elif isinstance(version, dict):
                params.update(version)
            else:
                params["version"] = version
        if draft is not None:
            if isinstance(draft, PythonCoreBaseModel):
                params.update(draft.json_dict(by_alias=True))
            elif isinstance(draft, dict):
                params.update(draft)
            else:
                params["draft"] = draft
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/by-key/{key}",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_by_key_key_base(
        self,
        key: str,
        version: Optional["str"] = None,
        base_version: Optional["str"] = None,
        draft: Optional["bool"] = None,
        **kwargs: Any,
    ) -> ContentNodeTransport:
        params: Dict[str, Any] = {}
        if version is not None:
            if isinstance(version, PythonCoreBaseModel):
                params.update(version.json_dict(by_alias=True))
            elif isinstance(version, dict):
                params.update(version)
            else:
                params["version"] = version
        if base_version is not None:
            if isinstance(base_version, PythonCoreBaseModel):
                params.update(base_version.json_dict(by_alias=True))
            elif isinstance(base_version, dict):
                params.update(base_version)
            else:
                params["baseVersion"] = base_version
        if draft is not None:
            if isinstance(draft, PythonCoreBaseModel):
                params.update(draft.json_dict(by_alias=True))
            elif isinstance(draft, dict):
                params.update(draft)
            else:
                params["draft"] = draft
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/by-key/{key}/base",
            params=params,
            parse_json=True,
            type_=ContentNodeTransport,
            **kwargs,
        )

    async def get_api_internal_final_nodes_all_teams(
        self, asset_type: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[TeamNodesTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/all-teams",
            params=params,
            parse_json=True,
            type_=List[Optional[TeamNodesTransport]],
            **kwargs,
        )

    async def get_api_internal_final_nodes_all_teams_all_teams_by_regex(
        self,
        asset_type: Optional["str"] = None,
        regex: Optional["str"] = None,
        with_variable_replacement: Optional["bool"] = None,
        **kwargs: Any,
    ) -> List[Optional[TeamNodesTransport]]:
        params: Dict[str, Any] = {}
        if asset_type is not None:
            if isinstance(asset_type, PythonCoreBaseModel):
                params.update(asset_type.json_dict(by_alias=True))
            elif isinstance(asset_type, dict):
                params.update(asset_type)
            else:
                params["assetType"] = asset_type
        if regex is not None:
            if isinstance(regex, PythonCoreBaseModel):
                params.update(regex.json_dict(by_alias=True))
            elif isinstance(regex, dict):
                params.update(regex)
            else:
                params["regex"] = regex
        if with_variable_replacement is not None:
            if isinstance(with_variable_replacement, PythonCoreBaseModel):
                params.update(with_variable_replacement.json_dict(by_alias=True))
            elif isinstance(with_variable_replacement, dict):
                params.update(with_variable_replacement)
            else:
                params["withVariableReplacement"] = with_variable_replacement
        return await self.client.request(
            method="GET",
            url=f"/api/internal/final-nodes/all-teams/all-teams/by-regex",
            params=params,
            parse_json=True,
            type_=List[Optional[TeamNodesTransport]],
            **kwargs,
        )

    async def get_api_internal_dimensions_for_data_model_data_model_id(
        self, data_model_id: str, **kwargs: Any
    ) -> List[Optional[DimensionTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/dimensions/for-data-model/{data_model_id}",
            parse_json=True,
            type_=List[Optional[DimensionTransport]],
            **kwargs,
        )

    async def get_api_internal_asset_nodes_manage_permissions_model(self, **kwargs: Any) -> PermissionsModelTransport:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/asset-nodes/manage-permissions/model",
            parse_json=True,
            type_=PermissionsModelTransport,
            **kwargs,
        )

    async def get_api_internal_app_features(self, **kwargs: Any) -> List[Optional[AppFeature]]:
        return await self.client.request(
            method="GET", url=f"/api/internal/app/features", parse_json=True, type_=List[Optional[AppFeature]], **kwargs
        )

    async def delete_api_internal_secured_spaces_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/secured/spaces/{id}", **kwargs)

    async def delete_api_internal_secured_packages_id(self, id: str, **kwargs: Any) -> None:
        return await self.client.request(method="DELETE", url=f"/api/internal/secured/packages/{id}", **kwargs)

    async def delete_api_internal_node_storage_by_term_contained_in_object_id_term(
        self, term: str, **kwargs: Any
    ) -> None:
        return await self.client.request(
            method="DELETE", url=f"/api/internal/node-storage/by-term-contained-in-object-id/{term}", **kwargs
        )

    pass


class PackageManagerExternalClient(PackageManagerClientBase):
    pass
