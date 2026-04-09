from unittest.mock import AsyncMock, Mock

from aio_pika import ExchangeType
from app.feature_rabbit_mq import TaskMessage
from app.services.integration_client import DataPoolTransport


class TestRabbitMQService:
    async def test_publish_task(self, mock_rabbit_mq_service):
        task = TaskMessage(name="test", description="test", status="test")
        channel_mock = AsyncMock()
        exchange_mock = AsyncMock()
        channel_mock.declare_exchange = AsyncMock(return_value=exchange_mock)

        await mock_rabbit_mq_service.publish_task(task, channel_mock)

        channel_mock.declare_exchange.assert_called_once_with("pcsandbox", durable=True, type=ExchangeType.TOPIC)
        exchange_mock.publish.assert_called_once_with(task, routing_key="task.created")

    async def test_process_task(self, mock_rabbit_mq_service):
        task = TaskMessage(name="test", description="test", status="test")
        await mock_rabbit_mq_service.process_task(task)

        mock_rabbit_mq_service.integration_client.post_api_internal_data_pools.assert_called_once_with(
            DataPoolTransport(name=task.name, description=task.description)
        )
