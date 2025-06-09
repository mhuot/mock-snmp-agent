#!/usr/bin/env python3
"""
Export/Import Endpoints

This module provides functionality for exporting and importing
configurations, metrics, and test data.
"""

import io
import csv
import json
import time
import zipfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile, File, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Export request model."""

    format: str = Field("json", description="Export format (json, csv, yaml)")
    include_metrics: bool = Field(True, description="Include metrics data")
    include_config: bool = Field(True, description="Include configuration")
    include_scenarios: bool = Field(True, description="Include test scenarios")
    include_history: bool = Field(False, description="Include historical data")
    time_range_hours: int = Field(24, description="Hours of history to include")

    class Config:
        schema_extra = {
            "example": {
                "format": "json",
                "include_metrics": True,
                "include_config": True,
                "include_scenarios": True,
                "include_history": True,
                "time_range_hours": 24,
            }
        }


class ImportResult(BaseModel):
    """Import operation result."""

    success: bool
    imported_items: Dict[str, int]
    warnings: List[str]
    errors: List[str]

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "imported_items": {
                    "configurations": 1,
                    "scenarios": 5,
                    "metrics_data_points": 1000,
                },
                "warnings": [],
                "errors": [],
            }
        }


class DataExporter:
    """Handles data export operations."""

    def __init__(self, controller, scenario_manager, history_manager):
        """Initialize exporter.

        Args:
            controller: Agent controller
            scenario_manager: Scenario manager
            history_manager: History manager
        """
        self.controller = controller
        self.scenario_manager = scenario_manager
        self.history_manager = history_manager

    def export_json(self, request: ExportRequest) -> Dict[str, Any]:
        """Export data as JSON.

        Args:
            request: Export request

        Returns:
            Exported data dictionary
        """
        export_data = {
            "export_timestamp": time.time(),
            "export_version": "1.0",
            "agent_version": "1.0.0",
        }

        if request.include_config:
            export_data["configuration"] = self.controller.get_configuration().dict()

        if request.include_metrics:
            export_data["current_metrics"] = self.controller.get_metrics().dict()

        if request.include_scenarios:
            export_data["scenarios"] = [
                scenario.dict() for scenario in self.scenario_manager.scenarios.values()
            ]

        if request.include_history:
            # Get historical data
            end_time = time.time()
            start_time = end_time - (request.time_range_hours * 3600)

            history = self.history_manager.query_metrics_history(
                start_time=start_time, end_time=end_time, interval_minutes=5
            )
            export_data["metrics_history"] = history.dict()

            state_history = self.history_manager.query_state_history()
            export_data["state_history"] = state_history.dict()

        return export_data

    def export_csv(self, request: ExportRequest) -> io.StringIO:
        """Export metrics data as CSV.

        Args:
            request: Export request

        Returns:
            CSV data as StringIO
        """
        output = io.StringIO()

        if request.include_metrics and request.include_history:
            # Get historical metrics
            end_time = time.time()
            start_time = end_time - (request.time_range_hours * 3600)

            history = self.history_manager.query_metrics_history(
                start_time=start_time, end_time=end_time, interval_minutes=5
            )

            if history.data_points:
                # Write CSV
                fieldnames = list(history.data_points[0].keys())
                if "datetime" not in fieldnames:
                    fieldnames.append("datetime")
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for point in history.data_points:
                    # Convert timestamp to readable format
                    point_copy = point.copy()
                    point_copy["datetime"] = datetime.fromtimestamp(
                        point_copy["timestamp"]
                    ).isoformat()
                    writer.writerow(point_copy)

        else:
            # Export current metrics only
            metrics = self.controller.get_metrics().dict()
            metrics["datetime"] = datetime.fromtimestamp(
                metrics["timestamp"]
            ).isoformat()

            writer = csv.DictWriter(output, fieldnames=list(metrics.keys()))
            writer.writeheader()
            writer.writerow(metrics)

        output.seek(0)
        return output

    def export_yaml(self, request: ExportRequest) -> str:
        """Export configuration as YAML.

        Args:
            request: Export request

        Returns:
            YAML string
        """
        import yaml

        export_data = {}

        if request.include_config:
            export_data["configuration"] = self.controller.get_configuration().dict()

        if request.include_scenarios:
            export_data["scenarios"] = [
                scenario.dict() for scenario in self.scenario_manager.scenarios.values()
            ]

        return yaml.dump(export_data, default_flow_style=False, sort_keys=False)

    def export_archive(self, request: ExportRequest) -> io.BytesIO:
        """Export all data as ZIP archive.

        Args:
            request: Export request

        Returns:
            ZIP archive as BytesIO
        """
        archive = io.BytesIO()

        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            # Export configuration
            if request.include_config:
                config_data = json.dumps(
                    self.controller.get_configuration().dict(), indent=2
                )
                zf.writestr("configuration.json", config_data)

            # Export scenarios
            if request.include_scenarios:
                scenarios_data = json.dumps(
                    [s.dict() for s in self.scenario_manager.scenarios.values()],
                    indent=2,
                )
                zf.writestr("scenarios.json", scenarios_data)

            # Export metrics
            if request.include_metrics:
                metrics_csv = self.export_csv(request)
                zf.writestr("metrics.csv", metrics_csv.getvalue())

            # Export full data
            full_export = self.export_json(request)
            zf.writestr("full_export.json", json.dumps(full_export, indent=2))

            # Add metadata
            metadata = {
                "export_timestamp": time.time(),
                "export_datetime": datetime.now().isoformat(),
                "included_components": {
                    "configuration": request.include_config,
                    "metrics": request.include_metrics,
                    "scenarios": request.include_scenarios,
                    "history": request.include_history,
                },
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        archive.seek(0)
        return archive


class DataImporter:
    """Handles data import operations."""

    def __init__(self, controller, scenario_manager):
        """Initialize importer.

        Args:
            controller: Agent controller
            scenario_manager: Scenario manager
        """
        self.controller = controller
        self.scenario_manager = scenario_manager

    async def import_json(self, data: Dict[str, Any]) -> ImportResult:
        """Import data from JSON.

        Args:
            data: JSON data dictionary

        Returns:
            Import result
        """
        result = ImportResult(success=True, imported_items={}, warnings=[], errors=[])

        # Import configuration
        if "configuration" in data:
            try:
                self.controller.update_configuration(data["configuration"])
                result.imported_items["configurations"] = 1
            except Exception as e:
                result.errors.append(f"Failed to import configuration: {str(e)}")
                result.success = False

        # Import scenarios
        if "scenarios" in data:
            imported_scenarios = 0
            for scenario_data in data["scenarios"]:
                try:
                    from .simulation_control import TestScenario

                    scenario = TestScenario(**scenario_data)
                    self.scenario_manager.create_scenario(scenario)
                    imported_scenarios += 1
                except Exception as e:
                    result.warnings.append(
                        f"Failed to import scenario '{scenario_data.get('name', 'unknown')}': {str(e)}"
                    )
            result.imported_items["scenarios"] = imported_scenarios

        return result

    async def import_archive(self, file_content: bytes) -> ImportResult:
        """Import data from ZIP archive.

        Args:
            file_content: ZIP file content

        Returns:
            Import result
        """
        result = ImportResult(success=True, imported_items={}, warnings=[], errors=[])

        try:
            archive = io.BytesIO(file_content)
            with zipfile.ZipFile(archive, "r") as zf:
                # Check for full export
                if "full_export.json" in zf.namelist():
                    data = json.loads(zf.read("full_export.json"))
                    return await self.import_json(data)

                # Import individual files
                if "configuration.json" in zf.namelist():
                    try:
                        config_data = json.loads(zf.read("configuration.json"))
                        self.controller.update_configuration(config_data)
                        result.imported_items["configurations"] = 1
                    except Exception as e:
                        result.errors.append(
                            f"Failed to import configuration: {str(e)}"
                        )

                if "scenarios.json" in zf.namelist():
                    try:
                        scenarios_data = json.loads(zf.read("scenarios.json"))
                        imported = 0
                        for scenario_data in scenarios_data:
                            try:
                                from .simulation_control import TestScenario

                                scenario = TestScenario(**scenario_data)
                                self.scenario_manager.create_scenario(scenario)
                                imported += 1
                            except Exception as e:
                                result.warnings.append(
                                    f"Scenario import error: {str(e)}"
                                )
                        result.imported_items["scenarios"] = imported
                    except Exception as e:
                        result.errors.append(f"Failed to import scenarios: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to read archive: {str(e)}")

        return result


def setup_export_import_endpoints(app, controller, scenario_manager, history_manager):
    """Setup export/import endpoints on the FastAPI app.

    Args:
        app: FastAPI application instance
        controller: Agent controller
        scenario_manager: Scenario manager
        history_manager: History manager
    """
    exporter = DataExporter(controller, scenario_manager, history_manager)
    importer = DataImporter(controller, scenario_manager)

    @app.post("/export/data", tags=["Export/Import"])
    async def export_data(request: ExportRequest):
        """Export agent data in various formats."""
        if request.format == "json":
            data = exporter.export_json(request)
            return StreamingResponse(
                io.StringIO(json.dumps(data, indent=2)),
                media_type="application/json",
                headers={
                    "Content-Disposition": "attachment; filename=snmp_agent_export.json"
                },
            )

        elif request.format == "csv":
            csv_data = exporter.export_csv(request)
            return StreamingResponse(
                csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=snmp_metrics.csv"
                },
            )

        elif request.format == "yaml":
            yaml_data = exporter.export_yaml(request)
            return StreamingResponse(
                io.StringIO(yaml_data),
                media_type="application/x-yaml",
                headers={
                    "Content-Disposition": "attachment; filename=snmp_config.yaml"
                },
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    @app.get("/export/archive", tags=["Export/Import"])
    async def export_archive(
        include_metrics: bool = Query(True, description="Include metrics"),
        include_config: bool = Query(True, description="Include configuration"),
        include_scenarios: bool = Query(True, description="Include scenarios"),
        include_history: bool = Query(True, description="Include history"),
        time_range_hours: int = Query(24, description="Hours of history"),
    ):
        """Export all data as ZIP archive."""
        request = ExportRequest(
            format="archive",
            include_metrics=include_metrics,
            include_config=include_config,
            include_scenarios=include_scenarios,
            include_history=include_history,
            time_range_hours=time_range_hours,
        )

        archive = exporter.export_archive(request)

        return StreamingResponse(
            archive,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=snmp_agent_export_{int(time.time())}.zip"
            },
        )

    @app.post("/import/data", response_model=ImportResult, tags=["Export/Import"])
    async def import_data(file: UploadFile = File(...)):
        """Import configuration and data from file."""
        content = await file.read()

        if file.filename.endswith(".json"):
            try:
                data = json.loads(content)
                return await importer.import_json(data)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON file")

        elif file.filename.endswith(".zip"):
            return await importer.import_archive(content)

        else:
            raise HTTPException(
                status_code=400, detail="Unsupported file format. Use .json or .zip"
            )

    @app.get("/export/templates/{template_name}", tags=["Export/Import"])
    async def get_export_template(template_name: str):
        """Get export template for manual editing."""
        templates = {
            "configuration": {
                "simulation": {
                    "behaviors": {
                        "delay": {"enabled": False, "global_delay": 0, "deviation": 0}
                    },
                    "state_machine": {
                        "enabled": False,
                        "device_type": "router",
                        "initial_state": "operational",
                    },
                }
            },
            "scenario": {
                "name": "Template Scenario",
                "description": "Description of the test scenario",
                "duration_seconds": 300,
                "behaviors": [
                    {
                        "name": "delay",
                        "enabled": True,
                        "parameters": {"global_delay": 100},
                    }
                ],
                "success_criteria": {
                    "min_success_rate": 95,
                    "max_response_time_ms": 200,
                },
            },
        }

        if template_name not in templates:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found. Available: {list(templates.keys())}",
            )

        return templates[template_name]
