#!/usr/bin/env python3
"""
Test suite for REST API functionality

This module tests the REST API server, controllers, and models.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from rest_api.controllers import MockSNMPAgentController

# Import modules to test
from rest_api.models import (
    AgentStatus,
    AgentStatusResponse,
    ConfigurationResponse,
    HealthResponse,
    HealthStatus,
    MetricsResponse,
    OIDListResponse,
    RestartResponse,
)
from rest_api.server import SNMPAgentAPIServer


class TestModels:
    """Test Pydantic models."""

    def test_health_response_model(self):
        """Test HealthResponse model."""
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            timestamp=1640995200.0,
            uptime_seconds=3600.0,
            version="1.0.0",
            snmp_endpoint="127.0.0.1:11611",
        )

        assert response.status == HealthStatus.HEALTHY
        assert response.timestamp == 1640995200.0
        assert response.uptime_seconds == 3600.0
        assert response.version == "1.0.0"
        assert response.snmp_endpoint == "127.0.0.1:11611"

    def test_metrics_response_model(self):
        """Test MetricsResponse model."""
        response = MetricsResponse(
            timestamp=1640995200.0,
            uptime_seconds=3600.0,
            requests_total=1000,
            requests_successful=950,
            requests_failed=50,
            avg_response_time_ms=75.5,
            current_connections=5,
        )

        assert response.requests_total == 1000
        assert response.requests_successful == 950
        assert response.requests_failed == 50
        assert response.avg_response_time_ms == 75.5

    def test_agent_status_response_model(self):
        """Test AgentStatusResponse model."""
        response = AgentStatusResponse(
            status=AgentStatus.RUNNING,
            timestamp=1640995200.0,
            pid=12345,
            snmp_endpoint="127.0.0.1:11611",
            data_directory="/app/data",
            configuration_file="/app/config.yaml",
            active_behaviors=["delay", "snmpv3_security"],
        )

        assert response.status == AgentStatus.RUNNING
        assert response.pid == 12345
        assert len(response.active_behaviors) == 2
        assert "delay" in response.active_behaviors


class TestMockSNMPAgentController:
    """Test MockSNMPAgentController class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_process = Mock()
        self.mock_config = Mock()
        self.controller = MockSNMPAgentController(
            agent_process=self.mock_process,
            config=self.mock_config,
            data_dir="/test/data",
            snmp_endpoint="127.0.0.1:11611",
        )

    def test_initialization(self):
        """Test controller initialization."""
        assert self.controller.agent_process == self.mock_process
        assert self.controller.config == self.mock_config
        assert self.controller.data_dir == "/test/data"
        assert self.controller.snmp_endpoint == "127.0.0.1:11611"

    def test_get_uptime(self):
        """Test uptime calculation."""
        # Mock start time to be 100 seconds ago
        self.controller.start_time = time.time() - 100

        uptime = self.controller.get_uptime()
        assert 99 <= uptime <= 101  # Allow small variance

    def test_get_health_running_agent(self):
        """Test health check with running agent."""
        self.mock_process.poll.return_value = None  # Process is running

        health = self.controller.get_health()

        assert health.status == HealthStatus.HEALTHY
        assert health.snmp_endpoint == "127.0.0.1:11611"
        assert health.version == "1.0.0"

    def test_get_health_stopped_agent(self):
        """Test health check with stopped agent."""
        self.mock_process.poll.return_value = 1  # Process has exited

        health = self.controller.get_health()

        assert health.status == HealthStatus.UNHEALTHY

    def test_get_health_no_agent(self):
        """Test health check with no agent process."""
        controller = MockSNMPAgentController(agent_process=None)

        health = controller.get_health()

        assert health.status == HealthStatus.DEGRADED

    def test_get_metrics(self):
        """Test metrics collection."""
        # Set up some metrics
        self.controller.requests_total = 100
        self.controller.requests_successful = 95
        self.controller.requests_failed = 5
        self.controller.response_times = [50.0, 75.0, 100.0]

        self.mock_process.pid = 12345

        with patch("psutil.Process") as mock_psutil:
            mock_process = Mock()
            mock_process.connections.return_value = [1, 2, 3]  # 3 connections
            mock_psutil.return_value = mock_process

            metrics = self.controller.get_metrics()

        assert metrics.requests_total == 100
        assert metrics.requests_successful == 95
        assert metrics.requests_failed == 5
        assert metrics.avg_response_time_ms == 75.0  # Average of [50, 75, 100]
        assert metrics.current_connections == 3

    def test_get_configuration(self):
        """Test configuration retrieval."""
        self.mock_config.config = {
            "simulation": {"behaviors": {"delay": {"enabled": True}}}
        }

        config_response = self.controller.get_configuration()

        assert "behaviors" in config_response.simulation
        assert config_response.simulation["behaviors"]["delay"]["enabled"] is True

    def test_update_configuration_success(self):
        """Test successful configuration update."""
        self.mock_config.config = {"simulation": {"behaviors": {}}}
        self.mock_config._merge_configs.return_value = {
            "behaviors": {"delay": {"enabled": True}}
        }
        self.mock_config._validate_config.return_value = None

        config_update = {"simulation": {"behaviors": {"delay": {"enabled": True}}}}

        result = self.controller.update_configuration(config_update)

        assert isinstance(result, ConfigurationResponse)
        self.mock_config._validate_config.assert_called_once()

    def test_update_configuration_invalid(self):
        """Test configuration update with invalid data."""
        self.mock_config._validate_config.side_effect = ValueError("Invalid config")

        config_update = {"simulation": {"invalid": "data"}}

        with pytest.raises(ValueError, match="Invalid config"):
            self.controller.update_configuration(config_update)

    def test_get_agent_status_running(self):
        """Test agent status when running."""
        self.mock_process.poll.return_value = None
        self.mock_process.pid = 12345

        self.mock_config.config = {
            "simulation": {
                "behaviors": {
                    "delay": {"enabled": True},
                    "snmpv3_security": {"enabled": False},
                }
            }
        }

        status = self.controller.get_agent_status()

        assert status.status == AgentStatus.RUNNING
        assert status.pid == 12345
        assert "delay" in status.active_behaviors
        assert "snmpv3_security" not in status.active_behaviors

    def test_get_agent_status_stopped(self):
        """Test agent status when stopped."""
        self.mock_process.poll.return_value = 1

        status = self.controller.get_agent_status()

        assert status.status == AgentStatus.STOPPED
        assert status.pid is None

    def test_restart_agent_healthy_no_force(self):
        """Test restart when agent is healthy and force=False."""
        self.mock_process.poll.return_value = None
        self.mock_process.pid = 12345

        result = self.controller.restart_agent(force=False)

        assert result.success is False
        assert "healthy" in result.message
        assert result.old_pid == 12345

    def test_restart_agent_force(self):
        """Test forced restart."""
        self.mock_process.poll.return_value = None
        self.mock_process.pid = 12345
        self.mock_process.terminate.return_value = None
        self.mock_process.wait.return_value = None

        result = self.controller.restart_agent(force=True)

        assert result.success is True
        assert result.old_pid == 12345
        self.mock_process.terminate.assert_called_once()

    def test_get_available_oids(self):
        """Test OID list generation."""
        # Create temporary test data
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.snmprec"
            test_file.write_text(
                """# Test SNMP data
1.3.6.1.2.1.1.1.0|4|Test System
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10
1.3.6.1.2.1.1.3.0|67|12345
"""
            )

            controller = MockSNMPAgentController(data_dir=temp_dir)
            oids_response = controller.get_available_oids()

        assert oids_response.total_count == 3
        assert "1.3.6.1.2.1.1.1.0" in oids_response.oids
        assert "1.3.6.1.2.1.1.2.0" in oids_response.oids
        assert "1.3.6.1.2.1.1.3.0" in oids_response.oids
        assert "test.snmprec" in oids_response.data_sources

    def test_record_request_success(self):
        """Test successful request recording."""
        initial_total = self.controller.requests_total
        initial_successful = self.controller.requests_successful

        self.controller.record_request(success=True, response_time_ms=50.0)

        assert self.controller.requests_total == initial_total + 1
        assert self.controller.requests_successful == initial_successful + 1
        assert 50.0 in self.controller.response_times

    def test_record_request_failure(self):
        """Test failed request recording."""
        initial_total = self.controller.requests_total
        initial_failed = self.controller.requests_failed

        self.controller.record_request(success=False, response_time_ms=0.0)

        assert self.controller.requests_total == initial_total + 1
        assert self.controller.requests_failed == initial_failed + 1


