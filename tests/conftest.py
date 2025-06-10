"""Pytest configuration and fixtures for Mock SNMP Agent tests."""

import asyncio
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import test dependencies
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_agent_process():
    """Create mock agent process."""
    process = Mock()
    process.poll.return_value = None  # Process is running
    process.pid = 12345
    process.terminate = Mock()
    process.kill = Mock()
    process.wait = Mock()
    return process


@pytest.fixture
def sample_snmprec_data():
    """Sample SNMP record data for testing."""
    return [
        "1.3.6.1.2.1.1.1.0|4|Mock SNMP Agent Test System",
        "1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.12345",
        "1.3.6.1.2.1.1.3.0|67|233425120",
        "1.3.6.1.2.1.1.4.0|4|admin@test.com",
        "1.3.6.1.2.1.1.5.0|4|test-agent",
        "1.3.6.1.2.1.1.6.0|4|Test Laboratory",
        "1.3.6.1.2.1.1.7.0|2|72",
    ]


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "simulation": {
            "behaviors": {
                "delay": {
                    "enabled": False,
                    "global_delay": 0,
                    "deviation": 0,
                    "oid_specific_delays": {},
                },
                "drop": {"enabled": False, "drop_rate": 0, "oid_specific_drops": {}},
                "snmpv3_security": {
                    "enabled": False,
                    "time_window_failures": {
                        "enabled": False,
                        "clock_skew_seconds": 150,
                        "failure_rate": 0,
                    },
                    "authentication_failures": {
                        "enabled": False,
                        "wrong_credentials_rate": 0,
                        "unsupported_auth_rate": 0,
                        "unknown_user_rate": 0,
                    },
                },
            },
            "state_machine": {
                "enabled": False,
                "device_type": "router",
                "initial_state": "operational",
                "auto_transitions": True,
            },
            "rest_api": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 8080,
                "cors": {"enabled": True, "origins": ["*"]},
            },
            "logging": {
                "enabled": True,
                "level": "info",
                "file": None,
                "format": "text",
            },
        }
    }


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for testing."""
    return {
        "timestamp": 1640995200.0,
        "uptime_seconds": 3600.0,
        "requests_total": 1000,
        "requests_successful": 950,
        "requests_failed": 50,
        "avg_response_time_ms": 75.5,
        "current_connections": 5,
    }


@pytest.fixture
def api_test_data():
    """Common test data for API testing."""
    return {
        "valid_oid_query": {
            "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"],
            "community": "public",
            "include_metadata": True,
        },
        "valid_config_update": {
            "simulation": {
                "behaviors": {"delay": {"enabled": True, "global_delay": 150}}
            }
        },
        "valid_export_request": {
            "format": "json",
            "include_config": True,
            "include_metrics": True,
            "include_scenarios": False,
            "include_history": False,
        },
    }


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


# Custom pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "api: mark test as API endpoint test")
    config.addinivalue_line("markers", "websocket: mark test as WebSocket test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test")
