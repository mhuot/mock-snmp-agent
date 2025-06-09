#!/usr/bin/env python3
"""
Bulk operation testing for Mock SNMP Agent.

This module provides comprehensive GetBulk operation testing capabilities
including large table simulation, PDU size management, and bandwidth testing.
"""

import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BulkTestConfig:
    """Configuration for bulk operation testing."""

    table_size: int = 1000  # Number of table entries
    max_repetitions: int = 50  # GetBulk max-repetitions
    max_pdu_size: int = 1472  # Maximum PDU size in bytes
    response_delay: float = 0.0  # Delay per entry (seconds)
    enable_fragmentation: bool = True
    bandwidth_limit: Optional[int] = None  # bytes per second
    failure_probability: float = 0.0  # Probability of operation failure


class BulkOperationSimulator:
    """Simulates large table operations and GetBulk scenarios."""

    def __init__(self, config: BulkTestConfig):
        self.config = config
        self.tables = {}
        self.operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "bytes_transferred": 0,
            "start_time": time.time(),
        }

    def create_interface_table(self, num_interfaces: int = None) -> Dict[str, List]:
        """Create a large interface table for testing.

        Args:
            num_interfaces: Number of interfaces (uses config.table_size if None)

        Returns:
            Dictionary with table data
        """
        if num_interfaces is None:
            num_interfaces = self.config.table_size

        table = {
            "ifIndex": [],
            "ifDescr": [],
            "ifType": [],
            "ifMtu": [],
            "ifSpeed": [],
            "ifPhysAddress": [],
            "ifAdminStatus": [],
            "ifOperStatus": [],
            "ifInOctets": [],
            "ifOutOctets": [],
            "ifInUcastPkts": [],
            "ifOutUcastPkts": [],
            "ifInDiscards": [],
            "ifOutDiscards": [],
            "ifInErrors": [],
            "ifOutErrors": [],
        }

        interface_types = [
            "ethernet-csmacd",
            "gigabitEthernet",
            "tunnel",
            "loopback",
            "ppp",
            "frameRelay",
        ]

        speeds = [10000000, 100000000, 1000000000, 10000000000]  # 10M, 100M, 1G, 10G

        for i in range(1, num_interfaces + 1):
            table["ifIndex"].append(i)
            table["ifDescr"].append(f"Interface {i}")
            table["ifType"].append(random.choice(interface_types))
            table["ifMtu"].append(1500)
            table["ifSpeed"].append(random.choice(speeds))
            table["ifPhysAddress"].append(
                ":".join([f"{random.randint(0,255):02x}" for _ in range(6)])
            )
            table["ifAdminStatus"].append(random.choice(["up", "down", "testing"]))
            table["ifOperStatus"].append(random.choice(["up", "down", "testing"]))

            # Counter values (simulate realistic traffic)
            base_octets = random.randint(1000000, 1000000000)
            table["ifInOctets"].append(base_octets + random.randint(0, 100000))
            table["ifOutOctets"].append(base_octets + random.randint(0, 100000))

            base_packets = base_octets // 1000
            table["ifInUcastPkts"].append(base_packets + random.randint(0, 1000))
            table["ifOutUcastPkts"].append(base_packets + random.randint(0, 1000))

            # Error counters (usually small)
            table["ifInDiscards"].append(random.randint(0, 100))
            table["ifOutDiscards"].append(random.randint(0, 100))
            table["ifInErrors"].append(random.randint(0, 50))
            table["ifOutErrors"].append(random.randint(0, 50))

        self.tables["ifTable"] = table
        return table

    def simulate_getbulk_operation(
        self, start_oid: str, max_repetitions: int = None, non_repeaters: int = 0
    ) -> Tuple[bool, Dict]:
        """Simulate a GetBulk operation.

        Args:
            start_oid: Starting OID for the bulk operation
            max_repetitions: Maximum repetitions (uses config if None)
            non_repeaters: Number of non-repeater varbinds

        Returns:
            (success, result_info) tuple
        """
        if max_repetitions is None:
            max_repetitions = self.config.max_repetitions

        self.operation_stats["total_operations"] += 1

        # Check for simulated failure
        if random.random() < self.config.failure_probability:
            self.operation_stats["failed_operations"] += 1
            return False, {"error": "genErr", "reason": "Simulated operation failure"}

        # Simulate response generation
        response_entries = []
        estimated_size = 0

        # For interface table operations
        if "1.3.6.1.2.1.2.2.1" in start_oid and "ifTable" in self.tables:
            table = self.tables["ifTable"]

            # Determine which column we're starting from
            oid_parts = start_oid.split(".")
            if len(oid_parts) >= 11:
                column = int(oid_parts[10])
                start_index = int(oid_parts[11]) if len(oid_parts) > 11 else 1
            else:
                column = 1
                start_index = 1

            # Generate response entries
            entries_added = 0
            current_column = column
            current_index = start_index

            while entries_added < max_repetitions:
                if current_index > len(table["ifIndex"]):
                    current_column += 1
                    current_index = 1

                    # Check if we've gone beyond available columns
                    if current_column > 16:  # ifTable has 16 columns
                        break

                # Create response entry
                oid = f"1.3.6.1.2.1.2.2.1.{current_column}.{current_index}"
                value = self._get_table_value(table, current_column, current_index - 1)

                entry = {
                    "oid": oid,
                    "type": self._get_snmp_type(current_column),
                    "value": value,
                }

                response_entries.append(entry)
                estimated_size += len(str(value)) + len(oid) + 20  # Rough estimate

                # Check PDU size limit
                if estimated_size > self.config.max_pdu_size:
                    break

                entries_added += 1
                current_index += 1

                # Add response delay if configured
                if self.config.response_delay > 0:
                    time.sleep(self.config.response_delay)

        # Bandwidth limiting
        if self.config.bandwidth_limit:
            transfer_time = estimated_size / self.config.bandwidth_limit
            time.sleep(transfer_time)

        self.operation_stats["successful_operations"] += 1
        self.operation_stats["bytes_transferred"] += estimated_size

        return True, {
            "entries": response_entries,
            "entry_count": len(response_entries),
            "estimated_size": estimated_size,
            "max_repetitions_requested": max_repetitions,
            "truncated": len(response_entries) < max_repetitions,
        }

    def _get_table_value(self, table: Dict, column: int, index: int):
        """Get value from table based on column and index."""
        column_map = {
            1: "ifIndex",
            2: "ifDescr",
            3: "ifType",
            4: "ifMtu",
            5: "ifSpeed",
            6: "ifPhysAddress",
            7: "ifAdminStatus",
            8: "ifOperStatus",
            10: "ifInOctets",
            16: "ifOutOctets",
            11: "ifInUcastPkts",
            17: "ifOutUcastPkts",
            13: "ifInDiscards",
            19: "ifOutDiscards",
            14: "ifInErrors",
            20: "ifOutErrors",
        }

        column_name = column_map.get(column, "ifIndex")
        if column_name in table and index < len(table[column_name]):
            return table[column_name][index]
        return 0

    def _get_snmp_type(self, column: int) -> str:
        """Get SNMP type for table column."""
        type_map = {
            1: "2",  # ifIndex - INTEGER
            2: "4",  # ifDescr - OCTET STRING
            3: "2",  # ifType - INTEGER
            4: "2",  # ifMtu - INTEGER
            5: "66",  # ifSpeed - Gauge32
            6: "4",  # ifPhysAddress - OCTET STRING
            7: "2",  # ifAdminStatus - INTEGER
            8: "2",  # ifOperStatus - INTEGER
            10: "65",  # ifInOctets - Counter32
            16: "65",  # ifOutOctets - Counter32
            11: "65",  # ifInUcastPkts - Counter32
            17: "65",  # ifOutUcastPkts - Counter32
            13: "65",  # ifInDiscards - Counter32
            19: "65",  # ifOutDiscards - Counter32
            14: "65",  # ifInErrors - Counter32
            20: "65",  # ifOutErrors - Counter32
        }
        return type_map.get(column, "2")

    def get_operation_statistics(self) -> Dict:
        """Get bulk operation statistics."""
        uptime = time.time() - self.operation_stats["start_time"]

        return {
            **self.operation_stats,
            "uptime_seconds": uptime,
            "success_rate": (
                self.operation_stats["successful_operations"]
                / max(self.operation_stats["total_operations"], 1)
            )
            * 100,
            "operations_per_second": (
                self.operation_stats["total_operations"] / max(uptime, 1)
            ),
            "bytes_per_second": (
                self.operation_stats["bytes_transferred"] / max(uptime, 1)
            ),
            "average_response_size": (
                self.operation_stats["bytes_transferred"]
                / max(self.operation_stats["successful_operations"], 1)
            ),
        }


