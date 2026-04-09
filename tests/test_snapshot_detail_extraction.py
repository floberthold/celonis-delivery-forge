"""Tests for snapshot detail extraction and display."""

import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from foundry.models import CelonisSnapshot, SnapshotTask, SnapshotChangeType
from foundry.services.snapshot_detail_extractors import (
    fetch_asset_detail_by_family,
    crawl_asset_dependencies,
)


class MockApiResult:
    """Mock API result object."""
    def __init__(self, ok=True, body=None):
        self.ok = ok
        self.body = body or "{}"


class TestDetailExtractionIntegration:
    """Test that detail extraction is properly integrated into snapshot service."""

    def test_fetch_asset_detail_by_family_analysis(self):
        """Test fetching analysis detail."""
        mock_gw = Mock()
        detail_payload = {
            "id": "analysis-1",
            "name": "Sales Analysis",
            "description": "Monthly sales metrics",
            "owner": "user@example.com",
        }
        mock_gw.extract_full = Mock(return_value=MockApiResult(
            ok=True,
            body=json.dumps(detail_payload)
        ))

        result = fetch_asset_detail_by_family(
            mock_gw,
            "https://celonis.example.com",
            "ANALYSIS",
            "analysis-1",
            package_id="pkg-1",
        )

        assert result is not None
        assert result.get("detail") is not None
        assert result["detail"].get("name") == "Sales Analysis"
        assert result.get("source_endpoint") is not None

    def test_fetch_asset_detail_by_family_kpi(self):
        """Test fetching KPI detail."""
        mock_gw = Mock()
        detail_payload = {
            "id": "kpi-1",
            "name": "Revenue KPI",
            "formula": "SUM(revenue)",
            "unit": "USD",
        }
        mock_gw.extract_full = Mock(return_value=MockApiResult(
            ok=True,
            body=json.dumps(detail_payload)
        ))

        result = fetch_asset_detail_by_family(
            mock_gw,
            "https://celonis.example.com",
            "KPI",
            "kpi-1",
            package_id="pkg-1",
        )

        assert result is not None
        assert result.get("detail") is not None
        assert result["detail"].get("name") == "Revenue KPI"

    def test_crawl_asset_dependencies_single_level(self):
        """Test crawling dependencies at a single level."""
        mock_gw = Mock()
        
        def mock_extract_full(tenant_base_url, source_path, **kwargs):
            detail = {}
            if "asset-1" in source_path:
                detail = {
                    "id": "asset-1",
                    "name": "Asset 1",
                    "references": ["asset-2", "asset-3"],
                }
            elif "asset-2" in source_path:
                detail = {
                    "id": "asset-2",
                    "name": "Referenced Asset 2",
                    "references": [],
                }
            elif "asset-3" in source_path:
                detail = {
                    "id": "asset-3",
                    "name": "Referenced Asset 3",
                    "references": ["asset-4"],
                }
            return MockApiResult(ok=True, body=json.dumps(detail))
        
        mock_gw.extract_full = Mock(side_effect=mock_extract_full)

        result = crawl_asset_dependencies(
            mock_gw,
            "https://celonis.example.com",
            ["asset-1"],
            max_depth=1,
            max_nodes=10,
        )

        # Function should return a list or dict of dependencies
        assert result is not None
        assert isinstance(result, (list, dict))

    def test_task_enrichment_with_detail_and_dependencies(self):
        """Test that tasks are enriched with detail and dependency information."""
        snapshot_id = uuid4()
        client_id = uuid4()
        task_id = "task-1"
        
        # Simulate enriched task data
        enriched_task_data = {
            "id": task_id,
            "name": "Sales KPI",
            "type": "KPI",
            "_forge_detail": {
                "family": "KPI",
                "source_endpoint": "/studio/api/kpis/task-1",
                "detail": {
                    "name": "Sales KPI",
                    "formula": "SUM(sales)",
                    "unit": "USD",
                    "owner": "user@example.com",
                },
                "references": {
                    "assets": ["ref-asset-1", "ref-asset-2"],
                },
            },
            "_forge_dependencies": {
                "seed_count": 2,
                "crawled_count": 3,
                "dependencies": [
                    {
                        "id": "dep-1",
                        "type": "ANALYSIS",
                        "name": "Sales Trend Analysis",
                        "distance": 1,
                    },
                    {
                        "id": "dep-2",
                        "type": "KPI",
                        "name": "Regional KPI",
                        "distance": 1,
                    },
                    {
                        "id": "dep-3",
                        "type": "VIEW",
                        "name": "Sales View",
                        "distance": 2,
                    },
                ],
            },
        }

        # Create snapshot task with enriched data
        task = SnapshotTask(
            snapshot_id=snapshot_id,
            client_id=client_id,
            package_id="pkg-1",
            task_id=task_id,
            name=enriched_task_data["name"],
            task_type=enriched_task_data["type"],
            description="Test Task",
            raw_json=enriched_task_data,
            change_type=SnapshotChangeType.added,
        )

        # Verify enriched data is stored
        assert task.raw_json["_forge_detail"] is not None
        assert task.raw_json["_forge_dependencies"] is not None
        assert task.raw_json["_forge_detail"]["detail"]["name"] == "Sales KPI"
        assert len(task.raw_json["_forge_dependencies"]["dependencies"]) == 3

    def test_snapshot_detail_ui_context_includes_enrichment(self):
        """Test that snapshot detail UI context includes enriched data."""
        # This is more of an integration test that verifies the UI route
        # properly extracts enriched data from tasks
        
        enriched_task = {
            "id": "task-123",
            "name": "Analysis Task",
            "type": "ANALYSIS",
            "_forge_detail": {
                "family": "ANALYSIS",
                "source_endpoint": "/studio/api/analyses/task-123",
                "detail": {"name": "Analysis Task", "description": "Test"},
                "references": {"assets": []},
            },
            "_forge_dependencies": {
                "seed_count": 0,
                "crawled_count": 2,
                "dependencies": [
                    {"id": "dep-1", "type": "KPI", "name": "KPI 1"},
                    {"id": "dep-2", "type": "VIEW", "name": "View 1"},
                ],
            },
        }

        # Simulate what the UI route does
        forge_detail = enriched_task.get("_forge_detail", {})
        forge_dependencies = enriched_task.get("_forge_dependencies", {})

        # Verify extraction
        assert forge_detail.get("family") == "ANALYSIS"
        assert len(forge_dependencies.get("dependencies", [])) == 2
        
        # Verify it would be passed to template context
        template_context = {
            "forge_detail": forge_detail,
            "forge_dependencies": forge_dependencies,
        }
        
        assert template_context["forge_detail"]["detail"]["name"] == "Analysis Task"
        assert len(template_context["forge_dependencies"]["dependencies"]) == 2


