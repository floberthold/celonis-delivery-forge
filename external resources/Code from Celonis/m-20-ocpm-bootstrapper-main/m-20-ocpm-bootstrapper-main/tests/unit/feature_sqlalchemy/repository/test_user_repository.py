from unittest.mock import AsyncMock, Mock

from app.feature_sqlalchemy import UserRepository


class TestUserRepository:
    async def test_find_all_with_name(self, user_entity_mock):
        scalars_mock = Mock()
        scalars_mock.fetchall = Mock(return_value=[user_entity_mock])

        session_mock = Mock()
        session_mock.scalars = AsyncMock(return_value=scalars_mock)

        users = await UserRepository().find_all_with_name(user_entity_mock.name, session_mock)

        assert len(users) == 1
        assert users[0].id == user_entity_mock.id
        assert users[0].name == user_entity_mock.name
        assert users[0].email == user_entity_mock.email

        scalars_mock.fetchall.assert_called_once()
        session_mock.scalars.assert_called_once()
