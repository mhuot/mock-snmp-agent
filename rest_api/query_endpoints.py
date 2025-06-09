#!/usr/bin/env python3
"""
Enhanced Query Endpoints

This module provides advanced query capabilities for OIDs, metrics,
and historical data access.
"""

import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque

from fastapi import Query, HTTPException
from pydantic import BaseModel, Field


class OIDQueryRequest(BaseModel):
    """OID query request model."""

    oids: List[str] = Field(..., description="List of OIDs to query")
    community: str = Field("public", description="SNMP community string")
    include_metadata: bool = Field(False, description="Include OID metadata")

    class Config:
        schema_extra = {
            "example": {
                "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"],
                "community": "public",
                "include_metadata": True,
            }
        }


class OIDQueryResponse(BaseModel):
    """OID query response model."""

    timestamp: float = Field(..., description="Query timestamp")
    results: Dict[str, Any] = Field(..., description="OID query results")
    errors: Dict[str, str] = Field(default_factory=dict, description="Query errors")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": 1640995200.0,
                "results": {
                    "1.3.6.1.2.1.1.1.0": {
                        "value": "Linux System",
                        "type": "STRING",
                        "metadata": {"name": "sysDescr", "mib": "SNMPv2-MIB"},
                    }
                },
                "errors": {},
            }
        }


class HistoryQueryRequest(BaseModel):
    """History query request model."""

    start_time: Optional[float] = Field(None, description="Start timestamp (Unix)")
    end_time: Optional[float] = Field(None, description="End timestamp (Unix)")
    interval_minutes: int = Field(5, description="Data point interval in minutes")
    metrics: List[str] = Field(
        default_factory=list, description="Specific metrics to include"
    )

    class Config:
        schema_extra = {
            "example": {
                "start_time": 1640991600.0,
                "end_time": 1640995200.0,
                "interval_minutes": 5,
                "metrics": ["requests_total", "avg_response_time_ms"],
            }
        }


class MetricsHistoryResponse(BaseModel):
    """Metrics history response model."""

    start_time: float
    end_time: float
    interval_minutes: int
    data_points: List[Dict[str, Any]]

    class Config:
        schema_extra = {
            "example": {
                "start_time": 1640991600.0,
                "end_time": 1640995200.0,
                "interval_minutes": 5,
                "data_points": [
                    {
                        "timestamp": 1640991600.0,
                        "requests_total": 100,
                        "avg_response_time_ms": 75.5,
                    }
                ],
            }
        }


class StateHistoryResponse(BaseModel):
    """State history response model."""

    device_type: str
    current_state: str
    total_transitions: int
    transitions: List[Dict[str, Any]]
    state_durations: Dict[str, float]

    class Config:
        schema_extra = {
            "example": {
                "device_type": "router",
                "current_state": "operational",
                "total_transitions": 5,
                "transitions": [
                    {
                        "timestamp": 1640991600.0,
                        "from_state": "booting",
                        "to_state": "operational",
                        "trigger": "time_based",
                        "duration_seconds": 45.0,
                    }
                ],
                "state_durations": {"booting": 45.0, "operational": 3555.0},
            }
        }


