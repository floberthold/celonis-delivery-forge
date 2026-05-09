import pytest
from app.feature_vector import VectorService, router
from fastapi import HTTPException
from python_core_fast_api import PythonCoreAPI
from python_core_persistence import TableTenantErasable
from python_core_vector.tenant_erasion.tenant_eraser import CollectionTenantErasable
from python_core_web_security_testing.context import use_team_context

app = PythonCoreAPI(tenant_erasables=[TableTenantErasable(), CollectionTenantErasable()], disable_rabbit_mq=True)
app.include_router(router)


class TestVector:
    async def test_nonexistent_vector_raises_404(self, example_collection):
        with use_team_context("TEST"):
            vector_service = VectorService()
            with pytest.raises(HTTPException):
                await vector_service.search_vector([0.1] * 16, example_collection)

    async def test_create_and_get_vector(self, example_collection):
        with use_team_context("TEST"):
            vector_service = VectorService()
            test_vector = [{"user_id": 1, "embedding": [0.1] * 16}]

            insert_count = await vector_service.create_vectors(test_vector, example_collection)
            assert insert_count == 1
            await example_collection.flush_async()

            vector_id = await vector_service.search_vector(test_vector[0]["embedding"], example_collection)
            user_id = (await example_collection.query_async(f"id=={vector_id}", output_fields=["user_id"]))[0][
                "user_id"
            ]
            assert user_id == 1

    async def test_create_and_delete_vector(self, example_collection):
        with use_team_context("TEST"):
            vector_service = VectorService()
            test_vector = [{"user_id": 1, "embedding": [0.1] * 16}]

            insert_count = await vector_service.create_vectors(test_vector, example_collection)
            assert insert_count == 1
            await example_collection.flush_async()

            vector_id = await vector_service.search_vector(test_vector[0]["embedding"], example_collection)

            # Delete vector
            await vector_service.delete_vector(vector_id, example_collection)
            await example_collection.flush_async()

            # Test vector does not exist
            with pytest.raises(HTTPException):
                await vector_service.search_vector([0.1] * 16, example_collection)

    async def test_create_vector(self, example_collection):
        with use_team_context("TEST"):
            vector_service = VectorService()
            test_vector = [{"user_id": 1, "embedding": [0.1] * 16}]

            # Create vector
            insert_count = await vector_service.create_vectors(test_vector, example_collection)
            assert insert_count == 1
            await example_collection.flush_async()

            # Test vector exists
            vector_id = await vector_service.search_vector(test_vector[0]["embedding"], example_collection)
            user_id = (await example_collection.query_async(f"id=={vector_id}", output_fields=["user_id"]))[0][
                "user_id"
            ]
            assert user_id == 1
