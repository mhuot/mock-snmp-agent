#!/usr/bin/env python3
"""
WebSocket Integration Tests

Tests for WebSocket functionality including connection management,
message broadcasting, and real-time data streaming.
"""

import asyncio
import json
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import websockets
from websockets.exceptions import ConnectionClosed

from rest_api.controllers import MockSNMPAgentController
from rest_api.websocket import ConnectionManager, MetricsCollector, manager


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.messages = []
        self.closed = False
        # Import WebSocketState to use the correct enum value
        from fastapi.websockets import WebSocketState

        self.client_state = WebSocketState.CONNECTED

    async def accept(self):
        """Mock accept method."""
        pass

    async def send_json(self, data):
        """Mock send_json method."""
        if not self.closed:
            self.messages.append(data)
        else:
            raise ConnectionClosed(None, None)

    async def receive_text(self):
        """Mock receive_text method."""
        if self.closed:
            raise ConnectionClosed(None, None)
        await asyncio.sleep(0.1)  # Simulate waiting
        return "ping"

    def close(self):
        """Mock close method."""
        self.closed = True


@pytest.mark.asyncio
class TestConnectionManager:
    """Test suite for WebSocket connection management."""

    @pytest.fixture
    def connection_manager(self):
        """Create fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        return MockWebSocket()

    async def test_connection_management(self, connection_manager, mock_websocket):
        """Test basic connection management."""
        # Test connection
        await connection_manager.connect(mock_websocket, "metrics")

        assert mock_websocket in connection_manager.active_connections
        assert mock_websocket in connection_manager.channel_connections["metrics"]

        # Test disconnection
        connection_manager.disconnect(mock_websocket)

        assert mock_websocket not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.channel_connections["metrics"]

    async def test_metrics_broadcasting(self, connection_manager, mock_websocket):
        """Test metrics broadcasting."""
        await connection_manager.connect(mock_websocket, "metrics")

        test_metrics = {
            "requests_total": 100,
            "requests_successful": 95,
            "avg_response_time_ms": 50.5,
        }

        await connection_manager.broadcast_metrics(test_metrics)

        assert len(mock_websocket.messages) == 1
        message = mock_websocket.messages[0]

        assert message["type"] == "metrics_update"
        assert "timestamp" in message
        assert message["data"] == test_metrics

    async def test_log_broadcasting(self, connection_manager, mock_websocket):
        """Test log broadcasting."""
        await connection_manager.connect(mock_websocket, "logs")

        await connection_manager.broadcast_log(
            level="info", message="Test log message", source="test"
        )

        assert len(mock_websocket.messages) == 1
        message = mock_websocket.messages[0]

        assert message["type"] == "log_entry"
        assert message["data"]["level"] == "info"
        assert message["data"]["message"] == "Test log message"
        assert message["data"]["source"] == "test"

    async def test_state_change_broadcasting(self, connection_manager, mock_websocket):
        """Test state change broadcasting."""
        await connection_manager.connect(mock_websocket, "state")

        await connection_manager.broadcast_state_change(
            device_type="router",
            old_state="booting",
            new_state="operational",
            trigger="time_based",
            reason="Boot complete",
        )

        assert len(mock_websocket.messages) == 1
        message = mock_websocket.messages[0]

        assert message["type"] == "state_transition"
        assert message["data"]["device_type"] == "router"
        assert message["data"]["old_state"] == "booting"
        assert message["data"]["new_state"] == "operational"

    async def test_snmp_activity_broadcasting(self, connection_manager, mock_websocket):
        """Test SNMP activity broadcasting."""
        await connection_manager.connect(mock_websocket, "snmp_activity")

        await connection_manager.broadcast_snmp_activity(
            request_type="GET",
            oid="1.3.6.1.2.1.1.1.0",
            community="public",
            source_ip="192.168.1.100",
            success=True,
            response_time_ms=45.2,
        )

        assert len(mock_websocket.messages) == 1
        message = mock_websocket.messages[0]

        assert message["type"] == "snmp_activity"
        assert message["data"]["request_type"] == "GET"
        assert message["data"]["oid"] == "1.3.6.1.2.1.1.1.0"
        assert message["data"]["success"] is True
        assert message["data"]["response_time_ms"] == 45.2

    async def test_buffer_management(self, connection_manager):
        """Test message buffering."""
        # Add messages to buffers
        test_metrics = {"requests_total": 50}
        await connection_manager.broadcast_metrics(test_metrics)

        assert len(connection_manager.metrics_buffer) == 1

        # Connect new client and check it receives buffered data
        mock_websocket = MockWebSocket()
        await connection_manager.connect(mock_websocket, "metrics")

        # Should receive buffered message
        assert len(mock_websocket.messages) >= 1

    async def test_connection_cleanup(self, connection_manager):
        """Test automatic cleanup of disconnected clients."""
        mock_websocket = MockWebSocket()
        await connection_manager.connect(mock_websocket, "metrics")

        # Simulate connection failure
        mock_websocket.closed = True

        # Broadcasting should clean up failed connections
        await connection_manager.broadcast_metrics({"test": "data"})

        assert mock_websocket not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.channel_connections["metrics"]

    def test_connection_stats(self, connection_manager):
        """Test connection statistics."""
        stats = connection_manager.get_connection_stats()

        assert "total_connections" in stats
        assert "channel_connections" in stats
        assert "buffer_sizes" in stats

        assert isinstance(stats["total_connections"], int)
        assert isinstance(stats["channel_connections"], dict)
        assert isinstance(stats["buffer_sizes"], dict)


@pytest.mark.asyncio
class TestMetricsCollector:
    """Test suite for metrics collection and broadcasting."""

    @pytest.fixture
    def mock_controller(self):
        """Create mock controller."""
        controller = Mock(spec=MockSNMPAgentController)
        controller.get_metrics.return_value = Mock()
        controller.get_metrics.return_value.dict.return_value = {
            "timestamp": time.time(),
            "requests_total": 100,
            "requests_successful": 95,
            "avg_response_time_ms": 50.0,
        }
        return controller

    @pytest.fixture
    def metrics_collector(self, mock_controller):
        """Create metrics collector."""
        return MetricsCollector(mock_controller, interval_seconds=0.1)

    async def test_metrics_collection_start_stop(self, metrics_collector):
        """Test starting and stopping metrics collection."""
        # Start collector
        await metrics_collector.start()
        assert metrics_collector.running is True
        assert metrics_collector.task is not None

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Stop collector
        await metrics_collector.stop()
        assert metrics_collector.running is False

    async def test_metrics_collection_loop(self, metrics_collector, mock_controller):
        """Test metrics collection loop."""
        with patch("rest_api.websocket.manager") as mock_manager:
            mock_manager.broadcast_metrics = AsyncMock()

            # Start collector
            await metrics_collector.start()

            # Let it run for a few iterations
            await asyncio.sleep(0.3)

            # Stop collector
            await metrics_collector.stop()

            # Check that metrics were collected and broadcast
            assert mock_controller.get_metrics.called
            assert mock_manager.broadcast_metrics.called

    async def test_metrics_collection_error_handling(self, mock_controller):
        """Test error handling in metrics collection."""
        # Make controller raise an exception
        mock_controller.get_metrics.side_effect = Exception("Test error")

        collector = MetricsCollector(mock_controller, interval_seconds=0.1)

        # Should not crash when starting
        await collector.start()
        await asyncio.sleep(0.2)
        await collector.stop()

        # Should have handled the error gracefully
        assert not collector.running


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    async def test_multiple_channel_connections(self):
        """Test connections to multiple channels."""
        manager = ConnectionManager()

        # Create connections to different channels
        ws_metrics = MockWebSocket()
        ws_logs = MockWebSocket()
        ws_state = MockWebSocket()

        await manager.connect(ws_metrics, "metrics")
        await manager.connect(ws_logs, "logs")
        await manager.connect(ws_state, "state")

        # Broadcast to different channels
        await manager.broadcast_metrics({"test": "metrics"})
        await manager.broadcast_log("info", "test log")
        await manager.broadcast_state_change("router", "old", "new", "manual", "test")

        # Check messages were delivered to correct channels
        assert len(ws_metrics.messages) == 1
        assert len(ws_logs.messages) == 1
        assert len(ws_state.messages) == 1

        assert ws_metrics.messages[0]["type"] == "metrics_update"
        assert ws_logs.messages[0]["type"] == "log_entry"
        assert ws_state.messages[0]["type"] == "state_transition"

    async def test_concurrent_broadcasting(self):
        """Test concurrent message broadcasting."""
        manager = ConnectionManager()

        # Create multiple connections to same channel
        websockets = [MockWebSocket() for _ in range(5)]
        for ws in websockets:
            await manager.connect(ws, "metrics")

        # Broadcast multiple messages concurrently
        tasks = []
        for i in range(10):
            task = manager.broadcast_metrics({"request_id": i})
            tasks.append(task)

        await asyncio.gather(*tasks)

        # All websockets should have received all messages
        for ws in websockets:
            assert len(ws.messages) == 10

    async def test_buffer_overflow_handling(self):
        """Test buffer overflow handling."""
        manager = ConnectionManager()

        # Fill metrics buffer beyond capacity
        for i in range(150):  # Buffer max is 100
            await manager.broadcast_metrics({"message": i})

        # Buffer should not exceed max size
        assert len(manager.metrics_buffer) == 100

        # Should contain the most recent messages
        last_message = list(manager.metrics_buffer)[-1]
        assert last_message["data"]["message"] == 149

    async def test_websocket_reconnection_scenario(self):
        """Test websocket reconnection scenario."""
        manager = ConnectionManager()

        # Initial connection
        ws1 = MockWebSocket()
        await manager.connect(ws1, "metrics")

        # Send some messages
        for i in range(5):
            await manager.broadcast_metrics({"message": i})

        # Simulate disconnection
        manager.disconnect(ws1)

        # Send more messages while disconnected
        for i in range(5, 10):
            await manager.broadcast_metrics({"message": i})

        # Reconnect (new websocket)
        ws2 = MockWebSocket()
        await manager.connect(ws2, "metrics")

        # Should receive recent buffered messages
        assert len(ws2.messages) > 0

        # New messages should be delivered
        await manager.broadcast_metrics({"message": "new"})

        # Find the new message
        new_messages = [m for m in ws2.messages if m["data"].get("message") == "new"]
        assert len(new_messages) == 1


class TestWebSocketConfiguration:
    """Test WebSocket configuration and setup."""

    def test_channel_configuration(self):
        """Test channel configuration."""
        manager = ConnectionManager()

        expected_channels = ["metrics", "logs", "state", "snmp_activity"]
        assert set(manager.channel_connections.keys()) == set(expected_channels)

    def test_buffer_configuration(self):
        """Test buffer configuration."""
        manager = ConnectionManager()

        # Check buffer instances exist
        assert hasattr(manager, "metrics_buffer")
        assert hasattr(manager, "logs_buffer")
        assert hasattr(manager, "state_buffer")
        assert hasattr(manager, "snmp_activity_buffer")

        # Check buffer sizes
        assert manager.metrics_buffer.maxlen == 100
        assert manager.logs_buffer.maxlen == 500
        assert manager.state_buffer.maxlen == 50
        assert manager.snmp_activity_buffer.maxlen == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
