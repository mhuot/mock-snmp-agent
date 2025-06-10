#!/usr/bin/env python3
"""
Simple PRD Requirements Test

Quick validation that core PRD requirements are met.
"""

import os
import subprocess
import sys
import time


def test_snmp_protocols():
    """Test basic SNMP protocol support"""
    print("🔍 Testing SNMP Protocol Support...")

    tests = [
        (
            "SNMPv1",
            ["snmpget", "-v1", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"],
        ),
        (
            "SNMPv2c",
            ["snmpget", "-v2c", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1.1.0"],
        ),
        (
            "SNMPv3",
            [
                "snmpget",
                "-v3",
                "-l",
                "authPriv",
                "-u",
                "simulator",
                "-a",
                "MD5",
                "-A",
                "auctoritas",
                "-x",
                "DES",
                "-X",
                "privatus",
                "127.0.0.1:11611",
                "1.3.6.1.2.1.1.1.0",
            ],
        ),
        (
            "GETNEXT",
            ["snmpgetnext", "-v2c", "-c", "public", "127.0.0.1:11611", "1.3.6.1.2.1.1"],
        ),
        (
            "GETBULK",
            [
                "snmpbulkget",
                "-v2c",
                "-c",
                "public",
                "-Cn0",
                "-Cr3",
                "127.0.0.1:11611",
                "1.3.6.1.2.1.1",
            ],
        ),
    ]

    results = []
    for test_name, cmd in tests:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {test_name}: PASS")
                results.append(True)
            else:
                print(f"  ❌ {test_name}: FAIL - {result.stderr.strip()}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {test_name}: FAIL - {str(e)}")
            results.append(False)

    return results


def test_performance():
    """Test basic performance requirements"""
    print("\n⚡ Testing Performance...")

    response_times = []
    successful = 0

    for i in range(10):
        try:
            start = time.time()
            result = subprocess.run(
                [
                    "snmpget",
                    "-v2c",
                    "-c",
                    "public",
                    "127.0.0.1:11611",
                    "1.3.6.1.2.1.1.1.0",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            end = time.time()

            if result.returncode == 0:
                response_times.append((end - start) * 1000)  # Convert to ms
                successful += 1
        except:
            pass

    if successful >= 8:
        avg_time = sum(response_times) / len(response_times)
        print(
            f"  ✅ Response Time: {avg_time:.2f}ms average ({successful}/10 successful)"
        )
        return avg_time < 500  # Reasonable threshold
    else:
        print(f"  ❌ Performance: Too many failures ({10-successful}/10 failed)")
        return False


def test_configuration():
    """Test configuration file support"""
    print("\n⚙️ Testing Configuration...")

    config_files = [
        "config/comprehensive.yaml",
        "config/simple.yaml",
        "config/advanced.yaml",
    ]
    found = False

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ Configuration file found: {config_file}")
            found = True
            break

    if not found:
        print("  ❌ No configuration files found")

    return found


def test_data_files():
    """Test SNMP data file support"""
    print("\n📁 Testing Data Files...")

    data_dir = "data"
    if os.path.exists(data_dir):
        snmprec_files = [f for f in os.listdir(data_dir) if f.endswith(".snmprec")]
        if snmprec_files:
            print(f"  ✅ SNMP data files found: {snmprec_files}")
            return True
        else:
            print("  ❌ No .snmprec files found in data directory")
            return False
    else:
        print("  ❌ Data directory not found")
        return False


def main():
    """Main test function"""
    print("🚀 Simple PRD Requirements Test")
    print("=" * 40)

    # Check if we're in the right directory
    if not os.path.exists("mock_snmp_agent.py"):
        print("❌ mock_snmp_agent.py not found. Run from project root.")
        return 1

    # Start the SNMP agent
    print("🚀 Starting Mock SNMP Agent...")
    agent_process = subprocess.Popen(
        [sys.executable, "mock_snmp_agent.py", "--port", "11611"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for agent to start
    time.sleep(10)

    try:
        # Run tests
        snmp_results = test_snmp_protocols()
        perf_result = test_performance()
        config_result = test_configuration()
        data_result = test_data_files()

        # Calculate results
        total_tests = len(snmp_results) + 3  # SNMP tests + perf + config + data
        passed_tests = sum(snmp_results) + sum(
            [perf_result, config_result, data_result]
        )

        print(f"\n📊 Results Summary")
        print("=" * 40)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")

        success_rate = (passed_tests / total_tests) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("\n🎉 Core PRD Requirements: VALIDATED ✅")
            print("The Mock SNMP Agent meets basic PRD requirements!")
            return 0
        else:
            print("\n❌ Core PRD Requirements: NOT MET")
            print("Some basic requirements are failing.")
            return 1

    finally:
        # Stop the agent
        agent_process.terminate()
        try:
            agent_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            agent_process.kill()
        print("🛑 Mock SNMP Agent stopped")


if __name__ == "__main__":
    sys.exit(main())
