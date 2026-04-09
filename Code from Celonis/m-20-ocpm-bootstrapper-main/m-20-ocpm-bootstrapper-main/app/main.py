from app import feature_a, feature_rabbit_mq, feature_sqlalchemy, feature_vector
from python_core_fast_api import PythonCoreAPI
from python_core_fast_api.settings import fast_api_settings
from python_core_logging import load_log_config
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable

ROOT = f"/{fast_api_settings.app.name}/api"


app = PythonCoreAPI(tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()])
app.include_router(router=feature_a.router, prefix=ROOT)
app.include_router(router=feature_sqlalchemy.router, prefix=ROOT)
app.include_router(router=feature_rabbit_mq.router, prefix=ROOT)
app.include_router(router=feature_vector.router, prefix=ROOT)
app.include_broker(broker=feature_rabbit_mq.broker)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=fast_api_settings.server.port,
        log_config=load_log_config(),
    )
