import uuid
from typing import List, Union

from app.feature_sqlalchemy.repository.user import UserRepository
from app.feature_sqlalchemy.repository.user_type import UserTypeRepository
from app.feature_sqlalchemy.transport.user import CreateUserTransport, UpdateUserTransport, UserTransport
from app.feature_sqlalchemy.transport.user_type import UserTypeTransport
from fastapi import HTTPException
from python_core_persistence import TenantAwareAsyncSession
from sqlalchemy.exc import NoResultFound


class UserService:
    """Service for user related CRUD methods."""

    def __init__(self, user_repository: UserRepository, user_type_repository: UserTypeRepository) -> None:
        """Initialize service."""
        self.user_repository = user_repository
        self.user_type_repository = user_type_repository

    async def create_user(
        self, create_transport: CreateUserTransport, tenant_aware_async_session: TenantAwareAsyncSession
    ) -> UserTransport:
        """Create user."""
        async with tenant_aware_async_session.begin():
            entity = await self.user_repository.create(create_transport, tenant_aware_async_session)
        return UserTransport.from_orm(entity)

    async def find_user(
        self, id_: Union[str, uuid.UUID], tenant_aware_async_session: TenantAwareAsyncSession
    ) -> UserTransport:
        """Get user with given id."""
        try:
            entity = await self.user_repository.find(id_, tenant_aware_async_session)
            return UserTransport.from_orm(entity)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=f"User with id {id_} not found") from e

    async def find_all_users(self, tenant_aware_async_session: TenantAwareAsyncSession) -> List[UserTransport]:
        """Return a list of users."""
        entities = await self.user_repository.find_all(tenant_aware_async_session)
        return [UserTransport.from_orm(entity) for entity in entities]

    async def find_all_users_with_name(
        self, name: str, tenant_aware_async_session: TenantAwareAsyncSession
    ) -> List[UserTransport]:
        """Return a list of users with given name."""
        entities = await self.user_repository.find_all_with_name(name, tenant_aware_async_session)
        return [UserTransport.from_orm(entity) for entity in entities]

    async def delete_user(
        self, id_: Union[str, uuid.UUID], tenant_aware_async_session: TenantAwareAsyncSession
    ) -> None:
        """Delete user with given id."""
        try:
            async with tenant_aware_async_session.begin():
                await self.user_repository.delete(id_, tenant_aware_async_session)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=f"User with id {id_} not found") from e

    async def update_user(
        self,
        id_: Union[str, uuid.UUID],
        update_transport: UpdateUserTransport,
        tenant_aware_async_session: TenantAwareAsyncSession,
    ) -> UserTransport:
        """Update user."""
        try:
            async with tenant_aware_async_session.begin():
                entity = await self.user_repository.update(id_, update_transport, tenant_aware_async_session)
            return UserTransport.from_orm(entity)
        except NoResultFound as e:
            raise HTTPException(status_code=404, detail=f"User with id {id_} not found") from e

    async def find_all_user_types(self, tenant_aware_async_session: TenantAwareAsyncSession) -> List[UserTypeTransport]:
        """Return a list of user types with given name."""
        entities = await self.user_type_repository.find_all(tenant_aware_async_session)
        return [UserTypeTransport.from_orm(entity) for entity in entities]
