# Mock SNMP Agent - Product Requirements Document

## Overview

The Mock SNMP Agent is a comprehensive SNMP simulator designed to simulate the behavior of real SNMP agents for testing and training purposes. It allows developers to test their SNMP management tools against various scenarios and edge cases in a controlled environment, including advanced simulation behaviors and real-time monitoring capabilities.

## Objectives

1. Simulate a variety of SNMP agent behaviors for testing and training
2. Provide a controllable and deterministic environment for SNMP tool development
3. Support easy integration with existing SNMP tools and frameworks
4. Enable comprehensive testing of SNMP monitoring systems under various conditions

## Functional Requirements

### 1. SNMP Protocol Support
- Implement SNMP v1, v2c, and v3 protocol support ✅
- Respond to SNMP GET, GETNEXT, GETBULK, and SET requests ✅
- Allow defining custom MIB (Management Information Base) for the agent ✅
- Support community string authentication ✅
- Full SNMPv3 USM (User-based Security Model) support ✅
- Writeable OID support via variation/writecache community ✅

### 2. Simulation Behaviors
- **Normal operation**: Respond to requests as a typical SNMP agent ✅
- **Slow responses**: Add configurable delays before sending responses ✅
- **Intermittent responses**: Randomly drop a configurable percentage of requests ✅
- **Packet loss**: Randomly drop a configurable percentage of response packets ✅
- **Counter wrap simulation**: Simulate 32-bit and 64-bit counter wraps ✅
- **Resource constraints**: Simulate CPU and memory limitations ✅
- **Network conditions**: Simulate various network reliability scenarios ✅

### 3. Configuration Management
- Allow setting simulation behaviors via YAML configuration files ✅
- Support loading custom MIB definitions from .snmprec files ✅
- Allow overriding specific MIB values via configuration ✅
- Runtime configuration changes via REST API ✅
- Hot-reload capability without agent restart ✅

### 4. REST API & Real-time Monitoring
- **FastAPI-based HTTP API** for remote agent control ✅
- **WebSocket support** for real-time streaming of metrics and logs ✅
- **Agent lifecycle management** (start, stop, restart, configure) ✅
- **Query endpoints** with advanced OID querying capabilities ✅
- **Export/Import functionality** in multiple formats (JSON, CSV, YAML, ZIP) ✅

### 5. Logging and Metrics
- Log all received requests and sent responses ✅
- Provide metrics on request/response counts, latencies, error rates ✅
- Real-time WebSocket streaming of activity ✅
- Export logs and metrics in multiple formats ✅
- Prometheus-compatible metrics endpoint ✅

### 6. Test Scenario Management
- Create and execute complex testing scenarios ✅
- Scenario templates for common testing patterns ✅
- Automated test execution with validation ✅
- Performance benchmarking capabilities ✅

## Non-functional Requirements

### 1. Performance
- Handle up to 1000 requests per second ✅
- Average response latency under 10ms (in normal operation mode) ✅
- Support multiple concurrent SNMP agents ✅
- Efficient memory usage with large MIB datasets ✅

### 2. Reliability
- Maintain stable operation under high load and error scenarios ✅
- Graceful handling of invalid requests or configurations ✅
- Comprehensive error handling and recovery ✅
- Automated health checking ✅

### 3. Usability
- Provide clear documentation and examples for setup and usage ✅
- Include predefined MIBs and simulation configurations ✅
- Intuitive REST API with OpenAPI documentation ✅
- Docker support for easy deployment ✅

### 4. Portability
- Support running on Linux, macOS, and Windows platforms ✅
- Docker containerization for consistent deployment ✅
- Python virtual environment compatibility ✅

## Implementation Status

### ✅ Completed Features

**Core SNMP Functionality:**
- SNMPv1, v2c, and v3 protocol support via snmpsim-lextudio
- GET, GETNEXT, GETBULK operations
- Custom MIB definitions via .snmprec files
- Community string and SNMPv3 authentication

**Advanced Simulation:**
- Configurable response delays with deviation
- Packet drop simulation
- Counter wrap behaviors
- Resource constraint modeling
- Bulk operation testing

**REST API & WebSocket:**
- FastAPI-based HTTP API server
- Real-time WebSocket communication
- Agent control and monitoring endpoints
- Export/import in multiple formats
- Query endpoints with metadata

**Configuration & Management:**
- YAML configuration file support
- Runtime configuration via API
- Comprehensive logging system
- Metrics collection and export
- Docker deployment support

**Testing Framework:**
- 78+ automated API tests
- CI/CD integration
- Performance testing suite
- Comprehensive test coverage

### ✅ Recently Completed

**Performance Validation:**
- Enhanced performance testing framework with memory monitoring ✅
- Comprehensive load testing scenarios implemented ✅
- Performance benchmarking tools available ✅
- Quick validation scripts for CI/CD ✅

**Documentation:**
- Advanced usage examples ✅
- Best practices guide ✅
- Troubleshooting documentation ✅
- API reference with examples ✅

## Advanced Testing Scenarios

