# Advanced Testing Scenarios Guide

## Overview

The Mock SNMP Agent enables comprehensive testing of the 8 major SNMP monitoring challenges that commonly occur in production environments. This guide provides detailed instructions for testing each scenario and validating your monitoring system's response.

The Mock SNMP Agent addresses the 8 major SNMP monitoring challenges outlined in the [main README](README.md#-addressing-the-8-major-snmp-monitoring-challenges). This guide provides detailed testing scenarios for each challenge.

## Detailed Testing Scenarios

### 1. Counter Wrap Testing

Test 32-bit counter wrap scenarios critical for network monitoring:

```bash
# Start agent with counter wrap acceleration
python mock_snmp_agent.py --config config/counter_wrap_test.yaml

# Monitor counter progression (see SNMP Commands Reference for details)
watch -n 1 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.2.2.1.10.1'

# Observe wrap from 4294967295 to 0
```

For complete SNMP command examples and options, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md).

**Key Testing Points:**
- Counter wrap detection at 2^32-1 (4,294,967,295)
- Multiple wraps between polling intervals
- Relationship preservation between related counters
- Acceleration factors for different interface speeds

**Configuration**: See [Counter Wrap Testing Configuration](CONFIGURATION_GUIDE.md#counter-wrap-testing-configuration) for complete YAML examples.

### 2. Resource Constraint Testing

Simulate device resource exhaustion scenarios:

```bash
# Test under CPU constraints
python mock_snmp_agent.py --config config/resource_limits.yaml

# Generate high request load (see SNMP Commands Reference for command details)
for i in {1..100}; do
  snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0 &
done
```

**Resource Limits Tested:**
- CPU utilization above 80%
- Memory usage above 90%  
- Concurrent request limits (50+ simultaneous)
- Request queue overflow conditions

**Configuration**: See [Resource Constraint Testing Configuration](CONFIGURATION_GUIDE.md#resource-constraint-testing-configuration) for complete YAML examples.

### 3. Bulk Operation Testing

Test large SNMP responses and GetBulk operations:

```bash
# Test large GetBulk operations
snmpbulkget -v2c -c public -Cn0 -Cr50 localhost:11611 1.3.6.1.2.1.2.2.1

# Test with bulk operation configuration
python mock_snmp_agent.py --config config/bulk_test.yaml
```

For complete GetBulk command syntax and examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#bulk-operations).

**Bulk Testing Features:**
- Large table simulation (1000+ interface entries)
- GetBulk with max-repetitions from 10-200
- PDU size management and fragmentation
- Memory allocation stress testing

### 4. Network Condition Simulation

Test various network conditions and timeouts:

```bash
# High latency simulation
python mock_snmp_agent.py --delay 2000 --packet-loss 10

# Progressive timeout testing
for delay in 100 500 1000 2000 5000; do
  echo "Testing ${delay}ms delay..."
  time snmpget -v2c -c public -t 3 localhost:11611 1.3.6.1.2.1.1.1.0
done
```

For timeout and timing command options, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#performance-and-timing-options).

**Network Conditions Tested:**
- High latency (100ms to 5000ms)
- Packet loss (1% to 20% loss rates)
- Request timeouts and retries
- Intermittent connectivity issues

### 5. Error Response Testing

Generate various SNMP error conditions using error simulation communities. For complete command syntax, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#error-testing).

```bash
# Trigger authorization error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.1

# Trigger no-access error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1

# Test with wrong community
snmpget -v2c -c invalid 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

**Error Types Tested:**
- `noSuchName` - Invalid OID requests
- `authorizationError` - Authentication failures
- `noAccess` - Access control violations
- `genErr` - General errors
- `tooBig` - Response size limitations

### 6. Agent Restart/Unavailability Testing

Test monitoring system resilience:

```bash
# Test restart simulation
python mock_snmp_agent.py --restart-interval 300

# Manual restart testing
# 1. Start agent
python mock_snmp_agent.py --port 11611

# 2. In another terminal, monitor continuously
while true; do
  snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.3.0 || echo "Agent down"
  sleep 5
done

# 3. Stop and restart agent to test reconnection
```

For continuous monitoring commands, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#monitoring-and-watching-commands).

**Restart Scenarios:**
- Graceful shutdowns
- Abrupt disconnections
- Restart with configuration changes
- Service unavailability periods

### 7. Dynamic Value Changes

Test real-time data fluctuations:

```bash
# Test writeable OIDs with dynamic changes
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Modified system description"

# Monitor dynamic values
watch -n 2 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.3.0'
```

For complete SET operation examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#set-operations).

**Dynamic Testing Features:**
- Value modifications during polling
- Rapid value changes
- Threshold crossing simulations
- State machine transitions

### 8. SNMPv3 Authentication Testing

Test secure SNMP implementations using different security levels. For complete SNMPv3 command syntax, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#snmpv3-commands).

```bash
# Valid SNMPv3 authentication
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test authentication failures
snmpget -v3 -l authPriv -u simulator -a MD5 -A wrongpassword -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test privacy failures  
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X wrongkey \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

**Security Testing Points:**
- Authentication protocol validation (MD5, SHA)
- Privacy protocol validation (DES, AES)
- User security model testing
- Engine discovery failure modes

## Automated Testing with API

Use the REST API to automate complex testing scenarios. For complete API examples and endpoint documentation, see [REST API Documentation](REST_API_DOCUMENTATION.md).

Example scenario creation and execution:
- Create test scenarios via `/simulation/scenarios` endpoint
- Execute scenarios via `/simulation/execute` endpoint  
- Monitor progress via WebSocket connections
- Analyze results via `/metrics/history` endpoint

## Validation and Analysis

### Monitoring System Validation Checklist

For each test scenario, verify your monitoring system:

- [ ] **Detects the issue correctly**
- [ ] **Generates appropriate alerts**
- [ ] **Maintains data accuracy during issues**
- [ ] **Recovers gracefully after resolution**
- [ ] **Logs sufficient detail for troubleshooting**

### Performance Metrics to Monitor

During testing, track these key metrics:

- **Request Success Rate**: Should maintain >95% under normal conditions
- **Response Time**: Baseline <100ms, acceptable <500ms under stress
- **Counter Accuracy**: Verify wrap detection and calculation accuracy
- **Memory Usage**: Monitor for leaks during bulk operations
- **Connection Stability**: Track reconnection success rates

### Common Issues and Solutions

**Issue**: Counter wrap not detected
- **Solution**: Verify polling interval vs. counter speed
- **Test**: Use acceleration to force rapid wraps

**Issue**: Bulk operations timing out
- **Solution**: Adjust max-repetitions and timeouts
- **Test**: Progressive bulk size increases

**Issue**: Authentication failing intermittently
- **Solution**: Check clock synchronization and engine discovery
- **Test**: Systematic credential validation

## Integration with Monitoring Tools

### SNMP Monitoring Tools Testing

Test with popular monitoring solutions:

- **Nagios/Icinga**: Plugin response validation
- **Zabbix**: Template behavior verification  
- **PRTG**: Sensor accuracy testing
- **LibreNMS**: Discovery and polling validation
- **Observium**: Device classification testing

### Custom Application Testing

For custom SNMP applications:

```python
# Example Python testing with pysnmp
from pysnmp.hlapi import *

def test_counter_wrap_detection():
    # Monitor counter before wrap
    before_wrap = next(nextCmd(
        SnmpEngine(),
        CommunityData('public'),
        UdpTransportTarget(('127.0.0.1', 11611)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1')),
        lexicographicMode=False
    ))
    
    # Wait for wrap to occur
    time.sleep(60)
    
    # Monitor counter after wrap
    after_wrap = next(nextCmd(
        SnmpEngine(),
        CommunityData('public'),
        UdpTransportTarget(('127.0.0.1', 11611)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1')),
        lexicographicMode=False
    ))
    
    # Verify wrap detection logic
    assert after_wrap < before_wrap, "Counter wrap not detected"
```

## Conclusion

The Mock SNMP Agent provides comprehensive capabilities for testing all major SNMP monitoring challenges. By systematically working through these scenarios, you can ensure your monitoring solution is robust, accurate, and resilient to real-world conditions.

For additional testing automation and API integration, see the [API Testing Guide](API_TESTING_GUIDE.md) and [REST API Documentation](REST_API_DOCUMENTATION.md).