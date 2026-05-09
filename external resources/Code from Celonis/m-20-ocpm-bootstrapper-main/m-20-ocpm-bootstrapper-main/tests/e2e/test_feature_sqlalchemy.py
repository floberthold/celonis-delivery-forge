import pytest
from app.feature_sqlalchemy import PATH, router
from python_core_fast_api import PythonCoreAPI
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable

app = PythonCoreAPI(
    tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()], disable_rabbit_mq=True, disable_vector=True
)
app.include_router(router)


@pytest.mark.vcr
@pytest.mark.parametrize("authenticated_client", [app], indirect=True)
class TestSQLAlchemyRouter:
    async def test_create_user(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME", "email": "TEST_EMAIL"})

        assert response.status_code == 200

        content = response.json()
        assert content["id"]
        assert content["name"] == "TEST_NAME"
        assert content["email"] == "TEST_EMAIL"

    async def test_find_user(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME", "email": "TEST_EMAIL"})
        assert response.status_code == 200

        response = await authenticated_client.get(f"{PATH}/{response.json()['id']}")
        assert response.status_code == 200

        content = response.json()
        assert content["id"]
        assert content["name"] == "TEST_NAME"
        assert content["email"] == "TEST_EMAIL"

    async def test_find_users_with_same_name(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME1", "email": "TEST_EMAIL1"})
        assert response.status_code == 200
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME2", "email": "TEST_EMAIL2"})
        assert response.status_code == 200

        response = await authenticated_client.get(f"{PATH}/{response.json()['id']}/same")
        assert response.status_code == 200

        content = response.json()
        assert len(content) == 1
        assert content[0]["id"]
        assert content[0]["name"] == "TEST_NAME2"
        assert content[0]["email"] == "TEST_EMAIL2"

    async def test_find_all_users(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME", "email": "TEST_EMAIL"})
        assert response.status_code == 200

        response = await authenticated_client.get(PATH)
        assert response.status_code == 200

        content = response.json()
        assert len(content) == 1
        assert content[0]["id"]
        assert content[0]["name"] == "TEST_NAME"
        assert content[0]["email"] == "TEST_EMAIL"

    async def test_update_user(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME", "email": "TEST_EMAIL"})
        assert response.status_code == 200

        response = await authenticated_client.put(
            f"{PATH}/{response.json()['id']}", json={"name": "UPDATED_NAME", "email": "UPDATED_EMAIL"}
        )
        assert response.status_code == 200

        content = response.json()
        assert content["id"]
        assert content["name"] == "UPDATED_NAME"
        assert content["email"] == "UPDATED_EMAIL"

    async def test_delete_user(self, authenticated_client, postgres_auto_lifecycle):
        response = await authenticated_client.post(PATH, json={"name": "TEST_NAME", "email": "TEST_EMAIL"})
        assert response.status_code == 200

        user_id = response.json()["id"]

        response = await authenticated_client.delete(f"{PATH}/{user_id}")
        assert response.status_code == 204

        response = await authenticated_client.get(f"{PATH}/{user_id}")
        assert response.status_code == 404