class DataHistoryManager:
    """Manages historical data storage and retrieval."""

    def __init__(self, data_dir: str = "./data/history"):
        """Initialize history manager.

        Args:
            data_dir: Directory for storing historical data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory buffers for recent data
        self.metrics_buffer = deque(maxlen=2880)  # 24 hours at 30s intervals
        self.state_buffer = deque(maxlen=1000)  # Last 1000 state transitions
        self.oid_cache = {}  # OID value cache

        # Persistence files
        self.metrics_file = self.data_dir / "metrics_history.jsonl"
        self.state_file = self.data_dir / "state_history.jsonl"

    def record_metrics(self, metrics: Dict[str, Any]):
        """Record metrics data point.

        Args:
            metrics: Metrics dictionary
        """
        data_point = {"timestamp": time.time(), **metrics}
        self.metrics_buffer.append(data_point)

        # Persist to file
        try:
            with open(self.metrics_file, "a") as f:
                f.write(json.dumps(data_point) + "\n")
        except Exception:
            pass  # Silent fail for demo

    def record_state_transition(self, transition: Dict[str, Any]):
        """Record state transition.

        Args:
            transition: State transition data
        """
        self.state_buffer.append(transition)

        # Persist to file
        try:
            with open(self.state_file, "a") as f:
                f.write(json.dumps(transition) + "\n")
        except Exception:
            pass

    def query_metrics_history(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        interval_minutes: int = 5,
        metrics: Optional[List[str]] = None,
    ) -> MetricsHistoryResponse:
        """Query metrics history.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            interval_minutes: Data aggregation interval
            metrics: Specific metrics to include

        Returns:
            MetricsHistoryResponse with aggregated data
        """
        # Default time range: last 24 hours
        if not end_time:
            end_time = time.time()
        if not start_time:
            start_time = end_time - 86400  # 24 hours

        # Get data from buffer
        data_points = []
        for point in self.metrics_buffer:
            if start_time <= point["timestamp"] <= end_time:
                if metrics:
                    filtered_point = {
                        "timestamp": point["timestamp"],
                        **{k: v for k, v in point.items() if k in metrics},
                    }
                    data_points.append(filtered_point)
                else:
                    data_points.append(point)

        # Aggregate by interval
        aggregated = self._aggregate_metrics(data_points, interval_minutes)

        return MetricsHistoryResponse(
            start_time=start_time,
            end_time=end_time,
            interval_minutes=interval_minutes,
            data_points=aggregated,
        )

    def query_state_history(
        self, device_type: Optional[str] = None
    ) -> StateHistoryResponse:
        """Query state transition history.

        Args:
            device_type: Filter by device type

        Returns:
            StateHistoryResponse with transition data
        """
        transitions = list(self.state_buffer)

        if device_type:
            transitions = [
                t for t in transitions if t.get("device_type") == device_type
            ]

        # Calculate state durations
        state_durations = defaultdict(float)
        for i, transition in enumerate(transitions):
            if i > 0:
                duration = transition["timestamp"] - transitions[i - 1]["timestamp"]
                state_durations[transitions[i - 1]["to_state"]] += duration

        # Current state info
        current_state = transitions[-1]["to_state"] if transitions else "unknown"
        current_device = (
            transitions[-1].get("device_type", "unknown") if transitions else "unknown"
        )

        return StateHistoryResponse(
            device_type=current_device,
            current_state=current_state,
            total_transitions=len(transitions),
            transitions=transitions[-50:],  # Last 50 transitions
            state_durations=dict(state_durations),
        )

    def _aggregate_metrics(
        self, data_points: List[Dict], interval_minutes: int
    ) -> List[Dict]:
        """Aggregate metrics by time interval.

        Args:
            data_points: Raw data points
            interval_minutes: Aggregation interval

        Returns:
            Aggregated data points
        """
        if not data_points:
            return []

        interval_seconds = interval_minutes * 60
        aggregated = []
        current_bucket = []
        bucket_start = None

        for point in sorted(data_points, key=lambda x: x["timestamp"]):
            point_time = point["timestamp"]

            if not bucket_start:
                bucket_start = point_time

            if point_time - bucket_start < interval_seconds:
                current_bucket.append(point)
            else:
                # Process current bucket
                if current_bucket:
                    aggregated.append(self._aggregate_bucket(current_bucket))

                # Start new bucket
                current_bucket = [point]
                bucket_start = point_time

        # Process last bucket
        if current_bucket:
            aggregated.append(self._aggregate_bucket(current_bucket))

        return aggregated

    def _aggregate_bucket(self, bucket: List[Dict]) -> Dict:
        """Aggregate a bucket of data points.

        Args:
            bucket: List of data points in the bucket

        Returns:
            Aggregated data point
        """
        if not bucket:
            return {}

        # Use the middle timestamp
        timestamp = bucket[len(bucket) // 2]["timestamp"]

        # Aggregate numeric values
        aggregated = {"timestamp": timestamp}
        numeric_fields = defaultdict(list)

        for point in bucket:
            for key, value in point.items():
                if key != "timestamp" and isinstance(value, (int, float)):
                    numeric_fields[key].append(value)

        # Calculate averages
        for field, values in numeric_fields.items():
            if field.endswith("_total") or field.startswith("requests_"):
                # Use last value for counters
                aggregated[field] = values[-1]
            else:
                # Average for gauges
                aggregated[field] = sum(values) / len(values)

        return aggregated


def setup_query_endpoints(app, controller, data_dir: Optional[str] = None):
    """Setup enhanced query endpoints on the FastAPI app.

    Args:
        app: FastAPI application instance
        controller: Agent controller instance
        data_dir: Data directory path
    """
    history_manager = DataHistoryManager(data_dir or "./data/history")

    @app.post("/oids/query", response_model=OIDQueryResponse, tags=["OIDs"])
    async def query_oids(request: OIDQueryRequest):
        """Query specific OID values with metadata."""
        results = {}
        errors = {}

        for oid in request.oids:
            try:
                # Simulate OID query (in real implementation, would query agent)
                value = controller.query_oid(oid, request.community)

                result = {
                    "value": value.get("value"),
                    "type": value.get("type", "STRING"),
                }

                if request.include_metadata:
                    # Add metadata (would come from MIB in real implementation)
                    result["metadata"] = {
                        "name": _get_oid_name(oid),
                        "mib": _get_oid_mib(oid),
                        "description": _get_oid_description(oid),
                    }

                results[oid] = result

            except Exception as e:
                errors[oid] = str(e)

        return OIDQueryResponse(timestamp=time.time(), results=results, errors=errors)

    @app.get("/oids/search", tags=["OIDs"])
    async def search_oids(
        pattern: str = Query(..., description="Search pattern"),
        mib: Optional[str] = Query(None, description="Filter by MIB"),
        limit: int = Query(50, description="Maximum results"),
    ):
        """Search for OIDs by pattern or MIB."""
        # In real implementation, would search through MIB database
        matching_oids = controller.search_oids(pattern, mib, limit)

        return {
            "pattern": pattern,
            "mib": mib,
            "count": len(matching_oids),
            "oids": matching_oids,
        }

    @app.post(
        "/metrics/history", response_model=MetricsHistoryResponse, tags=["Monitoring"]
    )
    async def get_metrics_history(request: HistoryQueryRequest):
        """Get historical metrics data."""
        return history_manager.query_metrics_history(
            start_time=request.start_time,
            end_time=request.end_time,
            interval_minutes=request.interval_minutes,
            metrics=request.metrics,
        )

    @app.get(
        "/state/history", response_model=StateHistoryResponse, tags=["State Machine"]
    )
    async def get_state_history(
        device_type: Optional[str] = Query(None, description="Filter by device type")
    ):
        """Get state transition history."""
        return history_manager.query_state_history(device_type)

    @app.get("/oids/tree", tags=["OIDs"])
    async def get_oid_tree(
        root_oid: str = Query("1.3.6.1", description="Root OID to start from"),
        max_depth: int = Query(3, description="Maximum tree depth"),
    ):
        """Get OID tree structure for visualization."""
        # In real implementation, would build tree from MIB
        tree = controller.get_oid_tree(root_oid, max_depth)

        return {"root_oid": root_oid, "max_depth": max_depth, "tree": tree}

    # Make history manager available to other components
    app.state.history_manager = history_manager

    return history_manager


def _get_oid_name(oid: str) -> str:
    """Get OID name from MIB (placeholder)."""
    oid_names = {
        "1.3.6.1.2.1.1.1.0": "sysDescr",
        "1.3.6.1.2.1.1.2.0": "sysObjectID",
        "1.3.6.1.2.1.1.3.0": "sysUpTime",
        "1.3.6.1.2.1.1.4.0": "sysContact",
        "1.3.6.1.2.1.1.5.0": "sysName",
        "1.3.6.1.2.1.1.6.0": "sysLocation",
    }
    return oid_names.get(oid, "unknown")


def _get_oid_mib(oid: str) -> str:
    """Get OID MIB module (placeholder)."""
    if oid.startswith("1.3.6.1.2.1.1"):
        return "SNMPv2-MIB"
    elif oid.startswith("1.3.6.1.2.1.2"):
        return "IF-MIB"
    return "Unknown-MIB"


def _get_oid_description(oid: str) -> str:
    """Get OID description (placeholder)."""
    descriptions = {
        "1.3.6.1.2.1.1.1.0": "A textual description of the entity",
        "1.3.6.1.2.1.1.3.0": "The time since the network management portion was last re-initialized",
        "1.3.6.1.2.1.1.5.0": "An administratively-assigned name for this managed node",
    }
    return descriptions.get(oid, "No description available")
