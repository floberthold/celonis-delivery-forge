import logging
import typing
import uuid
from abc import ABC
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr
from python_core_internal_client import AsyncClient, PythonCoreBaseEnum, PythonCoreBaseModel, PythonCoreDatetime

logger = logging.getLogger("python_core_internal_client.team")


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
    cloud_admin: Optional["bool"] = Field(None, alias="cloudAdmin")
    migrated_to_idp: Optional["bool"] = Field(None, alias="migratedToIdp")
    analyst: Optional["bool"] = Field(None, alias="analyst")
    member: Optional["bool"] = Field(None, alias="member")
    admin: Optional["bool"] = Field(None, alias="admin")
    name_or_email: Optional["str"] = Field(None, alias="nameOrEmail")
    name_and_email: Optional["str"] = Field(None, alias="nameAndEmail")


class UserServicePermissionsTransport(PythonCoreBaseModel):
    service_name: Optional["str"] = Field(None, alias="serviceName")
    permissions: Optional["List[Optional[str]]"] = Field(None, alias="permissions")


class ApplicationKeyTransport(PythonCoreBaseModel):
    id: Optional["str"] = Field(None, alias="id")
    name: Optional["str"] = Field(None, alias="name")
    key: Optional["str"] = Field(None, alias="key")
    created_at: Optional["PythonCoreDatetime"] = Field(None, alias="createdAt")
    last_used_at: Optional["PythonCoreDatetime"] = Field(None, alias="lastUsedAt")
    team_role: Optional["int"] = Field(None, alias="teamRole")
    ssh_enabled: Optional["bool"] = Field(None, alias="sshEnabled")


ExceptionReference.model_rebuild()
ValidationError.model_rebuild()
ValidationExceptionDescriptor.model_rebuild()
UserTransport.model_rebuild()
UserServicePermissionsTransport.model_rebuild()
ApplicationKeyTransport.model_rebuild()


class TeamClientBase(ABC):
    client: AsyncClient

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.client = AsyncClient(base_url=base_url, **kwargs)

    async def get_api_cloud(self, **kwargs: Any) -> UserTransport:
        return await self.client.request(
            method="GET", url=f"/api/cloud", parse_json=True, type_=UserTransport, **kwargs
        )

    async def get_api_cloud_permissions(self, **kwargs: Any) -> List[Optional[UserServicePermissionsTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/cloud/permissions",
            parse_json=True,
            type_=List[Optional[UserServicePermissionsTransport]],
            **kwargs,
        )


class TeamClient(TeamClientBase):
    async def get_api_internal_applications(self, **kwargs: Any) -> List[Optional[ApplicationKeyTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/api/internal/applications",
            parse_json=True,
            type_=List[Optional[ApplicationKeyTransport]],
            **kwargs,
        )

    async def post_api_internal_applications(
        self, request_body: ApplicationKeyTransport, **kwargs: Any
    ) -> ApplicationKeyTransport:
        return await self.client.request(
            method="POST",
            url=f"/api/internal/applications",
            request_body=request_body,
            parse_json=True,
            type_=ApplicationKeyTransport,
            **kwargs,
        )

    pass


class TeamExternalClient(TeamClientBase):
    pass
