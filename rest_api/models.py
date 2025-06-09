#!/usr/bin/env python3
"""
REST API Models

Pydantic models for request/response validation and documentation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"


class HealthResponse(BaseModel):
    """Health check response model."""
    status: HealthStatus
    timestamp: float = Field(..., description="Unix timestamp of health check")
    uptime_seconds: float = Field(..., description="Agent uptime in seconds")
    version: str = Field(..., description="Agent version")
    snmp_endpoint: str = Field(..., description="SNMP endpoint (host:port)")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": 1640995200.0,
                "uptime_seconds": 3600.0,
                "version": "1.0.0",
                "snmp_endpoint": "127.0.0.1:11611"
            }
        }


class MetricsResponse(BaseModel):
    """Metrics response model."""
    timestamp: float = Field(..., description="Unix timestamp of metrics collection")
    uptime_seconds: float = Field(..., description="Agent uptime in seconds")
    requests_total: int = Field(..., description="Total SNMP requests received")
    requests_successful: int = Field(..., description="Successful SNMP requests")
    requests_failed: int = Field(..., description="Failed SNMP requests")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    current_connections: int = Field(..., description="Current active connections")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1640995200.0,
                "uptime_seconds": 3600.0,
                "requests_total": 1000,
                "requests_successful": 950,
                "requests_failed": 50,
                "avg_response_time_ms": 75.5,
                "current_connections": 5
            }
        }


class ConfigurationUpdate(BaseModel):
    """Configuration update request model."""
    simulation: Optional[Dict[str, Any]] = Field(None, description="Simulation configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "simulation": {
                    "behaviors": {
                        "delay": {
                            "enabled": True,
                            "global_delay": 100,
                            "deviation": 50
                        }
                    }
                }
            }
        }


class ConfigurationResponse(BaseModel):
    """Configuration response model."""
    simulation: Dict[str, Any] = Field(..., description="Current simulation configuration")
    timestamp: float = Field(..., description="Configuration timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "simulation": {
                    "behaviors": {
                        "delay": {
                            "enabled": False,
                            "global_delay": 0,
                            "deviation": 0
                        }
                    }
                },
                "timestamp": 1640995200.0
            }
        }


class AgentStatusResponse(BaseModel):
    """Agent status response model."""
    status: AgentStatus
    timestamp: float = Field(..., description="Status timestamp")
    pid: Optional[int] = Field(None, description="Process ID")
    snmp_endpoint: str = Field(..., description="SNMP endpoint")
    data_directory: str = Field(..., description="Data directory path")
    configuration_file: Optional[str] = Field(None, description="Configuration file path")
    active_behaviors: List[str] = Field(..., description="List of active simulation behaviors")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "running",
                "timestamp": 1640995200.0,
                "pid": 12345,
                "snmp_endpoint": "127.0.0.1:11611",
                "data_directory": "/app/data",
                "configuration_file": "/app/config.yaml",
                "active_behaviors": ["delay", "snmpv3_security"]
            }
        }


class RestartRequest(BaseModel):
    """Agent restart request model."""
    force: bool = Field(False, description="Force restart even if agent is healthy")
    timeout_seconds: int = Field(30, description="Timeout for restart operation")
    
    class Config:
        schema_extra = {
            "example": {
                "force": False,
                "timeout_seconds": 30
            }
        }


class RestartResponse(BaseModel):
    """Agent restart response model."""
    success: bool = Field(..., description="Whether restart was successful")
    message: str = Field(..., description="Restart operation message")
    old_pid: Optional[int] = Field(None, description="Previous process ID")
    new_pid: Optional[int] = Field(None, description="New process ID")
    restart_time_seconds: float = Field(..., description="Time taken for restart")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Agent restarted successfully",
                "old_pid": 12345,
                "new_pid": 12346,
                "restart_time_seconds": 5.2
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: float = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid configuration format",
                "timestamp": 1640995200.0
            }
        }


class OIDListResponse(BaseModel):
    """OID list response model."""
    oids: List[str] = Field(..., description="List of available OIDs")
    total_count: int = Field(..., description="Total number of OIDs")
    data_sources: List[str] = Field(..., description="Data source files")
    timestamp: float = Field(..., description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "oids": [
                    "1.3.6.1.2.1.1.1.0",
                    "1.3.6.1.2.1.1.2.0",
                    "1.3.6.1.2.1.1.3.0"
                ],
                "total_count": 3,
                "data_sources": ["public.snmprec", "variation.snmprec"],
                "timestamp": 1640995200.0
            }
        }