import logging
from typing import Dict, List, Optional

from app.feature_a.model import FeatureAItemTransport
from app.feature_a.service import FeatureAService
from app.services.feature_configuration_client import FeatureActiveResponseTransport
from app.services.integration_client import DataPoolTransport
from app.services.machine_learning_client import JobExecution
from app.services.package_manager_client import SpaceTransport
from app.services.team_client import UserServicePermissionsTransport
from fastapi import Body
from python_core_web_security.security.router import AuthenticatedAPIRouter

PATH = "/feature_a"
TAGS = ["feature_a"]

router = AuthenticatedAPIRouter(prefix=PATH, tags=TAGS)  # type: ignore
service = FeatureAService()

logger = logging.getLogger(__name__)


@router.get("", operation_id="getDescription", response_model=str)
async def get_description() -> str:
    """Returns an example description."""
    result = await service.get_description()
    logger.info("Queried description '%s'", result)  # Example log message
    return result


@router.get("/items", operation_id="getItems", response_model=List[FeatureAItemTransport])
async def get_items() -> List[FeatureAItemTransport]:
    """Returns a list of items."""
    result = await service.get_items()
    return result


@router.get(
    "/permissions",
    operation_id="getPermissions",
    response_model=List[Optional[UserServicePermissionsTransport]],
)
async def get_permissions() -> List[Optional[UserServicePermissionsTransport]]:
    """Returns users permissions."""
    result = await service.get_permissions()
    return result


@router.get("/internal/pools", operation_id="getDataPools", response_model=List[Optional[DataPoolTransport]])
async def get_data_pools_internal() -> List[Optional[DataPoolTransport]]:
    """Returns data pools using internal endpoint."""
    result = await service.get_data_pools_internal()
    return result


@router.post("/internal/pools", operation_id="createDataPool", response_model=DataPoolTransport)
async def create_data_pool_internal(pool_transport: DataPoolTransport) -> DataPoolTransport:
    """Creates data pool using internal endpoint."""
    result = await service.create_data_pool_internal(pool_transport)
    return result


@router.get("/spaces", operation_id="getSpaces", response_model=List[Optional[SpaceTransport]])
async def get_spaces() -> List[Optional[SpaceTransport]]:
    """Returns spaces."""
    result = await service.get_spaces()
    return result


@router.delete("/packages/{id_}", operation_id="deletePackage", status_code=204)
async def delete_package(id_: str) -> None:
    """Returns spaces."""
    await service.delete_package(id_)


@router.post("/ml-job/pc-sandbox", operation_id="triggerJob", response_model=JobExecution)
async def execute_ml_job(job_input: Dict = Body(...)) -> JobExecution:
    """Triggers pc-sandbox ml job with given input."""
    return await service.execute_ml_job(job_input)


@router.post("/ml-job/{execution_id}/cancel", operation_id="cancelJob", response_model=JobExecution)
async def cancel_ml_job(execution_id: str) -> JobExecution:
    """Cancel pc-sandbox ml job with given JobExecution."""
    await service.cancel_ml_job(execution_id)
    return await service.get_ml_job_status(execution_id)


@router.get("/ml-job/{execution_id}", operation_id="getJobStatus", response_model=JobExecution)
async def get_ml_job_status(execution_id: str) -> JobExecution:
    """Get pc-sandbox ml job JobExecution status."""
    return await service.get_ml_job_status(execution_id)


@router.get(
    "/features", operation_id="getMyTeamFeatures", response_model=List[Optional[FeatureActiveResponseTransport]]
)
async def get_my_team_features() -> List[Optional[FeatureActiveResponseTransport]]:
    """Returns features of current team."""
    return await service.get_my_team_features()


@router.get("/features/ml", operation_id="getMLFeatures", response_model=List[Optional[FeatureActiveResponseTransport]])
async def get_machine_learning_images_features() -> List[Optional[FeatureActiveResponseTransport]]:
    """Example how to get features for specific prefix."""
    return await service.get_machine_learning_images_features()
