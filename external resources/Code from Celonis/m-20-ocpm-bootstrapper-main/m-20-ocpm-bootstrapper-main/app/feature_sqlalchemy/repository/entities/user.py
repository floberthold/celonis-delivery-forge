from python_core_persistence import Base, TenantAware
from sqlalchemy.orm import Mapped, mapped_column


# Use tenant aware entities for all tenant/customer related data that can't be shared between tenants/customers.
class User(TenantAware, Base):
    """Example model class of tenant aware user."""

    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
