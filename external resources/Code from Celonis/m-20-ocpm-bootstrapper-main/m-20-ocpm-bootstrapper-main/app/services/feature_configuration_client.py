import logging
import typing
import uuid
from abc import ABC
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr
from python_core_internal_client import AsyncClient, PythonCoreBaseEnum, PythonCoreBaseModel, PythonCoreDatetime

logger = logging.getLogger("python_core_internal_client.feature_configuration")


class SsoProtocol(PythonCoreBaseEnum):
    CELONIS_LOGIN = "CELONIS_LOGIN"
    IDP = "IDP"
    OIDC = "OIDC"
    SAML = "SAML"


class CelonisServiceTransport(PythonCoreBaseModel):
    feature_key: Optional["str"] = Field(None, alias="featureKey")
    frontend_app: Optional["bool"] = Field(None, alias="frontendApp")
    frontend_name: Optional["str"] = Field(None, alias="frontendName")
    icon: Optional["str"] = Field(None, alias="icon")
    min_role: Optional["int"] = Field(None, alias="minRole")
    order: Optional["int"] = Field(None, alias="order")
    path: Optional["str"] = Field(None, alias="path")
    pinned_by_default: Optional["bool"] = Field(None, alias="pinnedByDefault")


class ConfigValue(PythonCoreBaseModel):
    value: Optional["str"] = Field(None, alias="value")


class ExceptionReference(PythonCoreBaseModel):
    message: Optional["str"] = Field(None, alias="message")
    reference: Optional["str"] = Field(None, alias="reference")
    short_message: Optional["str"] = Field(None, alias="shortMessage")


class FeatureActiveResponseTransport(PythonCoreBaseModel):
    active: Optional["bool"] = Field(None, alias="active")
    effective_configuration: Optional["Dict[str, Optional[ConfigValue]]"] = Field(None, alias="effectiveConfiguration")
    feature_key: Optional["str"] = Field(None, alias="featureKey")


class FeatureStatusOption(PythonCoreBaseModel):
    with_config: Optional["bool"] = Field(None, alias="withConfig")


class FrontendHandledBackendError(PythonCoreBaseModel):
    error_information: Optional["Any"] = Field(None, alias="errorInformation")
    frontend_error_key: Optional["str"] = Field(None, alias="frontendErrorKey")


class SlimFeatureTransport(PythonCoreBaseModel):
    child_features: Optional["List[Optional[SlimFeatureTransport]]"] = Field(None, alias="childFeatures")
    feature_key: Optional["str"] = Field(None, alias="featureKey")
    feature_name: Optional["str"] = Field(None, alias="featureName")


class ValidationError(PythonCoreBaseModel):
    additional_info: Optional["str"] = Field(None, alias="additionalInfo")
    attribute: Optional["str"] = Field(None, alias="attribute")
    error: Optional["str"] = Field(None, alias="error")
    error_code: Optional["str"] = Field(None, alias="errorCode")


CelonisServiceTransport.model_rebuild()
ConfigValue.model_rebuild()
ExceptionReference.model_rebuild()
FeatureActiveResponseTransport.model_rebuild()
FeatureStatusOption.model_rebuild()
FrontendHandledBackendError.model_rebuild()
SlimFeatureTransport.model_rebuild()
ValidationError.model_rebuild()


class FeatureConfigurationClientBase(ABC):
    client: AsyncClient

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        self.client = AsyncClient(base_url=base_url, **kwargs)


