import logging
from typing import Any, Dict, List

from fastapi import HTTPException
from python_core_vector.collection.tenant_aware import TenantAwareCollection

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector DB related methods."""

    async def create_vectors(self, vectors: List[Dict[str, Any]], collection: TenantAwareCollection) -> int:
        """Creates vector in collection."""
        result = await collection.insert_async(vectors)
        return result.insert_count

    async def search_vector(self, vector_transport: List[float], collection: TenantAwareCollection) -> int:
        """Searches vector in collection."""
        results = await collection.search_async(
            [vector_transport],
            anns_field="embedding",
            param={"metric_type": "IP"},
            limit=1,
        )

        if len(results) == 0 or len(results[0]) == 0:
            raise HTTPException(status_code=404, detail="No vector found")

        return results[0][0].id

    async def delete_vector(self, vector_id: int, collection: TenantAwareCollection) -> None:
        """Deletes vector in collection."""
        await collection.delete_async(f"id=={vector_id}")
