import logging
from typing import Optional

from aio_pika import ExchangeType
from app.feature_rabbit_mq.message import TaskMessage
from app.services.integration_client import DataPoolTransport, IntegrationClient
from python_core_internal_client.settings import internal_client_settings
from python_core_rabbit_mq.aio_pika.connection import PythonCoreChannel

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service for rabbit mq related methods."""

    def __init__(self, integration_client: Optional[IntegrationClient] = None):
        self.integration_client = integration_client or IntegrationClient(
            internal_client_settings.celonis.services["integration"].url
        )

    async def publish_task(self, task: TaskMessage, channel: PythonCoreChannel) -> None:
        """Publish task."""
        exchange = await channel.declare_exchange("pcsandbox", durable=True, type=ExchangeType.TOPIC)
        await exchange.publish(task, routing_key="task.created")

    async def process_task(self, task: TaskMessage) -> None:
        """Process incoming task and create pool with task name."""
        logger.info("Processing task `%s`...", task)
        await self.integration_client.post_api_internal_data_pools(
            DataPoolTransport(name=task.name, description=task.description)
        )
