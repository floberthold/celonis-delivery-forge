from python_core_persistence import Base, TenantIndependent
from sqlalchemy.orm import Mapped, mapped_column


# Use tenant independent entities for service specific entities that are the same for all tenants.
class UserType(TenantIndependent, Base):
    """Example model class of tenant independent user type."""

    name: Mapped[str] = mapped_column()
