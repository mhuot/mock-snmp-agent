#!/usr/bin/env python3
"""
Resource constraint simulation for Mock SNMP Agent.

This module simulates device resource constraints including CPU, memory,
and concurrent request limits to test monitoring system resilience.
"""

import time
import threading
import psutil
import queue
from typing import Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Resource constraint configuration."""

    max_cpu_percent: float = 85.0
    max_memory_percent: float = 90.0
    max_concurrent_requests: int = 50
    max_pdu_size: int = 1472  # bytes
    response_timeout: float = 5.0  # seconds
    enable_overload_errors: bool = True


class ResourceConstraintSimulator:
    """Simulates device resource constraints and their effects on SNMP responses."""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.active_requests = 0
        self.request_queue = queue.Queue()
        self.cpu_load_active = False
        self.memory_pressure_active = False
        self.lock = threading.Lock()

        # Performance monitoring
        self.total_requests = 0
        self.dropped_requests = 0
        self.timeout_requests = 0
        self.start_time = time.time()

    def simulate_cpu_load(self, duration: float = 10.0, target_percent: float = 85.0):
        """Simulate high CPU load for specified duration."""
        self.cpu_load_active = True

        def cpu_burner():
            end_time = time.time() + duration
            while time.time() < end_time and self.cpu_load_active:
                # Busy work to consume CPU
                _ = sum(i * i for i in range(1000))

                # Brief pause to allow other threads
                time.sleep(0.001)

            self.cpu_load_active = False

        thread = threading.Thread(target=cpu_burner, daemon=True)
        thread.start()
        return thread

    def simulate_memory_pressure(self, duration: float = 10.0):
        """Simulate memory pressure for specified duration."""
        self.memory_pressure_active = True

        def memory_consumer():
            # Allocate large chunks of memory
            memory_hogs = []
            try:
                end_time = time.time() + duration
                while time.time() < end_time and self.memory_pressure_active:
                    # Allocate 10MB chunks
                    chunk = bytearray(10 * 1024 * 1024)
                    memory_hogs.append(chunk)
                    time.sleep(0.1)

                    # Check if we should stop
                    memory_info = psutil.virtual_memory()
                    if memory_info.percent > self.limits.max_memory_percent:
                        break
            finally:
                # Clean up memory
                del memory_hogs
                self.memory_pressure_active = False

        thread = threading.Thread(target=memory_consumer, daemon=True)
        thread.start()
        return thread

    def check_request_allowed(self, request_size: int = 0) -> tuple[bool, str]:
        """Check if a request should be allowed based on current constraints.

        Returns:
            (allowed, reason) tuple
        """
        with self.lock:
            self.total_requests += 1

            # Check concurrent request limit
            if self.active_requests >= self.limits.max_concurrent_requests:
                self.dropped_requests += 1
                return False, "genErr"  # Too many concurrent requests

            # Check PDU size limit
            if request_size > self.limits.max_pdu_size:
                return False, "tooBig"

            # Check CPU load
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                if cpu_percent > self.limits.max_cpu_percent:
                    self.dropped_requests += 1
                    return False, "resourceUnavailable"
            except:
                pass  # If we can't check CPU, allow the request

            # Check memory usage
            try:
                memory_info = psutil.virtual_memory()
                if memory_info.percent > self.limits.max_memory_percent:
                    self.dropped_requests += 1
                    return False, "resourceUnavailable"
            except:
                pass  # If we can't check memory, allow the request

            # Request is allowed
            self.active_requests += 1
            return True, "noError"

    def complete_request(self):
        """Mark a request as completed."""
        with self.lock:
            if self.active_requests > 0:
                self.active_requests -= 1

    def get_performance_stats(self) -> Dict:
        """Get current performance statistics."""
        uptime = time.time() - self.start_time

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
        except:
            cpu_percent = 0.0
            memory_percent = 0.0

        return {
            "uptime_seconds": uptime,
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "dropped_requests": self.dropped_requests,
            "timeout_requests": self.timeout_requests,
            "success_rate": (
                (self.total_requests - self.dropped_requests)
                / max(self.total_requests, 1)
            )
            * 100,
            "requests_per_second": self.total_requests / max(uptime, 1),
            "current_cpu_percent": cpu_percent,
            "current_memory_percent": memory_percent,
            "cpu_overloaded": cpu_percent > self.limits.max_cpu_percent,
            "memory_overloaded": memory_percent > self.limits.max_memory_percent,
            "concurrent_limit_reached": self.active_requests
            >= self.limits.max_concurrent_requests,
        }


def create_resource_test_scenarios() -> Dict[str, ResourceConstraintSimulator]:
    """Create predefined resource constraint test scenarios."""

    scenarios = {}

    # Light load scenario
    scenarios["light_load"] = ResourceConstraintSimulator(
        ResourceLimits(
            max_cpu_percent=95.0,
            max_memory_percent=95.0,
            max_concurrent_requests=100,
            enable_overload_errors=False,
        )
    )

    # Moderate constraints
    scenarios["moderate_load"] = ResourceConstraintSimulator(
        ResourceLimits(
            max_cpu_percent=80.0, max_memory_percent=85.0, max_concurrent_requests=50
        )
    )

    # Heavy constraints (stress testing)
    scenarios["heavy_load"] = ResourceConstraintSimulator(
        ResourceLimits(
            max_cpu_percent=70.0,
            max_memory_percent=75.0,
            max_concurrent_requests=20,
            max_pdu_size=512,  # Smaller PDU limit
        )
    )

    # Extreme constraints (failure testing)
    scenarios["extreme_load"] = ResourceConstraintSimulator(
        ResourceLimits(
            max_cpu_percent=60.0,
            max_memory_percent=65.0,
            max_concurrent_requests=10,
            max_pdu_size=256,
            response_timeout=2.0,
        )
    )

    return scenarios


def generate_resource_snmprec_entries(
    simulator: ResourceConstraintSimulator, include_system_stats: bool = True
) -> list[str]:
    """Generate .snmprec entries for resource monitoring.

    Args:
        simulator: Resource constraint simulator
        include_system_stats: Include system resource statistics

    Returns:
        List of .snmprec file lines
    """
    lines = []

    if include_system_stats:
        # Add resource monitoring OIDs
        lines.extend(
            [
                # CPU utilization (custom OID)
                "1.3.6.1.4.1.99999.1.1.0|2:numeric|function=cpu_percent\n",
                # Memory utilization (custom OID)
                "1.3.6.1.4.1.99999.1.2.0|2:numeric|function=memory_percent\n",
                # Active SNMP requests (custom OID)
                "1.3.6.1.4.1.99999.1.3.0|2:numeric|function=active_requests\n",
                # Request drop rate (custom OID)
                "1.3.6.1.4.1.99999.1.4.0|2:numeric|function=drop_rate\n",
            ]
        )

    return lines


if __name__ == "__main__":
    # Demo usage
    print("Resource Constraint Simulation Demo")
    print("=" * 40)

    # Create test scenarios
    scenarios = create_resource_test_scenarios()

    for name, simulator in scenarios.items():
        print(f"\nScenario: {name}")
        print(f"  Max CPU: {simulator.limits.max_cpu_percent}%")
        print(f"  Max Memory: {simulator.limits.max_memory_percent}%")
        print(f"  Max Concurrent: {simulator.limits.max_concurrent_requests}")
        print(f"  Max PDU Size: {simulator.limits.max_pdu_size} bytes")

        # Test a few requests
        for i in range(5):
            allowed, reason = simulator.check_request_allowed()
            print(f"  Request {i+1}: {'✓' if allowed else '✗'} ({reason})")
            if allowed:
                simulator.complete_request()

    # Show performance stats
    print(f"\nPerformance Stats for 'moderate_load':")
    stats = scenarios["moderate_load"].get_performance_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
