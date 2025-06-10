#!/usr/bin/env python3
"""
Test Setup Validation Script

This script validates that all testing infrastructure is properly configured
before running the comprehensive Docker tests.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (missing)")
        return False


def check_docker_setup() -> bool:
    """Check Docker installation and availability."""
    print("\nChecking Docker setup...")

    try:
        # Check Docker command
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker: {result.stdout.strip()}")
        else:
            print("✗ Docker: Command failed")
            return False

        # Check Docker Compose
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✓ Docker Compose: {result.stdout.strip()}")
        else:
            print("✗ Docker Compose: Command failed")
            return False

        # Check Docker daemon
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Docker daemon: Running")
        else:
            print("✗ Docker daemon: Not running")
            return False

        return True

    except FileNotFoundError:
        print("✗ Docker: Not installed")
        return False


def validate_config_files() -> bool:
    """Validate configuration files."""
    print("\nValidating configuration files...")

    config_files = [
        ("config/snmpv3_security_test.yaml", "SNMPv3 Security Test Config"),
        ("config/api_config.yaml", "REST API Config"),
        ("config/state_machine_test.yaml", "State Machine Test Config"),
        ("config/comprehensive.yaml", "Comprehensive Test Config"),
    ]

    all_valid = True
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            all_valid = False
            continue

        # Try to parse YAML
        try:
            import yaml

            with open(file_path) as f:
                config = yaml.safe_load(f)
                if "simulation" in config:
                    print(f"  ✓ Valid YAML structure")
                else:
                    print(f"  ✗ Missing 'simulation' section")
                    all_valid = False
        except ImportError:
            print(f"  ⚠ Cannot validate YAML (PyYAML not installed)")
        except Exception as e:
            print(f"  ✗ Invalid YAML: {e}")
            all_valid = False

    return all_valid


def validate_test_files() -> bool:
    """Validate test files."""
    print("\nValidating test files...")

    test_files = [
        ("docker-compose.testing.yml", "Docker Compose Test File"),
        ("Dockerfile.test-runner", "Test Runner Dockerfile"),
        ("tests/docker_comprehensive_test.py", "Comprehensive Test Script"),
        ("test_all_features.sh", "Main Test Script"),
    ]

    all_valid = True
    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_valid = False

    return all_valid


def validate_example_scripts() -> bool:
    """Validate example scripts."""
    print("\nValidating example scripts...")

    example_files = [
        ("examples/snmpv3_security_demo.py", "SNMPv3 Security Demo"),
        ("examples/api_client_demo.py", "API Client Demo"),
        ("examples/device_lifecycle_demo.py", "Device Lifecycle Demo"),
    ]

    all_valid = True
    for file_path, description in example_files:
        if not check_file_exists(file_path, description):
            all_valid = False

    return all_valid


def validate_test_modules() -> bool:
    """Validate test modules."""
    print("\nValidating test modules...")

    test_modules = [
        ("behaviors/snmpv3_security.py", "SNMPv3 Security Module"),
        ("rest_api/server.py", "REST API Server"),
        ("state_machine/core.py", "State Machine Core"),
        ("tests/test_snmpv3_security.py", "SNMPv3 Security Tests"),
        ("tests/test_rest_api.py", "REST API Tests"),
    ]

    all_valid = True
    for file_path, description in test_modules:
        if not check_file_exists(file_path, description):
            all_valid = False

    return all_valid


def check_python_dependencies() -> bool:
    """Check Python dependencies."""
    print("\nChecking Python dependencies...")

    required_packages = [
        ("yaml", "PyYAML"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
        ("psutil", "PSUtil"),
    ]

    all_available = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"✓ {package_name}: Available")
        except ImportError:
            print(f"✗ {package_name}: Not available")
            all_available = False

    return all_available


def generate_test_plan() -> None:
    """Generate test execution plan."""
    print("\nTest Execution Plan:")
    print("=" * 50)

    test_plan = {
        "Phase 1: Docker Infrastructure": [
            "Build Docker images (main + test runner)",
            "Start test containers (4 instances)",
            "Wait for container health checks",
            "Validate network connectivity",
        ],
        "Phase 2: Individual Feature Tests": [
            "SNMPv3 Security - Valid/invalid credentials",
            "REST API - All endpoints functionality",
            "State Machine - Device lifecycle simulation",
            "Combined Features - Integration testing",
        ],
        "Phase 3: Comprehensive Testing": [
            "Automated test suite execution",
            "Performance under load testing",
            "Error scenario validation",
            "Metrics collection verification",
        ],
        "Phase 4: Results and Cleanup": [
            "Generate test reports",
            "Collect container logs",
            "Clean up test containers",
            "Archive test results",
        ],
    }

    for phase, tasks in test_plan.items():
        print(f"\n{phase}:")
        for task in tasks:
            print(f"  • {task}")


def main():
    """Main validation function."""
    print("Mock SNMP Agent - Test Setup Validation")
    print("=" * 50)

    # Run all validations
    validations = [
        ("Docker Setup", check_docker_setup),
        ("Configuration Files", validate_config_files),
        ("Test Files", validate_test_files),
        ("Example Scripts", validate_example_scripts),
        ("Test Modules", validate_test_modules),
        ("Python Dependencies", check_python_dependencies),
    ]

    results = {}
    for name, validation_func in validations:
        try:
            results[name] = validation_func()
        except Exception as e:
            print(f"✗ {name}: Validation failed - {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 50)
    print("Validation Summary:")

    total_checks = len(results)
    passed_checks = sum(results.values())

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} {name}")

    print(f"\nOverall: {passed_checks}/{total_checks} validations passed")

    if passed_checks == total_checks:
        print("\n🎉 All validations passed! Ready to run comprehensive tests.")
        print("\nTo run tests:")
        print("  ./test_all_features.sh")
        print("  ./test_all_features.sh quick    # Quick connectivity tests")
        print("  ./test_all_features.sh clean    # Clean up only")

        generate_test_plan()
        return 0
    else:
        print(f"\n❌ {total_checks - passed_checks} validation(s) failed.")
        print("\nPlease fix the issues above before running tests.")

        if not results.get("Docker Setup", True):
            print("\nDocker Setup Issues:")
            print("  • Install Docker: https://docs.docker.com/get-docker/")
            print("  • Start Docker daemon")

        if not results.get("Python Dependencies", True):
            print("\nPython Dependencies Issues:")
            print("  • Run: pip install -r requirements.txt")
            print("  • Or: pip install pyyaml fastapi uvicorn pydantic requests psutil")

        return 1


if __name__ == "__main__":
    sys.exit(main())
