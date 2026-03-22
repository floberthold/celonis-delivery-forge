import os
from pathlib import Path

from fastapi.testclient import TestClient

# Keep this test isolated from any developer local DB.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_celonis_ui_route_presence_test.db")

from foundry.api.main import app


DB_FILE = Path("tmp_celonis_ui_route_presence_test.db")


def test_celonis_ui_endpoints_are_registered() -> None:
    with TestClient(app) as api_client:
        for path in [
            "/celonis-credentials-ui",
            "/celonis-discovery-ui",
            "/celonis-deployments-ui",
        ]:
            response = api_client.get(path, follow_redirects=False)
            assert response.status_code != 404, f"Endpoint unexpectedly missing: {path}"


def teardown_module(_: object) -> None:
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
