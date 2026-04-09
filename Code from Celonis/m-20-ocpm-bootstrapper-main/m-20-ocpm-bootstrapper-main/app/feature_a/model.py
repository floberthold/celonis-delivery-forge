from typing import Optional

from pydantic import BaseModel


class FeatureAItemTransport(BaseModel):
    """Example Transport class of Feature A item."""

    name: str
    number: float
    description: Optional[str] = None
