#!/usr/bin/env python3
"""
Port Cleanup Utility

Cleans up any processes using SNMP and API ports before running tests.
"""

import subprocess
import sys
import os
import signal


def kill_processes_on_port(port):
    """Kill any processes using the specified port"""
    try:
        # Find processes using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    print(f"Killing process {pid} on port {port}")
                    os.kill(pid, signal.SIGTERM)
                    # Give it a moment to terminate gracefully
                    import time

                    time.sleep(1)
                    # Force kill if still running
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Already terminated
                except (ValueError, ProcessLookupError):
                    pass
        return True
    except Exception as e:
        print(f"Error cleaning port {port}: {e}")
        return False


def cleanup_docker():
    """Stop any running Docker containers"""
    try:
        result = subprocess.run(
            ["docker", "compose", "down"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("Docker containers stopped")
        return True
    except Exception as e:
        print(f"Error stopping Docker containers: {e}")
        return False


def main():
    """Main cleanup function"""
    print("🧹 Cleaning up ports and processes...")

    # Clean up SNMP port (11611) and API port (8080)
    ports_to_clean = [11611, 8080, 9116]  # SNMP, API, SNMP Exporter

    for port in ports_to_clean:
        kill_processes_on_port(port)

    # Clean up Docker
    cleanup_docker()

    # Kill any mock agent processes by name
    try:
        subprocess.run(
            ["pkill", "-f", "mock_snmp_agent.py"], capture_output=True, timeout=10
        )
    except:
        pass

    print("✅ Cleanup completed")


if __name__ == "__main__":
    main()
