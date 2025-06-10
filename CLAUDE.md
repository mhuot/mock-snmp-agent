# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mock SNMP Agent is a comprehensive SNMP simulator built on snmpsim-lextudio, featuring advanced simulation behaviors and a REST API with real-time monitoring capabilities. It can act as multiple virtual SNMP-enabled devices with configurable behaviors for comprehensive testing of SNMP monitoring systems.

### Key Features
- **REST API**: FastAPI-based HTTP API for remote control and monitoring
- **WebSocket Support**: Real-time streaming of metrics, logs, and SNMP activity
- **Advanced Simulation**: Delay, packet loss, counter wrap, and resource constraint simulation
- **Test Scenarios**: Create and execute complex testing scenarios
- **Export/Import**: Configuration and data exchange in multiple formats
- **Comprehensive Testing**: 78+ automated API tests with CI/CD integration

## Common Development Commands

### Setup Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### Installation
```bash
# Install in development mode (after activating venv)
pip install -e .

# Install with all dependencies (recommended for development)
pip install -e .[dev,test,api]

# Install core dependencies only
pip install -r requirements.txt

# Install testing dependencies
pip install -r requirements-test.txt

# Makefile shortcuts
make install        # Basic installation
make install-dev    # Install with dev and test dependencies
make dev-setup      # Complete development environment setup
```

### Running the Simulator
```bash
# Start basic SNMP simulator
python mock_snmp_agent.py --port 11611

# Start with REST API
python mock_snmp_agent.py --rest-api --api-port 8080 --port 11611

# Start with configuration file
python mock_snmp_agent.py --config config/comprehensive.yaml --port 11611

# Start REST API server separately
python -m rest_api.server --port 8080
```

### Testing
```bash
# Run complete API test suite
python run_api_tests.py all

# Run specific test categories
python run_api_tests.py endpoints
python run_api_tests.py websockets
python run_api_tests.py scenarios
python run_api_tests.py export

# Run with coverage and verbose output
python run_api_tests.py all --coverage --verbose

# Pytest-based testing
pytest -v                    # Run all tests
pytest -m "not slow" -v      # Skip slow tests
pytest --run-extensive -v    # Run extensive tests
pytest tests/ -v             # Run specific test directory

# Legacy/standalone tests
python test_prd_requirements.py
python performance_test.py
python test_prd_requirements.py --basic

# Makefile shortcuts
make test          # Fast tests (excludes slow ones)
make test-all      # All tests including slow ones
make test-extensive # Extensive test suite
```

### Linting and Code Quality
```bash
# Run pylint on the codebase
pylint mock_snmp_agent.py rest_api/

# Format code with black
black .

# Run security checks
bandit -r rest_api/
safety check

# Makefile shortcuts
make lint      # Complete linting suite (pylint, bandit, safety)
make format    # Format code with black
make clean     # Clean build artifacts and cache files
```

## High-Level Architecture

### Core Components
- **`mock_snmp_agent.py`** - Enhanced main module with CLI options and configuration management
- **`rest_api/server.py`** - FastAPI application server for HTTP/WebSocket API
- **`rest_api/controllers.py`** - Business logic for agent control and monitoring
- **`rest_api/websocket.py`** - Real-time WebSocket communication manager
- **`rest_api/models.py`** - Pydantic data models for API validation
- **`behaviors/`** - Simulation behavior modules (counter wrap, resource limits, SNMPv3 security, bulk operations)
- **`state_machine/`** - Device state management and device type definitions

### REST API Architecture
- **WebSocket Manager**: Handles real-time connections for metrics, logs, and SNMP activity
- **Query Endpoints**: Advanced OID querying with metadata and history tracking
- **Simulation Control**: Test scenario creation, execution, and analysis
- **Export/Import**: Multi-format data exchange (JSON, CSV, YAML, ZIP)
- **Agent Control**: Remote agent management and configuration

### Data Flow
1. SNMP requests arrive at the simulator endpoint
2. Requests are processed through configured simulation behaviors
3. WebSocket manager broadcasts real-time activity to connected clients
4. Metrics are collected and stored for historical analysis
5. API endpoints provide access to current state and historical data

### Simulation Data Format (.snmprec)
```
OID|TYPE|VALUE
1.3.6.1.2.1.1.1.0|4|Linux System
1.3.6.1.2.1.1.3.0|67|233425120
```

### Variation Module Interface
Variation modules in `/variation/` implement dynamic behavior by providing:
- `init()` - Called once when module loads
- `record()` - Called during recording phase (optional)
- `variate()` - Called to generate dynamic responses

## Key Development Patterns

1. **Async/Await**: All REST API endpoints and WebSocket handlers use async patterns
2. **Pydantic Models**: Use Pydantic for all API request/response validation
3. **FastAPI Patterns**: Follow FastAPI best practices for dependency injection and error handling
4. **WebSocket Management**: Centralized connection management with channel-based broadcasting
5. **Test-Driven Development**: Comprehensive test coverage with pytest and automated CI/CD
6. **Configuration-Driven**: YAML/JSON configuration for simulation behaviors and test scenarios
7. **Real-time Monitoring**: WebSocket streaming for live metrics and activity monitoring
8. **Multi-format Support**: Export/import in JSON, CSV, YAML, and ZIP formats

## API Development Workflow

### Adding New API Endpoints
1. **Define Pydantic models** in `rest_api/models.py`
2. **Implement business logic** in `rest_api/controllers.py`
3. **Add FastAPI routes** in appropriate endpoint modules
4. **Write comprehensive tests** in `tests/test_*.py`
5. **Update API documentation** in `REST_API_DOCUMENTATION.md`
6. **Run test suite** with `python run_api_tests.py all`

### WebSocket Development
1. **Add channel support** in `rest_api/websocket.py`
2. **Implement message broadcasting** in controllers
3. **Create WebSocket tests** in `tests/test_websocket_integration.py`
4. **Test real-time functionality** with integration tests

### Simulation Behavior Development
1. **Define behavior configuration** in YAML schema
2. **Implement behavior logic** in `behaviors/` directory
3. **Add scenario tests** in `tests/test_simulation_scenarios.py`
4. **Validate with test execution** using API endpoints

## Build and Distribution
```bash
# Build package
make build        # Clean and build package
python -m build   # Direct build command

# Docker operations
make docker           # Build standard Docker image
make docker-extended  # Build extended Docker image with additional features
make docker-test      # Test Docker image functionality

# Cleanup
make clean           # Remove build artifacts, cache, and temporary files
```