#!/usr/bin/env python3
"""
SNMPv3 Security Failure Simulation

This module provides simulation of various SNMPv3 security failures
for testing SNMP monitoring tools' error handling capabilities.

Simulates:
- Time window violations (clock skew beyond 150-second window)
- Authentication failures (wrong credentials, unsupported algorithms)
- Privacy failures (decryption errors, unsupported encryption)
- Engine discovery failures (wrong engine ID, boot counter issues)
"""

import random
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SecurityFailureConfig:
    """Configuration for SNMPv3 security failure simulation."""

    time_window_enabled: bool = False
    clock_skew_seconds: int = 200
    time_window_failure_rate: int = 15

    auth_failures_enabled: bool = False
    wrong_credentials_rate: int = 10
    unsupported_auth_rate: int = 5
    unknown_user_rate: int = 8

    privacy_failures_enabled: bool = False
    decryption_error_rate: int = 7
    unsupported_privacy_rate: int = 3

    engine_failures_enabled: bool = False
    wrong_engine_id_rate: int = 12
    boot_counter_issues_rate: int = 5


class SNMPv3SecuritySimulator:
    """
    Simulates various SNMPv3 security failures for testing purposes.

    This class generates .snmprec entries that trigger different types
    of SNMPv3 security errors during retrieval operations.
    """

    def __init__(self, config: SecurityFailureConfig):
        """Initialize the security failure simulator."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Standard security error codes
        self.error_codes = {
            "time_window": "notInTimeWindow",
            "auth_failure": "authenticationFailure",
            "wrong_digest": "wrongDigest",
            "unknown_user": "unknownUserName",
            "unsupported_security": "unsupportedSecurityLevel",
            "decryption_error": "decryptionError",
            "wrong_length": "wrongLength",
            "unknown_engine": "unknownEngineID",
        }

    def should_trigger_failure(self, failure_type: str, base_rate: int) -> bool:
        """Determine if a security failure should be triggered."""
        if not self._is_failure_type_enabled(failure_type):
            return False

        return random.randint(1, 100) <= base_rate

    def _is_failure_type_enabled(self, failure_type: str) -> bool:
        """Check if a specific failure type is enabled."""
        type_mapping = {
            "time_window": self.config.time_window_enabled,
            "auth": self.config.auth_failures_enabled,
            "privacy": self.config.privacy_failures_enabled,
            "engine": self.config.engine_failures_enabled,
        }
        return type_mapping.get(failure_type, False)

    def generate_time_window_failure(self, oid: str) -> Optional[str]:
        """Generate time window violation failure."""
        if not self.should_trigger_failure(
            "time_window", self.config.time_window_failure_rate
        ):
            return None

        # Use error variation module to trigger time window failure
        error_tag = f"error|status={self.error_codes['time_window']}"
        return f"{oid}|4:{error_tag}|Time window violation simulated"

    def generate_auth_failure(self, oid: str) -> Optional[str]:
        """Generate authentication failure."""
        if not self.should_trigger_failure("auth", self.config.wrong_credentials_rate):
            return None

        # Randomly select auth failure type
        failure_types = [
            self.error_codes["auth_failure"],
            self.error_codes["wrong_digest"],
            self.error_codes["unknown_user"],
        ]

        error_code = random.choice(failure_types)
        error_tag = f"error|status={error_code}"
        return f"{oid}|4:{error_tag}|Authentication failure simulated"

    def generate_privacy_failure(self, oid: str) -> Optional[str]:
        """Generate privacy/encryption failure."""
        if not self.should_trigger_failure(
            "privacy", self.config.decryption_error_rate
        ):
            return None

        # Privacy-related errors
        failure_types = [
            self.error_codes["decryption_error"],
            self.error_codes["wrong_length"],
        ]

        error_code = random.choice(failure_types)
        error_tag = f"error|status={error_code}"
        return f"{oid}|4:{error_tag}|Privacy failure simulated"

    def generate_engine_failure(self, oid: str) -> Optional[str]:
        """Generate engine discovery failure."""
        if not self.should_trigger_failure("engine", self.config.wrong_engine_id_rate):
            return None

        error_tag = f"error|status={self.error_codes['unknown_engine']}"
        return f"{oid}|4:{error_tag}|Engine discovery failure simulated"

    def generate_security_failures(self, base_oids: List[str]) -> List[str]:
        """
        Generate .snmprec entries with various security failures.

        Args:
            base_oids: List of OIDs to apply security failures to

        Returns:
            List of .snmprec lines with security failure variations
        """
        failure_entries = []

        for oid in base_oids:
            # Try each failure type
            failures = [
                self.generate_time_window_failure(oid),
                self.generate_auth_failure(oid),
                self.generate_privacy_failure(oid),
                self.generate_engine_failure(oid),
            ]

            # Add non-None failures
            failure_entries.extend([f for f in failures if f is not None])

        if failure_entries:
            self.logger.info(
                f"Generated {len(failure_entries)} security failure entries"
            )

        return failure_entries

    def create_security_test_data(self, output_file: str) -> None:
        """
        Create a complete .snmprec file with security failure test data.

        Args:
            output_file: Path to output .snmprec file
        """
        # Standard test OIDs for security testing
        test_oids = [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.2.0",  # sysObjectID
            "1.3.6.1.2.1.1.3.0",  # sysUpTime
            "1.3.6.1.2.1.1.4.0",  # sysContact
            "1.3.6.1.2.1.1.5.0",  # sysName
            "1.3.6.1.2.1.1.6.0",  # sysLocation
            "1.3.6.1.2.1.2.1.0",  # ifNumber
            "1.3.6.1.2.1.2.2.1.1.1",  # ifIndex
            "1.3.6.1.2.1.2.2.1.2.1",  # ifDescr
            "1.3.6.1.2.1.2.2.1.10.1",  # ifInOctets
        ]

        # Generate normal responses first
        normal_entries = [
            "1.3.6.1.2.1.1.1.0|4|SNMPv3 Security Test System",
            "1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10",
            "1.3.6.1.2.1.1.3.0|67|12345600",
            "1.3.6.1.2.1.1.4.0|4|Security Test Contact",
            "1.3.6.1.2.1.1.5.0|4|security-test-agent",
            "1.3.6.1.2.1.1.6.0|4|Security Testing Lab",
            "1.3.6.1.2.1.2.1.0|2|2",
            "1.3.6.1.2.1.2.2.1.1.1|2|1",
            "1.3.6.1.2.1.2.2.1.2.1|4|eth0",
            "1.3.6.1.2.1.2.2.1.10.1|41|1234567890",
        ]

        # Generate security failure entries
        security_entries = self.generate_security_failures(test_oids)

        # Combine and write to file
        all_entries = normal_entries + security_entries

        with open(output_file, "w") as f:
            f.write("# SNMPv3 Security Failure Test Data\n")
            f.write("# Generated by SNMPv3SecuritySimulator\n")
            f.write(f"# Configuration: {self.config}\n")
            f.write("\n")

            for entry in all_entries:
                f.write(f"{entry}\n")

        self.logger.info(f"Created security test data file: {output_file}")
        self.logger.info(
            f"Total entries: {len(all_entries)} "
            f"(Normal: {len(normal_entries)}, "
            f"Security failures: {len(security_entries)})"
        )

    def get_security_statistics(self) -> Dict[str, any]:
        """Get statistics about enabled security failure types."""
        stats = {"enabled_failures": [], "failure_rates": {}, "total_failure_types": 0}

        if self.config.time_window_enabled:
            stats["enabled_failures"].append("time_window_violations")
            stats["failure_rates"]["time_window"] = self.config.time_window_failure_rate

        if self.config.auth_failures_enabled:
            stats["enabled_failures"].append("authentication_failures")
            stats["failure_rates"]["auth"] = {
                "wrong_credentials": self.config.wrong_credentials_rate,
                "unsupported_auth": self.config.unsupported_auth_rate,
                "unknown_user": self.config.unknown_user_rate,
            }

        if self.config.privacy_failures_enabled:
            stats["enabled_failures"].append("privacy_failures")
            stats["failure_rates"]["privacy"] = {
                "decryption_error": self.config.decryption_error_rate,
                "unsupported_privacy": self.config.unsupported_privacy_rate,
            }

        if self.config.engine_failures_enabled:
            stats["enabled_failures"].append("engine_discovery_failures")
            stats["failure_rates"]["engine"] = {
                "wrong_engine_id": self.config.wrong_engine_id_rate,
                "boot_counter_issues": self.config.boot_counter_issues_rate,
            }

        stats["total_failure_types"] = len(stats["enabled_failures"])

        return stats


def create_security_config_from_dict(config_dict: Dict) -> SecurityFailureConfig:
    """Create SecurityFailureConfig from dictionary (for YAML loading)."""
    security_config = config_dict.get("snmpv3_security", {})

    time_window = security_config.get("time_window_failures", {})
    auth = security_config.get("authentication_failures", {})
    privacy = security_config.get("privacy_failures", {})
    engine = security_config.get("engine_discovery_failures", {})

    return SecurityFailureConfig(
        time_window_enabled=time_window.get("enabled", False),
        clock_skew_seconds=time_window.get("clock_skew_seconds", 200),
        time_window_failure_rate=time_window.get("failure_rate", 15),
        auth_failures_enabled=auth.get("enabled", False),
        wrong_credentials_rate=auth.get("wrong_credentials_rate", 10),
        unsupported_auth_rate=auth.get("unsupported_auth_rate", 5),
        unknown_user_rate=auth.get("unknown_user_rate", 8),
        privacy_failures_enabled=privacy.get("enabled", False),
        decryption_error_rate=privacy.get("decryption_error_rate", 7),
        unsupported_privacy_rate=privacy.get("unsupported_privacy_rate", 3),
        engine_failures_enabled=engine.get("enabled", False),
        wrong_engine_id_rate=engine.get("wrong_engine_id_rate", 12),
        boot_counter_issues_rate=engine.get("boot_counter_issues_rate", 5),
    )


if __name__ == "__main__":
    # Demo usage
    config = SecurityFailureConfig(
        time_window_enabled=True,
        auth_failures_enabled=True,
        privacy_failures_enabled=True,
        engine_failures_enabled=True,
    )

    simulator = SNMPv3SecuritySimulator(config)
    simulator.create_security_test_data("snmpv3_security_test.snmprec")

    stats = simulator.get_security_statistics()
    print("Security Failure Configuration:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
