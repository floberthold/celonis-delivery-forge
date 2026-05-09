from python_core_internal_client import PythonCoreBaseModel
from python_core_persistence import TenantIndependentTransportMixin


class UserTypeTransport(TenantIndependentTransportMixin, PythonCoreBaseModel):
    """Transport class of tenant aware user."""

    name: str
