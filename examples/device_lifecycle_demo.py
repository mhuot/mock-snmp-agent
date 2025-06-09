#!/usr/bin/env python3
"""
Device Lifecycle State Machine Demonstration

This script demonstrates the state machine functionality for device
lifecycle simulation in the Mock SNMP Agent.

Usage:
    python examples/device_lifecycle_demo.py [device_type]

Arguments:
    device_type: router, switch, server, printer, or generic (default: router)

Prerequisites:
    - Mock SNMP Agent with state machine support
    - net-snmp tools for testing SNMP responses
"""

import sys
import time
import subprocess
from typing import Dict, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_machine.core import DeviceStateMachine
from state_machine.device_types import (
    create_device_state_machine,
    get_supported_device_types,
    get_device_type_info
)


class DeviceLifecycleDemo:
    """Demonstrates device lifecycle state machine functionality."""
    
    def __init__(self, device_type: str = "router"):
        """Initialize the demo.
        
        Args:
            device_type: Type of device to simulate
        """
        self.device_type = device_type
        self.state_machine = None
        
    def create_state_machine(self) -> None:
        """Create and configure the state machine."""
        print(f"Creating {self.device_type} state machine...")
        
        try:
            self.state_machine = create_device_state_machine(self.device_type)
            print(f"✓ Created {self.device_type} state machine")
            print(f"  Initial state: {self.state_machine.current_state}")
            print(f"  Available states: {len(self.state_machine.states)}")
            
            # Add state change callback for demonstration
            self.state_machine.add_state_change_callback(self._on_state_change)
            
        except ValueError as e:
            print(f"✗ Failed to create state machine: {e}")
            print(f"Supported device types: {', '.join(get_supported_device_types())}")
            return False
        
        return True
    
    def _on_state_change(self, old_state: str, new_state: str, transition) -> None:
        """Callback for state changes."""
        print(f"🔄 State change: {old_state} → {new_state}")
        print(f"   Trigger: {transition.trigger.value}")
        print(f"   Reason: {transition.reason}")
        print(f"   Time in previous state: {transition.duration_in_previous_state:.1f}s")
    
    def show_device_info(self) -> None:
        """Show information about the device type."""
        device_info = get_device_type_info()
        if self.device_type in device_info:
            info = device_info[self.device_type]
            print(f"\n{self.device_type.upper()} Device Information:")
            print(f"  Description: {info['description']}")
            print(f"  Default initial state: {info['default_initial_state']}")
            print(f"  Typical states: {info['typical_states']}")
    
    def show_current_state_details(self) -> None:
        """Show details about the current state."""
        if not self.state_machine:
            return
        
        current_state_def = self.state_machine.get_current_state()
        if not current_state_def:
            print("⚠ No state definition found for current state")
            return
        
        print(f"\nCurrent State Details:")
        print(f"  State: {current_state_def.name}")
        print(f"  Description: {current_state_def.description}")
        print(f"  Duration: {current_state_def.duration_seconds}s" if current_state_def.duration_seconds else "  Duration: Indefinite")
        print(f"  OID Availability: {current_state_def.oid_availability}%")
        print(f"  Response Delay: {current_state_def.response_delay_ms}ms")
        print(f"  Error Rate: {current_state_def.error_rate}%")
        print(f"  Possible next states: {', '.join(current_state_def.next_states)}")
        
        if current_state_def.oid_overrides:
            print(f"  OID Overrides: {len(current_state_def.oid_overrides)} defined")
    
    def demonstrate_manual_transitions(self) -> None:
        """Demonstrate manual state transitions."""
        if not self.state_machine:
            return
        
        print(f"\n--- Manual Transition Demonstration ---")
        
        current_state_def = self.state_machine.get_current_state()
        if not current_state_def or not current_state_def.next_states:
            print("No manual transitions available from current state")
            return
        
        # Try transitioning to each possible next state
        for next_state in current_state_def.next_states[:2]:  # Limit to first 2 for demo
            print(f"\nTesting transition to '{next_state}'...")
            
            if self.state_machine.transition_to(next_state, reason=f"Demo transition to {next_state}"):
                print(f"✓ Successfully transitioned to {next_state}")
                time.sleep(2)  # Brief pause
                
                self.show_current_state_details()
                
                # Transition back if possible
                current_state_def = self.state_machine.get_current_state()
                if current_state_def and current_state_def.next_states:
                    back_state = current_state_def.next_states[0]
                    print(f"\nTransitioning back to {back_state}...")
                    self.state_machine.transition_to(back_state, reason="Demo return transition")
                    time.sleep(1)
                
                break  # Only demo one transition
            else:
                print(f"✗ Failed to transition to {next_state}")
    
    def demonstrate_automatic_transitions(self) -> None:
        """Demonstrate automatic state transitions."""
        if not self.state_machine:
            return
        
        print(f"\n--- Automatic Transition Demonstration ---")
        print("Starting automatic transitions for 30 seconds...")
        
        # Start automatic transitions
        self.state_machine.start_automatic_transitions()
        
        start_time = time.time()
        last_stats_time = start_time
        
        try:
            while time.time() - start_time < 30:  # Run for 30 seconds
                time.sleep(1)
                
                # Show stats every 10 seconds
                if time.time() - last_stats_time >= 10:
                    self.show_statistics()
                    last_stats_time = time.time()
        
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
        
        finally:
            # Stop automatic transitions
            self.state_machine.stop_automatic_transitions()
            print("\nStopped automatic transitions")
    
    def show_statistics(self) -> None:
        """Show state machine statistics."""
        if not self.state_machine:
            return
        
        stats = self.state_machine.get_state_statistics()
        
        print(f"\n--- State Machine Statistics ---")
        print(f"Device Type: {stats['device_type']}")
        print(f"Current State: {stats['current_state']}")
        print(f"Time in Current State: {stats['time_in_current_state']:.1f}s")
        print(f"Total Uptime: {stats['total_uptime']:.1f}s")
        print(f"Total Transitions: {stats['total_transitions']}")
        print(f"Auto Transitions: {'Enabled' if stats['auto_transitions_enabled'] else 'Disabled'}")
        
        current_info = stats['current_state_info']
        print(f"Current State Effects:")
        print(f"  OID Availability: {current_info['oid_availability']}%")
        print(f"  Response Delay: {current_info['response_delay_ms']}ms")
        print(f"  Error Rate: {current_info['error_rate']}%")
    
    def show_state_history(self) -> None:
        """Show state transition history."""
        if not self.state_machine:
            return
        
        history = self.state_machine.get_state_history(limit=10)
        if not history:
            print("\nNo state transitions recorded yet")
            return
        
        print(f"\n--- Recent State Transitions (last {len(history)}) ---")
        for i, transition in enumerate(reversed(history), 1):
            print(f"{i:2d}. {transition['from_state']} → {transition['to_state']}")
            print(f"     Trigger: {transition['trigger']}")
            print(f"     Reason: {transition['reason']}")
            print(f"     Duration in previous state: {transition['duration_in_previous_state']:.1f}s")
            print()
    
    def demonstrate_snmp_effects(self) -> None:
        """Demonstrate how state machine affects SNMP responses."""
        if not self.state_machine:
            return
        
        print(f"\n--- SNMP Response Effects Demonstration ---")
        
        # Example SNMP record lines
        test_lines = [
            "1.3.6.1.2.1.1.1.0|4|Test System Description",
            "1.3.6.1.2.1.1.3.0|67|123456",
            "1.3.6.1.2.1.2.2.1.10.1|41|1000000"
        ]
        
        print("Original SNMP responses:")
        for line in test_lines:
            print(f"  {line}")
        
        print(f"\nAfter applying {self.state_machine.current_state} state effects:")
        for line in test_lines:
            modified_line = self.state_machine.apply_state_effects_to_snmprec_line(line)
            if modified_line != line:
                print(f"  {modified_line} (modified)")
            else:
                print(f"  {modified_line}")
    
    def run_complete_demonstration(self) -> None:
        """Run the complete device lifecycle demonstration."""
        print("Device Lifecycle State Machine Demonstration")
        print("=" * 60)
        
        # Create state machine
        if not self.create_state_machine():
            return
        
        # Show device information
        self.show_device_info()
        
        # Show initial state
        self.show_current_state_details()
        
        # Demonstrate SNMP effects
        self.demonstrate_snmp_effects()
        
        # Demonstrate manual transitions
        self.demonstrate_manual_transitions()
        
        # Show statistics
        self.show_statistics()
        
        # Demonstrate automatic transitions
        print(f"\nPress Ctrl+C to skip automatic transition demo")
        try:
            self.demonstrate_automatic_transitions()
        except KeyboardInterrupt:
            print("\nSkipped automatic transition demo")
        
        # Show final statistics and history
        self.show_statistics()
        self.show_state_history()
        
        # Cleanup
        if self.state_machine:
            self.state_machine.cleanup()
        
        print("\n" + "=" * 60)
        print("🎉 Device lifecycle demonstration completed!")
        print("\nTo use state machine in Mock SNMP Agent:")
        print("  python mock_snmp_agent.py --config config/state_machine_test.yaml")


def main():
    """Main demonstration function."""
    # Parse command line arguments
    device_type = "router"
    if len(sys.argv) > 1:
        device_type = sys.argv[1].lower()
    
    # Validate device type
    if device_type not in get_supported_device_types():
        print(f"Error: Unsupported device type '{device_type}'")
        print(f"Supported types: {', '.join(get_supported_device_types())}")
        return 1
    
    # Run demonstration
    demo = DeviceLifecycleDemo(device_type)
    demo.run_complete_demonstration()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())