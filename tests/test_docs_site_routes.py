import os
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure this test uses an isolated SQLite database.
os.environ.setdefault("FORGE_DATABASE_URL", "sqlite:///./tmp_docs_site_routes_test.db")

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


if __name__ == "__main__":
    if DB_FILE.exists():
        DB_FILE.unlink()
    test_legacy_docu_routes_redirect_to_docs_site()
