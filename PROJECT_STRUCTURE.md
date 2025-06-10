# Project Structure

## Overview

This document provides a comprehensive map of the Mock SNMP Agent codebase, explaining the purpose and organization of each component.

## Repository Layout

```
mock-snmp-agent/
├── README.md                          # Main project documentation and quick start
├── CLAUDE.md                          # Development guide for Claude Code
├── ADVANCED_TESTING_GUIDE.md          # Detailed testing scenarios and validation
├── ADVANCED_USAGE_GUIDE.md            # Community strings, SNMPv3, and advanced features
├── API_TESTING_GUIDE.md               # Comprehensive API testing procedures
├── CONFIGURATION_GUIDE.md             # YAML configuration examples and reference
├── REST_API_DOCUMENTATION.md          # Complete REST API endpoint documentation
├── TROUBLESHOOTING.md                 # Common issues and debugging guide
├── PROJECT_STRUCTURE.md               # This document - codebase organization
├── PERFORMANCE_RESULTS.md             # Benchmarking results and metrics
├── REACT_UI_PROJECT_PLAN.md           # React UI implementation roadmap
│
├── mock_snmp_agent.py                 # Main application entry point
├── requirements.txt                   # Core Python dependencies
├── requirements-test.txt              # Testing framework dependencies
├── setup.py                           # Package installation script
├── pyproject.toml                     # Modern Python project configuration
├── run_api_tests.py                   # Comprehensive API test runner
│
├── rest_api/                          # REST API and WebSocket server components
│   ├── __init__.py                    # Package initialization
│   ├── server.py                      # FastAPI application server
│   ├── models.py                      # Pydantic data models for validation
│   ├── controllers.py                 # Business logic controllers
│   ├── websocket.py                   # WebSocket real-time monitoring
│   ├── query_endpoints.py             # Advanced OID querying and search
│   ├── simulation_control.py          # Test scenario management
│   └── export_import.py               # Data export/import functionality
│
├── tests/                             # Comprehensive test suite (78+ tests)
│   ├── __init__.py                    # Test package initialization
│   ├── conftest.py                    # Pytest configuration and shared fixtures
│   ├── test_api_endpoints.py          # REST API endpoint validation (25 tests)
│   ├── test_websocket_integration.py  # WebSocket functionality tests (17 tests)
│   ├── test_simulation_scenarios.py   # Scenario management tests (24 tests)
│   ├── test_export_import.py          # Export/import functionality tests (12 tests)
│   ├── test_basic_functionality.py    # Core SNMP functionality validation
│   ├── test_performance.py            # Performance benchmarking tests
│   └── docker_integration_test.py     # Docker testing automation
│
├── .github/workflows/                 # CI/CD automation
│   └── api-tests.yml                  # GitHub Actions test workflow
│
├── config/                            # Configuration examples and templates
│   ├── simple.yaml                    # Basic delay configuration
│   ├── advanced.yaml                  # All features demonstration
│   ├── comprehensive.yaml             # Testing all 8 SNMP monitoring issues
│   ├── counter_wrap_test.yaml         # Counter wrap focus scenarios
│   ├── resource_limits.yaml           # Resource constraint testing
│   └── bulk_test.yaml                 # Bulk operation testing scenarios
│
├── behaviors/                         # Advanced simulation behavior modules
│   ├── __init__.py                    # Behaviors package initialization
│   ├── counter_wrap.py                # Counter wrap simulation logic
│   ├── resource_limits.py             # CPU/memory constraint simulation
│   └── bulk_operations.py             # Large table and GetBulk testing
│
├── examples/                          # Usage examples and demonstrations
│   ├── README.md                      # Examples guide and documentation
│   ├── basic_snmp_test.py             # Simple SNMP operations demonstration
│   ├── api_client_demo.py             # REST API usage examples
│   ├── community_variations.py        # Community string examples
│   ├── snmpv3_examples.py             # SNMPv3 authentication examples
│   ├── load_testing.py                # Performance testing examples
│   ├── counter_wrap_demo.py           # Counter wrap demonstration
│   ├── delay_demo.py                  # Response delay simulation
│   ├── drop_demo.py                   # Packet loss simulation
│   ├── device_lifecycle_demo.py       # Device state machine demonstration
│   └── snmpv3_security_demo.py        # SNMPv3 security testing
│
├── docker-compose.test.yml            # Docker test scenarios configuration
├── docker-compose.yml                 # Basic Docker setup
├── Dockerfile                         # Standard container build
├── Dockerfile.enhanced                # Production-ready container
├── .dockerignore                      # Docker build optimizations
│
├── quick_docker_test.py               # Fast Docker functionality validation
├── test_prd_requirements.py           # PRD compliance testing
├── performance_test.py                # Performance benchmarking script
├── test_basic.py                      # Basic functionality validation
│
├── data/                              # Simulation data files (built-in)
└── venv/                              # Python virtual environment (local development)
```

## Core Components

