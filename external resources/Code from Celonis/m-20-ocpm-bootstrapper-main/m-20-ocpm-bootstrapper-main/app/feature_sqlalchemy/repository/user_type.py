from app.feature_sqlalchemy.repository.entities.user_type import UserType
from python_core_persistence.repository.base import BaseRepository


class UserTypeRepository(BaseRepository[UserType]):
    """A repository that provides methods related to User models."""

    ModelClass = UserType
