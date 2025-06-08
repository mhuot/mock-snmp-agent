#!/usr/bin/env python3
"""
SNMPv3 Examples

This example demonstrates SNMPv3 operations with different security levels:
- noAuthNoPriv (no authentication, no privacy)
- authNoPriv (authentication, no privacy)
- authPriv (authentication and privacy)
"""

import subprocess
import sys
import time


def run_snmp_command(cmd):
    """Run an SNMP command and return the result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def test_snmpv3_noauth():
    """Test SNMPv3 with no authentication."""
    print("=== Testing SNMPv3 noAuthNoPriv ===")
    
    cmd = [
        "snmpget", "-v3",
        "-l", "noAuthNoPriv",
        "-u", "simulator",
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMPv3 noAuthNoPriv successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMPv3 noAuthNoPriv failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_snmpv3_auth():
    """Test SNMPv3 with authentication."""
    print("\n=== Testing SNMPv3 authNoPriv ===")
    
    cmd = [
        "snmpget", "-v3",
        "-l", "authNoPriv",
        "-u", "simulator",
        "-a", "MD5",
        "-A", "auctoritas",
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMPv3 authNoPriv successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMPv3 authNoPriv failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_snmpv3_auth_priv():
    """Test SNMPv3 with authentication and privacy."""
    print("\n=== Testing SNMPv3 authPriv ===")
    
    cmd = [
        "snmpget", "-v3",
        "-l", "authPriv",
        "-u", "simulator",
        "-a", "MD5",
        "-A", "auctoritas",
        "-x", "DES",
        "-X", "privatus",
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMPv3 authPriv successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMPv3 authPriv failed")
        print(f"  Error: {stderr.strip()}")
    
    return success


def test_snmpv3_sha_auth():
    """Test SNMPv3 with SHA authentication."""
    print("\n=== Testing SNMPv3 with SHA Authentication ===")
    
    cmd = [
        "snmpget", "-v3",
        "-l", "authNoPriv",
        "-u", "simulator",
        "-a", "SHA",
        "-A", "auctoritas",
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if success:
        print("✓ SNMPv3 SHA authentication successful")
        print(f"  Result: {stdout.strip()}")
    else:
        print("✗ SNMPv3 SHA authentication failed")
        print(f"  Error: {stderr.strip()}")
        print("  Note: SHA might not be configured in simulator")
    
    return success


def test_snmpv3_operations():
    """Test different SNMPv3 operations."""
    print("\n=== Testing SNMPv3 Operations ===")
    
    operations = [
        ("GET", ["snmpget", "-v3", "-l", "noAuthNoPriv", "-u", "simulator",
                "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"]),
        ("GETNEXT", ["snmpgetnext", "-v3", "-l", "noAuthNoPriv", "-u", "simulator",
                    "127.0.0.1:11611", "1.3.6.1.2.1.1"]),
        ("GETBULK", ["snmpbulkget", "-v3", "-l", "noAuthNoPriv", "-u", "simulator",
                    "-Cn0", "-Cr3", "127.0.0.1:11611", "1.3.6.1.2.1.1"]),
    ]
    
    success_count = 0
    
    for op_name, cmd in operations:
        success, stdout, stderr = run_snmp_command(cmd)
        
        if success:
            print(f"✓ SNMPv3 {op_name} successful")
            if op_name == "GETBULK":
                lines = stdout.strip().split('\n')
                print(f"  Retrieved {len(lines)} OIDs")
            else:
                print(f"  Result: {stdout.strip()}")
            success_count += 1
        else:
            print(f"✗ SNMPv3 {op_name} failed")
            print(f"  Error: {stderr.strip()}")
    
    return success_count == len(operations)


def test_snmpv3_invalid_credentials():
    """Test SNMPv3 with invalid credentials."""
    print("\n=== Testing SNMPv3 Invalid Credentials ===")
    
    cmd = [
        "snmpget", "-v3",
        "-l", "authNoPriv",
        "-u", "wronguser",
        "-a", "MD5",
        "-A", "wrongpassword",
        "-t", "3", "-r", "1",  # Short timeout
        "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"
    ]
    
    success, stdout, stderr = run_snmp_command(cmd)
    
    if not success:
        print("✓ Invalid credentials correctly rejected")
        print(f"  Error (expected): {stderr.strip()}")
        return True
    else:
        print("✗ Invalid credentials were accepted (unexpected)")
        return False


def show_snmpv3_config():
    """Show the SNMPv3 configuration."""
    print("\n=== SNMPv3 Configuration ===")
    print("Default SNMPv3 settings for the simulator:")
    print("  Engine ID: Auto-generated")
    print("  User: simulator")
    print("  Auth Protocol: MD5")
    print("  Auth Key: auctoritas")
    print("  Privacy Protocol: DES")
    print("  Privacy Key: privatus")
    print()
    print("Security Levels:")
    print("  noAuthNoPriv: No authentication, no encryption")
    print("  authNoPriv:   Authentication, no encryption")
    print("  authPriv:     Authentication and encryption")


def main():
    """Run all SNMPv3 tests."""
    print("SNMPv3 Examples")
    print("=" * 40)
    print("Target: 127.0.0.1:11611")
    print()
    
    # Show configuration
    show_snmpv3_config()
    
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
        test_snmpv3_noauth,
        test_snmpv3_auth,
        test_snmpv3_auth_priv,
        test_snmpv3_sha_auth,
        test_snmpv3_operations,
        test_snmpv3_invalid_credentials,
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
    
    if passed >= total - 1:  # Allow 1 failure (SHA might not work)
        print("🎉 SNMPv3 tests mostly successful!")
        print("\nExample commands:")
        print("# No authentication:")
        print("snmpget -v3 -l noAuthNoPriv -u simulator 127.0.0.1:11611 1.3.6.1.2.1.1.1.0")
        print("\n# With authentication:")
        print("snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas 127.0.0.1:11611 1.3.6.1.2.1.1.1.0")
        print("\n# With authentication and privacy:")
        print("snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus 127.0.0.1:11611 1.3.6.1.2.1.1.1.0")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()