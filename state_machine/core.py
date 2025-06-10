#!/usr/bin/env python3
"""
State Machine Core Engine

This module provides the core state machine functionality for device
lifecycle simulation in the Mock SNMP Agent.
"""

import logging
import random
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TransitionTrigger(str, Enum):
    """State transition trigger types."""

    TIME_BASED = "time_based"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    LOAD_BASED = "load_based"


@dataclass
class StateDefinition:
    """Definition of a device state."""

    name: str
    description: str
    duration_seconds: Optional[int] = None
    oid_availability: float = 100.0  # Percentage of OIDs available
    response_delay_ms: int = 50  # Additional delay for responses
    error_rate: float = 0.0  # Percentage of requests that fail
    next_states: List[str] = None  # Possible next states
    transition_probabilities: Dict[str, float] = None  # Transition probabilities
    oid_overrides: Dict[str, str] = None  # OID value overrides for this state

    def __post_init__(self):
        """Initialize default values."""
        if self.next_states is None:
            self.next_states = []
        if self.transition_probabilities is None:
            self.transition_probabilities = {}
        if self.oid_overrides is None:
            self.oid_overrides = {}


@dataclass
class StateTransition:
    """Represents a state transition."""

    from_state: str
    to_state: str
    trigger: TransitionTrigger
    timestamp: float
    reason: str
    duration_in_previous_state: float


