from pydantic import Field
from python_core_rabbit_mq.aio_pika.message import VersionedMessage


class TaskMessage(VersionedMessage):
    """Task message."""

    version: str = Field(default="1.0.0")

    name: str
    description: str
    status: str
