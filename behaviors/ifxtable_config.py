#!/usr/bin/env python3
"""
ifXTable Configuration Loader for Mock SNMP Agent.

This module loads ifXTable configurations from YAML files and integrates
them with the ifXTable simulator and interface state engine.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .ifxtable import (
    AdminStatus,
    IfXTableSimulator,
    InterfaceDefinition,
    InterfaceType,
    LinkTrapEnable,
    OperStatus,
)
from .interface_engine import InterfaceStateEngine, StateChangeEvent


@dataclass
class ScenarioEvent:
    """Configuration for a scenario event."""

    event_type: str
    interface: int
    delay: int
    new_speed: Optional[int] = None
    down_duration: Optional[int] = None


@dataclass
class SimulationScenario:
    """Configuration for a simulation scenario."""

    name: str
    description: str
    interfaces: List[int]
    duration: int
    events: List[ScenarioEvent]


class IfXTableConfigLoader:
    """Loads and manages ifXTable configuration from YAML files."""

    def __init__(self):
        self.config_data: Dict = {}
        self.simulator: Optional[IfXTableSimulator] = None
        self.state_engine: Optional[InterfaceStateEngine] = None

    def load_config(self, config_file: Path) -> bool:
        """Load ifXTable configuration from YAML file."""
        try:
            with open(config_file, encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)

            print(f"Loaded ifXTable configuration from {config_file}")
            return True

        except Exception as e:
            print(f"Error loading ifXTable config: {e}")
            return False

    def create_simulator(self) -> IfXTableSimulator:
        """Create and configure the ifXTable simulator from loaded config."""
        if not self.config_data:
            raise RuntimeError("No configuration loaded")

        self.simulator = IfXTableSimulator()

        # Process interface definitions
        interfaces_config = self.config_data.get("interfaces", {})

        for category_name, interface_list in interfaces_config.items():
            if isinstance(interface_list, list):
                for interface_config in interface_list:
                    interface_def = self._create_interface_definition(interface_config)
                    self.simulator.add_interface(interface_def)
                    print(
                        f"Added interface {interface_def.index}: {interface_def.name}"
                    )

        # Apply global simulation settings
        simulation_config = self.config_data.get("simulation", {})
        self._apply_simulation_settings(simulation_config)

        print(
            f"Created ifXTable simulator with {len(self.simulator.interfaces)} interfaces"
        )
        return self.simulator

    def create_state_engine(self) -> InterfaceStateEngine:
        """Create and configure the interface state engine."""
        if not self.simulator:
            raise RuntimeError("Simulator must be created first")

        self.state_engine = InterfaceStateEngine(self.simulator)

        # Configure based on loaded settings
        simulation_config = self.config_data.get("simulation", {})
        random_events = simulation_config.get("random_events", {})

        if random_events.get("enabled", True):
            self.state_engine.enable_random_events = True
            self.state_engine.random_event_probability = random_events.get(
                "probability", 0.0005
            )

        # Schedule periodic link flaps from interface config
        interfaces_config = self.config_data.get("interfaces", {})
        for category_name, interface_list in interfaces_config.items():
            if isinstance(interface_list, list):
                for interface_config in interface_list:
                    interface_index = interface_config.get("index")
                    link_flap = interface_config.get("link_flap", {})

                    if link_flap.get("enabled", False):
                        interval = link_flap.get("interval", 3600)
                        down_duration = link_flap.get("down_duration", 30)
                        self.state_engine.schedule_periodic_link_flaps(
                            interface_index, interval, down_duration
                        )

        print(f"Created interface state engine with configured behaviors")
        return self.state_engine

    def _create_interface_definition(self, config: Dict) -> InterfaceDefinition:
        """Create InterfaceDefinition from config dictionary."""
        # Map interface type string to enum
        type_mapping = {
            "ethernetCsmacd": InterfaceType.ETHERNET_CSMACD,
            "gigabitEthernet": InterfaceType.GIGABITETHERNET,
            "fastEthernet": InterfaceType.FASTETHER,
            "ppp": InterfaceType.PPP,
            "tunnel": InterfaceType.TUNNEL,
        }

        interface_type = type_mapping.get(
            config.get("type", "ethernetCsmacd"), InterfaceType.ETHERNET_CSMACD
        )

        # Map admin/oper status strings to enums
        admin_status = (
            AdminStatus.UP
            if config.get("admin_status", "up") == "up"
            else AdminStatus.DOWN
        )
        oper_status = (
            OperStatus.UP
            if config.get("oper_status", "up") == "up"
            else OperStatus.DOWN
        )

        # Create traffic ratios with defaults
        traffic_ratios = config.get("traffic_ratios", {})
        default_ratios = {"unicast": 0.8, "multicast": 0.15, "broadcast": 0.05}
        default_ratios.update(traffic_ratios)

        # Create error rates with defaults
        error_simulation = config.get("error_simulation", {})
        error_rates = {
            "input_errors": error_simulation.get("input_errors_rate", 0.0001),
            "output_errors": error_simulation.get("output_errors_rate", 0.0001),
            "input_discards": error_simulation.get("input_discards_rate", 0.0001),
            "output_discards": error_simulation.get("output_discards_rate", 0.0001),
        }

        return InterfaceDefinition(
            index=config["index"],
            name=config["name"],
            alias=config.get("alias", ""),
            interface_type=interface_type,
            speed_mbps=config.get("speed_mbps", 1000),
            mtu=config.get("mtu", 1500),
            admin_status=admin_status,
            oper_status=oper_status,
            utilization_pattern=config.get("utilization_pattern", "constant_low"),
            base_utilization=config.get("base_utilization", 0.1),
            traffic_ratios=default_ratios,
            error_rates=error_rates,
            link_flap_enabled=config.get("link_flap", {}).get("enabled", False),
            link_flap_interval=config.get("link_flap", {}).get("interval", 3600),
            link_down_duration=config.get("link_flap", {}).get("down_duration", 30),
        )

    def _apply_simulation_settings(self, simulation_config: Dict) -> None:
        """Apply global simulation settings to the simulator."""
        # Counter acceleration
        counter_accel = simulation_config.get("counter_acceleration", {})
        if counter_accel.get("enabled", False):
            acceleration_factor = counter_accel.get("factor", 1)
            # Apply acceleration to all counters
            for oid, counter in self.simulator.counter_simulator.counters.items():
                counter.acceleration_factor = acceleration_factor
            print(f"Applied counter acceleration factor: {acceleration_factor}x")

    def load_simulation_scenarios(self) -> Dict[str, SimulationScenario]:
        """Load simulation scenarios from configuration."""
        scenarios = {}
        scenario_configs = self.config_data.get("simulation_scenarios", {})

        for name, scenario_config in scenario_configs.items():
            events = []
            for event_config in scenario_config.get("events", []):
                event = ScenarioEvent(
                    event_type=event_config["type"],
                    interface=event_config["interface"],
                    delay=event_config.get("delay", 0),
                    new_speed=event_config.get("new_speed"),
                    down_duration=event_config.get("down_duration"),
                )
                events.append(event)

            scenario = SimulationScenario(
                name=name,
                description=scenario_config.get("description", ""),
                interfaces=scenario_config.get("interfaces", []),
                duration=scenario_config.get("duration", 600),
                events=events,
            )
            scenarios[name] = scenario

        print(f"Loaded {len(scenarios)} simulation scenarios")
        return scenarios

    def execute_scenario(self, scenario_name: str) -> bool:
        """Execute a simulation scenario."""
        if not self.state_engine:
            print("State engine not initialized")
            return False

        scenarios = self.load_simulation_scenarios()
        if scenario_name not in scenarios:
            print(f"Scenario '{scenario_name}' not found")
            return False

        scenario = scenarios[scenario_name]
        print(f"Executing scenario: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Duration: {scenario.duration}s")

        # Schedule scenario events
        start_time = time.time()
        for event in scenario.events:
            scheduled_time = start_time + event.delay

            if event.event_type == "link_flap":
                self.state_engine.scheduled_events.append(
                    {
                        "scheduled_time": scheduled_time,
                        "event_type": StateChangeEvent.LINK_DOWN,
                        "interface_index": event.interface,
                        "down_duration": event.down_duration or 30,
                    }
                )

            elif event.event_type == "speed_change":
                self.state_engine.scheduled_events.append(
                    {
                        "scheduled_time": scheduled_time,
                        "event_type": StateChangeEvent.SPEED_CHANGE,
                        "interface_index": event.interface,
                        "new_speed": event.new_speed or 1000,
                    }
                )

            elif event.event_type == "admin_down":
                self.state_engine.scheduled_events.append(
                    {
                        "scheduled_time": scheduled_time,
                        "event_type": StateChangeEvent.ADMIN_STATUS_CHANGE,
                        "interface_index": event.interface,
                        "new_status": "down",
                    }
                )

            elif event.event_type == "admin_up":
                self.state_engine.scheduled_events.append(
                    {
                        "scheduled_time": scheduled_time,
                        "event_type": StateChangeEvent.ADMIN_STATUS_CHANGE,
                        "interface_index": event.interface,
                        "new_status": "up",
                    }
                )

        print(f"Scheduled {len(scenario.events)} events for scenario")
        return True

    def get_traffic_patterns(self) -> Dict[str, Dict]:
        """Get traffic pattern definitions from configuration."""
        return self.config_data.get("traffic_patterns", {})

    def get_interface_types(self) -> Dict[str, Dict]:
        """Get interface type definitions from configuration."""
        return self.config_data.get("interface_types", {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring and alerting configuration."""
        return self.config_data.get("monitoring", {})

    def generate_snmprec_file(self, output_file: Path) -> bool:
        """Generate .snmprec file from current configuration."""
        if not self.simulator:
            print("Simulator not initialized")
            return False

        try:
            self.simulator.generate_ifxtable_snmprec(output_file)
            print(f"Generated ifXTable .snmprec file: {output_file}")
            return True
        except Exception as e:
            print(f"Error generating .snmprec file: {e}")
            return False


