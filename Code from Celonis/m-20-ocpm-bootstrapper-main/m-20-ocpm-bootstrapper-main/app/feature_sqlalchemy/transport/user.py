from python_core_internal_client import PythonCoreBaseModel
from python_core_persistence.transport.tenant_aware import TenantAwareTransportMixin


class CreateUserTransport(PythonCoreBaseModel):
    """Transport class to create tenant aware user."""

    name: str
    email: str


class UpdateUserTransport(CreateUserTransport):
    """Transport class to update tenant aware user."""


class UserTransport(TenantAwareTransportMixin, CreateUserTransport):
    """Transport class of tenant aware user."""
