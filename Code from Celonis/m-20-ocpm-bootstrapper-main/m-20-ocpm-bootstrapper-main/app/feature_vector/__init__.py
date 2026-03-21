import logging
from typing import Annotated, Any, Dict, List

from app.feature_vector.service import VectorService
from fastapi import Depends
from python_core_vector.collection.tenant_aware import TenantAwareCollection
from python_core_web_security import AuthenticatedAPIRouter

logger = logging.getLogger(__name__)

PATH = "/feature_vector"
TAGS = ["feature_vector"]

service = VectorService()
router = AuthenticatedAPIRouter(prefix=PATH, tags=TAGS)  # type: ignore


async def example_collection_dependency() -> TenantAwareCollection:
    """Returns example tenant aware collection."""
    return await TenantAwareCollection.get_async("example_collection")


ExampleCollectionDependency = Annotated[TenantAwareCollection, Depends(example_collection_dependency)]


@router.post("", operation_id="createVectors", response_model=int)
async def create_vectors(vectors: List[Dict[str, Any]], collection: ExampleCollectionDependency) -> int:
    """Creates vector in collection."""
    return await service.create_vectors(vectors, collection)


@router.post("/search", operation_id="searchVector", response_model=int)
async def search_vector(
    vector_transport: List[float],
    collection: Annotated[TenantAwareCollection, Depends(example_collection_dependency)],
) -> int:
    """Searches vector in collection."""
    return await service.search_vector(vector_transport, collection)


@router.delete("/{vector_id}", operation_id="deleteVector", status_code=204)
async def delete_vector(
    vector_id: int, collection: Annotated[TenantAwareCollection, Depends(example_collection_dependency)]
) -> None:
    """Deletes vector in collection."""
    await service.delete_vector(vector_id, collection)
