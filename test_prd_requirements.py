#!/usr/bin/env python
"""
Test script to verify PRD requirements for Mock SNMP Agent
"""

import subprocess
import time
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


def test_basic_snmp_functionality():
    """Test basic SNMP v1/v2c functionality"""
    print("=== Testing Basic SNMP Functionality ===")

    # Start the simulator using installed snmpsim-lextudio
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    with subprocess.Popen(
        [
            "snmpsim-command-responder",
            "--data-dir=./data",
            "--agent-udpv4-endpoint=127.0.0.1:11611",
            "--quiet",
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env=env,
    ) as simulator_process:

        # Give it time to start
        time.sleep(3)

        # Check if simulator started successfully
        if simulator_process.poll() is not None:
            stdout, stderr = simulator_process.communicate()
            print("Simulator failed to start!")
            print("STDERR:", stderr.decode())
            return

    try:
        # Test SNMPv1 GET
        print("\n1. Testing SNMPv1 GET:")
        result = subprocess.run(
            ["snmpget", "-v1", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Result: {result.stdout.strip()}")
        if result.stderr:
            print(f"   Error: {result.stderr.strip()}")
        print(f"   Success: {'SNMPv2-MIB::sysDescr.0' in result.stdout}")

        # Test SNMPv2c GET
        print("\n2. Testing SNMPv2c GET:")
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Result: {result.stdout.strip()}")
        print(f"   Success: {'SNMPv2-MIB::sysDescr.0' in result.stdout}")

        # Test GETNEXT
        print("\n3. Testing GETNEXT:")
        result = subprocess.run(
            ["snmpgetnext", "-v2c", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Result: {result.stdout.strip()}")
        print(f"   Success: {'SNMPv2-MIB::sysDescr.0' in result.stdout}")

        # Test GETBULK
        print("\n4. Testing GETBULK:")
        result = subprocess.run(
            [
                "snmpbulkget",
                "-v2c",
                "-c",
                "public",
                "-Cn0",
                "-Cr5",  # non-repeaters=0, max-repetitions=5
                "127.0.0.1:11611",
                "1.3.6.1.2.1.1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Result (first line): {result.stdout.split(chr(10))[0]}")
        print(f"   Success: {len(result.stdout.strip().split(chr(10))) >= 5}")

        # Test SNMPv3
        print("\n5. Testing SNMPv3 (noAuthNoPriv):")
        result = subprocess.run(
            [
                "snmpget",
                "-v3",
                "-l",
                "noAuthNoPriv",
                "-u",
                "simulator",
                "127.0.0.1:11611",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Result: {result.stdout.strip()}")
        print(f"   Success: {'SNMPv2-MIB::sysDescr.0' in result.stdout}")

    except Exception as exc:
        print(f"Error during testing: {exc}")
    finally:
        # Stop the simulator
        simulator_process.terminate()
        simulator_process.wait()
        print("\nSimulator stopped.")


def check_snmp_tools():
    """Check if SNMP tools are installed"""
    print("=== Checking SNMP Tools ===")
    tools = ["snmpget", "snmpgetnext", "snmpbulkget", "snmpset"]
    all_present = True

    for tool in tools:
        result = subprocess.run(["which", tool], capture_output=True, check=False)
        if result.returncode == 0:
            print(f"✓ {tool} found at: {result.stdout.decode().strip()}")
        else:
            print(f"✗ {tool} NOT FOUND - please install net-snmp tools")
            all_present = False

    return all_present


if __name__ == "__main__":
    print("Mock SNMP Agent PRD Requirements Test")
    print("=====================================\n")

    # Check for SNMP tools
    if not check_snmp_tools():
        print("\nPlease install net-snmp tools:")
        print("  macOS: brew install net-snmp")
        print("  Ubuntu/Debian: apt-get install snmp")
        print("  RHEL/CentOS: yum install net-snmp-utils")
        sys.exit(1)

    # Run tests
    test_basic_snmp_functionality()
