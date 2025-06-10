# API Testing Guide

## Overview

This guide covers how to run automated tests for the Mock SNMP Agent REST API, including unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_api_endpoints.py          # Core API endpoint tests
├── test_websocket_integration.py  # WebSocket functionality tests
├── test_simulation_scenarios.py   # Scenario management tests
└── test_export_import.py          # Export/import functionality tests
```

## Quick Start

### 1. Install Test Dependencies

```bash
# Install testing requirements
pip install -r requirements-test.txt

# Or install individually
pip install pytest pytest-asyncio websockets
```

### 2. Run All Tests

```bash
# Run all API tests
python run_api_tests.py

# Run with verbose output
python run_api_tests.py all --verbose

# Run with quiet output (minimal messages)
python run_api_tests.py all --quiet

# Run with coverage report
python run_api_tests.py all --coverage
```

### 3. Run Specific Test Suites

```bash
# API endpoint tests only
python run_api_tests.py endpoints

# WebSocket tests only
python run_api_tests.py websockets

# Scenario management tests
python run_api_tests.py scenarios

# Export/import tests
python run_api_tests.py export
```

## Test Categories

### Unit Tests

Test individual components in isolation with mocked dependencies.

```bash
# Run unit tests
python run_api_tests.py unit

# With pytest directly
pytest -m unit tests/
```

**Coverage:**
- REST API endpoint logic
- WebSocket message handling
- Data validation
- Error handling

### Integration Tests

Test complete workflows with real server instances.

```bash
# Run integration tests (starts test server)
python run_api_tests.py --integration

# Manual integration testing
pytest -m integration tests/
```

**Coverage:**
- API server startup/shutdown
- WebSocket connections
- End-to-end data flow
- Cross-component interactions

### API Endpoint Tests

Comprehensive testing of all REST endpoints.

```bash
# Test all endpoints
pytest tests/test_api_endpoints.py -v

# Test specific endpoint class
pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_health_endpoint -v
```

**Endpoints Tested:**
- `/health` - Health check
- `/metrics` - Performance metrics
- `/config` - Configuration management
- `/agent/status` - Agent status
- `/agent/restart` - Agent restart
- `/oids/available` - Available OIDs
- `/oids/query` - OID querying
- `/oids/search` - OID search
- `/simulation/scenarios` - Scenario management
- `/export/data` - Data export
- `/import/data` - Data import

### WebSocket Tests

Test real-time communication channels.

```bash
# Test WebSocket functionality
pytest tests/test_websocket_integration.py -v
```

**WebSocket Channels Tested:**
- `/ws/metrics` - Real-time metrics
- `/ws/logs` - Log streaming
- `/ws/state` - State transitions
- `/ws/snmp-activity` - SNMP activity

## Advanced Testing

### Performance Testing

```bash
# Generate comprehensive test report
python run_api_tests.py --report

# This creates:
# - test-reports/report.html - Test results
# - test-reports/coverage/ - Coverage report
# - test-reports/junit.xml - JUnit XML
```

### Load Testing

```bash
# Install locust for load testing
pip install locust

# Create load test script
cat > api_load_test.py << 'EOF'
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_health(self):
        self.client.get("/health")

    @task(2)
    def test_metrics(self):
        self.client.get("/metrics")

    @task(1)
    def test_scenarios(self):
        self.client.get("/simulation/scenarios")
EOF

# Run load test
locust -f api_load_test.py --host=http://localhost:8080
```

### Security Testing

```bash
# Install security tools
pip install bandit safety

# Run security scan
bandit -r rest_api/

# Check for vulnerable dependencies
safety check
```

## Test Configuration

### Environment Variables

```bash
# Test configuration
export PYTHONPATH=.
export TEST_API_URL=http://localhost:8080
export TEST_TIMEOUT=30
```

### Test Data

Tests use fixtures for consistent test data:

```python
# Example test data usage
def test_config_update(client, api_test_data):
    response = client.put("/config", json=api_test_data["valid_config_update"])
    assert response.status_code == 200
```

### Mock vs Real Testing

**Mock Testing (Default):**
- Fast execution
- No external dependencies
- Isolated component testing

**Real Server Testing:**
- `--integration` flag
- Full system testing
- Network communication validation

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Changes to `rest_api/` or `tests/`

**Matrix Testing:**
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Unit, integration, security tests
- Performance testing on main branch

### Test Reports

**Artifacts Generated:**
- Test results (HTML/XML)
- Coverage reports
- Security scan results
- Performance reports

## Writing New Tests

### API Endpoint Test Template

```python
def test_new_endpoint(self, client):
    """Test new API endpoint."""
    response = client.get("/new-endpoint")
    assert response.status_code == 200

    data = response.json()
    assert "expected_field" in data
    assert isinstance(data["expected_field"], str)
```

### WebSocket Test Template

```python
@pytest.mark.asyncio
async def test_new_websocket(self, connection_manager):
    """Test new WebSocket functionality."""
    mock_ws = MockWebSocket()
    await connection_manager.connect(mock_ws, "new_channel")

    await connection_manager.broadcast_to_channel(
        "new_channel",
        {"type": "test_message", "data": "test"}
    )

    assert len(mock_ws.messages) == 1
    assert mock_ws.messages[0]["type"] == "test_message"
```

### Async Test Template

```python
@pytest.mark.asyncio
async def test_async_functionality(self, scenario_manager):
    """Test async functionality."""
    result = await scenario_manager.async_method()
    assert result.success is True
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    """Unit test."""
    pass

@pytest.mark.api
def test_api_endpoint():
    """API endpoint test."""
    pass

@pytest.mark.websocket
def test_websocket_feature():
    """WebSocket test."""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test."""
    pass

@pytest.mark.slow
def test_performance():
    """Slow/performance test."""
    pass
```

Run specific markers:

```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

## Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
pytest tests/ -vvv --tb=long

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

### Test Debugging

```python
def test_with_debugging(client):
    """Test with debugging info."""
    response = client.get("/health")

    # Debug information
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Body: {response.text}")

    assert response.status_code == 200
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=rest_api --cov-report=html tests/

# View coverage
open htmlcov/index.html
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Or use pytest with path
python -m pytest tests/
```

**WebSocket Connection Failures:**
- Check if server is running
- Verify port availability
- Check firewall settings

**Test Timeout:**
```python
# Increase timeout for slow tests
@pytest.mark.timeout(60)
def test_slow_operation():
    pass
```

**Missing Dependencies:**
```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Check for missing packages
python -c "import pytest, websockets; print('OK')"
```

### Performance Issues

**Slow Tests:**
- Use mocks for external dependencies
- Reduce test data size
- Run tests in parallel: `pytest -n auto`

**Memory Issues:**
- Clean up resources in teardown
- Use `pytest-xvfb` for headless testing
- Monitor memory usage

## Best Practices

1. **Test Independence:** Each test should be independent
2. **Clear Assertions:** Use descriptive assertion messages
3. **Test Data:** Use fixtures for consistent test data
4. **Error Cases:** Test both success and failure scenarios
5. **Documentation:** Document complex test scenarios
6. **Performance:** Keep tests fast and focused
7. **Coverage:** Aim for high test coverage
8. **CI/CD:** Ensure tests pass in CI environment

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [WebSocket Testing](https://websockets.readthedocs.io/en/stable/reference/test.html)
- [Mock SNMP Agent API Docs](./REST_API_DOCUMENTATION.md)
