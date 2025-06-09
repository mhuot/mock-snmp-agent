#!/usr/bin/env python3
"""
Quick Docker functionality test for Mock SNMP Agent.

This script demonstrates Docker functionality without long build times.
"""

import subprocess
import time
import sys
from pathlib import Path


def run_simple_docker_test():
    """Run a simple Docker test using a basic container."""
    print("Quick Docker Test for Mock SNMP Agent")
    print("=" * 40)

    # Create a simple Docker run command
    print("\n1. Testing basic Docker functionality...")

    # Run a simple container with our agent
    try:
        print("Building minimal Docker image...")

        # Create a minimal Dockerfile
        minimal_dockerfile = """
FROM python:3.11-slim

# Install basic dependencies
RUN apt-get update && apt-get install -y snmp && apt-get clean

# Copy application files
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

# Expose port
EXPOSE 11611/udp

# Run the agent
CMD ["mock-snmp-agent", "--port", "11611", "--host", "0.0.0.0"]
"""

        with open("Dockerfile.minimal", "w") as f:
            f.write(minimal_dockerfile)

        # Build minimal image
        result = subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile.minimal",
                "-t",
                "mock-snmp-minimal",
                ".",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"✗ Docker build failed: {result.stderr}")
            return False

        print("✓ Docker image built successfully")

        # Run container
        print("\n2. Starting SNMP agent in Docker...")
        container = subprocess.Popen(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "--name",
                "mock-snmp-test",
                "-p",
                "11611:11611/udp",
                "mock-snmp-minimal",
            ],
            capture_output=True,
            text=True,
        )

        container_output = container.communicate()
        if container.returncode != 0:
            print(f"✗ Failed to start container: {container_output[1]}")
            return False

        container_id = container_output[0].strip()
        print(f"✓ Container started: {container_id[:12]}")

        # Wait for agent to start
        print("\n3. Waiting for agent to be ready...")
        time.sleep(5)

        # Test SNMP connectivity
        print("4. Testing SNMP connectivity...")
        test_result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "public",
                "-t",
                "3",
                "-r",
                "1",
                "localhost:11611",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
        )

        if test_result.returncode == 0:
            print("✓ SNMP test successful!")
            print(f"  Response: {test_result.stdout.strip()}")
            success = True
        else:
            print(f"✗ SNMP test failed: {test_result.stderr}")
            success = False

        # Test with delay
        print("\n5. Testing delay functionality...")
        delay_container = subprocess.Popen(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "--name",
                "mock-snmp-delay-test",
                "-p",
                "11612:11612/udp",
                "mock-snmp-minimal",
                "mock-snmp-agent",
                "--delay",
                "500",
                "--port",
                "11612",
                "--host",
                "0.0.0.0",
            ],
            capture_output=True,
            text=True,
        )

        delay_output = delay_container.communicate()
        if delay_container.returncode == 0:
            delay_container_id = delay_output[0].strip()
            print(f"✓ Delay container started: {delay_container_id[:12]}")

            time.sleep(3)

            # Test delay
            start_time = time.time()
            delay_test = subprocess.run(
                [
                    "snmpget",
                    "-v2c",
                    "-c",
                    "public",
                    "-t",
                    "5",
                    "localhost:11612",
                    "1.3.6.1.2.1.1.1.0",
                ],
                capture_output=True,
                text=True,
            )
            end_time = time.time()

            if delay_test.returncode == 0:
                response_time = (end_time - start_time) * 1000
                print(f"✓ Delay test successful! Response time: {response_time:.0f}ms")
                if response_time > 400:  # Should be around 500ms
                    print("✓ Delay is working correctly")
                else:
                    print("⚠ Delay might not be working as expected")
            else:
                print(f"✗ Delay test failed: {delay_test.stderr}")

            # Clean up delay container
            subprocess.run(
                ["docker", "stop", delay_container_id], capture_output=True, timeout=10
            )

        # Clean up main container
        subprocess.run(
            ["docker", "stop", container_id], capture_output=True, timeout=10
        )

        return success

    except subprocess.TimeoutExpired:
        print("✗ Docker operation timed out")
        return False
    except Exception as e:
        print(f"✗ Docker test failed: {e}")
        return False
    finally:
        # Cleanup
        subprocess.run(
            ["docker", "stop", "mock-snmp-test"], capture_output=True, timeout=5
        )
        subprocess.run(
            ["docker", "stop", "mock-snmp-delay-test"], capture_output=True, timeout=5
        )
        if Path("Dockerfile.minimal").exists():
            Path("Dockerfile.minimal").unlink()


def check_prerequisites():
    """Check if required tools are available."""
    print("Checking prerequisites...")

    # Check Docker
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Docker: {result.stdout.strip()}")
        else:
            print("✗ Docker not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Docker not found")
        return False

    # Check SNMP tools
    try:
        result = subprocess.run(
            ["snmpget", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("✓ SNMP tools available")
        else:
            print("✗ SNMP tools not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ SNMP tools not found")
        print(
            "Install with: brew install net-snmp (macOS) or apt-get install snmp-utils (Linux)"
        )
        return False

    return True


def main():
    """Main test function."""
    if not check_prerequisites():
        print("\nPrerequisites not met. Cannot run Docker tests.")
        return 1

    print("\nStarting Docker functionality test...")

    if run_simple_docker_test():
        print("\n" + "=" * 40)
        print("✓ Docker functionality test PASSED!")
        print("The Mock SNMP Agent works correctly in Docker containers.")
        return 0
    else:
        print("\n" + "=" * 40)
        print("✗ Docker functionality test FAILED!")
        print("Check the errors above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
