from __future__ import annotations

from fastapi.testclient import TestClient

from foundry.api.main import app


def test_docu_redirect_routes() -> None:
    with TestClient(app) as api_client:
        user_response = api_client.get("/docu/user.html", follow_redirects=False)
        developer_response = api_client.get("/docu/developer.html", follow_redirects=False)
        admin_setup_response = api_client.get("/docu/guide-admin-setup.html", follow_redirects=False)

    assert user_response.status_code == 307
    assert user_response.headers["location"] == "/docs-site/user/"
    assert developer_response.status_code == 307
    assert developer_response.headers["location"] == "/docs-site/developer/"
    assert admin_setup_response.status_code == 307
    assert admin_setup_response.headers["location"] == "/docs-site/admin/full-setup/"