def generate_bulk_test_snmprec(
    config: BulkTestConfig, output_file: Path, num_interfaces: int = None
) -> None:
    """Generate .snmprec file for bulk operation testing.

    Args:
        config: Bulk test configuration
        output_file: Output .snmprec file path
        num_interfaces: Number of interfaces to generate
    """
    if num_interfaces is None:
        num_interfaces = config.table_size

    simulator = BulkOperationSimulator(config)
    table = simulator.create_interface_table(num_interfaces)

    lines = []

    # Generate interface table entries
    for i, interface_index in enumerate(table["ifIndex"]):
        lines.extend(
            [
                f"1.3.6.1.2.1.2.2.1.1.{interface_index}|2|{interface_index}\n",
                f"1.3.6.1.2.1.2.2.1.2.{interface_index}|4|{table['ifDescr'][i]}\n",
                f"1.3.6.1.2.1.2.2.1.3.{interface_index}|2|6\n",  # ethernet-csmacd
                f"1.3.6.1.2.1.2.2.1.4.{interface_index}|2|{table['ifMtu'][i]}\n",
                f"1.3.6.1.2.1.2.2.1.5.{interface_index}|66|{table['ifSpeed'][i]}\n",
                f"1.3.6.1.2.1.2.2.1.6.{interface_index}|4|{table['ifPhysAddress'][i]}\n",
                f"1.3.6.1.2.1.2.2.1.7.{interface_index}|2|1\n",  # up
                f"1.3.6.1.2.1.2.2.1.8.{interface_index}|2|1\n",  # up
                f"1.3.6.1.2.1.2.2.1.10.{interface_index}|65|{table['ifInOctets'][i]}\n",
                f"1.3.6.1.2.1.2.2.1.16.{interface_index}|65|{table['ifOutOctets'][i]}\n",
            ]
        )

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    # Demo usage
    print("Bulk Operation Testing Demo")
    print("=" * 30)

    # Create test configuration
    config = BulkTestConfig(
        table_size=100,
        max_repetitions=25,
        max_pdu_size=1472,
        response_delay=0.001,  # 1ms per entry
        failure_probability=0.05,  # 5% failure rate
    )

    # Create simulator
    simulator = BulkOperationSimulator(config)
    table = simulator.create_interface_table(10)

    print(f"Created interface table with {len(table['ifIndex'])} entries")

    # Simulate some GetBulk operations
    for i in range(5):
        success, result = simulator.simulate_getbulk_operation(
            "1.3.6.1.2.1.2.2.1.1.1", max_repetitions=10  # Start from ifIndex.1
        )

        if success:
            print(
                f"Operation {i+1}: ✓ {result['entry_count']} entries, "
                f"{result['estimated_size']} bytes"
            )
        else:
            print(f"Operation {i+1}: ✗ {result['error']} - {result['reason']}")

    # Show statistics
    stats = simulator.get_operation_statistics()
    print(f"\nOperations Statistics:")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
    print(f"  Bytes/sec: {stats['bytes_per_second']:.0f}")
    print(f"  Avg response size: {stats['average_response_size']:.0f} bytes")
