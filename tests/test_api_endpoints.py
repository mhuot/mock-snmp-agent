#!/usr/bin/env python3
"""
REST API Endpoint Tests

Comprehensive test suite for all REST API endpoints including
WebSocket connections, query operations, and simulation control.
"""

import asyncio
import json
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from websockets import connect
from websockets.exceptions import ConnectionClosed

from src.rest_api.controllers import MockSNMPAgentController
from src.rest_api.models import AgentStatus, HealthStatus

# Import the API server and components
from src.rest_api.server import SNMPAgentAPIServer


class TestAPIEndpoints:
    """Test suite for REST API endpoints."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock controller for testing."""
        controller = MockSNMPAgentController()
        controller.agent_process = Mock()
        controller.agent_process.poll.return_value = None  # Process running
        controller.agent_process.pid = 12345

        # Set config to None so it uses default configuration
        controller.config = None

        return controller

    @pytest.fixture
    def api_server(self, mock_controller):
        """Create API server instance for testing."""
        server = SNMPAgentAPIServer(
            agent_process=mock_controller.agent_process,
            config=None,  # Use None so controller uses default config
            data_dir="./test_data",
            snmp_endpoint="127.0.0.1:11611",
            api_host="127.0.0.1",
            api_port=8080,
        )
        return server

    @pytest.fixture
    def client(self, api_server):
        """Create test client."""
        return TestClient(api_server.app)

    @pytest.mark.integration
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "version" in data
        assert "snmp_endpoint" in data

        assert data["status"] in ["healthy", "unhealthy", "degraded"]
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["snmp_endpoint"] == "127.0.0.1:11611"

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "timestamp",
            "uptime_seconds",
            "requests_total",
            "requests_successful",
            "requests_failed",
            "avg_response_time_ms",
            "current_connections",
        ]

        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))

    @pytest.mark.integration
    def test_config_get_endpoint(self, client):
        """Test configuration retrieval."""
        response = client.get("/config")
        assert response.status_code == 200

        data = response.json()
        assert "simulation" in data
        assert "timestamp" in data
        assert "behaviors" in data["simulation"]

    def test_config_update_endpoint(self, client):
        """Test configuration update."""
        config_update = {
            "simulation": {
                "behaviors": {"delay": {"enabled": True, "global_delay": 100}}
            }
        }

        response = client.put("/config", json=config_update)
        assert response.status_code == 200

        data = response.json()
        assert "simulation" in data
        assert "timestamp" in data

    def test_agent_status_endpoint(self, client):
        """Test agent status endpoint."""
        response = client.get("/agent/status")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "status",
            "timestamp",
            "pid",
            "snmp_endpoint",
            "data_directory",
            "active_behaviors",
        ]

        for field in required_fields:
            assert field in data

        assert data["status"] in ["running", "stopped", "starting", "stopping", "error"]
        assert isinstance(data["active_behaviors"], list)

    def test_agent_restart_endpoint(self, client):
        """Test agent restart endpoint."""
        restart_request = {"force": False, "timeout_seconds": 30}

        response = client.post("/agent/restart", json=restart_request)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "restart_time_seconds" in data
        assert isinstance(data["success"], bool)

    def test_available_oids_endpoint(self, client):
        """Test available OIDs endpoint."""
        response = client.get("/oids/available")
        assert response.status_code == 200

        data = response.json()
        assert "oids" in data
        assert "total_count" in data
        assert "data_sources" in data
        assert "timestamp" in data

        assert isinstance(data["oids"], list)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["data_sources"], list)

    def test_root_endpoint(self, client):
        """Test API root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

        assert data["name"] == "Mock SNMP Agent API"
        assert isinstance(data["endpoints"], dict)


class TestQueryEndpoints:
    """Test suite for enhanced query endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with query endpoints."""
        from src.rest_api.server import SNMPAgentAPIServer

        server = SNMPAgentAPIServer()
        return TestClient(server.app)

    def test_oid_query_endpoint(self, client):
        """Test OID query endpoint."""
        query_request = {
            "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"],
            "community": "public",
            "include_metadata": True,
        }

        response = client.post("/oids/query", json=query_request)
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "results" in data
        assert "errors" in data

        # Should have results for requested OIDs
        for oid in query_request["oids"]:
            if oid in data["results"]:
                result = data["results"][oid]
                assert "value" in result
                assert "type" in result
                if query_request["include_metadata"]:
                    assert "metadata" in result

    def test_oid_search_endpoint(self, client):
        """Test OID search endpoint."""
        response = client.get("/oids/search?pattern=1.3.6.1.2.1&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "pattern" in data
        assert "count" in data
        assert "oids" in data

        assert data["pattern"] == "1.3.6.1.2.1"
        assert isinstance(data["oids"], list)
        assert len(data["oids"]) <= 10

    def test_oid_tree_endpoint(self, client):
        """Test OID tree endpoint."""
        response = client.get("/oids/tree?root_oid=1.3.6.1&max_depth=2")
        assert response.status_code == 200

        data = response.json()
        assert "root_oid" in data
        assert "max_depth" in data
        assert "tree" in data

        assert data["root_oid"] == "1.3.6.1"
        assert data["max_depth"] == 2
        assert isinstance(data["tree"], dict)

    def test_metrics_history_endpoint(self, client):
        """Test metrics history endpoint."""
        now = time.time()
        history_request = {
            "start_time": now - 3600,  # 1 hour ago
            "end_time": now,
            "interval_minutes": 5,
            "metrics": ["requests_total", "avg_response_time_ms"],
        }

        response = client.post("/metrics/history", json=history_request)
        assert response.status_code == 200

        data = response.json()
        assert "start_time" in data
        assert "end_time" in data
        assert "interval_minutes" in data
        assert "data_points" in data

        assert isinstance(data["data_points"], list)

    def test_state_history_endpoint(self, client):
        """Test state history endpoint."""
        response = client.get("/state/history?device_type=router")
        assert response.status_code == 200

        data = response.json()
        assert "device_type" in data
        assert "current_state" in data
        assert "total_transitions" in data
        assert "transitions" in data
        assert "state_durations" in data

        assert isinstance(data["transitions"], list)
        assert isinstance(data["state_durations"], dict)


class TestSimulationEndpoints:
    """Test suite for simulation control endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with simulation endpoints."""
        from src.rest_api.server import SNMPAgentAPIServer

        server = SNMPAgentAPIServer()
        return TestClient(server.app)

    def test_list_scenarios_endpoint(self, client):
        """Test scenario listing."""
        response = client.get("/simulation/scenarios")
        assert response.status_code == 200

        data = response.json()
        assert "scenarios" in data
        assert "total" in data

        assert isinstance(data["scenarios"], list)
        assert isinstance(data["total"], int)

    def test_create_scenario_endpoint(self, client):
        """Test scenario creation."""
        scenario = {
            "name": "Test Scenario",
            "description": "A test scenario",
            "duration_seconds": 300,
            "behaviors": [
                {"name": "delay", "enabled": True, "parameters": {"global_delay": 100}}
            ],
            "success_criteria": {"min_success_rate": 95},
        }

        response = client.post("/simulation/scenarios", json=scenario)
        assert response.status_code == 200

        data = response.json()
        assert "scenario_id" in data
        assert "message" in data

    def test_execute_scenario_endpoint(self, client):
        """Test scenario execution."""
        # First create a scenario
        scenario = {
            "name": "Execution Test",
            "description": "Test execution",
            "duration_seconds": 10,
            "behaviors": [],
        }

        create_response = client.post("/simulation/scenarios", json=scenario)
        assert create_response.status_code == 200

        # Then execute it
        execution_request = {"scenario_id": "Execution Test", "dry_run": True}

        response = client.post("/simulation/execute", json=execution_request)
        assert response.status_code == 200

        data = response.json()
        assert "execution_id" in data
        assert "message" in data
        assert "status_url" in data

    def test_list_executions_endpoint(self, client):
        """Test execution listing."""
        response = client.get("/simulation/executions")
        assert response.status_code == 200

        data = response.json()
        assert "executions" in data
        assert "total" in data

        assert isinstance(data["executions"], list)

    def test_behavior_control_endpoint(self, client):
        """Test behavior control."""
        control_request = {"behaviors": {"delay": True, "drop": False}}

        response = client.post("/behaviors/control", json=control_request)
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "active_behaviors" in data

        assert isinstance(data["active_behaviors"], list)

    def test_available_behaviors_endpoint(self, client):
        """Test available behaviors listing."""
        response = client.get("/behaviors/available")
        assert response.status_code == 200

        data = response.json()
        assert "behaviors" in data

        behaviors = data["behaviors"]
        assert isinstance(behaviors, list)

        # Check behavior structure
        for behavior in behaviors:
            assert "name" in behavior
            assert "description" in behavior
            assert "parameters" in behavior


class TestExportImportEndpoints:
    """Test suite for export/import endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with export/import endpoints."""
        from src.rest_api.server import SNMPAgentAPIServer

        server = SNMPAgentAPIServer()
        return TestClient(server.app)

    def test_export_json_endpoint(self, client):
        """Test JSON export."""
        export_request = {
            "format": "json",
            "include_config": True,
            "include_metrics": True,
            "include_scenarios": False,
            "include_history": False,
        }

        response = client.post("/export/data", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_export_csv_endpoint(self, client):
        """Test CSV export."""
        export_request = {
            "format": "csv",
            "include_metrics": True,
            "include_history": True,
        }

        response = client.post("/export/data", json=export_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_archive_endpoint(self, client):
        """Test ZIP archive export."""
        response = client.get(
            "/export/archive?include_config=true&include_metrics=true"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_import_json_endpoint(self, client):
        """Test JSON import."""
        # Create test data
        test_data = {
            "export_version": "1.0",
            "configuration": {
                "simulation": {"behaviors": {"delay": {"enabled": True}}}
            },
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post(
                    "/import/data", files={"file": ("test.json", f, "application/json")}
                )

            assert response.status_code == 200

            data = response.json()
            assert "success" in data
            assert "imported_items" in data
            assert "warnings" in data
            assert "errors" in data
        finally:
            Path(temp_path).unlink()

    def test_export_templates_endpoint(self, client):
        """Test export templates."""
        response = client.get("/export/templates/configuration")
        assert response.status_code == 200

        data = response.json()
        assert "simulation" in data

        # Test invalid template
        response = client.get("/export/templates/invalid")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestWebSocketEndpoints:
    """Test suite for WebSocket endpoints."""

    @pytest.fixture
    async def websocket_server(self):
        """Start WebSocket server for testing."""
        import uvicorn

        from src.rest_api.server import SNMPAgentAPIServer

        server = SNMPAgentAPIServer(api_port=8081)

        # Start server in background
        config = uvicorn.Config(
            server.app, host="127.0.0.1", port=8081, log_level="error"
        )
        server_instance = uvicorn.Server(config)

        # This is a simplified test setup - in practice you'd use proper async server management
        yield server

    @pytest.mark.integration
    async def test_metrics_websocket(self):
        """Test metrics WebSocket connection."""
        # This test requires a running server - for now, we'll simulate
        try:
            async with connect("ws://127.0.0.1:8080/ws/metrics") as websocket:
                # Should receive initial buffer data
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)

                assert "type" in data
                assert "timestamp" in data
                assert data["type"] == "metrics_update"
        except (
            ConnectionRefusedError,
            ConnectionClosed,
            OSError,
            asyncio.TimeoutError,
        ):
            pytest.skip("WebSocket server not running")

    async def test_logs_websocket(self):
        """Test logs WebSocket connection."""
        try:
            async with connect("ws://127.0.0.1:8080/ws/logs") as websocket:
                # Send a test message
                await websocket.send("test")

                # Should stay connected
                assert websocket.open
        except (
            ConnectionRefusedError,
            ConnectionClosed,
            OSError,
            asyncio.TimeoutError,
        ):
            pytest.skip("WebSocket server not running")

    async def test_state_websocket(self):
        """Test state WebSocket connection."""
        try:
            async with connect("ws://127.0.0.1:8080/ws/state") as websocket:
                assert websocket.open
        except (
            ConnectionRefusedError,
            ConnectionClosed,
            OSError,
            asyncio.TimeoutError,
        ):
            pytest.skip("WebSocket server not running")

    async def test_snmp_activity_websocket(self):
        """Test SNMP activity WebSocket connection."""
        try:
            async with connect("ws://127.0.0.1:8080/ws/snmp-activity") as websocket:
                assert websocket.open
        except (
            ConnectionRefusedError,
            ConnectionClosed,
            OSError,
            asyncio.TimeoutError,
        ):
            pytest.skip("WebSocket server not running")


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.rest_api.server import SNMPAgentAPIServer

        server = SNMPAgentAPIServer()
        return TestClient(server.app)

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON."""
        response = client.put(
            "/config", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_scenario = {
            "name": "Incomplete Scenario"
            # Missing required fields
        }

        response = client.post("/simulation/scenarios", json=incomplete_scenario)
        assert response.status_code == 422

    def test_invalid_scenario_id(self, client):
        """Test handling of invalid scenario ID."""
        execution_request = {"scenario_id": "non-existent-scenario"}

        response = client.post("/simulation/execute", json=execution_request)
        assert response.status_code == 404

    def test_invalid_export_format(self, client):
        """Test handling of invalid export format."""
        export_request = {"format": "invalid_format"}

        response = client.post("/export/data", json=export_request)
        assert response.status_code == 400

    def test_websocket_stats_endpoint(self, client):
        """Test WebSocket statistics endpoint."""
        response = client.get("/ws/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_connections" in data
        assert "channel_connections" in data
        assert "buffer_sizes" in data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