class FeatureConfigurationClient(FeatureConfigurationClientBase):
    async def get_fc_api_internal_features(
        self, prefix: Optional["str"] = None, form_tree: Optional["bool"] = None, **kwargs: Any
    ) -> List[Optional[SlimFeatureTransport]]:
        params: Dict[str, Any] = {}
        if prefix is not None:
            if isinstance(prefix, PythonCoreBaseModel):
                params.update(prefix.json_dict(by_alias=True))
            elif isinstance(prefix, dict):
                params.update(prefix)
            else:
                params["prefix"] = prefix
        if form_tree is not None:
            if isinstance(form_tree, PythonCoreBaseModel):
                params.update(form_tree.json_dict(by_alias=True))
            elif isinstance(form_tree, dict):
                params.update(form_tree)
            else:
                params["formTree"] = form_tree
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/features",
            params=params,
            parse_json=True,
            type_=List[Optional[SlimFeatureTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_my_team_celonis_services(
        self, **kwargs: Any
    ) -> List[Optional[CelonisServiceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/my-team/celonis-services",
            parse_json=True,
            type_=List[Optional[CelonisServiceTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_my_team_features(
        self, **kwargs: Any
    ) -> List[Optional[FeatureActiveResponseTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/my-team/features",
            parse_json=True,
            type_=List[Optional[FeatureActiveResponseTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_my_team_features_filters(
        self, prefix: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[FeatureActiveResponseTransport]]:
        params: Dict[str, Any] = {}
        if prefix is not None:
            if isinstance(prefix, PythonCoreBaseModel):
                params.update(prefix.json_dict(by_alias=True))
            elif isinstance(prefix, dict):
                params.update(prefix)
            else:
                params["prefix"] = prefix
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/my-team/features/filters",
            params=params,
            parse_json=True,
            type_=List[Optional[FeatureActiveResponseTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_my_team_features_key_status(
        self, key: str, **kwargs: Any
    ) -> FeatureActiveResponseTransport:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/my-team/features/{key}/status",
            parse_json=True,
            type_=FeatureActiveResponseTransport,
            **kwargs,
        )

    async def get_fc_api_internal_teams_id_celonis_services(
        self, id: str, **kwargs: Any
    ) -> List[Optional[CelonisServiceTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/teams/{id}/celonis-services",
            parse_json=True,
            type_=List[Optional[CelonisServiceTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_teams_id_features(
        self, id: str, **kwargs: Any
    ) -> List[Optional[FeatureActiveResponseTransport]]:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/teams/{id}/features",
            parse_json=True,
            type_=List[Optional[FeatureActiveResponseTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_teams_id_features_filters(
        self, id: str, prefix: Optional["str"] = None, **kwargs: Any
    ) -> List[Optional[FeatureActiveResponseTransport]]:
        params: Dict[str, Any] = {}
        if prefix is not None:
            if isinstance(prefix, PythonCoreBaseModel):
                params.update(prefix.json_dict(by_alias=True))
            elif isinstance(prefix, dict):
                params.update(prefix)
            else:
                params["prefix"] = prefix
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/teams/{id}/features/filters",
            params=params,
            parse_json=True,
            type_=List[Optional[FeatureActiveResponseTransport]],
            **kwargs,
        )

    async def get_fc_api_internal_teams_id_features_key_status(
        self, id: str, key: str, **kwargs: Any
    ) -> FeatureActiveResponseTransport:
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/teams/{id}/features/{key}/status",
            parse_json=True,
            type_=FeatureActiveResponseTransport,
            **kwargs,
        )

    async def get_fc_api_internal_v2_my_team_features_key_status(
        self, key: str, option: Optional["FeatureStatusOption"] = None, **kwargs: Any
    ) -> FeatureActiveResponseTransport:
        params: Dict[str, Any] = {}
        if option is not None:
            if isinstance(option, PythonCoreBaseModel):
                params.update(option.json_dict(by_alias=True))
            elif isinstance(option, dict):
                params.update(option)
            else:
                params["option"] = option
        return await self.client.request(
            method="GET",
            url=f"/fc/api/internal/v2/my-team/features/{key}/status",
            params=params,
            parse_json=True,
            type_=FeatureActiveResponseTransport,
            **kwargs,
        )

    pass


class FeatureConfigurationExternalClient(FeatureConfigurationClientBase):
    pass
