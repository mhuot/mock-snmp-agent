#!/usr/bin/env python3
"""
Basic SNMP Testing Example

This example demonstrates basic SNMP operations using the Mock SNMP Agent.
It shows how to perform GET, GETNEXT, and GETBULK operations.
"""

import subprocess
import sys
import time


def run_snmp_command(cmd):
    """Run an SNMP command and return the result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def test_snmp_get():
    """Test basic SNMP GET operation."""
    print("=== Testing SNMP GET ===")
    
    cmd = [
        "snmpget", "-v2c", "-c", "public",
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMP GET successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMP GET failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_snmp_getnext():
    """Test SNMP GETNEXT operation."""
    print("\n=== Testing SNMP GETNEXT ===")
    
    cmd = [
        "snmpgetnext", "-v2c", "-c", "public",
        "127.0.0.1:11611", "1.3.6.1.2.1.1"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMP GETNEXT successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMP GETNEXT failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_snmp_getbulk():
    """Test SNMP GETBULK operation."""
    print("\n=== Testing SNMP GETBULK ===")
    
    cmd = [
        "snmpbulkget", "-v2c", "-c", "public",
        "-Cn0", "-Cr5",  # non-repeaters=0, max-repetitions=5
        "127.0.0.1:11611", "1.3.6.1.2.1.1"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMP GETBULK successful")
        lines = stdout.strip().split('\n')
        print(f"  Retrieved {len(lines)} OIDs:")
        for i, line in enumerate(lines[:3], 1):  # Show first 3
            print(f"    {i}. {line}")
        if len(lines) > 3:
            print(f"    ... and {len(lines) - 3} more")
    else:
        print("✗ SNMP GETBULK failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_different_oids():
    """Test different OIDs to show variety."""
    print("\n=== Testing Different OIDs ===")
    
    oids = [
        ("1.3.6.1.2.1.1.1.0", "System Description"),
        ("1.3.6.1.2.1.1.3.0", "System Uptime"),
        ("1.3.6.1.2.1.1.5.0", "System Name"),
        ("1.3.6.1.2.1.1.6.0", "System Location"),
    ]
    
    success_count = 0
    
    for oid, description in oids:
        cmd = ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11611", oid]
        success, stdout, stderr = run_snmp_command(cmd)
        
        if success:
            print(f"✓ {description}: {stdout.strip().split('=')[1].strip() if '=' in stdout else 'N/A'}")
            success_count += 1
        else:
            print(f"✗ {description}: Failed")
    
    return success_count == len(oids)


def test_snmp_walk():
    """Test SNMP WALK operation."""
    print("\n=== Testing SNMP WALK ===")
    
    cmd = [
        "snmpwalk", "-v2c", "-c", "public",
        "127.0.0.1:11611", "1.3.6.1.2.1.1"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        lines = stdout.strip().split('\n')
        print(f"✓ SNMP WALK successful - found {len(lines)} OIDs")
        print("  Sample results:")
        for i, line in enumerate(lines[:3], 1):
            print(f"    {i}. {line}")
        if len(lines) > 3:
            print(f"    ... and {len(lines) - 3} more")
    else:
        print("✗ SNMP WALK failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def main():
    """Run all basic SNMP tests."""
    print("Basic SNMP Testing Example")
    print("=" * 40)
    print("Target: 127.0.0.1:11611")
    print("Community: public")
    print()
    
    # Check if simulator is running
    print("Checking if simulator is running...")
    cmd = ["snmpget", "-v2c", "-c", "public", "-t", "2", "-r", "1",
           "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"]
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
        test_snmp_get,
        test_snmp_getnext,
        test_snmp_getbulk,
        test_different_oids,
        test_snmp_walk,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()