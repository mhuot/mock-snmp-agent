#!/usr/bin/env python3
"""
Device-Specific State Definitions

This module provides predefined state definitions for different types
of network devices and systems.
"""

from typing import Dict, List

from .core import DeviceStateMachine, StateDefinition


def create_router_states() -> List[StateDefinition]:
    """Create state definitions for a network router.

    Returns:
        List of router state definitions
    """
    return [
        StateDefinition(
            name="booting",
            description="Router is booting up",
            duration_seconds=45,
            oid_availability=20.0,  # Limited OIDs during boot
            response_delay_ms=500,
            error_rate=25.0,
            next_states=["operational", "boot_failure"],
            transition_probabilities={"operational": 0.9, "boot_failure": 0.1},
            oid_overrides={
                "1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Booting",  # sysDescr
                "1.3.6.1.2.1.1.3.0": "67:0",  # sysUpTime (0 during boot)
            },
        ),
        StateDefinition(
            name="operational",
            description="Router is operating normally",
            duration_seconds=1800,  # 30 minutes
            oid_availability=100.0,
            response_delay_ms=25,
            error_rate=1.0,
            next_states=["maintenance", "degraded", "overloaded", "rebooting"],
            transition_probabilities={
                "maintenance": 0.1,
                "degraded": 0.15,
                "overloaded": 0.05,
                "rebooting": 0.02,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Operational"},
        ),
        StateDefinition(
            name="degraded",
            description="Router performance is degraded",
            duration_seconds=300,  # 5 minutes
            oid_availability=85.0,
            response_delay_ms=150,
            error_rate=10.0,
            next_states=["operational", "failed", "rebooting"],
            transition_probabilities={
                "operational": 0.7,
                "failed": 0.2,
                "rebooting": 0.1,
            },
            oid_overrides={
                "1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Performance Degraded"
            },
        ),
        StateDefinition(
            name="overloaded",
            description="Router is overloaded with traffic",
            duration_seconds=180,  # 3 minutes
            oid_availability=70.0,
            response_delay_ms=300,
            error_rate=20.0,
            next_states=["operational", "degraded", "failed"],
            transition_probabilities={
                "operational": 0.4,
                "degraded": 0.4,
                "failed": 0.2,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Overloaded"},
        ),
        StateDefinition(
            name="maintenance",
            description="Router is in maintenance mode",
            duration_seconds=600,  # 10 minutes
            oid_availability=60.0,
            response_delay_ms=100,
            error_rate=5.0,
            next_states=["operational", "rebooting"],
            transition_probabilities={"operational": 0.8, "rebooting": 0.2},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Maintenance Mode"},
        ),
        StateDefinition(
            name="failed",
            description="Router has failed",
            duration_seconds=None,  # Manual recovery required
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["rebooting"],
            transition_probabilities={},
            oid_overrides={},
        ),
        StateDefinition(
            name="boot_failure",
            description="Router failed to boot properly",
            duration_seconds=60,
            oid_availability=5.0,
            response_delay_ms=1000,
            error_rate=90.0,
            next_states=["rebooting", "failed"],
            transition_probabilities={"rebooting": 0.7, "failed": 0.3},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Cisco IOS Router - Boot Failure"},
        ),
        StateDefinition(
            name="rebooting",
            description="Router is rebooting",
            duration_seconds=20,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["booting"],
            transition_probabilities={"booting": 1.0},
            oid_overrides={},
        ),
    ]


def create_switch_states() -> List[StateDefinition]:
    """Create state definitions for a network switch.

    Returns:
        List of switch state definitions
    """
    return [
        StateDefinition(
            name="booting",
            description="Switch is booting up",
            duration_seconds=30,
            oid_availability=25.0,
            response_delay_ms=300,
            error_rate=20.0,
            next_states=["operational", "boot_failure"],
            transition_probabilities={"operational": 0.95, "boot_failure": 0.05},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Catalyst Switch - Booting"},
        ),
        StateDefinition(
            name="operational",
            description="Switch is operating normally",
            duration_seconds=3600,  # 1 hour
            oid_availability=100.0,
            response_delay_ms=15,
            error_rate=0.5,
            next_states=["spanning_tree_convergence", "port_flapping", "rebooting"],
            transition_probabilities={
                "spanning_tree_convergence": 0.1,
                "port_flapping": 0.05,
                "rebooting": 0.01,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Catalyst Switch - Operational"},
        ),
        StateDefinition(
            name="spanning_tree_convergence",
            description="Switch is converging spanning tree",
            duration_seconds=60,
            oid_availability=90.0,
            response_delay_ms=75,
            error_rate=8.0,
            next_states=["operational"],
            transition_probabilities={"operational": 1.0},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Catalyst Switch - STP Convergence"},
        ),
        StateDefinition(
            name="port_flapping",
            description="Switch has flapping ports",
            duration_seconds=120,
            oid_availability=95.0,
            response_delay_ms=50,
            error_rate=3.0,
            next_states=["operational", "failed"],
            transition_probabilities={"operational": 0.9, "failed": 0.1},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Catalyst Switch - Port Flapping"},
        ),
        StateDefinition(
            name="failed",
            description="Switch has failed",
            duration_seconds=None,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["rebooting"],
            transition_probabilities={},
            oid_overrides={},
        ),
        StateDefinition(
            name="boot_failure",
            description="Switch failed to boot",
            duration_seconds=45,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["rebooting", "failed"],
            transition_probabilities={"rebooting": 0.8, "failed": 0.2},
            oid_overrides={},
        ),
        StateDefinition(
            name="rebooting",
            description="Switch is rebooting",
            duration_seconds=15,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["booting"],
            transition_probabilities={"booting": 1.0},
            oid_overrides={},
        ),
    ]


def create_server_states() -> List[StateDefinition]:
    """Create state definitions for a server.

    Returns:
        List of server state definitions
    """
    return [
        StateDefinition(
            name="booting",
            description="Server is booting up",
            duration_seconds=120,  # Servers take longer to boot
            oid_availability=15.0,
            response_delay_ms=800,
            error_rate=30.0,
            next_states=["operational", "boot_failure"],
            transition_probabilities={"operational": 0.92, "boot_failure": 0.08},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - Booting"},
        ),
        StateDefinition(
            name="operational",
            description="Server is operating normally",
            duration_seconds=7200,  # 2 hours
            oid_availability=100.0,
            response_delay_ms=30,
            error_rate=0.5,
            next_states=["high_load", "maintenance", "backup_running", "rebooting"],
            transition_probabilities={
                "high_load": 0.2,
                "maintenance": 0.05,
                "backup_running": 0.1,
                "rebooting": 0.005,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - Operational"},
        ),
        StateDefinition(
            name="high_load",
            description="Server under high CPU/memory load",
            duration_seconds=900,  # 15 minutes
            oid_availability=95.0,
            response_delay_ms=200,
            error_rate=8.0,
            next_states=["operational", "overloaded", "maintenance"],
            transition_probabilities={
                "operational": 0.7,
                "overloaded": 0.2,
                "maintenance": 0.1,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - High Load"},
        ),
        StateDefinition(
            name="overloaded",
            description="Server is severely overloaded",
            duration_seconds=300,
            oid_availability=80.0,
            response_delay_ms=500,
            error_rate=25.0,
            next_states=["operational", "failed", "rebooting"],
            transition_probabilities={
                "operational": 0.5,
                "failed": 0.3,
                "rebooting": 0.2,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - Overloaded"},
        ),
        StateDefinition(
            name="backup_running",
            description="Server is running backup operations",
            duration_seconds=1800,  # 30 minutes
            oid_availability=100.0,
            response_delay_ms=100,
            error_rate=2.0,
            next_states=["operational"],
            transition_probabilities={"operational": 1.0},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - Backup Running"},
        ),
        StateDefinition(
            name="maintenance",
            description="Server in maintenance mode",
            duration_seconds=1200,  # 20 minutes
            oid_availability=70.0,
            response_delay_ms=150,
            error_rate=3.0,
            next_states=["operational", "rebooting"],
            transition_probabilities={"operational": 0.8, "rebooting": 0.2},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "Linux Server - Maintenance"},
        ),
        StateDefinition(
            name="failed",
            description="Server has failed",
            duration_seconds=None,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["rebooting"],
            transition_probabilities={},
            oid_overrides={},
        ),
        StateDefinition(
            name="boot_failure",
            description="Server failed to boot",
            duration_seconds=180,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["rebooting", "failed"],
            transition_probabilities={"rebooting": 0.6, "failed": 0.4},
            oid_overrides={},
        ),
        StateDefinition(
            name="rebooting",
            description="Server is rebooting",
            duration_seconds=60,
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["booting"],
            transition_probabilities={"booting": 1.0},
            oid_overrides={},
        ),
    ]


def create_printer_states() -> List[StateDefinition]:
    """Create state definitions for a network printer.

    Returns:
        List of printer state definitions
    """
    return [
        StateDefinition(
            name="ready",
            description="Printer is ready to print",
            duration_seconds=1200,  # 20 minutes
            oid_availability=100.0,
            response_delay_ms=50,
            error_rate=1.0,
            next_states=["printing", "paper_jam", "low_toner", "offline"],
            transition_probabilities={
                "printing": 0.6,
                "paper_jam": 0.05,
                "low_toner": 0.1,
                "offline": 0.02,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Ready"},
        ),
        StateDefinition(
            name="printing",
            description="Printer is actively printing",
            duration_seconds=180,  # 3 minutes
            oid_availability=100.0,
            response_delay_ms=75,
            error_rate=2.0,
            next_states=["ready", "paper_jam", "out_of_paper"],
            transition_probabilities={
                "ready": 0.9,
                "paper_jam": 0.05,
                "out_of_paper": 0.05,
            },
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Printing"},
        ),
        StateDefinition(
            name="paper_jam",
            description="Printer has a paper jam",
            duration_seconds=None,  # Manual intervention required
            oid_availability=100.0,
            response_delay_ms=25,
            error_rate=0.0,
            next_states=["ready"],
            transition_probabilities={},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Paper Jam"},
        ),
        StateDefinition(
            name="out_of_paper",
            description="Printer is out of paper",
            duration_seconds=None,  # Manual intervention required
            oid_availability=100.0,
            response_delay_ms=25,
            error_rate=0.0,
            next_states=["ready"],
            transition_probabilities={},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Out of Paper"},
        ),
        StateDefinition(
            name="low_toner",
            description="Printer has low toner",
            duration_seconds=3600,  # 1 hour before critical
            oid_availability=100.0,
            response_delay_ms=50,
            error_rate=1.0,
            next_states=["ready", "out_of_toner"],
            transition_probabilities={"ready": 0.7, "out_of_toner": 0.3},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Low Toner"},
        ),
        StateDefinition(
            name="out_of_toner",
            description="Printer is out of toner",
            duration_seconds=None,  # Manual intervention required
            oid_availability=100.0,
            response_delay_ms=25,
            error_rate=0.0,
            next_states=["ready"],
            transition_probabilities={},
            oid_overrides={"1.3.6.1.2.1.1.1.0": "HP LaserJet - Out of Toner"},
        ),
        StateDefinition(
            name="offline",
            description="Printer is offline",
            duration_seconds=300,  # 5 minutes
            oid_availability=0.0,
            response_delay_ms=0,
            error_rate=100.0,
            next_states=["ready"],
            transition_probabilities={"ready": 1.0},
            oid_overrides={},
        ),
    ]


def create_device_state_machine(
    device_type: str, initial_state: str = None
) -> DeviceStateMachine:
    """Create a preconfigured state machine for a device type.

    Args:
        device_type: Type of device (router, switch, server, printer)
        initial_state: Initial state (defaults to appropriate state for device type)

    Returns:
        Configured DeviceStateMachine instance

    Raises:
        ValueError: If device_type is not supported
    """
    device_type = device_type.lower()

    # Define state generators and default initial states
    state_generators = {
        "router": (create_router_states, "booting"),
        "switch": (create_switch_states, "booting"),
        "server": (create_server_states, "booting"),
        "printer": (create_printer_states, "ready"),
        "generic": (
            lambda: [],
            "operational",
        ),  # Generic device with no predefined states
    }

    if device_type not in state_generators:
        raise ValueError(
            f"Unsupported device type: {device_type}. "
            f"Supported types: {', '.join(state_generators.keys())}"
        )

    state_generator, default_initial_state = state_generators[device_type]

    # Use provided initial state or default
    if initial_state is None:
        initial_state = default_initial_state

    # Create state machine
    state_machine = DeviceStateMachine(
        device_type=device_type, initial_state=initial_state
    )

    # Add states for non-generic devices
    if device_type != "generic":
        for state in state_generator():
            state_machine.add_state(state)

    return state_machine


def get_supported_device_types() -> List[str]:
    """Get list of supported device types.

    Returns:
        List of supported device type names
    """
    return ["router", "switch", "server", "printer", "generic"]


def get_device_type_info() -> Dict[str, Dict[str, str]]:
    """Get information about supported device types.

    Returns:
        Dictionary with device type information
    """
    return {
        "router": {
            "description": "Network router with routing and interface states",
            "default_initial_state": "booting",
            "typical_states": "booting, operational, degraded, overloaded, maintenance, failed, rebooting",
        },
        "switch": {
            "description": "Network switch with layer 2 switching states",
            "default_initial_state": "booting",
            "typical_states": "booting, operational, spanning_tree_convergence, port_flapping, failed, rebooting",
        },
        "server": {
            "description": "Server with load and maintenance states",
            "default_initial_state": "booting",
            "typical_states": "booting, operational, high_load, overloaded, backup_running, maintenance, failed, rebooting",
        },
        "printer": {
            "description": "Network printer with consumables and jam states",
            "default_initial_state": "ready",
            "typical_states": "ready, printing, paper_jam, out_of_paper, low_toner, out_of_toner, offline",
        },
        "generic": {
            "description": "Generic device with customizable states",
            "default_initial_state": "operational",
            "typical_states": "user-defined",
        },
    }
