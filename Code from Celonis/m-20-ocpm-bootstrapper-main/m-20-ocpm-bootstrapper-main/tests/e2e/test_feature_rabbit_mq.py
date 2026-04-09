import pytest
from app.feature_rabbit_mq import PATH, broker, router
from python_core_fast_api import PythonCoreAPI
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable

app = PythonCoreAPI(tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()], disable_vector=True)
app.include_router(router)
app.include_broker(broker)


@pytest.mark.vcr
@pytest.mark.parametrize("authenticated_client", [app], indirect=True)
class TestRabbitMQ:
    async def test_app(self, authenticated_client, rabbit_mq):
        content = {"name": "test", "description": "test", "status": "START", "version": "1.0.0"}
        response = await authenticated_client.post(PATH, json=content)

        assert response.status_code == 200

        assert content == response.json()
