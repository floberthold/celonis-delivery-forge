from typing import List

from app.feature_sqlalchemy.repository.entities.user import User
from python_core_persistence import TenantAwareAsyncSession
from python_core_persistence.repository.base import BaseRepository
from sqlalchemy import select


class UserRepository(BaseRepository[User]):
    """A repository that provides methods related to User models."""

    ModelClass = User

    async def find_all_with_name(self, name: str, tenant_aware_async_session: TenantAwareAsyncSession) -> List["User"]:
        """Return a list of users with given name."""
        users = await tenant_aware_async_session.scalars(select(User).where(User.name == name))
        return users.fetchall()
