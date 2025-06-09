#!/usr/bin/env python3
"""
REST API Controllers

Business logic for API endpoints.
"""

import time
import os
import psutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import (
    HealthStatus, AgentStatus, HealthResponse, MetricsResponse,
    ConfigurationResponse, AgentStatusResponse, RestartResponse,
    ErrorResponse, OIDListResponse
)


class MockSNMPAgentController:
    """Controller for Mock SNMP Agent REST API operations."""
    
    def __init__(self, agent_process=None, config=None, data_dir=None, snmp_endpoint=None):
        """Initialize the controller.
        
        Args:
            agent_process: Reference to the SNMP agent process
            config: Current configuration object
            data_dir: Data directory path
            snmp_endpoint: SNMP endpoint (host:port)
        """
        self.agent_process = agent_process
        self.config = config
        self.data_dir = data_dir or "."
        self.snmp_endpoint = snmp_endpoint or "127.0.0.1:11611"
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        
        # Metrics tracking
        self.requests_total = 0
        self.requests_successful = 0
        self.requests_failed = 0
        self.response_times = []
        
    def get_uptime(self) -> float:
        """Get agent uptime in seconds."""
        return time.time() - self.start_time
    
    def get_health(self) -> HealthResponse:
        """Get agent health status."""
        try:
            # Check if agent process is running
            if self.agent_process and self.agent_process.poll() is None:
                status = HealthStatus.HEALTHY
            elif self.agent_process and self.agent_process.poll() is not None:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED
                
            return HealthResponse(
                status=status,
                timestamp=time.time(),
                uptime_seconds=self.get_uptime(),
                version="1.0.0",  # TODO: Get from package version
                snmp_endpoint=self.snmp_endpoint
            )
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status=HealthStatus.UNHEALTHY,
                timestamp=time.time(),
                uptime_seconds=self.get_uptime(),
                version="1.0.0",
                snmp_endpoint=self.snmp_endpoint
            )
    
    def get_metrics(self) -> MetricsResponse:
        """Get agent metrics."""
        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Get current connections (approximation)
        current_connections = 0
        if self.agent_process:
            try:
                process = psutil.Process(self.agent_process.pid)
                current_connections = len(process.connections())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                current_connections = 0
        
        return MetricsResponse(
            timestamp=time.time(),
            uptime_seconds=self.get_uptime(),
            requests_total=self.requests_total,
            requests_successful=self.requests_successful,
            requests_failed=self.requests_failed,
            avg_response_time_ms=avg_response_time,
            current_connections=current_connections
        )
    
    def get_configuration(self) -> ConfigurationResponse:
        """Get current configuration."""
        config_dict = {}
        if self.config:
            config_dict = self.config.config
        
        return ConfigurationResponse(
            simulation=config_dict.get("simulation", {}),
            timestamp=time.time()
        )
    
    def update_configuration(self, config_update: Dict[str, Any]) -> ConfigurationResponse:
        """Update configuration.
        
        Args:
            config_update: Configuration updates to apply
            
        Returns:
            Updated configuration response
            
        Raises:
            ValueError: If configuration update is invalid
        """
        if not self.config:
            raise ValueError("No configuration object available")
        
        try:
            # Apply configuration updates
            if "simulation" in config_update:
                self.config.config["simulation"] = self.config._merge_configs(
                    self.config.config["simulation"],
                    config_update["simulation"]
                )
            
            # Validate updated configuration
            self.config._validate_config()
            
            self.logger.info("Configuration updated successfully")
            
            return self.get_configuration()
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
    
    def get_agent_status(self) -> AgentStatusResponse:
        """Get detailed agent status."""
        # Determine agent status
        if self.agent_process:
            if self.agent_process.poll() is None:
                status = AgentStatus.RUNNING
                pid = self.agent_process.pid
            else:
                status = AgentStatus.STOPPED
                pid = None
        else:
            status = AgentStatus.STOPPED
            pid = None
        
        # Get active behaviors
        active_behaviors = []
        if self.config:
            behaviors = self.config.config.get("simulation", {}).get("behaviors", {})
            for behavior_name, behavior_config in behaviors.items():
                if isinstance(behavior_config, dict) and behavior_config.get("enabled", False):
                    active_behaviors.append(behavior_name)
        
        config_file = None
        if self.config and hasattr(self.config, 'config_path'):
            config_file = self.config.config_path
        
        return AgentStatusResponse(
            status=status,
            timestamp=time.time(),
            pid=pid,
            snmp_endpoint=self.snmp_endpoint,
            data_directory=str(self.data_dir),
            configuration_file=config_file,
            active_behaviors=active_behaviors
        )
    
    def restart_agent(self, force: bool = False, timeout_seconds: int = 30) -> RestartResponse:
        """Restart the SNMP agent.
        
        Args:
            force: Force restart even if agent is healthy
            timeout_seconds: Timeout for restart operation
            
        Returns:
            Restart operation response
        """
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
                        restart_time_seconds=time.time() - start_time
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
                    self.logger.warning("Agent did not shut down gracefully, forcing kill")
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
                restart_time_seconds=restart_time
            )
            
        except Exception as e:
            self.logger.error(f"Restart failed: {e}")
            return RestartResponse(
                success=False,
                message=f"Restart failed: {e}",
                old_pid=old_pid,
                new_pid=new_pid,
                restart_time_seconds=time.time() - start_time
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
                    with open(snmprec_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                parts = line.split('|', 1)
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
                timestamp=time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get OID list: {e}")
            return OIDListResponse(
                oids=[],
                total_count=0,
                data_sources=[],
                timestamp=time.time()
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