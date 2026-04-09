from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from app.feature_sqlalchemy.transport.user import CreateUserTransport, UpdateUserTransport
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound


class TestUserService:
    async def test_create(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.create = AsyncMock(return_value=user_entity_mock)

        session_mock = MagicMock()
        create_user_transport = CreateUserTransport(name=user_entity_mock.name, email=user_entity_mock.email)

        user = await mock_user_service.create_user(create_user_transport, session_mock)

        assert user.id == user_entity_mock.id
        assert user.name == user_entity_mock.name
        assert user.email == user_entity_mock.email
        mock_user_service.user_repository.create.assert_called_once_with(create_user_transport, session_mock)

    async def test_find(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.find = AsyncMock(return_value=user_entity_mock)
        session_mock = Mock()

        user = await mock_user_service.find_user(user_entity_mock.id, session_mock)

        assert user.id == user_entity_mock.id
        assert user.name == user_entity_mock.name
        assert user.email == user_entity_mock.email
        mock_user_service.user_repository.find.assert_called_once_with(user_entity_mock.id, session_mock)

    async def test_find_raises_http_exception_for_nonexistent_id(self, mock_user_service):
        mock_user_service.user_repository.find = AsyncMock(side_effect=NoResultFound)
        session_mock = Mock()

        with pytest.raises(HTTPException):
            await mock_user_service.find_user("NONEXISTENT", session_mock)

    async def test_find_all(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.find_all = AsyncMock(return_value=[user_entity_mock])
        session_mock = Mock()

        users = await mock_user_service.find_all_users(session_mock)

        assert len(users) == 1
        assert users[0].id == user_entity_mock.id
        assert users[0].name == user_entity_mock.name
        assert users[0].email == user_entity_mock.email
        mock_user_service.user_repository.find_all.assert_called_once_with(session_mock)

    async def test_find_all_with_name(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.find_all_with_name = AsyncMock(return_value=[user_entity_mock])
        session_mock = Mock()

        users = await mock_user_service.find_all_users_with_name(user_entity_mock.name, session_mock)

        assert len(users) == 1
        assert users[0].id == user_entity_mock.id
        assert users[0].name == user_entity_mock.name
        assert users[0].email == user_entity_mock.email
        mock_user_service.user_repository.find_all_with_name.assert_called_once_with(
            user_entity_mock.name, session_mock
        )

    async def test_delete(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.delete = AsyncMock()
        session_mock = MagicMock()

        await mock_user_service.delete_user(user_entity_mock.id, session_mock)

        mock_user_service.user_repository.delete.assert_called_once_with(user_entity_mock.id, session_mock)

    async def test_delete_raises_http_exception_for_nonexistent_id(self, mock_user_service):
        mock_user_service.user_repository.delete = AsyncMock(side_effect=NoResultFound)
        session_mock = MagicMock()

        with pytest.raises(HTTPException):
            await mock_user_service.delete_user("NONEXISTENT", session_mock)

    async def test_update(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.update = AsyncMock(return_value=user_entity_mock)

        session_mock = MagicMock()
        update_user_transport = UpdateUserTransport(name=user_entity_mock.name, email=user_entity_mock.email)

        user = await mock_user_service.update_user(user_entity_mock.id, update_user_transport, session_mock)

        assert user.id == user_entity_mock.id
        assert user.name == user_entity_mock.name
        assert user.email == user_entity_mock.email
        mock_user_service.user_repository.update.assert_called_once_with(
            user_entity_mock.id, update_user_transport, session_mock
        )

    async def test_update_raises_http_exception_for_nonexistent_id(self, mock_user_service, user_entity_mock):
        mock_user_service.user_repository.update = AsyncMock(side_effect=NoResultFound)
        session_mock = MagicMock()

        update_user_transport = UpdateUserTransport(name=user_entity_mock.name, email=user_entity_mock.email)

        with pytest.raises(HTTPException):
            await mock_user_service.update_user("NONEXISTENT", update_user_transport, session_mock)

    async def test_find_all_user_types(self, mock_user_service, user_type_entity_mock):
        mock_user_service.user_type_repository.find_all = AsyncMock(return_value=[user_type_entity_mock])
        session_mock = Mock()

        user_types = await mock_user_service.find_all_user_types(session_mock)

        assert len(user_types) == 1
        assert user_types[0].id == user_type_entity_mock.id
        assert user_types[0].name == user_type_entity_mock.name
        mock_user_service.user_type_repository.find_all.assert_called_once_with(session_mock)
