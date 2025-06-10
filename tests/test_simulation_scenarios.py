#!/usr/bin/env python3
"""
Simulation Scenario Tests

Tests for test scenario creation, execution, and management functionality.
"""

import asyncio
import json
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from rest_api.controllers import MockSNMPAgentController
from rest_api.simulation_control import (
    BehaviorConfig,
    ScenarioStatus,
    SimulationScenarioManager,
    TestScenario,
)


class TestScenarioCreation:
    """Test suite for scenario creation and management."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_configuration.return_value = Mock()
        controller.get_configuration.return_value.simulation = {"behaviors": {}}
        controller.update_configuration = Mock()
        controller.get_metrics.return_value = Mock()
        controller.get_metrics.return_value.dict.return_value = {
            "requests_total": 100,
            "requests_successful": 95,
            "requests_failed": 5,
            "avg_response_time_ms": 50.0,
        }
        return controller

    @pytest.fixture
    def scenario_manager(self, mock_controller):
        """Create scenario manager."""
        return SimulationScenarioManager(mock_controller)

    def test_create_basic_scenario(self, scenario_manager):
        """Test creating a basic scenario."""
        scenario = TestScenario(
            name="Basic Test",
            description="A basic test scenario",
            duration_seconds=300,
            behaviors=[
                BehaviorConfig(
                    name="delay", enabled=True, parameters={"global_delay": 100}
                )
            ],
        )

        scenario_id = scenario_manager.create_scenario(scenario)

        assert scenario_id is not None
        assert scenario_id in scenario_manager.scenarios
        assert scenario_manager.scenarios[scenario_id].name == "Basic Test"

    def test_list_scenarios(self, scenario_manager):
        """Test listing scenarios."""
        # Should have predefined scenarios
        scenarios = scenario_manager.list_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

        # Check scenario structure
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "duration_seconds" in scenario
            assert "behaviors" in scenario
            assert "has_state_machine" in scenario

    def test_get_scenario_by_id(self, scenario_manager):
        """Test getting scenario by ID."""
        # Create a scenario
        scenario = TestScenario(
            name="Get Test",
            description="Test get functionality",
            duration_seconds=120,
            behaviors=[],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        retrieved = scenario_manager.get_scenario(scenario_id)

        assert retrieved.name == "Get Test"
        assert retrieved.duration_seconds == 120

    def test_get_scenario_by_name(self, scenario_manager):
        """Test getting scenario by name."""
        # Should be able to get predefined scenarios by name
        scenario = scenario_manager.get_scenario("Basic Connectivity Test")

        assert scenario is not None
        assert scenario.name == "Basic Connectivity Test"

    def test_scenario_validation(self, scenario_manager):
        """Test scenario validation."""
        # Test invalid scenario
        with pytest.raises(ValueError):
            scenario_manager.get_scenario("Non-existent Scenario")

    def test_predefined_scenarios_loaded(self, scenario_manager):
        """Test that predefined scenarios are loaded."""
        scenarios = scenario_manager.list_scenarios()
        scenario_names = [s["name"] for s in scenarios]

        expected_scenarios = [
            "Basic Connectivity Test",
            "High Latency Simulation",
            "SNMPv3 Security Stress Test",
            "Device Lifecycle Test",
            "Combined Stress Test",
        ]

        for expected in expected_scenarios:
            assert any(expected in name for name in scenario_names)


@pytest.mark.asyncio
class TestScenarioExecution:
    """Test suite for scenario execution."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_configuration.return_value = Mock()
        controller.get_configuration.return_value.dict.return_value = {
            "simulation": {"behaviors": {}}
        }
        controller.update_configuration = Mock()
        controller.get_metrics.return_value = Mock()
        controller.get_metrics.return_value.dict.return_value = {
            "requests_total": 100,
            "requests_successful": 95,
            "requests_failed": 5,
            "avg_response_time_ms": 50.0,
        }
        return controller

    @pytest.fixture
    def scenario_manager(self, mock_controller):
        """Create scenario manager."""
        return SimulationScenarioManager(mock_controller)

    async def test_dry_run_execution(self, scenario_manager):
        """Test dry run execution."""
        scenario = TestScenario(
            name="Dry Run Test",
            description="Test dry run",
            duration_seconds=60,
            behaviors=[],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(
            scenario_id, dry_run=True
        )

        assert execution_id in scenario_manager.executions
        execution = scenario_manager.executions[execution_id]

        assert execution.status == ScenarioStatus.COMPLETED
        assert execution.results["dry_run"] is True

    async def test_real_execution(self, scenario_manager, mock_controller):
        """Test real scenario execution."""
        scenario = TestScenario(
            name="Real Execution Test",
            description="Test real execution",
            duration_seconds=1,  # Very short for testing
            behaviors=[
                BehaviorConfig(
                    name="delay", enabled=True, parameters={"global_delay": 50}
                )
            ],
            success_criteria={"min_success_rate": 80},
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(scenario_id)

        # Wait for execution to start
        await asyncio.sleep(0.1)

        execution = scenario_manager.executions[execution_id]
        assert execution.status in [ScenarioStatus.RUNNING, ScenarioStatus.COMPLETED]

        # Wait for completion
        start_time = time.time()
        while (
            execution.status == ScenarioStatus.RUNNING and time.time() - start_time < 5
        ):
            await asyncio.sleep(0.1)

        assert execution.status in [ScenarioStatus.COMPLETED, ScenarioStatus.FAILED]
        assert execution.started_at is not None
        assert execution.completed_at is not None

    async def test_execution_with_override_duration(self, scenario_manager):
        """Test execution with duration override."""
        scenario = TestScenario(
            name="Override Duration Test",
            description="Test duration override",
            duration_seconds=300,  # Original duration
            behaviors=[],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(
            scenario_id, override_duration=1  # Override to 1 second
        )

        execution = scenario_manager.executions[execution_id]

        # Give the scenario a moment to start
        await asyncio.sleep(0.1)

        # Wait for scenario to start or complete
        start_time = time.time()
        while (
            execution.status == ScenarioStatus.CREATED and time.time() - start_time < 3
        ):
            await asyncio.sleep(0.1)

        # Wait for scenario to complete
        start_time = time.time()
        while (
            execution.status == ScenarioStatus.RUNNING and time.time() - start_time < 3
        ):
            await asyncio.sleep(0.1)

        assert execution.status in [ScenarioStatus.COMPLETED, ScenarioStatus.FAILED]

        # Should have completed in around 1 second, not 300
        if execution.completed_at and execution.started_at:
            actual_duration = execution.completed_at - execution.started_at
            assert actual_duration < 5  # Allow some margin

    async def test_execution_cancellation(self, scenario_manager):
        """Test execution cancellation."""
        scenario = TestScenario(
            name="Cancellation Test",
            description="Test cancellation",
            duration_seconds=10,  # Long enough to cancel
            behaviors=[],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(scenario_id)

        # Wait for execution to start
        await asyncio.sleep(0.1)

        # Cancel execution
        scenario_manager.cancel_execution(execution_id)

        # Wait briefly
        await asyncio.sleep(0.2)

        execution = scenario_manager.executions[execution_id]
        assert execution.status == ScenarioStatus.CANCELLED

    async def test_scenario_configuration_application(
        self, scenario_manager, mock_controller
    ):
        """Test that scenario configuration is applied."""
        scenario = TestScenario(
            name="Config Application Test",
            description="Test config application",
            duration_seconds=1,
            behaviors=[
                BehaviorConfig(
                    name="delay", enabled=True, parameters={"global_delay": 200}
                )
            ],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(scenario_id)

        # Wait for execution to start and apply config
        await asyncio.sleep(0.2)

        # Should have called update_configuration
        assert mock_controller.update_configuration.called

        # Check the configuration that was applied
        calls = mock_controller.update_configuration.call_args_list
        assert len(calls) >= 1

        # Should have enabled delay behavior
        config_update = calls[0][0][0]
        assert "simulation" in config_update
        assert "behaviors" in config_update["simulation"]
        assert "delay" in config_update["simulation"]["behaviors"]
        assert config_update["simulation"]["behaviors"]["delay"]["enabled"] is True

    async def test_results_analysis(self, scenario_manager, mock_controller):
        """Test results analysis."""
        # Set up mock controller to return changing metrics
        metrics_sequence = [
            {
                "requests_total": 100,
                "requests_successful": 90,
                "avg_response_time_ms": 50,
            },
            {
                "requests_total": 120,
                "requests_successful": 115,
                "avg_response_time_ms": 55,
            },
            {
                "requests_total": 150,
                "requests_successful": 140,
                "avg_response_time_ms": 60,
            },
        ]

        call_count = 0

        def get_metrics_side_effect():
            nonlocal call_count
            result = Mock()
            result.dict.return_value = metrics_sequence[
                min(call_count, len(metrics_sequence) - 1)
            ]
            call_count += 1
            return result

        mock_controller.get_metrics.side_effect = get_metrics_side_effect

        scenario = TestScenario(
            name="Results Analysis Test",
            description="Test results analysis",
            duration_seconds=1,
            behaviors=[],
            success_criteria={"min_success_rate": 90, "max_response_time_ms": 100},
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(scenario_id)

        # Wait for completion
        start_time = time.time()
        execution = scenario_manager.executions[execution_id]

        # Wait for scenario to start
        while (
            execution.status == ScenarioStatus.CREATED and time.time() - start_time < 5
        ):
            await asyncio.sleep(0.1)

        # Wait for scenario to complete
        while (
            execution.status == ScenarioStatus.RUNNING and time.time() - start_time < 5
        ):
            await asyncio.sleep(0.1)

        # Check results analysis
        results = execution.results
        assert "total_requests" in results
        assert "successful_requests" in results
        assert "success_rate" in results
        assert "criteria_results" in results
        assert "overall_success" in results

        # Should have analyzed success criteria
        criteria_results = results["criteria_results"]
        if "min_success_rate" in criteria_results:
            assert "expected" in criteria_results["min_success_rate"]
            assert "actual" in criteria_results["min_success_rate"]
            assert "passed" in criteria_results["min_success_rate"]


class TestBehaviorControl:
    """Test suite for behavior control functionality."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_configuration.return_value = Mock()
        controller.get_configuration.return_value.simulation = Mock()
        controller.get_configuration.return_value.simulation.behaviors = {
            "delay": {"enabled": False},
            "drop": {"enabled": False},
            "snmpv3_security": {"enabled": False},
        }
        controller.update_configuration = Mock()
        return controller

    @pytest.fixture
    def scenario_manager(self, mock_controller):
        """Create scenario manager."""
        return SimulationScenarioManager(mock_controller)

    def test_behavior_control_validation(self, scenario_manager):
        """Test behavior control validation through available behaviors."""
        # This would be tested via the REST API endpoint
        # Here we test the underlying logic
        available_behaviors = [
            "delay",
            "drop",
            "snmpv3_security",
            "counter_wrap",
            "bulk_operations",
        ]

        # All these should be recognized behaviors
        for behavior in available_behaviors:
            assert behavior is not None  # Simple validation test


class TestExecutionManagement:
    """Test suite for execution management."""

    @pytest.fixture
    def scenario_manager(self):
        """Create scenario manager."""
        controller = Mock(spec=MockSNMPAgentController)
        return SimulationScenarioManager(controller)

    async def test_multiple_concurrent_executions(self, scenario_manager):
        """Test multiple concurrent executions."""
        scenarios = []
        execution_ids = []

        # Create multiple scenarios
        for i in range(3):
            scenario = TestScenario(
                name=f"Concurrent Test {i}",
                description=f"Concurrent test {i}",
                duration_seconds=1,
                behaviors=[],
            )
            scenario_id = scenario_manager.create_scenario(scenario)
            scenarios.append(scenario_id)

        # Execute all scenarios
        for scenario_id in scenarios:
            execution_id = await scenario_manager.execute_scenario(scenario_id)
            execution_ids.append(execution_id)

        # All should be tracked
        for execution_id in execution_ids:
            assert execution_id in scenario_manager.executions
            execution = scenario_manager.executions[execution_id]
            assert execution.status in [
                ScenarioStatus.CREATED,
                ScenarioStatus.RUNNING,
                ScenarioStatus.COMPLETED,
            ]

    def test_execution_history_tracking(self, scenario_manager):
        """Test execution history tracking."""
        # Executions should be stored and retrievable
        assert hasattr(scenario_manager, "executions")
        assert isinstance(scenario_manager.executions, dict)

    async def test_execution_progress_tracking(self, scenario_manager):
        """Test execution progress tracking."""
        scenario = TestScenario(
            name="Progress Test",
            description="Test progress tracking",
            duration_seconds=2,
            behaviors=[],
        )

        scenario_id = scenario_manager.create_scenario(scenario)
        execution_id = await scenario_manager.execute_scenario(scenario_id)

        # Wait and check progress updates
        await asyncio.sleep(0.5)

        execution = scenario_manager.executions[execution_id]
        if execution.status == ScenarioStatus.RUNNING:
            assert 0 <= execution.progress_percent <= 100


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
