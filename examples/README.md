# Examples

This directory contains practical examples for using the Mock SNMP Agent in various scenarios.

## Available Examples

### Basic Usage
- `basic_snmp_test.py` - Simple SNMP GET/GETNEXT/GETBULK operations
- `snmpv3_examples.py` - SNMPv3 authentication and privacy examples
- `community_variations.py` - Using different community strings and variations

### Testing Scenarios
- `network_monitoring_test.py` - Simulating network monitoring scenarios
- `device_discovery.py` - Device discovery and inventory testing
- `error_handling_test.py` - Testing error conditions and edge cases

### Performance Testing
- `load_testing.py` - Load testing SNMP applications
- `latency_measurement.py` - Measuring response times and latency

### Integration Examples
- `docker_usage.py` - Using the simulator in Docker environments
- `ci_cd_integration.py` - Integrating into CI/CD pipelines

## Running Examples

Make sure the Mock SNMP Agent is running before executing examples:

```bash
# Start the simulator
python mock_snmp_agent.py

# Or with Docker
docker-compose up -d

# Run an example
python examples/basic_snmp_test.py
```

## Prerequisites

All examples require:
- Python 3.8+
- snmpsim-lextudio package
- net-snmp tools (snmpget, snmpset, etc.)

Install with:
```bash
pip install snmpsim-lextudio
# macOS: brew install net-snmp
# Ubuntu: sudo apt-get install snmp
```