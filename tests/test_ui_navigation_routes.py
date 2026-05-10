from __future__ import annotations

from fastapi.testclient import TestClient

from foundry.api.main import app


def test_tenant_ui_route_is_available() -> None:
    with TestClient(app) as api_client:
        response = api_client.get("/tenant-ui")

    assert response.status_code == 200
    assert "Tenant" in response.text


def test_workspace_ui_route_uses_default_login_url() -> None:
    with TestClient(app) as api_client:
        response = api_client.get("/workspace-ui")

    assert response.status_code == 200
    assert "https://id.celonis.cloud/user/ui/login" in response.text
