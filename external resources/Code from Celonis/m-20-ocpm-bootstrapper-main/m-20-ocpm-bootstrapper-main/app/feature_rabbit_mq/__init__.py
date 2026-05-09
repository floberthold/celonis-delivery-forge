import logging

from app.feature_rabbit_mq.message import TaskMessage
from app.feature_rabbit_mq.service import RabbitMQService
from python_core_rabbit_mq.app.broker import RabbitMQBroker
from python_core_rabbit_mq.app.fastapi import RabbitMQChannelDependency
from python_core_web_security import AuthenticatedAPIRouter

logger = logging.getLogger(__name__)

PATH = "/feature_rabbit_mq"
TAGS = ["feature_rabbit_mq"]

service = RabbitMQService()
router = AuthenticatedAPIRouter(prefix=PATH, tags=TAGS)  # type: ignore


@router.post("", operation_id="publishTask", response_model=TaskMessage)
async def publish_task(task: TaskMessage, channel: RabbitMQChannelDependency) -> TaskMessage:
    """Creates task."""
    await service.publish_task(task, channel)
    return task


broker = RabbitMQBroker()


@broker.consume("PcSandbox.Task.Created", queue_kwargs={"arguments": {"x-queue-type": "quorum"}})
async def process_task(message: TaskMessage) -> None:
    """Consumes queue `PcSandbox.Task.Created` and processes task."""
    await service.process_task(message)