### Main Application

#### `mock_snmp_agent.py`
The primary entry point for the Mock SNMP Agent. This enhanced module provides:

- **CLI Interface**: Command-line argument parsing and configuration
- **Agent Initialization**: SNMP agent setup and configuration loading
- **REST API Integration**: Optional API server startup
- **Configuration Management**: YAML/JSON configuration file processing
- **Logging Setup**: Configurable logging levels and output

**Key Functions:**
- `main()`: Application entry point and orchestration
- `load_config()`: Configuration file parsing and validation
- `setup_logging()`: Logging configuration
- `start_api_server()`: REST API server initialization

#### Configuration Files

**`pyproject.toml`**: Modern Python project configuration including:
- Package metadata and dependencies
- Build system configuration
- Development tool settings (black, pylint, pytest)
- Entry point definitions

**`setup.py`**: Traditional package installation script for backward compatibility

**`requirements.txt`**: Core runtime dependencies
**`requirements-test.txt`**: Testing framework dependencies

## REST API Architecture

### `rest_api/server.py` - FastAPI Application
Main application server implementing:
- **FastAPI Framework**: Modern async web framework
- **CORS Configuration**: Cross-origin resource sharing setup
- **Middleware**: Request logging, error handling, security
- **Route Registration**: API endpoint organization
- **WebSocket Support**: Real-time communication infrastructure

### `rest_api/models.py` - Data Models
Pydantic models for API validation:
- **Request Models**: Input validation and serialization
- **Response Models**: Output formatting and documentation
- **Configuration Models**: YAML/JSON schema validation
- **Metrics Models**: Performance data structures

### `rest_api/controllers.py` - Business Logic
Core application logic:
- **Agent Management**: Start, stop, restart operations
- **Configuration Control**: Dynamic configuration updates
- **Metrics Collection**: Performance monitoring
- **Health Checks**: System status validation

### `rest_api/websocket.py` - Real-time Communication
WebSocket management:
- **Connection Manager**: Multi-client connection handling
- **Channel Broadcasting**: Topic-based message distribution
- **Message Formatting**: Structured real-time data
- **Buffer Management**: Efficient message queuing

### `rest_api/query_endpoints.py` - Advanced Querying
OID management and querying:
- **OID Search**: Pattern-based OID discovery
- **Metadata Retrieval**: OID information and descriptions
- **History Tracking**: Historical OID value changes
- **Tree Navigation**: Hierarchical OID browsing

### `rest_api/simulation_control.py` - Scenario Management
Test scenario orchestration:
- **Scenario Definition**: Test case configuration
- **Execution Control**: Start, stop, monitor scenarios
- **Results Analysis**: Performance and validation metrics
- **Automation**: Scheduled and triggered testing

### `rest_api/export_import.py` - Data Exchange
Configuration and data portability:
- **Multiple Formats**: JSON, CSV, YAML, ZIP support
- **Roundtrip Validation**: Import/export integrity
- **Archive Management**: Compressed data packages
- **Migration Tools**: Configuration transfer utilities

## Testing Infrastructure

### Test Organization

#### `tests/conftest.py` - Shared Testing Infrastructure
Common testing components:
- **Fixtures**: Reusable test data and mocks
- **Configuration**: Test environment setup
- **Utilities**: Helper functions for testing
- **Markers**: Test categorization and filtering

#### `tests/test_api_endpoints.py` - API Validation (25 tests)
Comprehensive REST API testing:
- **Endpoint Coverage**: All API routes tested
- **Request Validation**: Input parameter testing
- **Response Verification**: Output format validation
- **Error Handling**: Exception and edge case testing

#### `tests/test_websocket_integration.py` - Real-time Testing (17 tests)
WebSocket functionality validation:
- **Connection Management**: Connect, disconnect, reconnect
- **Message Broadcasting**: Channel-based communication
- **Data Streaming**: Real-time metrics and logs
- **Buffer Handling**: Message queuing and cleanup

#### `tests/test_simulation_scenarios.py` - Scenario Testing (24 tests)
Test scenario validation:
- **Scenario Creation**: Configuration and setup
- **Execution Monitoring**: Progress and status tracking
- **Results Validation**: Success criteria verification
- **Performance Analysis**: Metrics collection and analysis

#### `tests/test_export_import.py` - Data Exchange Testing (12 tests)
Import/export functionality:
- **Format Validation**: JSON, CSV, YAML, ZIP testing
- **Roundtrip Testing**: Import/export integrity
- **Error Handling**: Invalid data and format testing
- **Archive Testing**: Compressed package validation

### Test Runner

#### `run_api_tests.py` - Comprehensive Test Runner
Unified testing interface:
- **Test Selection**: Category-based test execution
- **Parallel Execution**: Multi-threaded test running
- **Coverage Reporting**: Code coverage analysis
- **CI/CD Integration**: Automated testing support
- **Output Formatting**: Structured test results

