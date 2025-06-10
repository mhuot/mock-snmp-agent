#!/usr/bin/env python3
"""
Counter wrap simulation for Mock SNMP Agent.

This module provides sophisticated counter wrap testing capabilities
for validating SNMP monitoring systems against counter overflow scenarios.
"""

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class CounterConfig:
    """Configuration for a counter wrap scenario."""

    oid: str
    counter_type: str  # "32bit" or "64bit"
    initial_value: int = 0
    increment_rate: int = 1000  # per second
    acceleration_factor: int = 1  # Speed up for testing
    max_value: Optional[int] = None

    def __post_init__(self):
        if self.max_value is None:
            if self.counter_type == "32bit":
                self.max_value = 2**32 - 1  # 4,294,967,295
            else:  # 64bit
                self.max_value = 2**64 - 1


class CounterWrapSimulator:
    """Manages counter wrap simulation for multiple OIDs."""

    def __init__(self):
        self.counters: Dict[str, CounterConfig] = {}
        self.start_time = time.time()
        self.last_update = self.start_time

    def add_counter(self, config: CounterConfig) -> None:
        """Add a counter for simulation."""
        self.counters[config.oid] = config

    def get_current_value(self, oid: str) -> int:
        """Get current counter value with wrap handling."""
        if oid not in self.counters:
            return 0

        config = self.counters[oid]
        current_time = time.time()
        elapsed_seconds = current_time - self.start_time

        # Calculate raw increment
        raw_increment = int(
            elapsed_seconds * config.increment_rate * config.acceleration_factor
        )

        # Apply wrapping
        current_value = (config.initial_value + raw_increment) % (config.max_value + 1)

        return current_value

    def get_wrap_info(self, oid: str) -> Dict:
        """Get detailed wrap information for a counter."""
        if oid not in self.counters:
            return {}

        config = self.counters[oid]
        current_time = time.time()
        elapsed_seconds = current_time - self.start_time

        # Calculate wrap statistics
        total_increments = int(
            elapsed_seconds * config.increment_rate * config.acceleration_factor
        )

        wrap_count = total_increments // (config.max_value + 1)
        current_value = total_increments % (config.max_value + 1)

        # Time to next wrap
        next_wrap_increments = (config.max_value + 1) - current_value
        seconds_to_next_wrap = next_wrap_increments / (
            config.increment_rate * config.acceleration_factor
        )

        return {
            "oid": oid,
            "current_value": current_value,
            "wrap_count": wrap_count,
            "seconds_to_next_wrap": seconds_to_next_wrap,
            "total_elapsed": elapsed_seconds,
            "counter_type": config.counter_type,
            "max_value": config.max_value,
            "acceleration_factor": config.acceleration_factor,
        }


def generate_interface_counters(
    num_interfaces: int = 10, interface_speeds: List[str] = None
) -> List[CounterConfig]:
    """Generate realistic interface counter configurations.

    Args:
        num_interfaces: Number of interfaces to simulate
        interface_speeds: List of speeds ["10M", "100M", "1G", "10G"]

    Returns:
        List of counter configurations
    """
    if interface_speeds is None:
        interface_speeds = ["100M", "1G", "10G"]

    # Speed to bytes/second mapping
    speed_map = {
        "10M": 1_250_000,  # 10 Mbps = 1.25 MB/s
        "100M": 12_500_000,  # 100 Mbps = 12.5 MB/s
        "1G": 125_000_000,  # 1 Gbps = 125 MB/s
        "10G": 1_250_000_000,  # 10 Gbps = 1.25 GB/s
    }

    counters = []

    for i in range(1, num_interfaces + 1):
        speed = interface_speeds[i % len(interface_speeds)]
        bytes_per_sec = speed_map[speed]

        # ifInOctets counter
        in_counter = CounterConfig(
            oid=f"1.3.6.1.2.1.2.2.1.10.{i}",  # ifInOctets
            counter_type="32bit",
            increment_rate=int(bytes_per_sec * 0.7),  # 70% utilization
            acceleration_factor=1000,  # Speed up for testing
        )
        counters.append(in_counter)

        # ifOutOctets counter
        out_counter = CounterConfig(
            oid=f"1.3.6.1.2.1.2.2.1.16.{i}",  # ifOutOctets
            counter_type="32bit",
            increment_rate=int(bytes_per_sec * 0.5),  # 50% utilization
            acceleration_factor=1000,
        )
        counters.append(out_counter)

    return counters


def generate_counter_snmprec(
    simulator: CounterWrapSimulator, output_file: Path, base_snmprec: Path = None
) -> None:
    """Generate .snmprec file with counter wrap behavior.

    Args:
        simulator: Counter wrap simulator instance
        output_file: Output .snmprec file path
        base_snmprec: Base .snmprec file to extend (optional)
    """
    lines = []

    # Copy base file if provided
    if base_snmprec and base_snmprec.exists():
        with open(base_snmprec, encoding="utf-8") as f:
            lines.extend(f.readlines())

    # Add counter entries
    for oid, config in simulator.counters.items():
        # Use numeric variation module for dynamic counters
        line = (
            f"{oid}|65:numeric|function=counter,rate={config.increment_rate},"
            f"max={config.max_value},acceleration={config.acceleration_factor}\n"
        )
        lines.append(line)

    # Write output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


def create_wrap_test_scenario(scenario_name: str = "counter_wrap_test") -> Dict:
    """Create a comprehensive counter wrap test scenario.

    Returns:
        Dictionary with scenario configuration and simulator
    """
    simulator = CounterWrapSimulator()

    # Add various interface speeds for different wrap times
    interface_configs = generate_interface_counters(
        num_interfaces=5, interface_speeds=["10M", "100M", "1G", "10G"]
    )

    for config in interface_configs:
        simulator.add_counter(config)

    # Add some system counters
    system_counters = [
        CounterConfig(
            oid="1.3.6.1.2.1.1.3.0",  # sysUpTime
            counter_type="32bit",
            increment_rate=100,  # centiseconds
            acceleration_factor=100,
        ),
        CounterConfig(
            oid="1.3.6.1.2.1.11.1.0",  # snmpInPkts
            counter_type="32bit",
            increment_rate=50,
            acceleration_factor=500,
        ),
    ]

    for config in system_counters:
        simulator.add_counter(config)

    return {
        "name": scenario_name,
        "simulator": simulator,
        "description": "Counter wrap testing with multiple interface speeds",
        "wrap_times": {
            "10M": "57.2 minutes (accelerated: 3.4 seconds)",
            "100M": "5.7 minutes (accelerated: 0.34 seconds)",
            "1G": "34 seconds (accelerated: 0.034 seconds)",
            "10G": "3.4 seconds (accelerated: 0.0034 seconds)",
        },
    }


if __name__ == "__main__":
    # Demo usage
    scenario = create_wrap_test_scenario()
    simulator = scenario["simulator"]

    print(f"Counter Wrap Test Scenario: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print("\nExpected wrap times:")
    for speed, time_info in scenario["wrap_times"].items():
        print(f"  {speed}: {time_info}")

    print(f"\nSimulating {len(simulator.counters)} counters...")

    # Show initial values
    for oid in simulator.counters:
        info = simulator.get_wrap_info(oid)
        print(f"\n{oid}:")
        print(f"  Current value: {info['current_value']:,}")
        print(f"  Wraps so far: {info['wrap_count']}")
        print(f"  Time to next wrap: {info['seconds_to_next_wrap']:.2f}s")
        print(f"  Acceleration factor: {info['acceleration_factor']}x")
