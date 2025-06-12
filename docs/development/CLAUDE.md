# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mock SNMP Agent is a comprehensive SNMP simulator built on snmpsim-lextudio, featuring advanced simulation behaviors and a REST API with real-time monitoring capabilities. It simulates multiple virtual SNMP-enabled devices with configurable behaviors for testing SNMP monitoring systems.

## Common Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# Development installation with all dependencies
pip install -e .[dev,test,api]

# Quick setup via Makefile
make dev-setup      # Complete development environment
make install-dev    # Install with dev/test dependencies
```

### Running the Simulator
```bash
# Basic SNMP simulator
python src/mock_snmp_agent.py --port 11611

# With REST API enabled
python src/mock_snmp_agent.py --rest-api --api-port 8080 --port 11611

# Using configuration file
python src/mock_snmp_agent.py --config config/comprehensive.yaml --port 11611

# REST API server standalone
python -m src.rest_api.server --port 8080
```

### Testing
```bash
# Run API test suite
python scripts/testing/run_api_tests.py all              # All API tests
python scripts/testing/run_api_tests.py endpoints        # Endpoint tests only
python scripts/testing/run_api_tests.py websockets       # WebSocket tests only
python scripts/testing/run_api_tests.py --coverage      # With coverage report

# Pytest commands
pytest -v                    # All tests
pytest -m "not slow" -v      # Fast tests only
pytest --run-extensive -v    # Include extensive tests
pytest tests/test_rest_api.py -v  # Specific test file

# Makefile shortcuts
make test          # Fast tests (excludes slow)
make test-all      # All tests including slow
make test-extensive # Full test suite
```

### Code Quality
```bash
# Format and lint
black .                                  # Format code
pylint src/mock_snmp_agent.py src/rest_api/ --fail-under=8.0

# Security and safety checks
bandit -r rest_api/
safety check

# Makefile shortcuts
make lint      # Full linting suite
make format    # Format with black
```

### Build and Docker
```bash
# Build package
make build                # Clean and build
python -m build           # Direct build

# Docker operations
make docker              # Standard image
make docker-extended     # Extended features
make docker-test         # Test Docker image
docker compose up -d     # Run with docker-compose.yml
```

## High-Level Architecture

### Core Components
- **`mock_snmp_agent.py`** - Main entry point, CLI parsing, agent orchestration
- **`rest_api/server.py`** - FastAPI application with route registration
- **`rest_api/controllers.py`** - Business logic for agent control
- **`rest_api/websocket.py`** - Real-time WebSocket connection manager
- **`rest_api/models.py`** - Pydantic models for validation
- **`behaviors/`** - Simulation behaviors (counter wrap, delays, errors)
- **`state_machine/`** - Device state management and transitions

### REST API Architecture

The API follows a layered architecture with FastAPI:

1. **Request Flow**: HTTP Request → FastAPI Router → Controller → Agent Process
2. **WebSocket Channels**: `metrics`, `logs`, `state`, `snmp_activity`
3. **Data Management**: Time-series storage, buffered history, export/import
4. **Async Design**: All endpoints use async/await for non-blocking operations

Key architectural patterns:
- Channel-based WebSocket broadcasting with automatic cleanup
- Pydantic models for all request/response validation
- Modular endpoint organization (core, query, simulation, export)
- Graceful degradation with health status reporting

### Simulation Data Format (.snmprec)
```
OID|TYPE|VALUE
1.3.6.1.2.1.1.1.0|4|Linux System
1.3.6.1.2.1.1.3.0|67|233425120
```

### Variation Module Interface
Modules in `/variation/` implement:
- `init()` - One-time initialization
- `variate()` - Generate dynamic responses
- `record()` - Recording phase (optional)

## Critical Development Guidelines

### Pre-Development Checklist (MANDATORY)
```bash
# 1. Clear port conflicts
python scripts/tools/cleanup_ports.py

# 2. Format code
black .

# 3. Verify imports
python -c "import src.rest_api.server; print('REST API OK')"
```

### Post-Development Validation (MANDATORY)
```bash
# 1. Format and lint
black . && make lint

# 2. Verify module structure
python -c "from src.rest_api.server import app; print('Imports OK')"

# 3. Run smoke test
python src/mock_snmp_agent.py --help > /dev/null && echo "CLI OK"
```

### Known Issues to Avoid
1. **Never** import Path twice in the same file
2. **Always** use specific exceptions, not `except Exception:`
3. **Avoid** Docker packages: `snmp-mibs-downloader`, `docker.io`
4. **Always** check ports before starting services
5. **Ensure** `rest_api/__main__.py` exists for module execution
6. **Use** try/finally blocks for process cleanup

## API Development Workflow

### Adding New Endpoints
1. Define Pydantic models in `rest_api/models.py`
2. Implement logic in `rest_api/controllers.py`
3. Add routes to appropriate module
4. Write tests in `tests/test_*.py`
5. Run `python scripts/testing/run_api_tests.py all`

### WebSocket Features
1. Add channel in `rest_api/websocket.py`
2. Implement broadcasting in controllers
3. Test with `tests/test_websocket_integration.py`

### Test Categories
- **endpoints**: Basic API functionality
- **websockets**: Real-time streaming
- **scenarios**: Simulation testing
- **export**: Data export/import

## Emergency Recovery

If CI/Docker fails:
```bash
python scripts/tools/cleanup_ports.py              # Clear ports
black . && make lint                 # Fix formatting
# Check Docker package names are valid for Ubuntu
# Verify rest_api/__main__.py exists
```

Common CI failures:
- Port conflicts (use cleanup_ports.py)
- Import errors (check module structure)
- Formatting (run black)
- Broad exceptions (use specific ones)

## CI/CD Troubleshooting

### GitHub Actions Issues

1. **Deprecated Action Versions**
   - Update `actions/upload-artifact@v3` to `@v4`
   - Update `actions/setup-python@v4` to `@v5`
   - Check other actions for deprecation warnings

2. **Hanging Tests**
   - `test_prd_requirements.py` - Ensure proper subprocess cleanup
   - Add timeouts to subprocess.wait() calls
   - Use try/finally with kill() fallback:
   ```python
   try:
       process.wait(timeout=5)
   except subprocess.TimeoutExpired:
       process.kill()
       process.wait()
   ```

3. **Indentation Errors**
   - Ensure try/except/finally blocks are properly indented inside context managers
   - Run `black .` before committing

4. **Process Cleanup**
   - Always use context managers (`with`) for subprocess.Popen
   - Implement proper cleanup in finally blocks
   - Kill orphan processes: `snmpsim-command-responder`