def load_ifxtable_configuration(
    config_file: Path,
) -> tuple[IfXTableSimulator, InterfaceStateEngine]:
    """Convenience function to load complete ifXTable configuration."""
    loader = IfXTableConfigLoader()

    if not loader.load_config(config_file):
        raise RuntimeError(f"Failed to load configuration from {config_file}")

    simulator = loader.create_simulator()
    state_engine = loader.create_state_engine()

    return simulator, state_engine


if __name__ == "__main__":
    # Demo usage
    config_file = Path("config/ifxtable.yaml")

    if not config_file.exists():
        print(f"Configuration file not found: {config_file}")
        exit(1)

    try:
        # Load configuration
        loader = IfXTableConfigLoader()
        loader.load_config(config_file)

        # Create simulator and state engine
        simulator = loader.create_simulator()
        state_engine = loader.create_state_engine()

        # Start state engine
        state_engine.start()

        # Show loaded interfaces
        print("\nLoaded Interfaces:")
        for idx, interface_def in simulator.interfaces.items():
            print(f"  {idx}: {interface_def.name} ({interface_def.speed_mbps}Mbps)")
            print(f"      Pattern: {interface_def.utilization_pattern}")
            print(f"      Flap enabled: {interface_def.link_flap_enabled}")

        # Show available scenarios
        scenarios = loader.load_simulation_scenarios()
        print(f"\nAvailable Scenarios: {list(scenarios.keys())}")

        # Generate sample .snmprec
        output_file = Path("data/ifxtable_configured.snmprec")
        output_file.parent.mkdir(exist_ok=True)
        loader.generate_snmprec_file(output_file)

        print(f"\nifXTable configuration loaded successfully!")

        # Run briefly to show activity
        print("Running for 10 seconds to show activity...")
        time.sleep(10)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "state_engine" in locals():
            state_engine.stop()
