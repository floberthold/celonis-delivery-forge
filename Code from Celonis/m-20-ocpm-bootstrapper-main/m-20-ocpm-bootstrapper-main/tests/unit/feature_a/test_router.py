from unittest.mock import patch

from app.feature_a import get_description, get_items
from app.feature_a.model import FeatureAItemTransport


class TestFeatureARouter:
    @patch("app.feature_a.service.FeatureAService.get_description")
    async def test_get_feature_a_should_call_feature_a_service_get_description(self, service_get_description):
        service_get_description.return_value = "test"

        result = await get_description()

        service_get_description.assert_called()
        assert result == "test"

    @patch("app.feature_a.service.FeatureAService.get_items")
    async def test_get_feature_a_should_call_feature_a_service_get_feature_a_string(self, service_get_items):
        service_get_items.return_value = [FeatureAItemTransport(name="test", number=1)]

        result = await get_items()

        service_get_items.assert_called()
        assert len(result) == 1
        assert result[0].name == "test"
        assert result[0].number == 1
