# Examples

This directory contains practical examples for using the Mock SNMP Agent in various scenarios.

## Available Examples

### Basic Usage
- `basic_snmp_test.py` - Simple SNMP GET/GETNEXT/GETBULK operations
- `snmpv3_examples.py` - SNMPv3 authentication and privacy examples
- `community_variations.py` - Using different community strings and variations

### API Integration
- `api_client_demo.py` - REST API usage examples and WebSocket connections
- `scenario_automation.py` - Automated test scenario creation and execution
- `real_time_monitoring.py` - WebSocket real-time monitoring examples

### Advanced Simulation Behaviors
- `delay_demo.py` - Response delay simulation and testing
- `drop_demo.py` - Packet loss and timeout simulation
- `counter_wrap_demo.py` - Counter wrap testing scenarios
- `device_lifecycle_demo.py` - Device state machine simulation
- `snmpv3_security_demo.py` - SNMPv3 security testing scenarios

### Performance Testing
- `load_testing.py` - Load testing SNMP applications and API endpoints
- `bulk_operations_test.py` - Testing large SNMP GetBulk operations
- `concurrent_connections.py` - Testing multiple simultaneous connections

## Running Examples

### Basic SNMP Examples

Make sure the Mock SNMP Agent is running before executing examples:

```bash
# Start the simulator
python mock_snmp_agent.py --port 11611

# Or with Docker
docker compose up -d

# Run an example
python examples/basic_snmp_test.py
```

### API Examples

Start the agent with REST API support:

```bash
# Start with REST API
python mock_snmp_agent.py --rest-api --api-port 8080 --port 11611

# Run API examples
python examples/api_client_demo.py
python examples/real_time_monitoring.py
```

### Advanced Simulation Examples

Use configuration files for complex behaviors:

```bash
# Start with behavior configuration
python mock_snmp_agent.py --config config/comprehensive.yaml --port 11611

# Run simulation examples
python examples/delay_demo.py
python examples/counter_wrap_demo.py
python examples/device_lifecycle_demo.py
```

## Prerequisites

See [main README.md](../README.md#-quick-start) for complete installation and setup instructions.
