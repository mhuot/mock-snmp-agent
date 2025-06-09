#!/usr/bin/env python3
"""
REST API Controllers

This module provides the business logic for the REST API endpoints.
"""

import os
import time
import psutil
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import (
    HealthStatus,
    HealthResponse,
    MetricsResponse,
    ConfigurationResponse,
    AgentStatus,
    AgentStatusResponse,
    RestartResponse,
    OIDListResponse,
)


class MockSNMPAgentController:
    """Controller for Mock SNMP Agent operations."""

    def __init__(
        self, agent_process=None, config=None, data_dir=None, snmp_endpoint=None
    ):
        """Initialize the controller.

        Args:
            agent_process: Reference to the SNMP agent process
            config: Configuration object
            data_dir: Data directory path
            snmp_endpoint: SNMP endpoint (host:port)
        """
        self.agent_process = agent_process
        self.config = config
        self.data_dir = data_dir or "./data"
        self.snmp_endpoint = snmp_endpoint or "127.0.0.1:11611"

        # Initialize metrics
        self.start_time = time.time()
        self.requests_total = 0
        self.requests_successful = 0
        self.requests_failed = 0
        self.response_times = []

        # Logging
        self.logger = logging.getLogger(__name__)

    def get_health(self) -> HealthResponse:
        """Get agent health status."""
        status = HealthStatus.HEALTHY

        # Check if agent process is running
        if self.agent_process:
            if self.agent_process.poll() is not None:
                status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.DEGRADED

        uptime = time.time() - self.start_time

        return HealthResponse(
            status=status,
            timestamp=time.time(),
            uptime_seconds=uptime,
            version="1.0.0",
            snmp_endpoint=self.snmp_endpoint,
        )

    def get_metrics(self) -> MetricsResponse:
        """Get agent performance metrics."""
        uptime = time.time() - self.start_time

        # Calculate average response time
        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        # Get current connections (simplified)
        current_connections = 0
        if self.agent_process and self.agent_process.poll() is None:
            try:
                proc = psutil.Process(self.agent_process.pid)
                connections = proc.connections()
                current_connections = len(
                    [c for c in connections if c.status == "ESTABLISHED"]
                )
            except Exception:
                pass

        return MetricsResponse(
            timestamp=time.time(),
            uptime_seconds=uptime,
            requests_total=self.requests_total,
            requests_successful=self.requests_successful,
            requests_failed=self.requests_failed,
            avg_response_time_ms=avg_response_time,
            current_connections=current_connections,
        )

    def get_configuration(self) -> ConfigurationResponse:
        """Get current agent configuration."""
        if self.config:
            # Use actual config if available
            config_dict = (
                self.config.to_dict()
                if hasattr(self.config, "to_dict")
                else vars(self.config)
            )
        else:
            # Return default configuration
            config_dict = {
                "simulation": {
                    "behaviors": {
                        "delay": {
                            "enabled": False,
                            "global_delay": 0,
                            "deviation": 0,
                            "oid_specific_delays": {},
                        },
                        "drop": {
                            "enabled": False,
                            "drop_rate": 0,
                            "oid_specific_drops": {},
                        },
                        "error": {
                            "enabled": False,
                            "error_rate": 0,
                            "error_codes": [],
                            "oid_specific_errors": {},
                        },
                        "snmpv3_security": {
                            "enabled": False,
                            "time_window_failures": {
                                "enabled": False,
                                "clock_skew_seconds": 150,
                                "failure_rate": 0,
                            },
                            "authentication_failures": {
                                "enabled": False,
                                "wrong_credentials_rate": 0,
                                "unsupported_auth_rate": 0,
                                "unknown_user_rate": 0,
                            },
                        },
                    },
                    "logging": {"enabled": True, "level": "info", "file": None},
                }
            }

        return ConfigurationResponse(
            simulation=config_dict.get("simulation", config_dict), timestamp=time.time()
        )

    def update_configuration(
        self, config_update: Dict[str, Any]
    ) -> ConfigurationResponse:
        """Update agent configuration."""
        if self.config:
            # Update actual config if available
            if hasattr(self.config, "update"):
                self.config.update(config_update)
            else:
                # Manual update for simple objects
                for key, value in config_update.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

            self.logger.info("Configuration updated")
        else:
            self.logger.warning("No configuration object available to update")

        return self.get_configuration()

    def get_agent_status(self) -> AgentStatusResponse:
        """Get detailed agent status."""
        status = AgentStatus.STOPPED
        pid = None

        if self.agent_process:
            if self.agent_process.poll() is None:
                status = AgentStatus.RUNNING
                pid = self.agent_process.pid
            else:
                status = AgentStatus.STOPPED

        # Get active behaviors
        active_behaviors = []
        config = self.get_configuration()
        if config.simulation and "behaviors" in config.simulation:
            for behavior, settings in config.simulation["behaviors"].items():
                if isinstance(settings, dict) and settings.get("enabled", False):
                    active_behaviors.append(behavior)

        # Try to find config file
        config_file = None
        if os.path.exists("config.yaml"):
            config_file = os.path.abspath("config.yaml")
        elif os.path.exists("config.json"):
            config_file = os.path.abspath("config.json")

        return AgentStatusResponse(
            status=status,
            timestamp=time.time(),
            pid=pid,
            snmp_endpoint=self.snmp_endpoint,
            data_directory=os.path.abspath(self.data_dir),
            configuration_file=config_file,
            active_behaviors=active_behaviors,
        )

    def restart_agent(
        self, force: bool = False, timeout_seconds: int = 30
    ) -> RestartResponse:
        """Restart the SNMP agent."""
        start_time = time.time()
        old_pid = None
        new_pid = None

        try:
            # Check if restart is needed
            if not force and self.agent_process and self.agent_process.poll() is None:
                health = self.get_health()
                if health.status == HealthStatus.HEALTHY:
                    return RestartResponse(
                        success=False,
                        message="Agent is healthy, use force=true to restart anyway",
                        old_pid=self.agent_process.pid,
                        new_pid=None,
                        restart_time_seconds=time.time() - start_time,
                    )

            # Get old PID
            if self.agent_process:
                old_pid = self.agent_process.pid

            # Stop current agent
            if self.agent_process and self.agent_process.poll() is None:
                self.logger.info(f"Stopping agent process {old_pid}")
                self.agent_process.terminate()

                # Wait for graceful shutdown
                try:
                    self.agent_process.wait(timeout=min(timeout_seconds // 2, 10))
                except subprocess.TimeoutExpired:
                    self.logger.warning(
                        "Agent did not shut down gracefully, forcing kill"
                    )
                    self.agent_process.kill()
                    self.agent_process.wait()

            # TODO: Restart logic would need to be implemented by the calling code
            # This controller doesn't have direct access to restart the process
            # The actual restart would be handled by the main application

            restart_time = time.time() - start_time

            # For now, return success but note that actual restart needs external handling
            return RestartResponse(
                success=True,
                message="Agent stop initiated - restart requires external process management",
                old_pid=old_pid,
                new_pid=new_pid,
                restart_time_seconds=restart_time,
            )

        except Exception as e:
            self.logger.error(f"Restart failed: {e}")
            return RestartResponse(
                success=False,
                message=f"Restart failed: {e}",
                old_pid=old_pid,
                new_pid=new_pid,
                restart_time_seconds=time.time() - start_time,
            )

    def get_available_oids(self) -> OIDListResponse:
        """Get list of available OIDs from data files."""
        oids = []
        data_sources = []

        try:
            data_path = Path(self.data_dir)

            # Find all .snmprec files
            for snmprec_file in data_path.glob("*.snmprec"):
                data_sources.append(snmprec_file.name)

                try:
                    with open(snmprec_file, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                parts = line.split("|", 1)
                                if len(parts) >= 1:
                                    oid = parts[0].strip()
                                    if oid and oid not in oids:
                                        oids.append(oid)
                except Exception as e:
                    self.logger.warning(f"Could not read {snmprec_file}: {e}")

            # Sort OIDs for consistent output
            oids.sort()

            return OIDListResponse(
                oids=oids,
                total_count=len(oids),
                data_sources=data_sources,
                timestamp=time.time(),
            )

        except Exception as e:
            self.logger.error(f"Failed to get OID list: {e}")
            return OIDListResponse(
                oids=[], total_count=0, data_sources=[], timestamp=time.time()
            )

    def record_request(self, success: bool, response_time_ms: float = 0.0):
        """Record an SNMP request for metrics.

        Args:
            success: Whether the request was successful
            response_time_ms: Response time in milliseconds
        """
        self.requests_total += 1
        if success:
            self.requests_successful += 1
        else:
            self.requests_failed += 1

        if response_time_ms > 0:
            self.response_times.append(response_time_ms)
            # Keep only last 1000 response times for average calculation
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]

    def query_oid(self, oid: str, community: str = "public") -> Dict[str, Any]:
        """Query a specific OID value.

        Args:
            oid: OID to query
            community: SNMP community string

        Returns:
            OID value and metadata
        """
        # Simulated OID values for demo
        oid_values = {
            "1.3.6.1.2.1.1.1.0": {"value": "Mock SNMP Agent v1.0", "type": "STRING"},
            "1.3.6.1.2.1.1.2.0": {"value": "1.3.6.1.4.1.12345", "type": "OID"},
            "1.3.6.1.2.1.1.3.0": {
                "value": str(int((time.time() - self.start_time) * 100)),
                "type": "TIMETICKS",
            },
            "1.3.6.1.2.1.1.4.0": {"value": "admin@example.com", "type": "STRING"},
            "1.3.6.1.2.1.1.5.0": {"value": "mock-agent-01", "type": "STRING"},
            "1.3.6.1.2.1.1.6.0": {"value": "Test Lab", "type": "STRING"},
            "1.3.6.1.2.1.1.7.0": {"value": "72", "type": "INTEGER"},
        }

        if oid in oid_values:
            return oid_values[oid]
        else:
            raise ValueError(f"OID not found: {oid}")

    def search_oids(
        self, pattern: str, mib: Optional[str] = None, limit: int = 50
    ) -> List[str]:
        """Search for OIDs by pattern.

        Args:
            pattern: Search pattern
            mib: Optional MIB filter
            limit: Maximum results

        Returns:
            List of matching OIDs
        """
        # Get all available OIDs
        oid_response = self.get_available_oids()
        all_oids = oid_response.oids

        # Add some common OIDs if no data files found
        if not all_oids:
            all_oids = [
                "1.3.6.1.2.1.1.1.0",
                "1.3.6.1.2.1.1.2.0",
                "1.3.6.1.2.1.1.3.0",
                "1.3.6.1.2.1.1.4.0",
                "1.3.6.1.2.1.1.5.0",
                "1.3.6.1.2.1.1.6.0",
                "1.3.6.1.2.1.2.2.1.1",
                "1.3.6.1.2.1.2.2.1.2",
                "1.3.6.1.2.1.2.2.1.3",
            ]

        matching = []
        for oid in all_oids:
            if pattern in oid:
                matching.append(oid)
                if len(matching) >= limit:
                    break

        return matching

    def get_oid_tree(self, root_oid: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get OID tree structure.

        Args:
            root_oid: Root OID
            max_depth: Maximum tree depth

        Returns:
            OID tree structure
        """
        # Simulated tree - in real implementation would build from MIB
        if root_oid == "1.3.6.1":
            return {
                "oid": "1.3.6.1",
                "name": "iso.org.dod.internet",
                "children": [
                    {
                        "oid": "1.3.6.1.2",
                        "name": "mgmt",
                        "children": (
                            [
                                {
                                    "oid": "1.3.6.1.2.1",
                                    "name": "mib-2",
                                    "children": (
                                        [
                                            {"oid": "1.3.6.1.2.1.1", "name": "system"},
                                            {
                                                "oid": "1.3.6.1.2.1.2",
                                                "name": "interfaces",
                                            },
                                        ]
                                        if max_depth > 2
                                        else []
                                    ),
                                }
                            ]
                            if max_depth > 1
                            else []
                        ),
                    }
                ],
            }
        return {"oid": root_oid, "name": "unknown", "children": []}