**Usage Examples:**
```bash
python run_api_tests.py all           # Run all tests
python run_api_tests.py endpoints     # API endpoint tests only
python run_api_tests.py --coverage    # With coverage reporting
python run_api_tests.py --integration # Full integration testing
```

## Simulation Behaviors

### `behaviors/counter_wrap.py`
Counter overflow simulation:
- **32-bit/64-bit Counters**: Different counter types
- **Acceleration**: Time-compressed testing
- **Wrap Detection**: Overflow event simulation
- **Relationship Preservation**: Related counter synchronization

### `behaviors/resource_limits.py`
Resource constraint simulation:
- **CPU Limiting**: Simulated processor constraints
- **Memory Limiting**: Memory usage simulation
- **Concurrency Control**: Request limiting
- **Queue Management**: Request overflow handling

### `behaviors/bulk_operations.py`
Large-scale operation simulation:
- **Table Generation**: Large SNMP table creation
- **GetBulk Optimization**: Bulk operation efficiency
- **Memory Management**: Large response handling
- **Performance Tuning**: Response optimization

## Configuration System

### Configuration Templates

#### `config/simple.yaml`
Basic delay and packet loss configuration for simple testing scenarios.

#### `config/comprehensive.yaml`
Complete testing configuration covering all 8 major SNMP monitoring challenges.

#### `config/counter_wrap_test.yaml`
Focused counter wrap testing with acceleration settings.

#### `config/resource_limits.yaml`
Resource constraint testing with CPU, memory, and concurrency limits.

#### `config/bulk_test.yaml`
Large table and bulk operation testing configuration.

### Configuration Features
- **YAML/JSON Support**: Multiple configuration formats
- **Environment Variables**: Dynamic value substitution
- **Validation**: Schema-based configuration validation
- **Hot Reload**: Runtime configuration updates
- **Template System**: Reusable configuration components

## Docker Infrastructure

### Container Definitions

#### `Dockerfile`
Standard container for basic usage:
- **Minimal Image**: Efficient resource usage
- **Essential Dependencies**: Core functionality only
- **Quick Startup**: Fast container initialization

#### `Dockerfile.enhanced`
Production-ready container:
- **Extended Features**: All simulation capabilities
- **Security Hardening**: Production security measures
- **Monitoring Integration**: Built-in observability
- **Performance Optimization**: Tuned for efficiency

#### `docker-compose.yml`
Basic multi-container setup:
- **Agent Service**: Main SNMP agent
- **API Service**: REST API server
- **Networking**: Inter-container communication

#### `docker-compose.test.yml`
Testing infrastructure:
- **Test Scenarios**: Multiple test configurations
- **Isolated Testing**: Container-based test isolation
- **Automated Validation**: CI/CD integration

## Documentation System

### User Documentation
- **README.md**: Quick start and overview
- **ADVANCED_USAGE_GUIDE.md**: Detailed usage patterns
- **CONFIGURATION_GUIDE.md**: Configuration reference
- **TROUBLESHOOTING.md**: Problem resolution

### Technical Documentation
- **API_TESTING_GUIDE.md**: Testing procedures
- **REST_API_DOCUMENTATION.md**: API reference
- **PROJECT_STRUCTURE.md**: Codebase organization
- **PERFORMANCE_RESULTS.md**: Benchmarking data

### Development Documentation
- **CLAUDE.md**: Development workflow
- **REACT_UI_PROJECT_PLAN.md**: UI implementation plan

## CI/CD Pipeline

### `.github/workflows/api-tests.yml`
Automated testing workflow:
- **Multi-Python Testing**: Python 3.8-3.12 support
- **Comprehensive Coverage**: All test categories
- **Security Scanning**: Vulnerability detection
- **Performance Testing**: Automated benchmarking
- **Artifact Management**: Test result preservation

**Pipeline Stages:**
1. **Environment Setup**: Python and dependencies
2. **Code Quality**: Linting and formatting
3. **Unit Testing**: Component validation
4. **Integration Testing**: Full system testing
5. **Security Scanning**: Vulnerability assessment
6. **Performance Testing**: Load and stress testing
7. **Documentation**: API documentation generation

## Development Workflow

### Local Development
1. **Environment Setup**: Virtual environment creation
2. **Dependency Installation**: Requirements installation
3. **Configuration**: Development configuration
4. **Testing**: Local test execution
5. **Code Quality**: Formatting and linting

### Code Organization Principles
- **Separation of Concerns**: Clear component boundaries
- **Async/Await Patterns**: Modern Python async programming
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Comprehensive code documentation
- **Testing**: High test coverage and quality

### Extension Points
- **Simulation Behaviors**: Custom simulation modules
- **API Endpoints**: Additional REST API functionality
- **Configuration**: Custom configuration options
- **Data Sources**: Additional data file formats
- **Export Formats**: New export/import formats

This structure enables easy navigation, maintenance, and extension of the Mock SNMP Agent codebase while maintaining clear separation between different functional areas.