class TestSNMPAgentAPIServer:
    """Test SNMPAgentAPIServer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_process = Mock()
        self.mock_config = Mock()

    def test_server_initialization(self):
        """Test API server initialization."""
        server = SNMPAgentAPIServer(
            agent_process=self.mock_process,
            config=self.mock_config,
            data_dir="/test/data",
            snmp_endpoint="127.0.0.1:11611",
            api_host="0.0.0.0",
            api_port=8080,
        )

        assert server.agent_process == self.mock_process
        assert server.config == self.mock_config
        assert server.api_host == "0.0.0.0"
        assert server.api_port == 8080
        assert server.app is not None

    def test_server_cors_disabled(self):
        """Test server with CORS disabled."""
        server = SNMPAgentAPIServer(cors_enabled=False)

        # CORS middleware should not be added
        middleware_types = [
            type(middleware) for middleware in server.app.user_middleware
        ]
        assert not any(
            "CORS" in str(middleware_type) for middleware_type in middleware_types
        )

    def test_update_agent_reference(self):
        """Test updating agent process reference."""
        server = SNMPAgentAPIServer()
        new_process = Mock()

        server.update_agent_reference(new_process)

        assert server.agent_process == new_process
        assert server.controller.agent_process == new_process

    def test_update_config_reference(self):
        """Test updating configuration reference."""
        server = SNMPAgentAPIServer()
        new_config = Mock()

        server.update_config_reference(new_config)

        assert server.config == new_config
        assert server.controller.config == new_config


class TestIntegration:
    """Integration tests for REST API components."""

    def test_full_api_flow(self):
        """Test complete API workflow."""
        # Create mock objects
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345

        mock_config = Mock()
        mock_config.config = {
            "simulation": {
                "behaviors": {
                    "delay": {"enabled": True},
                    "snmpv3_security": {"enabled": False},
                }
            }
        }
        mock_config._merge_configs.return_value = mock_config.config["simulation"]
        mock_config._validate_config.return_value = None

        # Create controller
        controller = MockSNMPAgentController(
            agent_process=mock_process, config=mock_config, data_dir="/test/data"
        )

        # Test health check
        health = controller.get_health()
        assert health.status == HealthStatus.HEALTHY

        # Test metrics
        metrics = controller.get_metrics()
        assert metrics.requests_total == 0

        # Test configuration
        config_response = controller.get_configuration()
        assert "behaviors" in config_response.simulation

        # Test configuration update
        config_update = {"simulation": {"behaviors": {"delay": {"enabled": False}}}}
        updated_config = controller.update_configuration(config_update)
        assert isinstance(updated_config, ConfigurationResponse)

        # Test agent status
        status = controller.get_agent_status()
        assert status.status == AgentStatus.RUNNING
        assert status.pid == 12345

    def test_api_server_creation(self):
        """Test API server creation function."""
        from src.rest_api.server import create_api_server

        server = create_api_server(
            api_host="127.0.0.1", api_port=8081, cors_enabled=True
        )

        assert isinstance(server, SNMPAgentAPIServer)
        assert server.api_host == "127.0.0.1"
        assert server.api_port == 8081


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