class DeviceStateMachine:
    """Core state machine engine for device lifecycle simulation."""

    def __init__(
        self, device_type: str = "generic", initial_state: str = "operational"
    ):
        """Initialize the state machine.

        Args:
            device_type: Type of device (router, switch, server, etc.)
            initial_state: Initial state name
        """
        self.device_type = device_type
        self.current_state = initial_state
        self.states: Dict[str, StateDefinition] = {}
        self.state_history: List[StateTransition] = []

        # Timing
        self.state_start_time = time.time()
        self.machine_start_time = time.time()

        # Configuration
        self.auto_transitions_enabled = True
        self.transition_delays = {"min": 5, "max": 30}

        # Threading
        self._running = False
        self._state_thread = None
        self._lock = threading.RLock()

        # Callbacks
        self._state_change_callbacks: List[Callable] = []

        # Logging
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            f"Initialized {device_type} state machine in state '{initial_state}'"
        )

    def add_state(self, state: StateDefinition) -> None:
        """Add a state definition to the machine.

        Args:
            state: State definition to add
        """
        with self._lock:
            self.states[state.name] = state
            self.logger.debug(f"Added state definition: {state.name}")

    def add_state_change_callback(self, callback: Callable) -> None:
        """Add a callback for state changes.

        Args:
            callback: Function to call on state changes
                     Signature: callback(old_state, new_state, transition)
        """
        self._state_change_callbacks.append(callback)

    def get_current_state(self) -> Optional[StateDefinition]:
        """Get the current state definition.

        Returns:
            Current state definition or None if not found
        """
        with self._lock:
            return self.states.get(self.current_state)

    def get_time_in_current_state(self) -> float:
        """Get time spent in current state.

        Returns:
            Time in seconds since entering current state
        """
        return time.time() - self.state_start_time

    def get_total_uptime(self) -> float:
        """Get total machine uptime.

        Returns:
            Total uptime in seconds
        """
        return time.time() - self.machine_start_time

    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is allowed.

        Args:
            target_state: Name of target state

        Returns:
            True if transition is allowed
        """
        with self._lock:
            current_state_def = self.states.get(self.current_state)
            if not current_state_def:
                return False

            return target_state in current_state_def.next_states

    def transition_to(
        self,
        target_state: str,
        trigger: TransitionTrigger = TransitionTrigger.MANUAL,
        reason: str = "Manual transition",
    ) -> bool:
        """Transition to a new state.

        Args:
            target_state: Name of target state
            trigger: Type of trigger that caused the transition
            reason: Human-readable reason for transition

        Returns:
            True if transition was successful
        """
        with self._lock:
            # Validate target state exists
            if target_state not in self.states:
                self.logger.error(f"Target state '{target_state}' does not exist")
                return False

            # Check if transition is allowed (unless forced)
            if not self.can_transition_to(target_state):
                self.logger.warning(
                    f"Transition from '{self.current_state}' to '{target_state}' not allowed"
                )
                return False

            # Record transition
            old_state = self.current_state
            time_in_previous_state = self.get_time_in_current_state()

            transition = StateTransition(
                from_state=old_state,
                to_state=target_state,
                trigger=trigger,
                timestamp=time.time(),
                reason=reason,
                duration_in_previous_state=time_in_previous_state,
            )

            # Update state
            self.current_state = target_state
            self.state_start_time = time.time()
            self.state_history.append(transition)

            self.logger.info(
                f"State transition: {old_state} -> {target_state} ({reason})"
            )

            # Notify callbacks
            for callback in self._state_change_callbacks:
                try:
                    callback(old_state, target_state, transition)
                except Exception as e:
                    self.logger.error(f"State change callback failed: {e}")

            return True

    def force_transition_to(
        self, target_state: str, reason: str = "Forced transition"
    ) -> bool:
        """Force transition to a state regardless of rules.

        Args:
            target_state: Name of target state
            reason: Reason for forced transition

        Returns:
            True if transition was successful
        """
        with self._lock:
            if target_state not in self.states:
                self.logger.error(f"Target state '{target_state}' does not exist")
                return False

            # Temporarily allow the transition
            current_state_def = self.states.get(self.current_state)
            if current_state_def and target_state not in current_state_def.next_states:
                current_state_def.next_states.append(target_state)

                # Perform transition
                result = self.transition_to(
                    target_state, TransitionTrigger.MANUAL, reason
                )

                # Remove temporary allowance
                current_state_def.next_states.remove(target_state)

                return result
            else:
                return self.transition_to(
                    target_state, TransitionTrigger.MANUAL, reason
                )

    def get_next_automatic_transition(self) -> Optional[str]:
        """Determine next automatic transition based on current state.

        Returns:
            Name of next state or None if no automatic transition
        """
        with self._lock:
            current_state_def = self.states.get(self.current_state)
            if not current_state_def or not current_state_def.next_states:
                return None

            # Check if we should transition based on duration
            if current_state_def.duration_seconds:
                time_in_state = self.get_time_in_current_state()
                if time_in_state >= current_state_def.duration_seconds:
                    # Choose next state based on probabilities
                    return self._choose_next_state_by_probability(current_state_def)

            return None

    def _choose_next_state_by_probability(self, state_def: StateDefinition) -> str:
        """Choose next state based on transition probabilities.

        Args:
            state_def: Current state definition

        Returns:
            Name of chosen next state
        """
        if not state_def.transition_probabilities:
            # No probabilities defined, choose randomly
            return random.choice(state_def.next_states)

        # Weighted random selection
        total_weight = sum(state_def.transition_probabilities.values())
        if total_weight == 0:
            return random.choice(state_def.next_states)

        random_value = random.uniform(0, total_weight)
        cumulative_weight = 0

        for state_name, weight in state_def.transition_probabilities.items():
            cumulative_weight += weight
            if random_value <= cumulative_weight:
                return state_name

        # Fallback
        return state_def.next_states[0] if state_def.next_states else state_def.name

    def start_automatic_transitions(self) -> None:
        """Start automatic state transitions in background thread."""
        if self._running:
            self.logger.warning("Automatic transitions already running")
            return

        self._running = True
        self._state_thread = threading.Thread(target=self._transition_loop, daemon=True)
        self._state_thread.start()

        self.logger.info("Started automatic state transitions")

    def stop_automatic_transitions(self) -> None:
        """Stop automatic state transitions."""
        self._running = False
        if self._state_thread:
            self._state_thread.join(timeout=5)

        self.logger.info("Stopped automatic state transitions")

    def _transition_loop(self) -> None:
        """Main loop for automatic transitions."""
        while self._running:
            try:
                if self.auto_transitions_enabled:
                    next_state = self.get_next_automatic_transition()
                    if next_state:
                        self.transition_to(
                            next_state,
                            TransitionTrigger.TIME_BASED,
                            "Automatic time-based transition",
                        )

                # Sleep for a short interval
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in transition loop: {e}")
                time.sleep(5)  # Longer sleep on error

    def get_state_statistics(self) -> Dict[str, Any]:
        """Get statistics about state machine operation.

        Returns:
            Dictionary with state machine statistics
        """
        with self._lock:
            current_state_def = self.get_current_state()

            # Calculate state durations
            state_durations = {}
            for transition in self.state_history:
                state_name = transition.from_state
                if state_name not in state_durations:
                    state_durations[state_name] = []
                state_durations[state_name].append(
                    transition.duration_in_previous_state
                )

            # Calculate averages
            avg_state_durations = {}
            for state_name, durations in state_durations.items():
                avg_state_durations[state_name] = sum(durations) / len(durations)

            return {
                "device_type": self.device_type,
                "current_state": self.current_state,
                "time_in_current_state": self.get_time_in_current_state(),
                "total_uptime": self.get_total_uptime(),
                "total_transitions": len(self.state_history),
                "states_defined": len(self.states),
                "auto_transitions_enabled": self.auto_transitions_enabled,
                "is_running": self._running,
                "state_durations": avg_state_durations,
                "current_state_info": {
                    "oid_availability": (
                        current_state_def.oid_availability if current_state_def else 100
                    ),
                    "response_delay_ms": (
                        current_state_def.response_delay_ms if current_state_def else 0
                    ),
                    "error_rate": (
                        current_state_def.error_rate if current_state_def else 0
                    ),
                },
            }

    def get_state_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get state transition history.

        Args:
            limit: Maximum number of transitions to return

        Returns:
            List of transition dictionaries
        """
        with self._lock:
            transitions = self.state_history
            if limit:
                transitions = transitions[-limit:]

            return [
                {
                    "from_state": t.from_state,
                    "to_state": t.to_state,
                    "trigger": t.trigger.value,
                    "timestamp": t.timestamp,
                    "reason": t.reason,
                    "duration_in_previous_state": t.duration_in_previous_state,
                }
                for t in transitions
            ]

    def apply_state_effects_to_snmprec_line(self, line: str) -> str:
        """Apply current state effects to an SNMP record line.

        Args:
            line: Original .snmprec line

        Returns:
            Modified line with state effects applied
        """
        current_state_def = self.get_current_state()
        if not current_state_def:
            return line

        try:
            parts = line.split("|", 2)
            if len(parts) != 3:
                return line

            oid, tag, value = parts

            # Check if OID should be available in current state
            if random.uniform(0, 100) > current_state_def.oid_availability:
                # OID not available - return noSuchObject error
                type_val = tag.split(":")[0] if ":" in tag else tag
                return f"{oid}|{type_val}:error|op=get,value=noSuchObject"

            # Apply OID-specific overrides
            if oid in current_state_def.oid_overrides:
                override_value = current_state_def.oid_overrides[oid]
                return f"{oid}|{tag}|{override_value}"

            # Apply error rate
            if random.uniform(0, 100) < current_state_def.error_rate:
                type_val = tag.split(":")[0] if ":" in tag else tag
                return f"{oid}|{type_val}:error|op=get,value=genErr"

            # Apply response delay
            if current_state_def.response_delay_ms > 0:
                type_val = tag.split(":")[0] if ":" in tag else tag
                if "delay" not in tag:
                    tag = f"{type_val}:delay"
                    if "=" in value:
                        value += f",wait={current_state_def.response_delay_ms}"
                    else:
                        value = (
                            f"value={value},wait={current_state_def.response_delay_ms}"
                        )

            return f"{oid}|{tag}|{value}"

        except Exception as e:
            self.logger.error(f"Error applying state effects: {e}")
            return line

    def cleanup(self) -> None:
        """Clean up state machine resources."""
        self.stop_automatic_transitions()
        self.logger.info("State machine cleaned up")
