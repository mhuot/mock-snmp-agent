#!/usr/bin/env python3
"""
Drop behavior demonstration for Mock SNMP Agent.

This example demonstrates how to simulate intermittent responses
and packet loss for testing SNMP client retry logic.
"""

import subprocess
import sys
import time
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_drop_behavior(drop_rate, num_requests=20):
    """Test drop behavior with multiple requests."""
    print(f"\n{'='*60}")
    print(f"Testing: {drop_rate}% drop rate with {num_requests} requests")
    print("=" * 60)

    # Start agent with drop rate
    cmd = [
        sys.executable,
        "mock_snmp_agent.py",
        "--drop-rate",
        str(drop_rate),
        "--port",
        "11615",
        "--quiet",
    ]

    print(f"Starting agent: {' '.join(cmd)}")
    agent = subprocess.Popen(cmd)

    try:
        time.sleep(2)

        success_count = 0
        timeout_count = 0
        error_count = 0

        print(f"Sending {num_requests} SNMP requests...")

        for i in range(num_requests):
            try:
                result = subprocess.run(
                    [
                        "snmpget",
                        "-v2c",
                        "-c",
                        "public",
                        "-t",
                        "2",
                        "-r",
                        "1",
                        "127.0.0.1:11615",
                        "1.3.6.1.2.1.1.1.0",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                if result.returncode == 0:
                    success_count += 1
                    print(f"  Request {i+1:2d}: ✓ Success")
                else:
                    error_count += 1
                    print(f"  Request {i+1:2d}: ✗ Error/Drop")

            except subprocess.TimeoutExpired:
                timeout_count += 1
                print(f"  Request {i+1:2d}: ⏱ Timeout")

        total_failures = error_count + timeout_count
        actual_drop_rate = (total_failures / num_requests) * 100

        print(f"\nResults:")
        print(f"  Successful requests: {success_count}/{num_requests}")
        print(f"  Failed/dropped requests: {total_failures}/{num_requests}")
        print(f"  Actual drop rate: {actual_drop_rate:.1f}%")
        print(f"  Expected drop rate: {drop_rate}%")

        if abs(actual_drop_rate - drop_rate) < 15:  # Allow some variance
            print(f"✓ Drop rate is within expected range")
        else:
            print(f"⚠ Drop rate differs significantly from expected")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        agent.terminate()
        agent.wait()


def main():
    """Main demo function."""
    print("Mock SNMP Agent - Drop Behavior Demonstration")
    print("This demo shows how drop rates affect SNMP reliability")

    # Check if we have snmpget available
    try:
        subprocess.run(["snmpget", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n✗ Error: snmpget command not found!")
        print("Please install net-snmp tools:")
        print("  macOS: brew install net-snmp")
        print("  Ubuntu: sudo apt-get install snmp-utils")
        return 1

    try:
        # Test various drop rates
        test_drop_behavior(0, 10)  # Baseline - no drops
        test_drop_behavior(20, 20)  # 20% drop rate
        test_drop_behavior(50, 20)  # 50% drop rate

        print(f"\n{'='*60}")
        print("Demo completed!")
        print("\nKey findings:")
        print("- Drop simulation helps test SNMP client retry logic")
        print("- Higher drop rates increase request failures")
        print("- Useful for testing unreliable network conditions")
        print("- Helps validate SNMP monitoring system resilience")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
