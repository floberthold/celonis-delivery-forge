import pytest
from app.feature_a import PATH, router
from python_core_fast_api import PythonCoreAPI
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable

app = PythonCoreAPI(
    tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()], disable_rabbit_mq=True, disable_vector=True
)
app.include_router(router)


@pytest.mark.vcr
@pytest.mark.parametrize("authenticated_client", [app], indirect=True)
class TestFeatureARouter:
    async def test_get_permissions(self, authenticated_client):
        """Test that permissions are returned without errors."""
        response = await authenticated_client.get(f"{PATH}/permissions")

        assert response.status_code == 200

    async def test_get_data_pools_internal(self, authenticated_client, data_pool):
        """Test that data pool created in fixture is returned by endpoint."""
        response = await authenticated_client.get(f"{PATH}/internal/pools")

        assert data_pool.id in [dp["id"] for dp in response.json()]

    async def test_get_spaces(self, authenticated_client, space):
        """Test that space created in fixture is returned by endpoint."""
        response = await authenticated_client.get(f"{PATH}/spaces")

        assert space.id in [s["id"] for s in response.json()]
