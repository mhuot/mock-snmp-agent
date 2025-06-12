#!/usr/bin/env python3
"""
SNMPv3 Security Failure Demonstration

This script demonstrates various SNMPv3 security failure scenarios
and how they can be used to test SNMP monitoring tool resilience.

Usage:
    python examples/snmpv3_security_demo.py

Prerequisites:
    - Mock SNMP Agent running with SNMPv3 security configuration
    - net-snmp tools installed (snmpget, snmpwalk, etc.)
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


class SNMPv3SecurityDemo:
    """Demonstrates SNMPv3 security failure scenarios."""

    def __init__(self, agent_host: str = "127.0.0.1", agent_port: int = 11611):
        """Initialize the demo."""
        self.agent_host = agent_host
        self.agent_port = agent_port
        self.endpoint = f"{agent_host}:{agent_port}"

        # Standard test OIDs
        self.test_oids = [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.2.0",  # sysObjectID
            "1.3.6.1.2.1.1.3.0",  # sysUpTime
            "1.3.6.1.2.1.1.4.0",  # sysContact
            "1.3.6.1.2.1.1.5.0",  # sysName
        ]

        # SNMPv3 configurations for testing
        self.snmpv3_configs = {
            "noauth": {
                "security_level": "noAuthNoPriv",
                "user": "simulator",
                "auth_protocol": None,
                "auth_key": None,
                "privacy_protocol": None,
                "privacy_key": None,
            },
            "auth_only": {
                "security_level": "authNoPriv",
                "user": "simulator",
                "auth_protocol": "MD5",
                "auth_key": "auctoritas",
                "privacy_protocol": None,
                "privacy_key": None,
            },
            "auth_priv": {
                "security_level": "authPriv",
                "user": "simulator",
                "auth_protocol": "MD5",
                "auth_key": "auctoritas",
                "privacy_protocol": "DES",
                "privacy_key": "privatus",
            },
            "wrong_user": {
                "security_level": "authNoPriv",
                "user": "wronguser",
                "auth_protocol": "MD5",
                "auth_key": "auctoritas",
                "privacy_protocol": None,
                "privacy_key": None,
            },
            "wrong_auth": {
                "security_level": "authNoPriv",
                "user": "simulator",
                "auth_protocol": "MD5",
                "auth_key": "wrongkey",
                "privacy_protocol": None,
                "privacy_key": None,
            },
        }

    def build_snmp_command(
        self, config_name: str, oid: str, operation: str = "get"
    ) -> List[str]:
        """Build SNMP command based on configuration."""
        config = self.snmpv3_configs[config_name]

        cmd = [f"snmp{operation}", "-v3", "-l", config["security_level"]]

        # Add user
        cmd.extend(["-u", config["user"]])

        # Add authentication if needed
        if config["auth_protocol"]:
            cmd.extend(["-a", config["auth_protocol"]])
            cmd.extend(["-A", config["auth_key"]])

        # Add privacy if needed
        if config["privacy_protocol"]:
            cmd.extend(["-x", config["privacy_protocol"]])
            cmd.extend(["-X", config["privacy_key"]])

        # Add timeout and retry settings
        cmd.extend(["-t", "3", "-r", "1"])

        # Add target and OID
        cmd.extend([self.endpoint, oid])

        return cmd

    def run_snmp_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Run SNMP command and return results."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def test_security_configuration(
        self, config_name: str, expected_to_succeed: bool = True
    ) -> Dict:
        """Test a specific SNMPv3 security configuration."""
        print(f"\n--- Testing {config_name} configuration ---")
        config = self.snmpv3_configs[config_name]

        results = {
            "config_name": config_name,
            "expected_success": expected_to_succeed,
            "tests": [],
            "success_count": 0,
            "total_tests": 0,
        }

        for oid in self.test_oids:
            print(f"  Testing OID: {oid}")
            cmd = self.build_snmp_command(config_name, oid)

            success, stdout, stderr = self.run_snmp_command(cmd)

            test_result = {
                "oid": oid,
                "command": " ".join(cmd),
                "success": success,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "matches_expectation": success == expected_to_succeed,
            }

            results["tests"].append(test_result)
            results["total_tests"] += 1

            if success:
                results["success_count"] += 1
                if expected_to_succeed:
                    print(f"    ✓ SUCCESS: {stdout.strip()}")
                else:
                    print(f"    ⚠ UNEXPECTED SUCCESS: {stdout.strip()}")
            else:
                if not expected_to_succeed:
                    print(f"    ✓ EXPECTED FAILURE: {stderr.strip()}")
                else:
                    print(f"    ✗ UNEXPECTED FAILURE: {stderr.strip()}")

            time.sleep(0.5)  # Small delay between requests

        return results

    def test_all_security_scenarios(self) -> Dict:
        """Test all SNMPv3 security scenarios."""
        print("SNMPv3 Security Failure Testing")
        print("=" * 50)
        print(f"Target: {self.endpoint}")
        print()

        # Check if agent is responding
        print("Checking if Mock SNMP Agent is running...")
        basic_cmd = [
            "snmpget",
            "-v2c",
            "-c",
            "public",
            "-t",
            "2",
            "-r",
            "1",
            self.endpoint,
            "1.3.6.1.2.1.1.1.0",
        ]

        success, _, _ = self.run_snmp_command(basic_cmd)
        if not success:
            print("✗ Mock SNMP Agent is not responding!")
            print("\nPlease start the agent with SNMPv3 security configuration:")
            print(
                "  python mock_snmp_agent.py --config config/snmpv3_security_test.yaml"
            )
            return {"error": "Agent not responding"}

        print("✓ Mock SNMP Agent is responding")

        # Test scenarios
        all_results = {
            "timestamp": time.time(),
            "agent_endpoint": self.endpoint,
            "test_scenarios": [],
        }

        # Valid configurations (should succeed)
        valid_configs = ["noauth", "auth_only", "auth_priv"]
        for config in valid_configs:
            result = self.test_security_configuration(config, expected_to_succeed=True)
            all_results["test_scenarios"].append(result)

        # Invalid configurations (should fail due to security failures)
        invalid_configs = ["wrong_user", "wrong_auth"]
        for config in invalid_configs:
            result = self.test_security_configuration(config, expected_to_succeed=False)
            all_results["test_scenarios"].append(result)

        return all_results

    def generate_test_report(self, results: Dict) -> None:
        """Generate a test report."""
        if "error" in results:
            return

        print("\n" + "=" * 50)
        print("SNMPv3 Security Test Summary")
        print("=" * 50)

        total_scenarios = len(results["test_scenarios"])
        successful_scenarios = 0

        for scenario in results["test_scenarios"]:
            config_name = scenario["config_name"]
            success_rate = scenario["success_count"] / scenario["total_tests"] * 100
            expected = scenario["expected_success"]

            # Calculate if scenario behaved as expected
            matches_expectation = True
            for test in scenario["tests"]:
                if not test["matches_expectation"]:
                    matches_expectation = False
                    break

            if matches_expectation:
                successful_scenarios += 1
                status = "✓ PASS"
            else:
                status = "✗ FAIL"

            print(
                f"{status} {config_name:15s} - {success_rate:5.1f}% success "
                f"(expected: {'SUCCESS' if expected else 'FAILURE'})"
            )

        print(
            f"\nOverall: {successful_scenarios}/{total_scenarios} scenarios behaved as expected"
        )

        # Security failure analysis
        print(f"\nSecurity Failure Analysis:")
        print(
            f"- Time window violations: Detected by failed requests with time window errors"
        )
        print(
            f"- Authentication failures: Detected by wrong user/credentials rejections"
        )
        print(f"- Privacy failures: Would be shown in privacy-enabled communications")
        print(f"- Engine discovery failures: Shown in initial handshake problems")

        # Save detailed results
        output_file = Path("snmpv3_security_test_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nDetailed results saved to: {output_file}")

    def demonstrate_security_failures(self) -> None:
        """Run the complete security failure demonstration."""
        print("Starting SNMPv3 Security Failure Demonstration...")
        print("This will test various security failure scenarios.\n")

        results = self.test_all_security_scenarios()
        self.generate_test_report(results)

        print("\nDemo completed!")
        print("\nTo see the configured security failure rates, check:")
        print("  config/snmpv3_security_test.yaml")
        print(
            "\nTo modify failure rates, edit the configuration and restart the agent."
        )


def main():
    """Main demonstration function."""
    demo = SNMPv3SecurityDemo()
    demo.demonstrate_security_failures()


if __name__ == "__main__":
    main()
