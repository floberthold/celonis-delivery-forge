import pytest
from app.feature_a import PATH, router


@pytest.mark.parametrize("app", [router], indirect=True)
class TestFeatureARouter:
    async def test_get_description(self, async_client, patched_feature_a_service):
        response = await async_client.get(PATH)
        assert response.status_code == 200
        assert response.text == '"This is a test"'

    async def test_get_items(self, async_client, patched_feature_a_service):
        response = await async_client.get(f"{PATH}/items")
        assert response.status_code == 200
        assert len(response.json()) == 10

    async def test_get_permissions(self, async_client, patched_feature_a_service, user_service_permission_transport):
        response = await async_client.get(f"{PATH}/permissions")

        assert response.json()[0] == user_service_permission_transport.model_dump(by_alias=True)

    async def test_get_data_pools_internal(self, async_client, patched_feature_a_service, data_pool_transport):
        response = await async_client.get(f"{PATH}/internal/pools")

        assert response.json()[0] == data_pool_transport.model_dump(by_alias=True)

    async def test_create_data_pool_internal(self, async_client, patched_feature_a_service, data_pool_transport):
        response = await async_client.post(f"{PATH}/internal/pools", json=data_pool_transport.model_dump(by_alias=True))

        assert response.json() == data_pool_transport.model_dump(by_alias=True)

    async def test_get_spaces(self, async_client, patched_feature_a_service, space_transport):
        response = await async_client.get(f"{PATH}/spaces")

        assert response.json()[0] == space_transport.model_dump(by_alias=True)

    async def test_delete_package(self, async_client, patched_feature_a_service):
        response = await async_client.delete(f"{PATH}/packages/TEST_ID")

        assert response.status_code == 204