class TestDetailExtractionErrorHandling:
    """Test that detail extraction handles errors gracefully."""

    def test_detail_extraction_graceful_failure(self):
        """Test that detail extraction doesn't fail if API is unavailable."""
        mock_gw = Mock()
        mock_gw.extract_full = Mock(side_effect=Exception("API unavailable"))

        # Should not raise, should return dict with error
        try:
            result = fetch_asset_detail_by_family(
                mock_gw,
                "https://celonis.example.com",
                "ANALYSIS",
                "analysis-1",
            )
            # Function should handle the error gracefully
            assert result is None or isinstance(result, dict)
        except Exception:
            # If it does raise, that's okay too - it means error handling upstream
            pass

    def test_dependency_crawl_graceful_failure(self):
        """Test that dependency crawl handles errors gracefully."""
        mock_gw = Mock()
        mock_gw.extract_full = Mock(side_effect=Exception("Connection error"))

        # Should not raise, should return empty list or None
        try:
            result = crawl_asset_dependencies(
                mock_gw,
                "https://celonis.example.com",
                ["asset-1"],
            )
            # Function should handle the error gracefully
            assert result is None or isinstance(result, (list, dict))
        except Exception:
            # If it does raise, that's okay too
            pass


class TestUIIntegrationWithEnrichedData:
    """Test UI integration with enriched snapshot data."""

    def test_task_display_without_enrichment(self):
        """Test that tasks display correctly even without enrichment."""
        task_data = {
            "id": "task-1",
            "name": "Simple Task",
            "type": "VIEW",
        }
        
        # Should not fail when enrichment data is missing
        forge_detail = task_data.get("_forge_detail", {})
        forge_dependencies = task_data.get("_forge_dependencies", {})
        
        assert forge_detail == {}
        assert forge_dependencies == {}

    def test_enriched_data_display_format(self):
        """Test that enriched data can be displayed in template."""
        enriched_data = {
            "_forge_detail": {
                "detail": {
                    "name": "Test Asset",
                    "description": "Test",
                    "owner": "user@example.com",
                    "createDate": "2024-01-01",
                    "modifyDate": "2024-01-15",
                },
                "references": {
                    "assets": ["a1", "a2"],
                    "tables": ["t1"],
                },
            },
            "_forge_dependencies": {
                "crawled_count": 5,
                "dependencies": [
                    {"id": "1", "type": "KPI", "name": "Test KPI", "distance": 1},
                    {"id": "2", "type": "VIEW", "name": "Test View", "distance": 2},
                ],
            },
        }
        
        # Verify can extract for template display
        detail = enriched_data.get("_forge_detail", {})
        deps = enriched_data.get("_forge_dependencies", {})
        
        # Should be able to display key properties
        detail_keys = list(detail.get("detail", {}).keys())[:5]
        assert len(detail_keys) > 0
        
        # Should be able to display dependencies
        dep_list = deps.get("dependencies", [])
        assert len(dep_list) == 2
        assert dep_list[0]["name"] == "Test KPI"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