### 1. Timeout/Polling Mismatch Testing
- Variable response delays (50ms-5000ms) with probabilistic distributions
- Network latency simulation with configurable jitter and packet loss
- Progressive response degradation under load
- Selective timeout scenarios for specific OIDs
- UDP packet loss simulation (1-10% rates)

### 2. Counter Wrap Simulation
- 32-bit counter wrap at 2^32-1 (4,294,967,295)
- Accelerated wrap testing for different interface speeds
- 64-bit counter support for high-capacity interfaces
- Multiple wrap detection between polling intervals
- Counter discontinuity event simulation

### 3. Resource Constraint Testing
- CPU exhaustion simulation (>80% sustained utilization)
- Memory constraint scenarios (<10% free memory)
- Concurrent request handling limits (10-100 simultaneous)
- Response buffer overflow conditions
- Cascading resource failure simulation

### 4. Bandwidth Consumption Testing
- Large MIB walk simulation (MB of data)
- GetBulk operation testing with max-repetitions 10-200
- PDU size management and fragmentation
- Bandwidth throttling simulation
- Concurrent bulk operation handling

### 5. MIB Compatibility Testing
- Missing OID simulation (noSuchObject, noSuchInstance)
- Data type mismatch testing
- Malformed response generation
- Version-specific error behaviors
- Custom MIB validation

### 6. Security/Authentication Testing
- SNMPv3 time window violations
- Engine ID mismatch scenarios
- Key synchronization failures
- Boot counter issues
- Authentication and privacy protocol testing

### 7. Bulk Operation Testing
- Max-repetitions overflow testing
- PDU size limit validation
- Partial response handling
- Memory allocation failure simulation
- GetBulk boundary conditions

## Technical Architecture

### Core Components
- **`mock_snmp_agent.py`** - Enhanced main module with CLI and configuration
- **`rest_api/server.py`** - FastAPI application server
- **`rest_api/controllers.py`** - Business logic for agent control
- **`rest_api/websocket.py`** - Real-time WebSocket manager
- **`behaviors/`** - Simulation behavior modules
- **`state_machine/`** - Device lifecycle and state management

### Configuration Schema
```yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 100        # ms
      deviation: 50            # ms
    drops:
      enabled: true
      rate: 10                 # percent
    counter_wrap:
      enabled: true
      acceleration_factor: 1000
  logging:
    enabled: true
    level: info
    format: json
  metrics:
    enabled: true
    export_format: prometheus
```

### API Endpoints
```
/api/v1/agents         - Agent management
/api/v1/scenarios      - Test scenario control
/api/v1/metrics        - Metrics and monitoring
/api/v1/query          - Advanced OID querying
/api/v1/export         - Data export/import
/ws/metrics           - Real-time metrics stream
/ws/logs              - Real-time log stream
/ws/activity          - SNMP activity stream
```

## Recently Enhanced (New Capabilities)

### ✅ AgentX-Style Response Simulation
- **Subagent registration delays** - Simulates AgentX subagent registration timeouts ✅
- **Master agent communication delays** - Variable delays by MIB subsystem ✅
- **Connection failure simulation** - Subagent disconnection/reconnection scenarios ✅
- **OID-specific delay patterns** - Different delays for interfaces, routing, hardware ✅

### ✅ SNMPv3 Context Handling
- **Multiple context support** - VRF, bridge domains, firewall zones ✅
- **Context-based access control** - User authorization per context ✅
- **Context-specific OID values** - Same OID, different values per context ✅
- **Enterprise context simulation** - Customer VRFs, management contexts ✅

### ✅ MIB Boundary Response Injection
- **endOfMibView responses** - Proper MIB walk termination ✅
- **noSuchObject simulation** - Missing MIB objects ✅
- **noSuchInstance handling** - Sparse table simulation ✅
- **Configurable boundary conditions** - Custom MIB view limits ✅

## Out of Scope

- SNMP trap generation
- Graphical user interface (provides config files and APIs)
- Package distribution (pip, apt, brew, etc.)

## Success Criteria

### Functionality
- All core SNMP operations working reliably ✅
- Advanced simulation behaviors operational ✅
- REST API and WebSocket functionality complete ✅
- Comprehensive test coverage maintained ✅

### Performance
- Maintains target request handling capacity ✅
- Average latency under 10ms in normal mode ✅
- Minimal memory footprint under load ✅
- Stable operation during extended testing ✅

### Usability
- Simple configuration and setup ✅
- Clear documentation and examples ✅
- Helpful error messages and validation ✅
- Docker deployment support ✅

## Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Running the Simulator
```bash
# Basic SNMP simulator
python src/mock_snmp_agent.py --port 11611

# With REST API
python src/mock_snmp_agent.py --rest-api --api-port 8080 --port 11611

# With configuration file
python src/mock_snmp_agent.py --config config/comprehensive.yaml --port 11611
```

### Testing and Quality
```bash
# Run complete API test suite
python scripts/testing/run_api_tests.py all

# Run with coverage
python scripts/testing/run_api_tests.py all --coverage --verbose

# Code quality checks
pylint src/mock_snmp_agent.py src/rest_api/
black .
```

This unified PRD combines the original requirements specification with implementation progress tracking and advanced testing capabilities into a single comprehensive document that serves as both specification and current status reference.
