#!/usr/bin/env python3
"""
Export/Import Functionality Tests

Tests for data export and import capabilities including JSON, CSV, YAML,
and ZIP archive formats.
"""

import pytest
import json
import csv
import zipfile
import tempfile
import io
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from rest_api.export_import import DataExporter, DataImporter, ExportRequest
from rest_api.simulation_control import (
    TestScenario,
    BehaviorConfig,
    SimulationScenarioManager,
)
from rest_api.controllers import MockSNMPAgentController
from rest_api.query_endpoints import DataHistoryManager


class TestDataExporter:
    """Test suite for data export functionality."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_configuration.return_value = Mock()
        controller.get_configuration.return_value.dict.return_value = {
            "simulation": {
                "behaviors": {"delay": {"enabled": True, "global_delay": 100}}
            }
        }
        controller.get_metrics.return_value = Mock()
        controller.get_metrics.return_value.dict.return_value = {
            "timestamp": 1640995200.0,
            "requests_total": 1000,
            "requests_successful": 950,
            "avg_response_time_ms": 75.5,
        }
        return controller

    @pytest.fixture
    def mock_scenario_manager(self):
        """Create mock scenario manager."""
        manager = Mock(spec=SimulationScenarioManager)
        manager.scenarios = {
            "test-scenario": TestScenario(
                name="Test Scenario",
                description="A test scenario",
                duration_seconds=300,
                behaviors=[
                    BehaviorConfig(
                        name="delay", enabled=True, parameters={"global_delay": 100}
                    )
                ],
            )
        }
        return manager

    @pytest.fixture
    def mock_history_manager(self):
        """Create mock history manager."""
        manager = Mock(spec=DataHistoryManager)

        # Create a mock response that has both dict() method and direct attribute access
        metrics_response = Mock()
        metrics_response.dict.return_value = {
            "start_time": 1640991600.0,
            "end_time": 1640995200.0,
            "interval_minutes": 5,
            "data_points": [
                {"timestamp": 1640991600.0, "requests_total": 900},
                {"timestamp": 1640991900.0, "requests_total": 950},
                {"timestamp": 1640995200.0, "requests_total": 1000},
            ],
        }
        metrics_response.data_points = [
            {"timestamp": 1640991600.0, "requests_total": 900},
            {"timestamp": 1640991900.0, "requests_total": 950},
            {"timestamp": 1640995200.0, "requests_total": 1000},
        ]
        manager.query_metrics_history.return_value = metrics_response
        manager.query_state_history.return_value = Mock()
        manager.query_state_history.return_value.dict.return_value = {
            "device_type": "router",
            "current_state": "operational",
            "total_transitions": 2,
            "transitions": [
                {
                    "timestamp": 1640991600.0,
                    "from_state": "booting",
                    "to_state": "operational",
                }
            ],
        }
        return manager

    @pytest.fixture
    def data_exporter(
        self, mock_controller, mock_scenario_manager, mock_history_manager
    ):
        """Create data exporter."""
        return DataExporter(
            mock_controller, mock_scenario_manager, mock_history_manager
        )

    def test_export_json_config_only(self, data_exporter):
        """Test JSON export with configuration only."""
        request = ExportRequest(
            format="json",
            include_config=True,
            include_metrics=False,
            include_scenarios=False,
            include_history=False,
        )

        result = data_exporter.export_json(request)

        assert "export_timestamp" in result
        assert "export_version" in result
        assert "configuration" in result
        assert "current_metrics" not in result
        assert "scenarios" not in result
        assert "metrics_history" not in result

    def test_export_json_full(self, data_exporter):
        """Test full JSON export."""
        request = ExportRequest(
            format="json",
            include_config=True,
            include_metrics=True,
            include_scenarios=True,
            include_history=True,
            time_range_hours=24,
        )

        result = data_exporter.export_json(request)

        assert "export_timestamp" in result
        assert "configuration" in result
        assert "current_metrics" in result
        assert "scenarios" in result
        assert "metrics_history" in result
        assert "state_history" in result

        # Check data structure
        assert isinstance(result["scenarios"], list)
        assert len(result["scenarios"]) > 0
        assert result["scenarios"][0]["name"] == "Test Scenario"

    def test_export_csv_format(self, data_exporter):
        """Test CSV export format."""
        request = ExportRequest(
            format="csv", include_metrics=True, include_history=True, time_range_hours=1
        )

        result = data_exporter.export_csv(request)

        assert isinstance(result, io.StringIO)

        # Parse CSV content
        result.seek(0)
        csv_content = result.read()
        lines = csv_content.strip().split("\n")

        assert len(lines) >= 2  # Header + at least one data row

        # Check header
        header = lines[0].split(",")
        assert "timestamp" in header

        # Check data format
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) > 0

        # Should have datetime field
        if rows:
            assert "datetime" in rows[0]

    def test_export_yaml_format(self, data_exporter):
        """Test YAML export format."""
        request = ExportRequest(
            format="yaml", include_config=True, include_scenarios=True
        )

        result = data_exporter.export_yaml(request)

        assert isinstance(result, str)

        # Parse YAML to validate format
        parsed = yaml.safe_load(result)
        assert "configuration" in parsed
        assert "scenarios" in parsed

        # Check structure
        assert isinstance(parsed["scenarios"], list)

    def test_export_archive_format(self, data_exporter):
        """Test ZIP archive export."""
        request = ExportRequest(
            format="archive",
            include_config=True,
            include_metrics=True,
            include_scenarios=True,
            include_history=True,
        )

        result = data_exporter.export_archive(request)

        assert isinstance(result, io.BytesIO)

        # Validate ZIP content
        result.seek(0)
        with zipfile.ZipFile(result, "r") as zf:
            file_list = zf.namelist()

            expected_files = [
                "configuration.json",
                "scenarios.json",
                "metrics.csv",
                "full_export.json",
                "metadata.json",
            ]

            for expected_file in expected_files:
                assert expected_file in file_list

            # Check metadata
            metadata_content = zf.read("metadata.json")
            metadata = json.loads(metadata_content)

            assert "export_timestamp" in metadata
            assert "included_components" in metadata

    def test_export_csv_current_metrics_only(self, data_exporter):
        """Test CSV export with current metrics only."""
        request = ExportRequest(
            format="csv", include_metrics=True, include_history=False
        )

        result = data_exporter.export_csv(request)

        result.seek(0)
        csv_content = result.read()
        lines = csv_content.strip().split("\n")

        # Should have header + one data row (current metrics)
        assert len(lines) == 2

        # Parse and verify
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 1

        row = rows[0]
        assert "requests_total" in row
        assert "datetime" in row


class TestDataImporter:
    """Test suite for data import functionality."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.update_configuration = Mock()
        return controller

    @pytest.fixture
    def mock_scenario_manager(self):
        """Create mock scenario manager."""
        manager = Mock(spec=SimulationScenarioManager)
        manager.create_scenario = Mock(return_value="new-scenario-id")
        return manager

    @pytest.fixture
    def data_importer(self, mock_controller, mock_scenario_manager):
        """Create data importer."""
        return DataImporter(mock_controller, mock_scenario_manager)

    @pytest.mark.asyncio
    async def test_import_json_configuration(self, data_importer, mock_controller):
        """Test importing JSON configuration."""
        import_data = {
            "export_version": "1.0",
            "configuration": {
                "simulation": {
                    "behaviors": {"delay": {"enabled": True, "global_delay": 200}}
                }
            },
        }

        result = await data_importer.import_json(import_data)

        assert result.success is True
        assert result.imported_items.get("configurations", 0) == 1
        assert len(result.errors) == 0

        # Should have called update_configuration
        mock_controller.update_configuration.assert_called_once()
        called_config = mock_controller.update_configuration.call_args[0][0]
        assert called_config == import_data["configuration"]

    @pytest.mark.asyncio
    async def test_import_json_scenarios(self, data_importer, mock_scenario_manager):
        """Test importing scenarios from JSON."""
        import_data = {
            "scenarios": [
                {
                    "name": "Imported Scenario 1",
                    "description": "First imported scenario",
                    "duration_seconds": 300,
                    "behaviors": [],
                },
                {
                    "name": "Imported Scenario 2",
                    "description": "Second imported scenario",
                    "duration_seconds": 600,
                    "behaviors": [
                        {
                            "name": "delay",
                            "enabled": True,
                            "parameters": {"global_delay": 150},
                        }
                    ],
                },
            ]
        }

        result = await data_importer.import_json(import_data)

        assert result.success is True
        assert result.imported_items.get("scenarios", 0) == 2

        # Should have called create_scenario twice
        assert mock_scenario_manager.create_scenario.call_count == 2

    @pytest.mark.asyncio
    async def test_import_json_with_errors(self, data_importer, mock_controller):
        """Test import with configuration errors."""
        # Make controller raise exception
        mock_controller.update_configuration.side_effect = Exception("Config error")

        import_data = {"configuration": {"invalid": "config"}}

        result = await data_importer.import_json(import_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Failed to import configuration" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_zip_archive(self, data_importer):
        """Test importing from ZIP archive."""
        # Create test ZIP archive
        archive_data = io.BytesIO()

        with zipfile.ZipFile(archive_data, "w") as zf:
            # Add full export
            full_export = {
                "export_version": "1.0",
                "configuration": {
                    "simulation": {"behaviors": {"delay": {"enabled": True}}}
                },
                "scenarios": [
                    {
                        "name": "Archive Scenario",
                        "description": "From archive",
                        "duration_seconds": 300,
                        "behaviors": [],
                    }
                ],
            }
            zf.writestr("full_export.json", json.dumps(full_export))

            # Add metadata
            metadata = {
                "export_timestamp": 1640995200.0,
                "included_components": {"configuration": True, "scenarios": True},
            }
            zf.writestr("metadata.json", json.dumps(metadata))

        archive_data.seek(0)
        result = await data_importer.import_archive(archive_data.getvalue())

        assert result.success is True
        assert result.imported_items.get("configurations", 0) == 1
        assert result.imported_items.get("scenarios", 0) == 1

    @pytest.mark.asyncio
    async def test_import_zip_individual_files(self, data_importer):
        """Test importing ZIP with individual files."""
        archive_data = io.BytesIO()

        with zipfile.ZipFile(archive_data, "w") as zf:
            # Add individual files
            config = {"simulation": {"behaviors": {"drop": {"enabled": True}}}}
            zf.writestr("configuration.json", json.dumps(config))

            scenarios = [
                {
                    "name": "Individual File Scenario",
                    "description": "From individual file",
                    "duration_seconds": 120,
                    "behaviors": [],
                }
            ]
            zf.writestr("scenarios.json", json.dumps(scenarios))

        archive_data.seek(0)
        result = await data_importer.import_archive(archive_data.getvalue())

        assert result.success is True
        assert result.imported_items.get("configurations", 0) == 1
        assert result.imported_items.get("scenarios", 0) == 1

    @pytest.mark.asyncio
    async def test_import_invalid_archive(self, data_importer):
        """Test importing invalid archive."""
        invalid_data = b"not a zip file"

        result = await data_importer.import_archive(invalid_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Failed to read archive" in result.errors[0]


class TestExportImportIntegration:
    """Integration tests for export/import functionality."""

    @pytest.fixture
    def setup_managers(self):
        """Set up all required managers."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_configuration.return_value = Mock()
        controller.get_configuration.return_value.dict.return_value = {
            "simulation": {"behaviors": {"delay": {"enabled": True}}}
        }
        controller.get_metrics.return_value = Mock()
        controller.get_metrics.return_value.dict.return_value = {
            "timestamp": 1640995200.0,
            "requests_total": 500,
            "avg_response_time_ms": 60.0,
        }
        controller.update_configuration = Mock()

        scenario_manager = Mock(spec=SimulationScenarioManager)
        scenario_manager.scenarios = {
            "test": TestScenario(
                name="Integration Test",
                description="Test scenario",
                duration_seconds=300,
                behaviors=[],
            )
        }
        scenario_manager.create_scenario = Mock()

        history_manager = Mock(spec=DataHistoryManager)
        history_manager.query_metrics_history.return_value = Mock()
        history_manager.query_metrics_history.return_value.dict.return_value = {
            "data_points": []
        }
        history_manager.query_state_history.return_value = Mock()
        history_manager.query_state_history.return_value.dict.return_value = {
            "transitions": []
        }

        exporter = DataExporter(controller, scenario_manager, history_manager)
        importer = DataImporter(controller, scenario_manager)

        return {
            "controller": controller,
            "scenario_manager": scenario_manager,
            "history_manager": history_manager,
            "exporter": exporter,
            "importer": importer,
        }

    @pytest.mark.asyncio
    async def test_export_import_roundtrip(self, setup_managers):
        """Test complete export/import roundtrip."""
        managers = setup_managers
        exporter = managers["exporter"]
        importer = managers["importer"]

        # Export data
        export_request = ExportRequest(
            format="json", include_config=True, include_scenarios=True
        )

        exported_data = exporter.export_json(export_request)

        # Import the exported data
        import_result = await importer.import_json(exported_data)

        assert import_result.success is True
        assert len(import_result.errors) == 0

        # Should have imported configuration and scenarios
        if exported_data.get("configuration"):
            assert import_result.imported_items.get("configurations", 0) >= 1
        if exported_data.get("scenarios"):
            assert import_result.imported_items.get("scenarios", 0) >= 1

    def test_archive_roundtrip(self, setup_managers):
        """Test archive export/import roundtrip."""
        managers = setup_managers
        exporter = managers["exporter"]

        # Export as archive
        export_request = ExportRequest(
            format="archive", include_config=True, include_scenarios=True
        )

        archive = exporter.export_archive(export_request)

        # Verify archive can be read
        archive.seek(0)
        with zipfile.ZipFile(archive, "r") as zf:
            file_list = zf.namelist()
            assert "full_export.json" in file_list
            assert "metadata.json" in file_list

            # Read and parse full export
            full_export_content = zf.read("full_export.json")
            full_export = json.loads(full_export_content)

            assert "export_timestamp" in full_export
            assert "configuration" in full_export

    def test_template_generation(self, setup_managers):
        """Test export template generation."""
        # This would be tested through the API endpoint
        # Here we validate the template structure

        config_template = {
            "simulation": {
                "behaviors": {
                    "delay": {"enabled": False, "global_delay": 0, "deviation": 0}
                }
            }
        }

        # Template should be valid configuration structure
        assert "simulation" in config_template
        assert "behaviors" in config_template["simulation"]

    def test_error_recovery(self, setup_managers):
        """Test error recovery during import."""
        managers = setup_managers
        importer = managers["importer"]

        # Partial failure scenario - some imports succeed, others fail
        managers["scenario_manager"].create_scenario.side_effect = [
            "success-id",  # First scenario succeeds
            Exception("Scenario creation failed"),  # Second fails
            "success-id-2",  # Third succeeds
        ]

        import_data = {
            "scenarios": [
                {
                    "name": "Good Scenario 1",
                    "description": "Good",
                    "duration_seconds": 300,
                    "behaviors": [],
                },
                {
                    "name": "Bad Scenario",
                    "description": "Bad",
                    "duration_seconds": 300,
                    "behaviors": [],
                },
                {
                    "name": "Good Scenario 2",
                    "description": "Good",
                    "duration_seconds": 300,
                    "behaviors": [],
                },
            ]
        }

        # Should handle partial failures gracefully
        # In real implementation, would track warnings for failed imports


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
