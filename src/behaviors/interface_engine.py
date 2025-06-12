#!/usr/bin/env python3
"""
Interface State Engine for Mock SNMP Agent.

This module provides dynamic interface state management including
link state changes, speed negotiation, and event-driven behavior.
"""

import random
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .ifxtable import AdminStatus, IfXTableSimulator, OperStatus


class StateChangeEvent(Enum):
    """Types of interface state change events."""

    LINK_UP = "link_up"
    LINK_DOWN = "link_down"
    SPEED_CHANGE = "speed_change"
    ADMIN_STATUS_CHANGE = "admin_status_change"
    ERROR_THRESHOLD_EXCEEDED = "error_threshold_exceeded"
    UTILIZATION_SPIKE = "utilization_spike"


@dataclass
class InterfaceEvent:
    """Interface state change event."""

    interface_index: int
    event_type: StateChangeEvent
    timestamp: float
    old_value: Any
    new_value: Any
    metadata: Dict[str, Any]


class InterfaceStateEngine:
    """Manages dynamic interface state changes and lifecycle events."""

    def __init__(self, ifxtable_simulator: IfXTableSimulator):
        self.simulator = ifxtable_simulator
        self.event_handlers: Dict[StateChangeEvent, List[Callable]] = {}
        self.scheduled_events: List[Dict] = []
        self.running = False
        self.event_thread = None
        self.event_history: List[InterfaceEvent] = []

        # State tracking
        self.interface_states: Dict[int, Dict[str, Any]] = {}
        self.link_flap_schedules: Dict[int, Dict] = {}
        self.speed_change_schedules: Dict[int, Dict] = {}

        # Event generation settings
        self.enable_random_events = True
        self.random_event_probability = 0.001  # Per interface per second
        self.max_event_history = 1000

    def register_event_handler(
        self, event_type: StateChangeEvent, handler: Callable
    ) -> None:
        """Register an event handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def start(self) -> None:
        """Start the interface state engine."""
        if self.running:
            return

        self.running = True
        self.event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self.event_thread.start()
        print("Interface State Engine started")

    def stop(self) -> None:
        """Stop the interface state engine."""
        self.running = False
        if self.event_thread:
            self.event_thread.join(timeout=5)
        print("Interface State Engine stopped")

    def _event_loop(self) -> None:
        """Main event processing loop."""
        while self.running:
            try:
                current_time = time.time()

                # Process scheduled events
                self._process_scheduled_events(current_time)

                # Generate random events if enabled
                if self.enable_random_events:
                    self._generate_random_events(current_time)

                # Process link flap schedules
                self._process_link_flap_schedules(current_time)

                # Process speed change schedules
                self._process_speed_change_schedules(current_time)

                # Monitor for threshold-based events
                self._monitor_threshold_events(current_time)

                # Sleep for a short interval
                time.sleep(1)

            except Exception as e:
                print(f"Error in interface state engine: {e}")
                time.sleep(5)

    def _process_scheduled_events(self, current_time: float) -> None:
        """Process events that are scheduled to occur."""
        events_to_remove = []

        for i, event in enumerate(self.scheduled_events):
            if current_time >= event["scheduled_time"]:
                try:
                    self._execute_event(event)
                    events_to_remove.append(i)
                except Exception as e:
                    print(f"Error executing scheduled event: {e}")
                    events_to_remove.append(i)

        # Remove processed events (in reverse order to maintain indices)
        for i in reversed(events_to_remove):
            self.scheduled_events.pop(i)

    def _generate_random_events(self, current_time: float) -> None:
        """Generate random interface events."""
        for interface_index in self.simulator.interfaces:
            if random.random() < self.random_event_probability:
                event_types = [
                    StateChangeEvent.LINK_DOWN,
                    StateChangeEvent.SPEED_CHANGE,
                    StateChangeEvent.UTILIZATION_SPIKE,
                ]

                event_type = random.choice(event_types)
                self._generate_event(interface_index, event_type)

    def _process_link_flap_schedules(self, current_time: float) -> None:
        """Process scheduled link flap events."""
        for interface_index, schedule in list(self.link_flap_schedules.items()):
            if current_time >= schedule["next_flap_time"]:
                self.simulate_link_flap(
                    interface_index, schedule.get("down_duration", 30)
                )

                # Schedule next flap
                schedule["next_flap_time"] = current_time + schedule.get(
                    "flap_interval", 3600
                )

    def _process_speed_change_schedules(self, current_time: float) -> None:
        """Process scheduled speed change events."""
        for interface_index, schedule in list(self.speed_change_schedules.items()):
            if current_time >= schedule["next_change_time"]:
                speeds = schedule.get("speed_sequence", [100, 1000, 10000])
                current_speed_idx = schedule.get("current_speed_index", 0)
                next_speed_idx = (current_speed_idx + 1) % len(speeds)

                self.change_interface_speed(interface_index, speeds[next_speed_idx])

                schedule["current_speed_index"] = next_speed_idx
                schedule["next_change_time"] = current_time + schedule.get(
                    "change_interval", 600
                )

    def _monitor_threshold_events(self, current_time: float) -> None:
        """Monitor interfaces for threshold-based events."""
        for interface_index in self.simulator.interfaces:
            state = self.simulator.get_interface_state(interface_index)
            if not state:
                continue

            utilization = state.get("current_utilization", 0)

            # Check for utilization spikes
            if utilization > 0.9:
                last_spike = self.interface_states.get(interface_index, {}).get(
                    "last_utilization_spike", 0
                )
                if (
                    current_time - last_spike > 300
                ):  # Don't trigger more than once per 5 minutes
                    self._fire_event(
                        interface_index,
                        StateChangeEvent.UTILIZATION_SPIKE,
                        old_value=None,
                        new_value=utilization,
                    )

                    if interface_index not in self.interface_states:
                        self.interface_states[interface_index] = {}
                    self.interface_states[interface_index][
                        "last_utilization_spike"
                    ] = current_time

    def _generate_event(
        self, interface_index: int, event_type: StateChangeEvent
    ) -> None:
        """Generate a specific type of event for an interface."""
        if event_type == StateChangeEvent.LINK_DOWN:
            self.simulate_link_flap(interface_index, random.randint(10, 120))

        elif event_type == StateChangeEvent.SPEED_CHANGE:
            current_speed = self.simulator.interfaces[interface_index].speed_mbps
            possible_speeds = [10, 100, 1000, 10000]
            new_speeds = [s for s in possible_speeds if s != current_speed]
            if new_speeds:
                new_speed = random.choice(new_speeds)
                self.change_interface_speed(interface_index, new_speed)

        elif event_type == StateChangeEvent.UTILIZATION_SPIKE:
            # This is handled by threshold monitoring
            pass

    def _execute_event(self, event: Dict) -> None:
        """Execute a scheduled event."""
        event_type = event["event_type"]
        interface_index = event["interface_index"]

        if event_type == StateChangeEvent.LINK_UP:
            self._restore_interface_after_flap(interface_index)

        elif event_type == StateChangeEvent.SPEED_CHANGE:
            new_speed = event.get("new_speed", 1000)
            self.change_interface_speed(interface_index, new_speed)

    def simulate_link_flap(self, interface_index: int, down_duration: int = 30) -> bool:
        """Simulate interface link going down and automatically coming back up."""
        if interface_index not in self.simulator.interfaces:
            return False

        interface_def = self.simulator.interfaces[interface_index]
        old_status = interface_def.oper_status

        # Change to down status
        interface_def.oper_status = OperStatus.DOWN
        self.simulator._pause_interface_counters(interface_index)

        # Fire link down event
        self._fire_event(
            interface_index,
            StateChangeEvent.LINK_DOWN,
            old_value=old_status,
            new_value=OperStatus.DOWN,
        )

        # Schedule link up event
        restore_time = time.time() + down_duration
        self.scheduled_events.append(
            {
                "scheduled_time": restore_time,
                "event_type": StateChangeEvent.LINK_UP,
                "interface_index": interface_index,
                "old_status": old_status,
            }
        )

        print(
            f"Interface {interface_index} link down - will restore in {down_duration}s"
        )
        return True

    def _restore_interface_after_flap(self, interface_index: int) -> None:
        """Restore interface to operational state after link flap."""
        if interface_index not in self.simulator.interfaces:
            return

        interface_def = self.simulator.interfaces[interface_index]
        old_status = interface_def.oper_status

        # Restore to up status
        interface_def.oper_status = OperStatus.UP
        self.simulator._resume_interface_counters(interface_index)

        # Fire link up event
        self._fire_event(
            interface_index,
            StateChangeEvent.LINK_UP,
            old_value=old_status,
            new_value=OperStatus.UP,
        )

        print(f"Interface {interface_index} link restored to UP")

    def change_interface_speed(self, interface_index: int, new_speed_mbps: int) -> bool:
        """Change interface speed and fire appropriate events."""
        if interface_index not in self.simulator.interfaces:
            return False

        interface_def = self.simulator.interfaces[interface_index]
        old_speed = interface_def.speed_mbps

        if old_speed == new_speed_mbps:
            return True  # No change needed

        # Change speed in simulator
        success = self.simulator.change_interface_speed(interface_index, new_speed_mbps)

        if success:
            # Fire speed change event
            self._fire_event(
                interface_index,
                StateChangeEvent.SPEED_CHANGE,
                old_value=old_speed,
                new_value=new_speed_mbps,
            )

        return success

    def set_admin_status(self, interface_index: int, admin_status: AdminStatus) -> bool:
        """Change interface administrative status."""
        if interface_index not in self.simulator.interfaces:
            return False

        interface_def = self.simulator.interfaces[interface_index]
        old_status = interface_def.admin_status

        if old_status == admin_status:
            return True  # No change needed

        interface_def.admin_status = admin_status

        # If admin down, set oper status to down as well
        if admin_status == AdminStatus.DOWN:
            interface_def.oper_status = OperStatus.DOWN
            self.simulator._pause_interface_counters(interface_index)
        elif (
            admin_status == AdminStatus.UP
            and interface_def.oper_status == OperStatus.DOWN
        ):
            # Only bring oper up if admin is up and there's no other issue
            interface_def.oper_status = OperStatus.UP
            self.simulator._resume_interface_counters(interface_index)

        # Fire admin status change event
        self._fire_event(
            interface_index,
            StateChangeEvent.ADMIN_STATUS_CHANGE,
            old_value=old_status,
            new_value=admin_status,
        )

        return True

    def schedule_periodic_link_flaps(
        self, interface_index: int, flap_interval: int = 3600, down_duration: int = 30
    ) -> None:
        """Schedule periodic link flaps for an interface."""
        if interface_index not in self.simulator.interfaces:
            return

        self.link_flap_schedules[interface_index] = {
            "flap_interval": flap_interval,
            "down_duration": down_duration,
            "next_flap_time": time.time() + flap_interval,
        }

        print(
            f"Scheduled periodic link flaps for interface {interface_index} "
            f"every {flap_interval}s (down for {down_duration}s)"
        )

    def schedule_periodic_speed_changes(
        self,
        interface_index: int,
        speed_sequence: List[int],
        change_interval: int = 600,
    ) -> None:
        """Schedule periodic speed changes for an interface."""
        if interface_index not in self.simulator.interfaces:
            return

        self.speed_change_schedules[interface_index] = {
            "speed_sequence": speed_sequence,
            "change_interval": change_interval,
            "current_speed_index": 0,
            "next_change_time": time.time() + change_interval,
        }

        print(
            f"Scheduled periodic speed changes for interface {interface_index}: "
            f"{speed_sequence} every {change_interval}s"
        )

    def _fire_event(
        self,
        interface_index: int,
        event_type: StateChangeEvent,
        old_value: Any,
        new_value: Any,
        metadata: Dict = None,
    ) -> None:
        """Fire an interface event and notify handlers."""
        if metadata is None:
            metadata = {}

        event = InterfaceEvent(
            interface_index=interface_index,
            event_type=event_type,
            timestamp=time.time(),
            old_value=old_value,
            new_value=new_value,
            metadata=metadata,
        )

        # Add to event history
        self.event_history.append(event)
        if len(self.event_history) > self.max_event_history:
            self.event_history.pop(0)

        # Notify handlers
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")

        print(
            f"Event fired: Interface {interface_index} {event_type.value} "
            f"({old_value} -> {new_value})"
        )

    def get_event_history(
        self,
        interface_index: Optional[int] = None,
        event_type: Optional[StateChangeEvent] = None,
        limit: int = 100,
    ) -> List[InterfaceEvent]:
        """Get event history with optional filtering."""
        events = self.event_history

        if interface_index is not None:
            events = [e for e in events if e.interface_index == interface_index]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]

    def get_interface_status_summary(self) -> Dict[int, Dict[str, Any]]:
        """Get summary of all interface statuses and scheduled events."""
        summary = {}

        for interface_index, interface_def in self.simulator.interfaces.items():
            state = self.simulator.get_interface_state(interface_index)

            summary[interface_index] = {
                "name": interface_def.name,
                "admin_status": interface_def.admin_status.name,
                "oper_status": interface_def.oper_status.name,
                "speed_mbps": interface_def.speed_mbps,
                "current_utilization": (
                    state.get("current_utilization", 0) if state else 0
                ),
                "link_flap_scheduled": interface_index in self.link_flap_schedules,
                "speed_change_scheduled": interface_index
                in self.speed_change_schedules,
                "recent_events": len(
                    [
                        e
                        for e in self.event_history[-50:]
                        if e.interface_index == interface_index
                    ]
                ),
            }

        return summary

    def simulate_network_event_scenario(self, scenario_name: str) -> None:
        """Simulate predefined network event scenarios."""
        scenarios = {
            "network_maintenance": self._simulate_maintenance_scenario,
            "power_failure": self._simulate_power_failure_scenario,
            "equipment_upgrade": self._simulate_equipment_upgrade_scenario,
            "congestion_event": self._simulate_congestion_scenario,
        }

        if scenario_name in scenarios:
            scenarios[scenario_name]()
        else:
            print(f"Unknown scenario: {scenario_name}")

    def _simulate_maintenance_scenario(self) -> None:
        """Simulate planned network maintenance."""
        print("Simulating network maintenance scenario...")

        # Take down interfaces in sequence with delays
        interface_indices = list(self.simulator.interfaces.keys())
        for i, interface_index in enumerate(
            interface_indices[:3]
        ):  # First 3 interfaces
            delay = i * 60  # 1 minute between each

            self.scheduled_events.append(
                {
                    "scheduled_time": time.time() + delay,
                    "event_type": StateChangeEvent.LINK_DOWN,
                    "interface_index": interface_index,
                    "down_duration": 300,  # 5 minutes down
                }
            )

    def _simulate_power_failure_scenario(self) -> None:
        """Simulate power failure affecting multiple interfaces."""
        print("Simulating power failure scenario...")

        # Simultaneous failure of multiple interfaces
        interface_indices = list(self.simulator.interfaces.keys())
        affected_interfaces = interface_indices[::2]  # Every other interface

        for interface_index in affected_interfaces:
            self.simulate_link_flap(interface_index, random.randint(180, 600))

    def _simulate_equipment_upgrade_scenario(self) -> None:
        """Simulate equipment upgrade with speed changes."""
        print("Simulating equipment upgrade scenario...")

        # Schedule speed upgrades for interfaces
        upgrade_schedule = [
            (1, 10000),  # Upgrade to 10G
            (2, 1000),  # Upgrade to 1G
            (3, 10000),  # Upgrade to 10G
        ]

        for i, (interface_index, new_speed) in enumerate(upgrade_schedule):
            if interface_index in self.simulator.interfaces:
                delay = i * 120  # 2 minutes between upgrades

                self.scheduled_events.append(
                    {
                        "scheduled_time": time.time() + delay,
                        "event_type": StateChangeEvent.SPEED_CHANGE,
                        "interface_index": interface_index,
                        "new_speed": new_speed,
                    }
                )

    def _simulate_congestion_scenario(self) -> None:
        """Simulate network congestion with utilization spikes."""
        print("Simulating network congestion scenario...")

        # Modify traffic patterns temporarily
        for interface_index, interface_def in self.simulator.interfaces.items():
            if interface_def.utilization_pattern != "constant_high":
                # Temporarily switch to high utilization
                original_pattern = interface_def.utilization_pattern
                interface_def.utilization_pattern = "constant_high"

                # Schedule restoration of original pattern
                self.scheduled_events.append(
                    {
                        "scheduled_time": time.time() + 1800,  # 30 minutes
                        "event_type": "restore_pattern",
                        "interface_index": interface_index,
                        "original_pattern": original_pattern,
                    }
                )


if __name__ == "__main__":
    # Demo usage
    from .ifxtable import IfXTableSimulator, create_sample_interfaces

    # Create simulator with sample interfaces
    simulator = IfXTableSimulator()
    interfaces = create_sample_interfaces(5)

    for interface in interfaces:
        simulator.add_interface(interface)

    # Create state engine
    state_engine = InterfaceStateEngine(simulator)

    # Register event handler
    def event_logger(event: InterfaceEvent):
        print(f"EVENT: Interface {event.interface_index} - {event.event_type.value}")

    state_engine.register_event_handler(StateChangeEvent.LINK_DOWN, event_logger)
    state_engine.register_event_handler(StateChangeEvent.LINK_UP, event_logger)
    state_engine.register_event_handler(StateChangeEvent.SPEED_CHANGE, event_logger)

    # Start state engine
    state_engine.start()

    # Schedule some events
    state_engine.schedule_periodic_link_flaps(1, flap_interval=300, down_duration=30)
    state_engine.schedule_periodic_speed_changes(
        2, speed_sequence=[100, 1000, 10000], change_interval=180
    )

    # Show initial status
    print("\nInterface Status Summary:")
    summary = state_engine.get_interface_status_summary()
    for idx, status in summary.items():
        print(
            f"  {idx}: {status['name']} - {status['oper_status']} - {status['speed_mbps']}Mbps"
        )

    print("\nInterface state engine running... (Press Ctrl+C to stop)")

    try:
        # Run for a demo period
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        state_engine.stop()
        print("\nDemo completed")
