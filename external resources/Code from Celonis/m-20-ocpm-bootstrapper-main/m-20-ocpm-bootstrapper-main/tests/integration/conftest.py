import pytest
from python_core_fast_api import PythonCoreAPI
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable
from python_core_web_security_testing import AuthenticatedAsyncTestClient


@pytest.fixture(scope="function")
def app(request):
    app = PythonCoreAPI(tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()])
    app.include_router(request.param)
    return app


@pytest.fixture(scope="function")
def async_client(app):
    return AuthenticatedAsyncTestClient(app=app, base_url="http://test")
