import uuid
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from app.feature_a import FeatureAService  # noqa: E402
from app.feature_rabbit_mq import RabbitMQService
from app.feature_sqlalchemy import UserService  # noqa: E402
from app.feature_sqlalchemy.repository.entities.user import User  # noqa: E402
from app.feature_sqlalchemy.repository.entities.user_type import UserType  # noqa: E402
from app.services.integration_client import DataPoolTransport  # noqa: E402
from app.services.package_manager_client import SpaceTransport  # noqa: E402
from app.services.team_client import UserServicePermissionsTransport  # noqa: E402
from pymilvus import DataType, FieldSchema
from python_core_testing import event_loop
from python_core_vector.collection.base import CollectionSchema
from python_core_vector.collection.tenant_aware import TenantAwareCollection


@pytest.fixture(scope="function")
def user_service_permission_transport():
    return UserServicePermissionsTransport(service_name="TEST_SERVICE")


@pytest.fixture(scope="function")
def data_pool_transport():
    return DataPoolTransport(name="TEST_POOL")


@pytest.fixture(scope="function")
def user_entity_mock():
    user_mock = Mock(User)
    user_mock.id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    user_mock.tenant_id = "TEST_TENANT_ID"
    user_mock.name = "TEST_NAME"
    user_mock.email = "TEST_EMAIL"
    return user_mock


@pytest.fixture(scope="function")
def user_type_entity_mock():
    user_type_mock = Mock(UserType)
    user_type_mock.id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    user_type_mock.name = "TEST_TYPE"
    return user_type_mock


@pytest.fixture(scope="function")
def space_transport():
    return SpaceTransport(name="TEST_SPACE")


@pytest.fixture(scope="function")
def mock_team_client(user_service_permission_transport):
    mock_team_client = Mock()
    mock_team_client.get_api_cloud_permissions = AsyncMock(return_value=[user_service_permission_transport])

    return mock_team_client


@pytest.fixture(scope="function")
def mock_package_manager_client(space_transport):
    mock_package_manager_client = Mock()
    mock_package_manager_client.get_api_spaces = AsyncMock(return_value=[space_transport])
    mock_package_manager_client.delete_api_packages_id = AsyncMock()

    return mock_package_manager_client


@pytest.fixture(scope="function")
def mock_integration_client(data_pool_transport):
    mock_integration_client = Mock()
    mock_integration_client.get_api_internal_data_pools = AsyncMock(return_value=[data_pool_transport])
    mock_integration_client.post_api_internal_data_pools = AsyncMock(return_value=data_pool_transport)

    return mock_integration_client


@pytest.fixture(scope="function")
def mock_feature_a_service(mock_team_client, mock_package_manager_client, mock_integration_client):
    return FeatureAService(
        team_client=mock_team_client,
        package_manager_client=mock_package_manager_client,
        integration_client=mock_integration_client,
    )


@pytest.fixture(scope="function")
def mock_rabbit_mq_service(mock_team_client, mock_package_manager_client, mock_integration_client):
    return RabbitMQService(integration_client=mock_integration_client)


@pytest.fixture(scope="function")
def mock_user_service():
    return UserService(
        user_repository=Mock(),
        user_type_repository=Mock(),
    )


@pytest.fixture(scope="function")
def patched_feature_a_service(mock_feature_a_service):
    with mock.patch("app.feature_a.service", mock_feature_a_service):
        yield


@pytest.fixture(scope="function")
async def example_collection(milvus_auto_lifecycle) -> TenantAwareCollection:
    id_field = FieldSchema(name="user_id", dtype=DataType.INT64)
    embedding_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=16)
    collection_schema = CollectionSchema(fields=[id_field, embedding_field])
    collection = await TenantAwareCollection.create_async("example_collection", schema=collection_schema)
    index_params = {"metric_type": "IP", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
    await collection.create_index_async(field_name="embedding", index_name="embedding", index_params=index_params)
    await collection.load_async()

    yield collection  # Cleanup is done automatically by milvus fixture
