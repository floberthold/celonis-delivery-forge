import logging
from typing import List

from app.feature_sqlalchemy.repository.user import UserRepository
from app.feature_sqlalchemy.repository.user_type import UserTypeRepository
from app.feature_sqlalchemy.service import UserService
from app.feature_sqlalchemy.transport.user import CreateUserTransport, UpdateUserTransport, UserTransport
from python_core_persistence import TenantAwareAsyncSessionDependency
from python_core_web_security import AuthenticatedAPIRouter

PATH = "/feature_sqlalchemy"
TAGS = ["feature_sqlalchemy"]

router = AuthenticatedAPIRouter(prefix=PATH, tags=TAGS)  # type: ignore
service = UserService(
    user_repository=UserRepository(),
    user_type_repository=UserTypeRepository(),
)


logger = logging.getLogger(__name__)


@router.post("", operation_id="createUser", response_model=UserTransport)
async def create_user(
    user_transport: CreateUserTransport, tenant_aware_async_session: TenantAwareAsyncSessionDependency
) -> UserTransport:
    """Creates and returns user."""
    return await service.create_user(user_transport, tenant_aware_async_session)


@router.get("/{user_id}", operation_id="findUser", response_model=UserTransport)
async def find_user(user_id: str, tenant_aware_async_session: TenantAwareAsyncSessionDependency) -> UserTransport:
    """Returns user."""
    return await service.find_user(user_id, tenant_aware_async_session)


@router.get("/{user_id}/same", operation_id="findUserWithSameName", response_model=List[UserTransport])
async def find_users_with_same_name(
    user_id: str, tenant_aware_async_session: TenantAwareAsyncSessionDependency
) -> List[UserTransport]:
    """Returns user."""
    user = await service.find_user(user_id, tenant_aware_async_session)
    return await service.find_all_users_with_name(user.name, tenant_aware_async_session)


@router.get("", operation_id="findUsers", response_model=List[UserTransport])
async def find_all_users(tenant_aware_async_session: TenantAwareAsyncSessionDependency) -> List[UserTransport]:
    """Returns all users."""
    return await service.find_all_users(tenant_aware_async_session)


@router.put("/{user_id}", operation_id="updateUser", response_model=UserTransport)
async def update_user(
    user_id: str, user_transport: UpdateUserTransport, tenant_aware_async_session: TenantAwareAsyncSessionDependency
) -> UserTransport:
    """Updates and returns user."""
    return await service.update_user(user_id, user_transport, tenant_aware_async_session)


@router.delete("/{user_id}", operation_id="deleteUser", status_code=204)
async def delete_user(user_id: str, tenant_aware_async_session: TenantAwareAsyncSessionDependency) -> None:
    """Deletes user."""
    await service.delete_user(user_id, tenant_aware_async_session)
