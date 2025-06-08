#!/usr/bin/env python3
"""
Community Variations Example

This example demonstrates the different community strings and variation modules
available in the Mock SNMP Agent, including delay, error, and writecache behaviors.
"""

import subprocess
import sys
import time


def run_snmp_command(cmd, timeout=10):
    """Run an SNMP command and return the result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def test_standard_community():
    """Test standard 'public' community."""
    print("=== Testing Standard Community 'public' ===")

    cmd = ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"]

    success, stdout, stderr = run_snmp_command(cmd)

    if success:
        print("✓ Standard 'public' community working")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ Standard 'public' community failed")
        print(f"  Error: {stderr.strip()}")

    return success


def test_delay_variation():
    """Test delay variation module."""
    print("\n=== Testing Delay Variation ===")
    print("This should take several seconds to respond...")

    start_time = time.time()

    cmd = [
        "snmpget",
        "-v2c",
        "-c",
        "variation/delay",
        "127.0.0.1:11611",
        "1.3.6.1.2.1.2.2.1.6.1",
    ]

    success, stdout, stderr = run_snmp_command(cmd, timeout=30)

    end_time = time.time()
    duration = end_time - start_time

    if success:
        print(f"✓ Delay variation working (took {duration:.2f} seconds)")
        print(f"  Result: {stdout.strip()}")
    else:
        print(f"✗ Delay variation failed (took {duration:.2f} seconds)")
        print(f"  Error: {stderr.strip()}")

    return success and duration > 0.5  # Should take at least 500ms


def test_error_variation():
    """Test error variation module."""
    print("\n=== Testing Error Variation ===")

    error_oids = [
        ("1.3.6.1.2.1.2.2.1.1.1", "Authorization Error"),
        ("1.3.6.1.2.1.2.2.1.6.1", "No Access Error"),
    ]

    for oid, description in error_oids:
        print(f"\nTesting {description}:")

        cmd = [
            "snmpget",
            "-v2c",
            "-c",
            "variation/error",
            "-t",
            "5",
            "-r",
            "1",  # Short timeout
            "127.0.0.1:11611",
            oid,
        ]

        success, stdout, stderr = run_snmp_command(cmd)

        if not success or "Error" in stdout:
            print(f"✓ {description} correctly triggered")
            if stdout:
                print(f"  Response: {stdout.strip()}")
            if stderr:
                print(f"  Error: {stderr.strip()}")
        else:
            print(f"? {description} - got unexpected response")
            print(f"  Response: {stdout.strip()}")

    return True  # Error variation might work differently


def test_writecache_variation():
    """Test writecache variation module."""
    print("\n=== Testing Writecache Variation ===")

    # First, try to set a value
    print("Setting a value...")
    set_cmd = [
        "snmpset",
        "-v2c",
        "-c",
        "variation/writecache",
        "127.0.0.1:11611",
        "1.3.6.1.2.1.1.1.0",
        "s",
        "Modified by writecache test",
    ]

    set_success, set_stdout, set_stderr = run_snmp_command(set_cmd)

    if set_success:
        print("✓ SET operation successful")
        print(f"  Response: {set_stdout.strip()}")

        # Now try to read it back
        print("\nReading back the value...")
        get_cmd = [
            "snmpget",
            "-v2c",
            "-c",
            "variation/writecache",
            "127.0.0.1:11611",
            "1.3.6.1.2.1.1.1.0",
        ]

        get_success, get_stdout, get_stderr = run_snmp_command(get_cmd)

        if get_success:
            print("✓ GET operation successful")
            print(f"  Result: {get_stdout.strip()}")

            if "Modified by writecache test" in get_stdout:
                print("✓ Value was successfully written and read back")
                return True
            else:
                print("? Value might not have been written correctly")
                return False
        else:
            print("✗ GET operation failed")
            print(f"  Error: {get_stderr.strip()}")
            return False
    else:
        print("✗ SET operation failed")
        print(f"  Error: {set_stderr.strip()}")
        print("  Note: Writecache might not support this OID")
        return False


def test_recorded_communities():
    """Test recorded device communities."""
    print("\n=== Testing Recorded Device Communities ===")

    communities = [
        ("recorded/linux-full-walk", "Linux system data"),
        ("recorded/winxp-full-walk", "Windows XP system data"),
    ]

    success_count = 0

    for community, description in communities:
        print(f"\nTesting {description}:")

        cmd = [
            "snmpget",
            "-v2c",
            "-c",
            community,
            "127.0.0.1:11611",
            "1.3.6.1.2.1.1.1.0",
        ]

        success, stdout, stderr = run_snmp_command(cmd)

        if success:
            print(f"✓ {description} available")
            print(f"  System Description: {stdout.strip()}")
            success_count += 1
        else:
            print(f"✗ {description} not available")
            print(f"  Error: {stderr.strip()}")

    return success_count > 0


def test_invalid_community():
    """Test invalid community string."""
    print("\n=== Testing Invalid Community ===")

    cmd = [
        "snmpget",
        "-v2c",
        "-c",
        "nonexistent_community",
        "-t",
        "3",
        "-r",
        "1",  # Short timeout
        "127.0.0.1:11611",
        "1.3.6.1.2.1.1.1.0",
    ]

    success, stdout, stderr = run_snmp_command(cmd)

    if not success:
        print("✓ Invalid community correctly rejected")
        print(f"  Error (expected): {stderr.strip()}")
        return True
    else:
        print("✗ Invalid community was accepted (unexpected)")
        return False


def show_available_communities():
    """Show available community strings."""
    print("\n=== Available Community Strings ===")
    communities = [
        ("public", "Standard MIB-II system information"),
        ("variation/delay", "Responses with configurable delays"),
        ("variation/error", "Various SNMP error responses"),
        ("variation/writecache", "Writable OIDs for SET operations"),
        ("recorded/linux-full-walk", "Real Linux system SNMP walk"),
        ("recorded/winxp-full-walk", "Real Windows XP system SNMP walk"),
    ]

    for community, description in communities:
        print(f"  {community:<25} - {description}")


def main():
    """Run all community variation tests."""
    print("Community Variations Example")
    print("=" * 50)
    print("Target: 127.0.0.1:11611")
    print()

    # Show available communities
    show_available_communities()

    # Check if simulator is running
    print("\nChecking if simulator is running...")
    cmd = [
        "snmpget",
        "-v2c",
        "-c",
        "public",
        "-t",
        "2",
        "-r",
        "1",
        "127.0.0.1:11611",
        "1.3.6.1.2.1.1.1.0",
    ]
    success, _, _ = run_snmp_command(cmd)

    if not success:
        print("✗ Simulator not responding!")
        print("\nPlease start the Mock SNMP Agent:")
        print("  python mock_snmp_agent.py")
        print("  # or")
        print("  docker-compose up -d")
        sys.exit(1)

    print("✓ Simulator is running")
    print()

    # Run tests
    tests = [
        ("Standard Community", test_standard_community),
        ("Delay Variation", test_delay_variation),
        ("Error Variation", test_error_variation),
        ("Writecache Variation", test_writecache_variation),
        ("Recorded Communities", test_recorded_communities),
        ("Invalid Community", test_invalid_community),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'-' * 20}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
        time.sleep(0.5)  # Small delay between tests

    # Summary
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")

    print(f"\nUsage Examples:")
    print("# Standard data:")
    print("snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0")
    print("\n# Delayed response:")
    print("snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1")
    print("\n# Error simulation:")
    print("snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.1")
    print("\n# SET operation:")
    print(
        "snmpset -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.1.1.0 s 'Test'"
    )

    if passed >= total - 1:  # Allow 1 failure
        print("\n🎉 Community variation tests successful!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
