#!/usr/bin/env python3
"""
Simulation Control Endpoints

This module provides endpoints for creating, managing, and executing
test scenarios for SNMP simulation.
"""

import asyncio
import json
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, Field


class ScenarioStatus(str, Enum):
    """Test scenario status."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BehaviorConfig(BaseModel):
    """Individual behavior configuration."""

    name: str = Field(..., description="Behavior name")
    enabled: bool = Field(True, description="Whether behavior is enabled")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Behavior parameters"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "delay",
                "enabled": True,
                "parameters": {"global_delay": 100, "deviation": 50},
            }
        }


class TestScenario(BaseModel):
    """Test scenario definition."""

    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    duration_seconds: int = Field(300, description="Scenario duration in seconds")
    behaviors: List[BehaviorConfig] = Field(..., description="Behaviors to enable")
    state_machine_config: Optional[Dict[str, Any]] = Field(
        None, description="State machine configuration"
    )
    success_criteria: Dict[str, Any] = Field(
        default_factory=dict, description="Success criteria"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "High Load Test",
                "description": "Test agent under high load with delays",
                "duration_seconds": 300,
                "behaviors": [
                    {
                        "name": "delay",
                        "enabled": True,
                        "parameters": {"global_delay": 200},
                    }
                ],
                "success_criteria": {
                    "max_response_time_ms": 500,
                    "min_success_rate": 95,
                },
            }
        }


class ScenarioExecution(BaseModel):
    """Scenario execution details."""

    id: str = Field(..., description="Execution ID")
    scenario_id: str = Field(..., description="Scenario ID")
    status: ScenarioStatus = Field(..., description="Execution status")
    started_at: Optional[float] = Field(None, description="Start timestamp")
    completed_at: Optional[float] = Field(None, description="Completion timestamp")
    progress_percent: float = Field(0.0, description="Execution progress")
    results: Dict[str, Any] = Field(
        default_factory=dict, description="Execution results"
    )
    logs: List[str] = Field(default_factory=list, description="Execution logs")


class ScenarioExecutionRequest(BaseModel):
    """Request to execute a scenario."""

    scenario_id: str = Field(..., description="Scenario ID to execute")
    override_duration: Optional[int] = Field(
        None, description="Override scenario duration"
    )
    dry_run: bool = Field(False, description="Perform dry run without applying changes")


class BehaviorToggleRequest(BaseModel):
    """Request to toggle behaviors."""

    behaviors: Dict[str, bool] = Field(..., description="Behaviors to enable/disable")

    class Config:
        schema_extra = {
            "example": {
                "behaviors": {"delay": True, "drop": False, "snmpv3_security": True}
            }
        }


class SimulationScenarioManager:
    """Manages test scenarios and executions."""

    def __init__(self, controller, data_dir: str = "./data/scenarios"):
        """Initialize scenario manager.

        Args:
            controller: Agent controller instance
            data_dir: Directory for storing scenarios
        """
        self.controller = controller
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.scenarios: Dict[str, TestScenario] = {}
        self.executions: Dict[str, ScenarioExecution] = {}
        self.running_executions: Dict[str, asyncio.Task] = {}

        # Load saved scenarios
        self._load_scenarios()

        # Load predefined scenarios
        self._load_predefined_scenarios()

    def _load_scenarios(self):
        """Load saved scenarios from disk."""
        scenarios_file = self.data_dir / "scenarios.json"
        if scenarios_file.exists():
            try:
                with open(scenarios_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for scenario_data in data:
                        scenario = TestScenario(**scenario_data)
                        self.scenarios[scenario.name] = scenario
            except Exception:
                pass

    def _save_scenarios(self):
        """Save scenarios to disk."""
        scenarios_file = self.data_dir / "scenarios.json"
        try:
            data = [scenario.dict() for scenario in self.scenarios.values()]
            with open(scenarios_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_predefined_scenarios(self):
        """Load predefined test scenarios."""
        predefined = [
            TestScenario(
                name="Basic Connectivity Test",
                description="Simple test to verify agent responds to basic queries",
                duration_seconds=60,
                behaviors=[],
                success_criteria={"min_success_rate": 100, "max_response_time_ms": 100},
            ),
            TestScenario(
                name="High Latency Simulation",
                description="Simulate network with high latency",
                duration_seconds=300,
                behaviors=[
                    BehaviorConfig(
                        name="delay",
                        enabled=True,
                        parameters={"global_delay": 500, "deviation": 200},
                    )
                ],
                success_criteria={"max_response_time_ms": 1000, "min_success_rate": 90},
            ),
            TestScenario(
                name="SNMPv3 Security Stress Test",
                description="Test SNMPv3 with various security failures",
                duration_seconds=600,
                behaviors=[
                    BehaviorConfig(
                        name="snmpv3_security",
                        enabled=True,
                        parameters={
                            "auth_failure_rate": 20,
                            "time_window_failure_rate": 15,
                        },
                    )
                ],
                success_criteria={
                    "min_success_rate": 60,
                    "security_failures_detected": True,
                },
            ),
            TestScenario(
                name="Device Lifecycle Test",
                description="Test device state transitions",
                duration_seconds=900,
                behaviors=[],
                state_machine_config={
                    "device_type": "router",
                    "initial_state": "booting",
                    "auto_transitions": True,
                    "transition_delays": {"min": 30, "max": 120},
                },
                success_criteria={
                    "state_transitions_occurred": True,
                    "min_uptime_percent": 70,
                },
            ),
            TestScenario(
                name="Combined Stress Test",
                description="All features enabled for comprehensive testing",
                duration_seconds=1200,
                behaviors=[
                    BehaviorConfig(
                        name="delay", enabled=True, parameters={"global_delay": 100}
                    ),
                    BehaviorConfig(
                        name="drop", enabled=True, parameters={"drop_rate": 5}
                    ),
                    BehaviorConfig(
                        name="snmpv3_security",
                        enabled=True,
                        parameters={"auth_failure_rate": 10},
                    ),
                ],
                state_machine_config={
                    "device_type": "switch",
                    "auto_transitions": True,
                },
                success_criteria={"min_success_rate": 75, "max_response_time_ms": 500},
            ),
        ]

        for scenario in predefined:
            if scenario.name not in self.scenarios:
                self.scenarios[scenario.name] = scenario

    def create_scenario(self, scenario: TestScenario) -> str:
        """Create a new test scenario.

        Args:
            scenario: Test scenario definition

        Returns:
            Scenario ID
        """
        scenario_id = str(uuid.uuid4())
        self.scenarios[scenario_id] = scenario
        self._save_scenarios()
        return scenario_id

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available scenarios.

        Returns:
            List of scenario summaries
        """
        return [
            {
                "id": sid,
                "name": scenario.name,
                "description": scenario.description,
                "duration_seconds": scenario.duration_seconds,
                "behaviors": len(scenario.behaviors),
                "has_state_machine": scenario.state_machine_config is not None,
            }
            for sid, scenario in self.scenarios.items()
        ]

    def get_scenario(self, scenario_id: str) -> TestScenario:
        """Get a specific scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            Test scenario
        """
        if scenario_id not in self.scenarios:
            # Try by name
            for scenario in self.scenarios.values():
                if scenario.name == scenario_id:
                    return scenario
            raise ValueError(f"Scenario not found: {scenario_id}")
        return self.scenarios[scenario_id]

    async def execute_scenario(
        self,
        scenario_id: str,
        override_duration: Optional[int] = None,
        dry_run: bool = False,
    ) -> str:
        """Execute a test scenario.

        Args:
            scenario_id: Scenario ID to execute
            override_duration: Override scenario duration
            dry_run: Perform dry run

        Returns:
            Execution ID
        """
        scenario = self.get_scenario(scenario_id)
        execution_id = str(uuid.uuid4())

        execution = ScenarioExecution(
            id=execution_id,
            scenario_id=scenario_id,
            status=ScenarioStatus.CREATED,
            results={},
        )
        self.executions[execution_id] = execution

        if not dry_run:
            # Start execution task
            task = asyncio.create_task(
                self._run_scenario(execution_id, scenario, override_duration)
            )
            self.running_executions[execution_id] = task
        else:
            # Dry run - just validate
            execution.status = ScenarioStatus.COMPLETED
            execution.results = {
                "dry_run": True,
                "validation": "Scenario validated successfully",
            }

        return execution_id

    async def _run_scenario(
        self,
        execution_id: str,
        scenario: TestScenario,
        override_duration: Optional[int] = None,
    ):
        """Run a scenario execution.

        Args:
            execution_id: Execution ID
            scenario: Test scenario
            override_duration: Override duration
        """
        execution = self.executions[execution_id]
        duration = override_duration or scenario.duration_seconds

        try:
            execution.status = ScenarioStatus.RUNNING
            execution.started_at = time.time()
            execution.logs.append(f"Starting scenario: {scenario.name}")

            # Save original configuration
            original_config = self.controller.get_configuration()

            # Apply scenario configuration
            await self._apply_scenario_config(scenario, execution)

            # Monitor execution
            start_time = time.time()
            metrics_samples = []

            while time.time() - start_time < duration:
                # Update progress
                elapsed = time.time() - start_time
                execution.progress_percent = (elapsed / duration) * 100

                # Collect metrics
                metrics = self.controller.get_metrics()
                metrics_samples.append(metrics.dict())

                # Check if cancelled
                if execution.status == ScenarioStatus.CANCELLED:
                    break

                # Check if we have time left for another sample
                if time.time() - start_time + 5 >= duration:
                    break  # Don't sleep if we're near the end

                await asyncio.sleep(5)  # Sample every 5 seconds

            # Restore original configuration
            self.controller.update_configuration(original_config)

            # Analyze results
            execution.results = self._analyze_results(scenario, metrics_samples)
            execution.status = ScenarioStatus.COMPLETED
            execution.completed_at = time.time()
            execution.logs.append("Scenario completed successfully")

        except Exception as e:
            execution.status = ScenarioStatus.FAILED
            execution.completed_at = time.time()
            execution.logs.append(f"Scenario failed: {str(e)}")
            execution.results["error"] = str(e)

        finally:
            # Clean up
            self.running_executions.pop(execution_id, None)

    async def _apply_scenario_config(
        self, scenario: TestScenario, execution: ScenarioExecution
    ):
        """Apply scenario configuration.

        Args:
            scenario: Test scenario
            execution: Scenario execution
        """
        config_update = {"simulation": {"behaviors": {}}}

        # Apply behaviors
        for behavior in scenario.behaviors:
            if behavior.enabled:
                config_update["simulation"]["behaviors"][behavior.name] = {
                    "enabled": True,
                    **behavior.parameters,
                }
                execution.logs.append(f"Enabled behavior: {behavior.name}")

        # Apply state machine config
        if scenario.state_machine_config:
            config_update["simulation"]["state_machine"] = {
                "enabled": True,
                **scenario.state_machine_config,
            }
            execution.logs.append("Configured state machine")

        # Update configuration
        self.controller.update_configuration(config_update)

    def _analyze_results(
        self, scenario: TestScenario, metrics_samples: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze scenario execution results.

        Args:
            scenario: Test scenario
            metrics_samples: Collected metrics samples

        Returns:
            Analysis results
        """
        if not metrics_samples:
            return {"error": "No metrics collected"}

        # Calculate statistics
        total_requests = metrics_samples[-1].get("requests_total", 0) - metrics_samples[
            0
        ].get("requests_total", 0)
        successful_requests = metrics_samples[-1].get(
            "requests_successful", 0
        ) - metrics_samples[0].get("requests_successful", 0)

        success_rate = (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0
        )

        response_times = [m.get("avg_response_time_ms", 0) for m in metrics_samples]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        max_response_time = max(response_times) if response_times else 0

        # Check success criteria
        criteria_results = {}
        for criterion, expected in scenario.success_criteria.items():
            if criterion == "min_success_rate":
                criteria_results[criterion] = {
                    "expected": expected,
                    "actual": success_rate,
                    "passed": success_rate >= expected,
                }
            elif criterion == "max_response_time_ms":
                criteria_results[criterion] = {
                    "expected": expected,
                    "actual": max_response_time,
                    "passed": max_response_time <= expected,
                }

        overall_success = all(
            r["passed"] for r in criteria_results.values() if "passed" in r
        )

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "criteria_results": criteria_results,
            "overall_success": overall_success,
            "samples_collected": len(metrics_samples),
        }

    def cancel_execution(self, execution_id: str):
        """Cancel a running execution.

        Args:
            execution_id: Execution ID to cancel
        """
        if execution_id in self.executions:
            self.executions[execution_id].status = ScenarioStatus.CANCELLED

        if execution_id in self.running_executions:
            self.running_executions[execution_id].cancel()


def setup_simulation_endpoints(app, controller):
    """Setup simulation control endpoints on the FastAPI app.

    Args:
        app: FastAPI application instance
        controller: Agent controller instance
    """
    manager = SimulationScenarioManager(controller)

    @app.get("/simulation/scenarios", tags=["Simulation"])
    async def list_scenarios():
        """List all available test scenarios."""
        return {"scenarios": manager.list_scenarios(), "total": len(manager.scenarios)}

    @app.post("/simulation/scenarios", tags=["Simulation"])
    async def create_scenario(scenario: TestScenario):
        """Create a new test scenario."""
        scenario_id = manager.create_scenario(scenario)
        return {"scenario_id": scenario_id, "message": "Scenario created successfully"}

    @app.get("/simulation/scenarios/{scenario_id}", tags=["Simulation"])
    async def get_scenario(scenario_id: str):
        """Get a specific test scenario."""
        try:
            scenario = manager.get_scenario(scenario_id)
            return scenario
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/simulation/execute", tags=["Simulation"])
    async def execute_scenario(
        request: ScenarioExecutionRequest, background_tasks: BackgroundTasks
    ):
        """Execute a test scenario."""
        try:
            execution_id = await manager.execute_scenario(
                scenario_id=request.scenario_id,
                override_duration=request.override_duration,
                dry_run=request.dry_run,
            )

            return {
                "execution_id": execution_id,
                "message": "Scenario execution started",
                "status_url": f"/simulation/executions/{execution_id}",
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.get("/simulation/executions", tags=["Simulation"])
    async def list_executions(status: Optional[ScenarioStatus] = None, limit: int = 50):
        """List scenario executions."""
        executions = list(manager.executions.values())

        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by start time, most recent first
        executions.sort(key=lambda x: x.started_at or 0, reverse=True)

        return {
            "executions": [e.dict() for e in executions[:limit]],
            "total": len(executions),
        }

    @app.get("/simulation/executions/{execution_id}", tags=["Simulation"])
    async def get_execution(execution_id: str):
        """Get execution status and results."""
        if execution_id not in manager.executions:
            raise HTTPException(status_code=404, detail="Execution not found")

        return manager.executions[execution_id]

    @app.post("/simulation/executions/{execution_id}/cancel", tags=["Simulation"])
    async def cancel_execution(execution_id: str):
        """Cancel a running execution."""
        if execution_id not in manager.executions:
            raise HTTPException(status_code=404, detail="Execution not found")

        manager.cancel_execution(execution_id)

        return {"execution_id": execution_id, "message": "Execution cancelled"}

    @app.post("/behaviors/control", tags=["Simulation"])
    async def control_behaviors(request: BehaviorToggleRequest):
        """Enable or disable specific behaviors."""
        config = controller.get_configuration()

        for behavior, enabled in request.behaviors.items():
            if behavior in config.simulation.get("behaviors", {}):
                config.simulation["behaviors"][behavior]["enabled"] = enabled

        controller.update_configuration(config.dict())

        return {
            "message": "Behaviors updated",
            "active_behaviors": [
                name
                for name, cfg in config.simulation.get("behaviors", {}).items()
                if cfg.get("enabled", False)
            ],
        }

    @app.get("/behaviors/available", tags=["Simulation"])
    async def get_available_behaviors():
        """Get list of available simulation behaviors."""
        # In real implementation, would discover from behavior modules
        return {
            "behaviors": [
                {
                    "name": "delay",
                    "description": "Add response delays",
                    "parameters": ["global_delay", "deviation", "oid_specific_delays"],
                },
                {
                    "name": "drop",
                    "description": "Drop requests randomly",
                    "parameters": ["drop_rate", "oid_specific_drops"],
                },
                {
                    "name": "snmpv3_security",
                    "description": "SNMPv3 security failure simulation",
                    "parameters": [
                        "auth_failure_rate",
                        "time_window_failure_rate",
                        "privacy_failure_rate",
                    ],
                },
                {
                    "name": "counter_wrap",
                    "description": "Counter wrapping simulation",
                    "parameters": ["wrap_at", "counter_oids"],
                },
                {
                    "name": "bulk_operations",
                    "description": "Bulk operation behaviors",
                    "parameters": ["max_repetitions", "truncate_responses"],
                },
            ]
        }

    # Make manager available to other components
    app.state.scenario_manager = manager

    return manager
