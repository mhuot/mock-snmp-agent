#!/usr/bin/env python3
"""
WebSocket Support for Real-time Updates

This module provides WebSocket endpoints for streaming real-time data
from the Mock SNMP Agent to connected clients.
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self.channel_connections: Dict[str, Set[WebSocket]] = {
            "metrics": set(),
            "logs": set(),
            "state": set(),
            "snmp_activity": set(),
        }
        self.logger = logging.getLogger(__name__)

        # Buffers for recent data
        self.metrics_buffer = deque(maxlen=100)
        self.logs_buffer = deque(maxlen=500)
        self.state_buffer = deque(maxlen=50)
        self.snmp_activity_buffer = deque(maxlen=200)

    async def connect(self, websocket: WebSocket, channel: str = None):
        """Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            channel: Optional channel to subscribe to
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        if channel and channel in self.channel_connections:
            self.channel_connections[channel].add(websocket)
            self.logger.info("WebSocket connected to channel: %s", channel)

            # Send recent data from buffer
            await self._send_buffer_data(websocket, channel)
        else:
            self.logger.info("WebSocket connected (no channel)")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)

        # Remove from all channels
        for channel_connections in self.channel_connections.values():
            channel_connections.discard(websocket)

        self.logger.info("WebSocket disconnected")

    async def _send_buffer_data(self, websocket: WebSocket, channel: str):
        """Send buffered data to newly connected client.

        Args:
            websocket: The WebSocket connection
            channel: The channel name
        """
        buffer_map = {
            "metrics": self.metrics_buffer,
            "logs": self.logs_buffer,
            "state": self.state_buffer,
            "snmp_activity": self.snmp_activity_buffer,
        }

        buffer = buffer_map.get(channel)
        if buffer:
            # Send last 10 items from buffer
            recent_items = list(buffer)[-10:]
            for item in recent_items:
                try:
                    await websocket.send_json(item)
                except Exception as e:
                    self.logger.error("Error sending buffer data: %s", str(e))
                    break

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast a message to all connections in a channel.

        Args:
            channel: The channel name
            message: The message to broadcast
        """
        if channel not in self.channel_connections:
            return

        # Add to appropriate buffer
        buffer_map = {
            "metrics": self.metrics_buffer,
            "logs": self.logs_buffer,
            "state": self.state_buffer,
            "snmp_activity": self.snmp_activity_buffer,
        }

        buffer = buffer_map.get(channel)
        if buffer is not None:
            buffer.append(message)

        # Broadcast to connected clients
        disconnected = set()
        for connection in self.channel_connections[channel]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.add(connection)
            except Exception as e:
                self.logger.error("Error broadcasting to WebSocket: %s", str(e))
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics update.

        Args:
            metrics: Metrics data to broadcast
        """
        message = {"type": "metrics_update", "timestamp": time.time(), "data": metrics}
        await self.broadcast_to_channel("metrics", message)

    async def broadcast_log(
        self, level: str, message: str, source: Optional[str] = None
    ):
        """Broadcast log message.

        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            source: Optional source component
        """
        log_entry = {
            "type": "log_entry",
            "timestamp": time.time(),
            "data": {
                "level": level,
                "message": message,
                "source": source or "system",
                "datetime": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_channel("logs", log_entry)

    async def broadcast_state_change(
        self,
        device_type: str,
        old_state: str,
        new_state: str,
        trigger: str,
        reason: str,
    ):
        """Broadcast state machine transition.

        Args:
            device_type: Type of device
            old_state: Previous state
            new_state: New state
            trigger: Transition trigger
            reason: Reason for transition
        """
        state_change = {
            "type": "state_transition",
            "timestamp": time.time(),
            "data": {
                "device_type": device_type,
                "old_state": old_state,
                "new_state": new_state,
                "trigger": trigger,
                "reason": reason,
                "datetime": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_channel("state", state_change)

    async def broadcast_snmp_activity(
        self,
        request_type: str,
        oid: str,
        community: str,
        source_ip: str,
        success: bool,
        response_time_ms: float,
        error_message: Optional[str] = None,
    ):
        """Broadcast SNMP request/response activity.

        Args:
            request_type: Type of SNMP request (GET, GETNEXT, GETBULK)
            oid: Requested OID
            community: SNMP community string
            source_ip: Source IP address
            success: Whether request succeeded
            response_time_ms: Response time in milliseconds
            error_message: Optional error message
        """
        activity = {
            "type": "snmp_activity",
            "timestamp": time.time(),
            "data": {
                "request_type": request_type,
                "oid": oid,
                "community": community,
                "source_ip": source_ip,
                "success": success,
                "response_time_ms": response_time_ms,
                "error_message": error_message,
                "datetime": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_channel("snmp_activity", activity)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": len(self.active_connections),
            "channel_connections": {
                channel: len(connections)
                for channel, connections in self.channel_connections.items()
            },
            "buffer_sizes": {
                "metrics": len(self.metrics_buffer),
                "logs": len(self.logs_buffer),
                "state": len(self.state_buffer),
                "snmp_activity": len(self.snmp_activity_buffer),
            },
        }


# Global connection manager instance
manager = ConnectionManager()


def setup_websocket_routes(app):
    """Setup WebSocket routes on the FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.websocket("/ws/metrics")
    async def websocket_metrics(websocket: WebSocket):
        """WebSocket endpoint for real-time metrics."""
        await manager.connect(websocket, "metrics")
        try:
            while True:
                # Keep connection alive and handle incoming messages
                await websocket.receive_text()
                # Could handle client commands here if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket):
        """WebSocket endpoint for real-time logs."""
        await manager.connect(websocket, "logs")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/state")
    async def websocket_state(websocket: WebSocket):
        """WebSocket endpoint for state machine updates."""
        await manager.connect(websocket, "state")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/snmp-activity")
    async def websocket_snmp_activity(websocket: WebSocket):
        """WebSocket endpoint for SNMP activity monitoring."""
        await manager.connect(websocket, "snmp_activity")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.get("/ws/stats", tags=["WebSocket"])
    async def get_websocket_stats():
        """Get WebSocket connection statistics."""
        return manager.get_connection_stats()


class MetricsCollector:
    """Collects and broadcasts metrics periodically."""

    def __init__(self, controller, interval_seconds: int = 5):
        """Initialize metrics collector.

        Args:
            controller: Agent controller instance
            interval_seconds: Update interval
        """
        self.controller = controller
        self.interval_seconds = interval_seconds
        self.running = False
        self.task = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start collecting and broadcasting metrics."""
        self.running = True
        self.task = asyncio.create_task(self._collect_loop())
        self.logger.info(
            f"Started metrics collector (interval: {self.interval_seconds}s)"
        )

    async def stop(self):
        """Stop collecting metrics."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped metrics collector")

    async def _collect_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                # Get current metrics
                metrics = self.controller.get_metrics()

                # Broadcast to WebSocket clients
                await manager.broadcast_metrics(metrics.dict())

            except Exception as e:
                self.logger.error("Error collecting metrics: %s", str(e))

            await asyncio.sleep(self.interval_seconds)
