#!/usr/bin/env python3
"""
Delay behavior demonstration for Mock SNMP Agent.

This example demonstrates how to use delay simulation to test SNMP client
timeout handling and latency behavior.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_delay_test(delay_ms, description):
    """Run a test with specified delay."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Expected delay: ~{delay_ms}ms")
    print("=" * 60)

    # Start the mock agent
    cmd = [
        sys.executable,
        "mock_snmp_agent.py",
        "--delay",
        str(delay_ms),
        "--port",
        "11613",
        "--quiet",
    ]

    print(f"Starting agent: {' '.join(cmd)}")
    agent = subprocess.Popen(cmd)

    try:
        # Wait for agent to start
        time.sleep(2)

        # Test SNMP GET with timing
        start_time = time.time()
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11613", "1.3.6.1.2.1.1.1.0"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        if result.returncode == 0:
            print(f"✓ Response received in {elapsed_ms:.0f}ms")
            print(f"  Value: {result.stdout.strip().split('=')[1].strip()}")

            # Check if delay is roughly correct (within 100ms tolerance)
            if abs(elapsed_ms - delay_ms) < 100:
                print(f"✓ Delay is within expected range")
            else:
                print(
                    f"⚠ Delay differs from expected by {abs(elapsed_ms - delay_ms):.0f}ms"
                )
        else:
            print(f"✗ SNMP request failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        print(f"✗ Request timed out (>{delay_ms}ms)")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Clean up
        agent.terminate()
        agent.wait()


def run_config_test():
    """Test using configuration file."""
    print(f"\n{'='*60}")
    print("Testing: Configuration file with delay")
    print("=" * 60)

    # Start agent with config
    cmd = [
        sys.executable,
        "mock_snmp_agent.py",
        "--config",
        "config/simple.yaml",
        "--port",
        "11614",
        "--quiet",
    ]

    print(f"Starting agent: {' '.join(cmd)}")
    agent = subprocess.Popen(cmd)

    try:
        time.sleep(2)

        start_time = time.time()
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11614", "1.3.6.1.2.1.1.1.0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        if result.returncode == 0:
            print(f"✓ Response received in {elapsed_ms:.0f}ms")
            print(f"  Configuration delay: 100ms (±20ms deviation)")
            print(f"  Value: {result.stdout.strip().split('=')[1].strip()}")
        else:
            print(f"✗ SNMP request failed: {result.stderr}")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        agent.terminate()
        agent.wait()


def main():
    """Main demo function."""
    print("Mock SNMP Agent - Delay Behavior Demonstration")
    print("This demo shows how delays affect SNMP response times")

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
        # Test various delay scenarios
        run_delay_test(0, "No delay (baseline)")
        run_delay_test(100, "100ms delay")
        run_delay_test(500, "500ms delay")
        run_delay_test(1000, "1 second delay")

        # Test configuration file
        run_config_test()

        print(f"\n{'='*60}")
        print("Demo completed!")
        print("\nKey findings:")
        print("- Delays are applied to all SNMP responses")
        print("- Configuration files allow complex delay patterns")
        print("- Useful for testing SNMP client timeout handling")
        print("- Helps simulate slow or distant network devices")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
