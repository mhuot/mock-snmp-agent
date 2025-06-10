#!/usr/bin/env python3
"""
Configuration management for Mock SNMP Agent.

This module handles loading and validating configuration from YAML/JSON files,
and provides utilities for generating .snmprec files based on configuration.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class SimulationConfig:
    """Handles simulation configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config_path = config_path
        self.config = self._default_config()

        if config_path:
            self.load_config(config_path)

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "simulation": {
                "behaviors": {
                    "delay": {
                        "enabled": False,
                        "global_delay": 0,
                        "deviation": 0,
                        "oid_specific": {},
                    },
                    "drops": {"enabled": False, "rate": 0},
                    "packet_loss": {"enabled": False, "rate": 0},
                    "restart": {"enabled": False, "interval": 300},
                    "counter_wrap": {
                        "enabled": False,
                        "acceleration_factor": 1000,
                        "interface_count": 10,
                        "interface_speeds": ["100M", "1G", "10G"],
                    },
                    "resource_limits": {
                        "enabled": False,
                        "max_cpu_percent": 85.0,
                        "max_memory_percent": 90.0,
                        "max_concurrent_requests": 50,
                        "max_pdu_size": 1472,
                    },
                    "bulk_operations": {
                        "enabled": False,
                        "table_size": 1000,
                        "max_repetitions": 50,
                        "max_pdu_size": 1472,
                        "bandwidth_limit": None,
                        "failure_probability": 0.0,
                    },
                    "snmpv3_security": {
                        "enabled": False,
                        "time_window_failures": {
                            "enabled": False,
                            "clock_skew_seconds": 200,
                            "failure_rate": 15,
                        },
                        "authentication_failures": {
                            "enabled": False,
                            "wrong_credentials_rate": 10,
                            "unsupported_auth_rate": 5,
                            "unknown_user_rate": 8,
                        },
                        "privacy_failures": {
                            "enabled": False,
                            "decryption_error_rate": 7,
                            "unsupported_privacy_rate": 3,
                        },
                        "engine_discovery_failures": {
                            "enabled": False,
                            "wrong_engine_id_rate": 12,
                            "boot_counter_issues_rate": 5,
                        },
                    },
                },
                "logging": {
                    "enabled": False,
                    "level": "info",
                    "file": None,
                    "format": "json",
                },
                "metrics": {
                    "enabled": False,
                    "export": {"format": "json", "interval": 60, "file": None},
                },
                "rest_api": {
                    "enabled": False,
                    "host": "127.0.0.1",
                    "port": 8080,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                    },
                    "auth": {
                        "enabled": False,
                        "api_key": None,
                    },
                },
                "state_machine": {
                    "enabled": False,
                    "device_type": "generic",
                    "initial_state": "operational",
                    "auto_transitions": True,
                    "transition_delays": {
                        "min": 5,
                        "max": 30,
                    },
                    "custom_states": {},
                    "oid_overrides": {},
                },
            }
        }

    def load_config(self, config_path: str) -> None:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Raises:
            ValueError: If configuration file format is invalid
            FileNotFoundError: If configuration file doesn't exist
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                loaded_config = yaml.safe_load(f)
            elif path.suffix == ".json":
                loaded_config = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")

        # Merge with defaults
        self.config = self._merge_configs(self._default_config(), loaded_config)
        self._validate_config()

    def _merge_configs(self, default: Dict, update: Dict) -> Dict:
        """Recursively merge configuration dictionaries.

        Args:
            default: Default configuration
            update: Configuration updates

        Returns:
            Merged configuration
        """
        result = default.copy()

        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _validate_config(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration contains invalid values
        """
        behaviors = self.config["simulation"]["behaviors"]

        # Validate delay settings
        if behaviors["delay"]["enabled"]:
            if behaviors["delay"]["global_delay"] < 0:
                raise ValueError("global_delay must be >= 0")
            if behaviors["delay"]["deviation"] < 0:
                raise ValueError("deviation must be >= 0")

        # Validate drop rate
        if behaviors["drops"]["enabled"]:
            rate = behaviors["drops"]["rate"]
            if not 0 <= rate <= 100:
                raise ValueError("drop rate must be between 0 and 100")

        # Validate packet loss rate
        if behaviors["packet_loss"]["enabled"]:
            rate = behaviors["packet_loss"]["rate"]
            if not 0 <= rate <= 100:
                raise ValueError("packet_loss rate must be between 0 and 100")

        # Validate restart interval
        if behaviors["restart"]["enabled"]:
            if behaviors["restart"]["interval"] < 1:
                raise ValueError("restart interval must be >= 1 second")

        # Validate SNMPv3 security settings
        if behaviors["snmpv3_security"]["enabled"]:
            security = behaviors["snmpv3_security"]

            # Validate time window settings
            if security["time_window_failures"]["enabled"]:
                clock_skew = security["time_window_failures"]["clock_skew_seconds"]
                if clock_skew < 151:  # Must be beyond 150-second window
                    raise ValueError("clock_skew_seconds must be > 150")

                failure_rate = security["time_window_failures"]["failure_rate"]
                if not 0 <= failure_rate <= 100:
                    raise ValueError(
                        "time_window failure_rate must be between 0 and 100"
                    )

            # Validate authentication failure rates
            if security["authentication_failures"]["enabled"]:
                auth = security["authentication_failures"]
                for rate_name in [
                    "wrong_credentials_rate",
                    "unsupported_auth_rate",
                    "unknown_user_rate",
                ]:
                    rate = auth[rate_name]
                    if not 0 <= rate <= 100:
                        raise ValueError(
                            f"authentication {rate_name} must be between 0 and 100"
                        )

            # Validate privacy failure rates
            if security["privacy_failures"]["enabled"]:
                privacy = security["privacy_failures"]
                for rate_name in ["decryption_error_rate", "unsupported_privacy_rate"]:
                    rate = privacy[rate_name]
                    if not 0 <= rate <= 100:
                        raise ValueError(
                            f"privacy {rate_name} must be between 0 and 100"
                        )

            # Validate engine discovery failure rates
            if security["engine_discovery_failures"]["enabled"]:
                engine = security["engine_discovery_failures"]
                for rate_name in ["wrong_engine_id_rate", "boot_counter_issues_rate"]:
                    rate = engine[rate_name]
                    if not 0 <= rate <= 100:
                        raise ValueError(
                            f"engine discovery {rate_name} must be between 0 and 100"
                        )

        # Validate REST API settings
        if self.config["simulation"]["rest_api"]["enabled"]:
            api_config = self.config["simulation"]["rest_api"]

            port = api_config["port"]
            if not 1 <= port <= 65535:
                raise ValueError("REST API port must be between 1 and 65535")

            # Validate CORS origins
            if api_config["cors"]["enabled"]:
                origins = api_config["cors"]["origins"]
                if not isinstance(origins, list):
                    raise ValueError("CORS origins must be a list")

        # Validate state machine settings
        if self.config["simulation"]["state_machine"]["enabled"]:
            sm_config = self.config["simulation"]["state_machine"]

            # Validate device type
            supported_types = ["router", "switch", "server", "printer", "generic"]
            device_type = sm_config["device_type"]
            if device_type not in supported_types:
                raise ValueError(
                    f"Device type must be one of: {', '.join(supported_types)}"
                )

            # Validate transition delays
            delays = sm_config["transition_delays"]
            if delays["min"] < 0 or delays["max"] < 0:
                raise ValueError("Transition delays must be >= 0")
            if delays["min"] > delays["max"]:
                raise ValueError(
                    "Minimum transition delay cannot be greater than maximum"
                )

    def generate_snmprec_files(
        self, source_dir: str, temp_dir: Optional[str] = None
    ) -> str:
        """Generate modified .snmprec files based on configuration.

        Args:
            source_dir: Directory containing source .snmprec files
            temp_dir: Directory for generated files (creates temp if None)

        Returns:
            Path to directory containing generated files
        """
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="mock-snmp-agent-")

        os.makedirs(temp_dir, exist_ok=True)

        # Process each .snmprec file
        source_path = Path(source_dir)
        for snmprec_file in source_path.glob("*.snmprec"):
            self._process_snmprec_file(snmprec_file, temp_dir)

        return temp_dir

    def _process_snmprec_file(self, source_file: Path, dest_dir: str) -> None:
        """Process a single .snmprec file.

        Args:
            source_file: Source .snmprec file
            dest_dir: Destination directory
        """
        behaviors = self.config["simulation"]["behaviors"]
        dest_file = Path(dest_dir) / source_file.name

        with open(source_file, encoding="utf-8") as infile, open(
            dest_file, "w", encoding="utf-8"
        ) as outfile:
            for line in infile:
                line = line.strip()
                if not line or line.startswith("#"):
                    outfile.write(line + "\n")
                    continue

                # Apply behavior modifications
                modified_line = self._apply_behaviors(line, behaviors)
                outfile.write(modified_line + "\n")

    def _apply_behaviors(self, line: str, behaviors: Dict[str, Any]) -> str:
        """Apply behavior modifications to a .snmprec line.

        Args:
            line: Original .snmprec line
            behaviors: Behavior configuration

        Returns:
            Modified line
        """
        try:
            parts = line.split("|", 2)
            if len(parts) != 3:
                return line

            oid, tag, value = parts

            # Apply delay behavior
            if behaviors["delay"]["enabled"]:
                delay_config = behaviors["delay"]

                # Check for OID-specific delay
                oid_delay = None
                for oid_pattern, oid_config in delay_config.get(
                    "oid_specific", {}
                ).items():
                    if oid.startswith(oid_pattern):
                        oid_delay = oid_config
                        break

                if oid_delay:
                    delay = oid_delay.get("delay", delay_config["global_delay"])
                    deviation = oid_delay.get("deviation", delay_config["deviation"])
                else:
                    delay = delay_config["global_delay"]
                    deviation = delay_config["deviation"]

                if delay > 0:
                    # Extract type from tag
                    type_val = tag.split(":")[0] if ":" in tag else tag
                    # Add delay variation module
                    tag = f"{type_val}:delay"
                    # Preserve original value format - ensure integers for wait/deviation
                    if "=" in value:
                        # Already has parameters, just add delay
                        value += f",wait={int(delay)}"
                    else:
                        # Simple value, wrap it
                        value = f"value={value},wait={int(delay)}"
                    if deviation > 0:
                        value += f",deviation={int(deviation)}"

            # Apply drop behavior (using error module)
            elif behaviors["drops"]["enabled"] and behaviors["drops"]["rate"] > 0:
                import random  # pylint: disable=import-outside-toplevel

                if random.randint(1, 100) <= behaviors["drops"]["rate"]:
                    type_val = tag.split(":")[0] if ":" in tag else tag
                    tag = f"{type_val}:error"
                    value = "op=get,value=genErr"

            # Apply packet loss (extreme delay)
            elif (
                behaviors["packet_loss"]["enabled"]
                and behaviors["packet_loss"]["rate"] > 0
            ):
                import random  # pylint: disable=import-outside-toplevel

                if random.randint(1, 100) <= behaviors["packet_loss"]["rate"]:
                    type_val = tag.split(":")[0] if ":" in tag else tag
                    tag = f"{type_val}:delay"
                    value = f"value={value},wait=99999"

            # Apply SNMPv3 security failures
            elif behaviors["snmpv3_security"]["enabled"]:
                from .behaviors.snmpv3_security import (  # pylint: disable=import-outside-toplevel
                    SNMPv3SecuritySimulator,
                    create_security_config_from_dict,
                )

                security_config = create_security_config_from_dict(
                    {"snmpv3_security": behaviors["snmpv3_security"]}
                )
                simulator = SNMPv3SecuritySimulator(security_config)

                # Try to apply security failures
                failure_line = None
                if security_config.time_window_enabled:
                    failure_line = simulator.generate_time_window_failure(oid)
                elif security_config.auth_failures_enabled:
                    failure_line = simulator.generate_auth_failure(oid)
                elif security_config.privacy_failures_enabled:
                    failure_line = simulator.generate_privacy_failure(oid)
                elif security_config.engine_failures_enabled:
                    failure_line = simulator.generate_engine_failure(oid)

                if failure_line:
                    # Extract the modified parts from the failure line
                    failure_parts = failure_line.split("|", 2)
                    if len(failure_parts) == 3:
                        _, failure_tag, failure_value = failure_parts
                        tag = failure_tag
                        value = failure_value

            # Apply state machine effects (can be combined with other behaviors)
            if behaviors["state_machine"]["enabled"]:
                # State machine effects are applied by the state machine instance
                # This is handled externally in the main application
                pass

            return f"{oid}|{tag}|{value}"

        except Exception:
            # If parsing fails, return original line
            return line

    def get_cli_args(self) -> List[str]:
        """Get additional CLI arguments based on configuration.

        Returns:
            List of CLI arguments for snmpsim
        """
        args = []

        # Logging configuration
        if self.config["simulation"]["logging"]["enabled"]:
            log_config = self.config["simulation"]["logging"]
            if log_config["file"]:
                args.extend(["--logging-method", f"file:{log_config['file']}"])
            args.extend(["--log-level", log_config["level"]])

        # Metrics configuration
        if self.config["simulation"]["metrics"]["enabled"]:
            metrics_config = self.config["simulation"]["metrics"]
            format_map = {
                "json": "fulljson",
                "minimal": "minimaljson",
                "prometheus": "null",  # Will need custom handling
            }
            report_format = format_map.get(
                metrics_config["export"]["format"], "fulljson"
            )
            args.extend(["--reporting-method", report_format])

        return args

    def should_restart(self) -> Tuple[bool, int]:
        """Check if restart behavior is enabled.

        Returns:
            Tuple of (enabled, interval_seconds)
        """
        restart_config = self.config["simulation"]["behaviors"]["restart"]
        return restart_config["enabled"], restart_config.get("interval", 300)
