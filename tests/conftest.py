"""Pytest configuration and fixtures for Mock SNMP Agent tests."""

import pytest
import subprocess
import time
import os
import signal
from pathlib import Path


@pytest.fixture(scope="session")
def snmp_simulator():
    """Start SNMP simulator for testing session."""
    # Find data directory
    current_dir = Path.cwd()
    data_dir = current_dir / "data"
    if not data_dir.exists():
        data_dir = current_dir

    # Start simulator
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"

    proc = subprocess.Popen(
        [
            "snmpsim-command-responder",
            f"--data-dir={data_dir}",
            "--agent-udpv4-endpoint=127.0.0.1:11611",
            "--quiet",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for startup
    time.sleep(3)

    # Check if simulator started successfully
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        pytest.fail(f"Simulator failed to start: {stderr.decode()}")

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def snmp_endpoint():
    """SNMP endpoint configuration for tests."""
    return {"host": "127.0.0.1", "port": 11611, "community": "public"}


@pytest.fixture
def snmp_tools_available():
    """Check if SNMP tools are available."""
    try:
        subprocess.run(["snmpget", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("SNMP tools not available")


@pytest.fixture
def simulator_ready(snmp_simulator, snmp_tools_available):
    """Ensure simulator is ready for testing."""
    # Additional ready check if needed
    return True
