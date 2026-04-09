# ruff: noqa: E402

import os
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_docs_site_routes_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app


DB_FILE = Path("tmp_docs_site_routes_test.db")


def test_legacy_docu_routes_redirect_to_docs_site() -> None:
    with TestClient(app) as api_client:
        response = api_client.get("/docu/user.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/user/"

        response = api_client.get("/docu/developer.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/developer/"

        response = api_client.get("/docu/guide-admin-setup.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/admin/full-setup/"

        response = api_client.get("/docu/guide-account-flows.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/guides/account-flows/"

        response = api_client.get("/docu/guide-delivery-walkthrough.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/guides/delivery-walkthrough/"

        response = api_client.get("/docu/guide-action-flow-templates.html", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers.get("location") == "/docs-site/guides/action-flow-template-catalog/"


if __name__ == "__main__":
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
        except PermissionError:
            pass
    test_legacy_docu_routes_redirect_to_docs_site()
