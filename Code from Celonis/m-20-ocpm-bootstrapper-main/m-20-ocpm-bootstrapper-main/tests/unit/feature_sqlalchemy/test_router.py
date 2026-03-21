from unittest.mock import Mock, patch

from app.feature_sqlalchemy import (
    CreateUserTransport,
    UpdateUserTransport,
    UserTransport,
    create_user,
    delete_user,
    find_all_users,
    find_user,
    find_users_with_same_name,
    update_user,
)


class TestSQLAlchemyRouter:
    @patch("app.feature_sqlalchemy.service.UserService.create_user")
    async def test_create_user_returns_created_user(self, service_create_user, user_entity_mock):
        user_transport = UserTransport(
            id=user_entity_mock.id,
            tenant_id=user_entity_mock.tenant_id,
            name=user_entity_mock.name,
            email=user_entity_mock.email,
        )
        service_create_user.return_value = user_transport

        session_mock = Mock()
        create_user_transport = CreateUserTransport(name=user_entity_mock.name, email=user_entity_mock.email)

        result = await create_user(create_user_transport, session_mock)

        assert result == user_transport
        service_create_user.assert_called_with(create_user_transport, session_mock)

    @patch("app.feature_sqlalchemy.service.UserService.find_user")
    async def test_find_user_returns_user(self, service_find_user, user_entity_mock):
        user_transport = UserTransport(
            id=user_entity_mock.id,
            tenant_id=user_entity_mock.tenant_id,
            name=user_entity_mock.name,
            email=user_entity_mock.email,
        )
        service_find_user.return_value = user_transport

        session_mock = Mock()

        result = await find_user(user_entity_mock.id, session_mock)

        assert result == user_transport
        service_find_user.assert_called_with(user_entity_mock.id, session_mock)

    @patch("app.feature_sqlalchemy.service.UserService.find_user")
    @patch("app.feature_sqlalchemy.service.UserService.find_all_users_with_name")
    async def test_find_users_with_same_name_returns_users_with_same_name(
        self, service_find_all_users_with_name, service_find_user, user_entity_mock
    ):
        user_transport = UserTransport(
            id=user_entity_mock.id,
            tenant_id=user_entity_mock.tenant_id,
            name=user_entity_mock.name,
            email=user_entity_mock.email,
        )
        service_find_user.return_value = user_transport
        service_find_all_users_with_name.return_value = [user_transport]

        session_mock = Mock()

        result = await find_users_with_same_name(user_entity_mock.id, session_mock)

        assert len(result) == 1
        assert result[0] == user_transport
        service_find_user.assert_called_with(user_entity_mock.id, session_mock)
        service_find_all_users_with_name.assert_called_with(user_entity_mock.name, session_mock)

    @patch("app.feature_sqlalchemy.service.UserService.find_all_users")
    async def test_find_all_users_returns_users(self, service_find_all_users, user_entity_mock):
        user_transport = UserTransport(
            id=user_entity_mock.id,
            tenant_id=user_entity_mock.tenant_id,
            name=user_entity_mock.name,
            email=user_entity_mock.email,
        )
        service_find_all_users.return_value = [user_transport]

        session_mock = Mock()

        result = await find_all_users(session_mock)

        assert len(result) == 1
        assert result[0] == user_transport
        service_find_all_users.assert_called_with(session_mock)

    @patch("app.feature_sqlalchemy.service.UserService.update_user")
    async def test_update_user_returns_updated_user(self, service_update_user, user_entity_mock):
        user_transport = UserTransport(
            id=user_entity_mock.id,
            tenant_id=user_entity_mock.tenant_id,
            name=user_entity_mock.name,
            email=user_entity_mock.email,
        )
        service_update_user.return_value = user_transport

        session_mock = Mock()
        update_user_transport = UpdateUserTransport(name=user_entity_mock.name, email=user_entity_mock.email)

        result = await update_user(user_entity_mock.id, update_user_transport, session_mock)

        assert result == user_transport
        service_update_user.assert_called_with(user_entity_mock.id, update_user_transport, session_mock)

    @patch("app.feature_sqlalchemy.service.UserService.delete_user")
    async def test_delete_user_deletes_user(self, service_delete_user, user_entity_mock):
        session_mock = Mock()

        await delete_user(user_entity_mock.id, session_mock)

        service_delete_user.assert_called_with(user_entity_mock.id, session_mock)
