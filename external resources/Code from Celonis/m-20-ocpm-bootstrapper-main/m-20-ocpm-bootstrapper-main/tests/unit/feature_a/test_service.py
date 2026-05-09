class TestFeatureAService:
    async def test_get_description(self, mock_feature_a_service):
        assert await mock_feature_a_service.get_description() == "This is a test"

    async def test_get_items(self, mock_feature_a_service):
        result = await mock_feature_a_service.get_items()
        assert len(result) == 10

    async def test_get_permissions(self, mock_feature_a_service, user_service_permission_transport):
        result = await mock_feature_a_service.get_permissions()

        assert len(result) == 1
        assert result[0] == user_service_permission_transport
        mock_feature_a_service.team_client.get_api_cloud_permissions.assert_called_once()

    async def test_get_data_pools_internal(self, mock_feature_a_service, data_pool_transport):
        result = await mock_feature_a_service.get_data_pools_internal()

        assert len(result) == 1
        assert result[0] == data_pool_transport
        mock_feature_a_service.integration_client.get_api_internal_data_pools.assert_called_once()

    async def test_create_data_pool_internal(self, mock_feature_a_service, data_pool_transport):
        result = await mock_feature_a_service.create_data_pool_internal(data_pool_transport)

        assert result == data_pool_transport
        mock_feature_a_service.integration_client.post_api_internal_data_pools.assert_called_once_with(
            data_pool_transport
        )

    async def test_get_spaces(self, mock_feature_a_service, space_transport):
        result = await mock_feature_a_service.get_spaces()

        assert len(result) == 1
        assert result[0] == space_transport
        mock_feature_a_service.package_manager_client.get_api_spaces.assert_called_once()

    async def test_delete_package(self, mock_feature_a_service):
        await mock_feature_a_service.delete_package("TEST_ID")

        mock_feature_a_service.package_manager_client.delete_api_packages_id.assert_called_once()
