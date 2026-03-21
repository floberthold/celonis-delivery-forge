import asyncio
from typing import Dict, List, Optional

from app.feature_a.model import FeatureAItemTransport
from app.services.feature_configuration_client import FeatureActiveResponseTransport, FeatureConfigurationClient
from app.services.integration_client import DataPoolTransport, IntegrationClient
from app.services.machine_learning_client import JobExecution, MachineLearningClient
from app.services.package_manager_client import PackageManagerClient, SpaceTransport
from app.services.team_client import TeamClient, UserServicePermissionsTransport
from python_core_caching import PydanticJsonSerializer, TenantAwareCacheable
from python_core_internal_client.settings import internal_client_settings
from python_core_web_security import team_context


class FeatureAService:
    """A service that provides methods related to Feature A."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        team_client: Optional[TeamClient] = None,
        integration_client: Optional[IntegrationClient] = None,
        package_manager_client: Optional[PackageManagerClient] = None,
        machine_learning_client: Optional[MachineLearningClient] = None,
        feature_configuration_client: Optional[FeatureConfigurationClient] = None,
    ):
        self.team_client = team_client or TeamClient(internal_client_settings.celonis.services["team"].url)
        self.integration_client = integration_client or IntegrationClient(
            internal_client_settings.celonis.services["integration"].url
        )
        self.package_manager_client = package_manager_client or PackageManagerClient(
            internal_client_settings.celonis.services["package-manager"].url
        )
        self.machine_learning_client = machine_learning_client or MachineLearningClient(
            internal_client_settings.celonis.services["machine-learning"].url
        )
        self.feature_configuration_client = feature_configuration_client or FeatureConfigurationClient(
            internal_client_settings.celonis.services["backend"].url
        )

    async def get_description(self) -> str:
        """Get description."""
        await asyncio.sleep(0.2)  # simulate request to service x
        return "This is a test"

    @TenantAwareCacheable(name="items", serializer=PydanticJsonSerializer(models=[FeatureAItemTransport]))
    async def get_items(self) -> List[FeatureAItemTransport]:
        """Return a list of 10 items."""
        return [FeatureAItemTransport(name=f"{x}_item", number=x) for x in range(10)]

    async def get_permissions(self) -> List[Optional[UserServicePermissionsTransport]]:
        """Returns user permissions."""
        return await self.team_client.get_api_cloud_permissions()

    async def get_data_pools_internal(self) -> List[Optional[DataPoolTransport]]:
        """Returns data pools using internal endpoint."""
        return await self.integration_client.get_api_internal_data_pools()

    async def create_data_pool_internal(self, data_pool_transport: DataPoolTransport) -> DataPoolTransport:
        """Creates data pool using internal endpoint."""
        return await self.integration_client.post_api_internal_data_pools(data_pool_transport)

    async def get_spaces(self) -> List[Optional[SpaceTransport]]:
        """Returns spaces."""
        return await self.package_manager_client.get_api_spaces()

    async def delete_package(self, id_: str) -> None:
        """Deletes package."""
        return await self.package_manager_client.delete_api_packages_id(id_)

    async def execute_ml_job(self, job_input: Dict) -> JobExecution:
        """Triggers pc-sandbox ml job with given input."""
        return await self.machine_learning_client.post_api_jobs_job_id_executions(
            job_id="pc-sandbox", request_body=job_input
        )

    async def cancel_ml_job(self, execution_id: str) -> None:
        """Triggers pc-sandbox ml job with given input."""
        return await self.machine_learning_client.post_api_jobs_executions_id_stop(execution_id)

    async def get_ml_job_status(self, execution_id: str) -> JobExecution:
        """Get status of ml job with given execution id."""
        return await self.machine_learning_client.get_api_jobs_executions_id(execution_id)

    async def get_my_team_features(self) -> List[Optional[FeatureActiveResponseTransport]]:
        """Returns features of current team."""
        return await self.feature_configuration_client.get_fc_api_internal_my_team_features()

    async def get_machine_learning_images_features(self) -> List[Optional[FeatureActiveResponseTransport]]:
        """Example how to get features for specific prefix."""
        return await self.feature_configuration_client.get_fc_api_internal_teams_id_features_filters(
            id=team_context.team_id, prefix="machine-learning.images"
        )
