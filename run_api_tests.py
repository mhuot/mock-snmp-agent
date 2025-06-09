#!/usr/bin/env python3
"""
API Test Runner

Script to run comprehensive API tests with proper setup and reporting.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def check_dependencies(quiet=False):
    """Check if required dependencies are installed."""
    required_packages = [
        ("pytest", "pytest"),
        ("pytest-asyncio", "pytest_asyncio"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("websockets", "websockets"),
        ("pyyaml", "yaml"),
        ("requests", "requests"),
    ]

    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        if not quiet:
            print(f"❌ Missing required packages: {', '.join(missing)}")
            print("Run: pip install pytest pytest-asyncio websockets")
        return False

    if not quiet:
        print("✅ All required dependencies are available")
    return True


def run_tests(test_type="all", verbose=False, coverage=False, quiet=False):
    """Run API tests with specified options."""

    if not check_dependencies(quiet=quiet):
        return False

    # Base pytest command - use the same Python interpreter we're running with
    cmd = [sys.executable, "-m", "pytest"]

    # Test selection
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "websocket":
        cmd.extend(["-m", "websocket"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "endpoints":
        cmd.append("tests/test_api_endpoints.py")
    elif test_type == "websockets":
        cmd.append("tests/test_websocket_integration.py")
    elif test_type == "scenarios":
        cmd.append("tests/test_simulation_scenarios.py")
    elif test_type == "export":
        cmd.append("tests/test_export_import.py")
    else:
        # Run all API tests
        cmd.extend(
            [
                "tests/test_api_endpoints.py",
                "tests/test_websocket_integration.py",
                "tests/test_simulation_scenarios.py",
                "tests/test_export_import.py",
            ]
        )

    # Options
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    else:
        cmd.extend(["-q"])

    if coverage:
        cmd.extend(["--cov=rest_api", "--cov-report=html", "--cov-report=term"])

    # Additional options
    cmd.extend(
        ["--asyncio-mode=auto", "--disable-warnings", "-x"]  # Stop on first failure
    )

    if not quiet:
        print(f"🧪 Running {test_type} tests...")
        print(f"Command: {' '.join(cmd)}")

    # Run tests
    start_time = time.time()
    result = subprocess.run(cmd)
    end_time = time.time()

    if not quiet:
        print(f"\n⏱️ Tests completed in {end_time - start_time:.2f} seconds")

    if result.returncode == 0:
        if not quiet:
            print("✅ All tests passed!")
        return True
    else:
        if not quiet:
            print("❌ Some tests failed")
        return False


def start_test_server():
    """Start a test API server for integration tests."""
    print("🚀 Starting test API server...")

    # Create a simple test server script
    test_server_script = """
import asyncio
import uvicorn
from rest_api.server import SNMPAgentAPIServer

async def main():
    server = SNMPAgentAPIServer(
        api_host="127.0.0.1",
        api_port=8080
    )
    
    config = uvicorn.Config(
        server.app,
        host="127.0.0.1",
        port=8080,
        log_level="error"
    )
    
    server_instance = uvicorn.Server(config)
    await server_instance.serve()

if __name__ == "__main__":
    asyncio.run(main())
"""

    with open("test_server.py", "w") as f:
        f.write(test_server_script)

    # Start server in background
    proc = subprocess.Popen(
        [sys.executable, "test_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(2)

    return proc


def run_integration_tests():
    """Run integration tests with real server."""
    server_proc = None

    try:
        # Start test server
        server_proc = start_test_server()

        # Check if server started
        if server_proc.poll() is not None:
            stdout, stderr = server_proc.communicate()
            print(f"❌ Test server failed to start: {stderr.decode()}")
            return False

        print("✅ Test server started")

        # Run integration tests
        result = run_tests("integration", verbose=True)

        return result

    finally:
        # Clean up
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()

        # Remove test server script
        if os.path.exists("test_server.py"):
            os.remove("test_server.py")


def generate_test_report():
    """Generate comprehensive test report."""
    print("📊 Generating test report...")

    # Run tests with coverage and detailed output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_api_endpoints.py",
        "tests/test_websocket_integration.py",
        "tests/test_simulation_scenarios.py",
        "tests/test_export_import.py",
        "--cov=rest_api",
        "--cov-report=html:test-reports/coverage",
        "--cov-report=xml:test-reports/coverage.xml",
        "--cov-report=term",
        "--html=test-reports/report.html",
        "--self-contained-html",
        "--junitxml=test-reports/junit.xml",
        "-v",
    ]

    # Create reports directory
    os.makedirs("test-reports", exist_ok=True)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ Test report generated successfully")
        print("📁 Reports available in test-reports/ directory:")
        print("   • test-reports/report.html - Test results")
        print("   • test-reports/coverage/index.html - Coverage report")
        print("   • test-reports/junit.xml - JUnit XML")
        return True
    else:
        print("❌ Test report generation failed")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="API Test Runner")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "api",
            "websocket",
            "integration",
            "endpoints",
            "websockets",
            "scenarios",
            "export",
        ],
        help="Type of tests to run",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet output (minimal messages)"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Run with coverage"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests with real server",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive test report"
    )

    args = parser.parse_args()

    if not args.quiet:
        print("🧪 Mock SNMP Agent API Test Runner")
        print("=" * 50)

    # Check environment
    if not Path("rest_api").exists():
        if not args.quiet:
            print("❌ rest_api module not found. Run from project root directory.")
        return 1

    success = True

    if args.integration:
        success = run_integration_tests()
    elif args.report:
        success = generate_test_report()
    else:
        success = run_tests(args.test_type, args.verbose, args.coverage, args.quiet)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
