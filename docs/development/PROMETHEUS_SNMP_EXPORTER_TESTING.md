# Testing Prometheus SNMP Exporter with Mock SNMP Agent

## Overview

The Mock SNMP Agent provides comprehensive testing capabilities for [prometheus-snmp-exporter](https://github.com/prometheus/snmp_exporter), enabling you to validate SNMP monitoring configurations, test edge cases, and simulate various network conditions without requiring physical network devices.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Testing Scenarios](#core-testing-scenarios)
- [Advanced Testing Patterns](#advanced-testing-patterns)
- [Configuration Examples](#configuration-examples)
- [Troubleshooting](#troubleshooting)
- [Performance Testing](#performance-testing)
- [CI/CD Integration](#cicd-integration)

## Quick Start

### 1. Setup Mock SNMP Agent

```bash
# Install and start the agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start with prometheus-optimized configuration
python src/mock_snmp_agent.py --config config/prometheus_testing.yaml --port 11611
```

### 2. Configure prometheus-snmp-exporter

```yaml
# snmp.yml
modules:
  mock_device:
    walk:
      - 1.3.6.1.2.1.1     # System information
      - 1.3.6.1.2.1.2.2   # Interface table
      - 1.3.6.1.2.1.25    # Host resources
    metrics:
      - name: sysUpTime
        oid: 1.3.6.1.2.1.1.3.0
        type: gauge
      - name: ifInOctets
        oid: 1.3.6.1.2.1.2.2.1.10
        type: counter
        indexes:
        - labelname: ifIndex
          type: gauge
```

### 3. Test Basic Integration

```bash
# Start snmp_exporter
./snmp_exporter --config.file=snmp.yml

# Test the integration
curl "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_device"
```

## Core Testing Scenarios

### 1. Basic SNMP Operations Testing

Test fundamental SNMP operations that prometheus-snmp-exporter relies on:

```bash
# Start agent with standard MIB data
python src/mock_snmp_agent.py --port 11611

# Test GET operations
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test WALK operations (used by prometheus)
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1

# Test GETBULK operations (efficient for prometheus)
snmpbulkget -v2c -c public -Cn0 -Cr10 127.0.0.1:11611 1.3.6.1.2.1.2.2.1
```

**Expected prometheus-snmp-exporter behavior:**
- Should successfully scrape metrics
- Counter metrics should have `_total` suffix
- Gauge metrics should maintain raw values
- Interface metrics should include proper labels

### 2. Counter Wrap Testing

Critical for network monitoring - test how prometheus handles counter wraps:

```yaml
# config/counter_wrap_prometheus.yaml
simulation:
  behaviors:
    counter_wrap:
      enabled: true
      counters:
        "1.3.6.1.2.1.2.2.1.10.1":  # ifInOctets.1
          acceleration: 100
          wrap_type: "32bit"
          initial_value: 4294967000  # Near wrap point
        "1.3.6.1.2.1.2.2.1.16.1":  # ifOutOctets.1
          acceleration: 100
          wrap_type: "32bit"
          initial_value: 4294967000
```

```bash
# Start agent with counter wrap simulation
python src/mock_snmp_agent.py --config config/counter_wrap_prometheus.yaml --port 11611

# Monitor counter progression
watch -n 5 'curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_device" | grep ifInOctets'
```

**Testing checklist:**
- [ ] Prometheus correctly handles counter resets
- [ ] `rate()` and `increase()` functions work across wraps
- [ ] No negative values in rate calculations
- [ ] Counter metadata includes proper type information

### 3. Network Timeout and Reliability Testing

Test prometheus-snmp-exporter resilience under various network conditions:

```yaml
# config/network_conditions_prometheus.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 1000      # 1 second delay
      deviation: 500          # ±500ms variation
    packet_loss:
      enabled: true
      drop_rate: 5            # 5% packet loss
```

```bash
# Test with network issues
python src/mock_snmp_agent.py --config config/network_conditions_prometheus.yaml --port 11611

# Monitor prometheus scrape duration and success
curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_device" | grep snmp_scrape
```

**Key metrics to monitor:**
- `snmp_scrape_duration_seconds` - Should handle delays gracefully
- `snmp_scrape_pdus_returned` - Should reflect partial responses
- Error rates in prometheus logs

### 4. Large MIB Table Testing

Test prometheus performance with large SNMP tables:

```yaml
# config/large_tables_prometheus.yaml
simulation:
  behaviors:
    bulk_operations:
      enabled: true
      large_tables:
        interface_table:
          base_oid: "1.3.6.1.2.1.2.2.1"
          num_interfaces: 1000    # Simulate 1000 interfaces
          bulk_size: 50           # Max GetBulk size
```

```bash
# Test large table handling
python src/mock_snmp_agent.py --config config/large_tables_prometheus.yaml --port 11611

# Time the scrape operation
time curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_device" > /dev/null
```

**Performance expectations:**
- Scrape completes within prometheus timeout (typically 60s)
- Memory usage remains reasonable
- All interfaces appear in metrics output

### 5. SNMPv3 Security Testing

Test SNMPv3 authentication and encryption with prometheus:

```bash
# Start agent with SNMPv3 support
python src/mock_snmp_agent.py --port 11611

# Configure snmp.yml for SNMPv3
```

```yaml
# snmp.yml - SNMPv3 module
modules:
  snmpv3_device:
    version: 3
    auth:
      username: simulator
      password: auctoritas
      protocol: MD5
    priv:
      password: privatus
      protocol: DES
    walk:
      - 1.3.6.1.2.1.1
```

```bash
# Test SNMPv3 scraping
curl "http://localhost:9116/snmp?target=127.0.0.1:11611&module=snmpv3_device"
```

## Advanced Testing Patterns

### 1. Device Lifecycle Simulation

Simulate device boot, operational, and maintenance states:

```yaml
# config/device_lifecycle_prometheus.yaml
simulation:
  behaviors:
    device_states:
      enabled: true
      states:
        - name: "booting"
          duration: 30
          oid_modifications:
            "1.3.6.1.2.1.1.3.0": 0        # sysUpTime = 0
            "1.3.6.1.2.1.2.2.1.8.1": 2    # ifOperStatus = down
        - name: "operational"
          duration: 300
          oid_modifications:
            "1.3.6.1.2.1.2.2.1.8.1": 1    # ifOperStatus = up
        - name: "maintenance"
          duration: 60
          oid_modifications:
            "1.3.6.1.2.1.1.1.0": "System in maintenance mode"
```

**Prometheus alerts to test:**
- Device unreachable alerts
- Interface down alerts
- System restart detection
- Maintenance mode handling

### 2. Multi-Device Environment Testing

Test prometheus-snmp-exporter with multiple simulated devices:

```bash
# Start multiple agents on different ports
python src/mock_snmp_agent.py --port 11611 --config config/router_sim.yaml &
python src/mock_snmp_agent.py --port 11612 --config config/switch_sim.yaml &
python src/mock_snmp_agent.py --port 11613 --config config/firewall_sim.yaml &

# Configure prometheus to scrape all devices
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'snmp'
    static_configs:
      - targets:
        - 127.0.0.1:11611  # Router
        - 127.0.0.1:11612  # Switch
        - 127.0.0.1:11613  # Firewall
    metrics_path: /snmp
    params:
      module: [mock_device]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:9116
```

### 3. Error Condition Testing

Test how prometheus handles various SNMP error conditions:

```yaml
# config/error_scenarios_prometheus.yaml
simulation:
  behaviors:
    error_injection:
      enabled: true
      error_scenarios:
        - oid_pattern: "1.3.6.1.2.1.99.*"
          error_type: "noSuchObject"
          probability: 100
        - oid_pattern: "1.3.6.1.2.1.2.2.1.1.*"
          error_type: "authorizationError"
          probability: 10
        - oid_pattern: "1.3.6.1.2.1.1.3.0"
          error_type: "timeout"
          probability: 5
```

**Error handling validation:**
- Missing OIDs don't break entire scrape
- Authentication errors are logged appropriately
- Timeouts trigger appropriate retry behavior
- Error metrics are exposed by snmp_exporter

## Configuration Examples

### Complete prometheus-snmp-exporter Configuration

```yaml
# snmp.yml - Complete configuration for Mock SNMP Agent testing
modules:
  mock_standard:
    # Standard network device simulation
    version: 2
    community: public
    walk:
      - 1.3.6.1.2.1.1        # System group
      - 1.3.6.1.2.1.2.2      # Interface table
      - 1.3.6.1.2.1.25.1     # Host resources
    metrics:
      - name: sysUpTime
        oid: 1.3.6.1.2.1.1.3.0
        type: gauge
        help: System uptime in centiseconds
      - name: sysDescr
        oid: 1.3.6.1.2.1.1.1.0
        type: DisplayString
      - name: ifNumber
        oid: 1.3.6.1.2.1.2.1.0
        type: gauge
      - name: ifInOctets
        oid: 1.3.6.1.2.1.2.2.1.10
        type: counter
        help: Octets received on interface
        indexes:
        - labelname: ifIndex
          type: gauge
        - labelname: ifDescr
          type: DisplayString
          oid: 1.3.6.1.2.1.2.2.1.2
      - name: ifOutOctets
        oid: 1.3.6.1.2.1.2.2.1.16
        type: counter
        help: Octets transmitted on interface
        indexes:
        - labelname: ifIndex
          type: gauge
        - labelname: ifDescr
          type: DisplayString
          oid: 1.3.6.1.2.1.2.2.1.2
      - name: ifOperStatus
        oid: 1.3.6.1.2.1.2.2.1.8
        type: gauge
        help: Interface operational status
        indexes:
        - labelname: ifIndex
          type: gauge
        - labelname: ifDescr
          type: DisplayString
          oid: 1.3.6.1.2.1.2.2.1.2

  mock_snmpv3:
    # SNMPv3 testing module
    version: 3
    auth:
      username: simulator
      password: auctoritas
      protocol: MD5
    priv:
      password: privatus
      protocol: DES
    walk:
      - 1.3.6.1.2.1.1
    metrics:
      - name: sysUpTime
        oid: 1.3.6.1.2.1.1.3.0
        type: gauge
      - name: sysDescr
        oid: 1.3.6.1.2.1.1.1.0
        type: DisplayString

  mock_high_frequency:
    # High-frequency polling for performance testing
    version: 2
    community: public
    walk:
      - 1.3.6.1.2.1.2.2.1.10  # Only ifInOctets for speed
      - 1.3.6.1.2.1.2.2.1.16  # Only ifOutOctets for speed
    metrics:
      - name: ifInOctets
        oid: 1.3.6.1.2.1.2.2.1.10
        type: counter
        indexes:
        - labelname: ifIndex
          type: gauge
      - name: ifOutOctets
        oid: 1.3.6.1.2.1.2.2.1.16
        type: counter
        indexes:
        - labelname: ifIndex
          type: gauge
```

### Mock Agent Configurations

```yaml
# config/prometheus_standard.yaml
simulation:
  logging:
    enabled: true
    level: info
  behaviors:
    delay:
      enabled: false
    counter_progression:
      enabled: true
      # Realistic counter progression
      counters:
        "1.3.6.1.2.1.2.2.1.10.1": 1000    # 1KB/s
        "1.3.6.1.2.1.2.2.1.16.1": 800     # 800B/s
```

```yaml
# config/prometheus_stress_test.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 2000      # 2 second delays
      deviation: 1000         # High variation
    packet_loss:
      enabled: true
      drop_rate: 10           # 10% packet loss
    counter_wrap:
      enabled: true
      acceleration: 1000      # Fast counter progression
    bulk_operations:
      enabled: true
      large_tables:
        interface_table:
          num_interfaces: 500  # Many interfaces
```

## Performance Testing

### 1. Scrape Performance Benchmarks

```bash
#!/bin/bash
# performance_test_prometheus.sh

# Test various scenarios and measure performance
scenarios=("standard" "high_frequency" "large_tables" "with_delays")

for scenario in "${scenarios[@]}"; do
    echo "Testing scenario: $scenario"

    # Start mock agent with scenario config
    python src/mock_snmp_agent.py --config "config/prometheus_${scenario}.yaml" --port 11611 &
    agent_pid=$!
    sleep 5

    # Measure scrape performance
    echo "Measuring scrape time..."
    time curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_${scenario}" > "/tmp/metrics_${scenario}.txt"

    # Count metrics returned
    metric_count=$(grep -c "^[a-zA-Z]" "/tmp/metrics_${scenario}.txt")
    echo "Metrics returned: $metric_count"

    # Stop agent
    kill $agent_pid
    wait $agent_pid 2>/dev/null

    echo "---"
done
```

### 2. Memory Usage Testing

```bash
# Monitor memory usage during large table scraping
python src/mock_snmp_agent.py --config config/prometheus_large_tables.yaml --port 11611 &
agent_pid=$!

# Monitor memory usage
while true; do
    memory=$(ps -o rss= -p $agent_pid)
    echo "$(date): Agent memory: ${memory}KB"
    sleep 10
done &
monitor_pid=$!

# Run scrape test
curl "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard"

# Cleanup
kill $monitor_pid $agent_pid
```

### 3. Concurrent Scraping Test

```bash
# Test multiple concurrent scrapes
for i in {1..10}; do
    (
        echo "Starting scrape $i"
        time curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" > "/tmp/scrape_$i.txt"
        echo "Completed scrape $i"
    ) &
done

# Wait for all scrapes to complete
wait
echo "All concurrent scrapes completed"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Timeout Errors

**Problem:** prometheus-snmp-exporter times out when scraping
```
level=error ts=2024-01-01T12:00:00.000Z caller=snmp.go:123 msg="Error scraping target" err="request timeout"
```

**Solution:**
```yaml
# Reduce simulation delays
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 100    # Reduce from higher value
      deviation: 50        # Lower deviation
```

#### 2. Missing Metrics

**Problem:** Expected metrics don't appear in prometheus output

**Debugging:**
```bash
# Check what OIDs are available
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1

# Verify snmp.yml configuration
curl "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard&debug=true"

# Check mock agent logs
python src/mock_snmp_agent.py --config config/prometheus_standard.yaml --port 11611 --verbose
```

#### 3. Counter Wrap Issues

**Problem:** Prometheus shows negative rate values

**Solution:**
```yaml
# Ensure proper counter progression
simulation:
  behaviors:
    counter_progression:
      enabled: true
      wrap_detection: true
      monotonic: true      # Ensure counters only increase
```

#### 4. SNMPv3 Authentication Failures

**Problem:** SNMPv3 scrapes fail with authentication errors

**Debugging:**
```bash
# Test SNMPv3 manually first
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Check engine ID discovery
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -E 0x80001f8880e9630000d61ff449 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### Debugging with REST API

The Mock SNMP Agent's REST API provides excellent debugging capabilities:

```bash
# Check agent health
curl http://localhost:8080/health

# Get current metrics and performance
curl http://localhost:8080/metrics

# Monitor real-time SNMP activity
curl http://localhost:8080/ws/snmp-activity
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/prometheus-snmp-exporter-test.yml
name: Test prometheus-snmp-exporter Integration

on: [push, pull_request]

jobs:
  test-integration:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        # Download prometheus-snmp-exporter
        wget https://github.com/prometheus/snmp_exporter/releases/download/v0.24.1/snmp_exporter-0.24.1.linux-amd64.tar.gz
        tar xzf snmp_exporter-0.24.1.linux-amd64.tar.gz

    - name: Start Mock SNMP Agent
      run: |
        python src/mock_snmp_agent.py --config config/prometheus_standard.yaml --port 11611 &
        sleep 5

    - name: Start SNMP Exporter
      run: |
        ./snmp_exporter-0.24.1.linux-amd64/snmp_exporter --config.file=tests/snmp.yml &
        sleep 5

    - name: Test Integration
      run: |
        # Test basic scraping
        curl -f "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard"

        # Test metrics format
        curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" | grep -q "ifInOctets_total"

        # Test scrape duration metric
        curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" | grep -q "snmp_scrape_duration_seconds"

    - name: Test Counter Wrap Handling
      run: |
        # Start agent with counter wrap simulation
        pkill -f mock_snmp_agent || true
        python src/mock_snmp_agent.py --config config/counter_wrap_prometheus.yaml --port 11611 &
        sleep 5

        # Scrape multiple times to observe counter behavior
        for i in {1..5}; do
          curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" > "scrape_$i.txt"
          sleep 10
        done

        # Verify counter values increase (allowing for wraps)
        python tests/verify_counter_progression.py scrape_*.txt
```

### Docker Compose for Testing

```yaml
# docker-compose.prometheus-test.yml
version: '3.8'

services:
  mock-snmp-agent:
    build: .
    ports:
      - "11611:161/udp"
    command: >
      python src/mock_snmp_agent.py
      --config config/prometheus_standard.yaml
      --port 161
    volumes:
      - ./config:/app/config
      - ./data:/app/data

  snmp-exporter:
    image: prom/snmp-exporter:latest
    ports:
      - "9116:9116"
    volumes:
      - ./tests/snmp.yml:/etc/snmp_exporter/snmp.yml
    depends_on:
      - mock-snmp-agent

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./tests/prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - snmp-exporter
```

```bash
# Run the complete test environment
docker-compose -f docker-compose.prometheus-test.yml up

# Test the full pipeline
curl "http://localhost:9090/api/v1/query?query=snmp_scrape_duration_seconds"
```

## Best Practices

### 1. Configuration Management

- Use separate configuration files for different test scenarios
- Version control your snmp.yml configurations
- Document expected behavior for each test case

### 2. Monitoring Test Health

```bash
# Create a monitoring script
cat > monitor_test_health.sh << 'EOF'
#!/bin/bash

echo "Checking Mock SNMP Agent health..."
curl -s http://localhost:8080/health | jq .

echo "Checking SNMP Exporter health..."
curl -s http://localhost:9116/metrics | grep snmp_exporter_build_info

echo "Testing scrape endpoint..."
response_time=$(curl -w "%{time_total}" -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" -o /dev/null)
echo "Scrape response time: ${response_time}s"

echo "Checking for common metrics..."
curl -s "http://localhost:9116/snmp?target=127.0.0.1:11611&module=mock_standard" | grep -E "(sysUpTime|ifInOctets|ifOutOctets)" | head -5
EOF

chmod +x monitor_test_health.sh
```

### 3. Automated Validation

```python
# tests/validate_prometheus_metrics.py
import requests
import re
import sys

def validate_prometheus_metrics(exporter_url, target, module):
    """Validate prometheus-snmp-exporter metrics format and content."""

    url = f"{exporter_url}/snmp"
    params = {"target": target, "module": module}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        metrics_text = response.text
        lines = metrics_text.strip().split('\n')

        # Validation checks
        checks = {
            "has_metrics": len([l for l in lines if not l.startswith('#') and l.strip()]) > 0,
            "has_counter_total": any("_total" in line for line in lines),
            "has_scrape_duration": any("snmp_scrape_duration_seconds" in line for line in lines),
            "has_help_text": any(line.startswith("# HELP") for line in lines),
            "has_type_info": any(line.startswith("# TYPE") for line in lines),
            "no_errors": "snmp_request_errors_total" not in metrics_text or
                        all(line.split()[-1] == "0" for line in lines if "snmp_request_errors_total" in line)
        }

        print("Validation Results:")
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check}: {status}")

        if all(checks.values()):
            print("\n🎉 All validations passed!")
            return True
        else:
            print("\n⚠️  Some validations failed!")
            return False

    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    exporter_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9116"
    target = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:11611"
    module = sys.argv[3] if len(sys.argv) > 3 else "mock_standard"

    success = validate_prometheus_metrics(exporter_url, target, module)
    sys.exit(0 if success else 1)
```

## Conclusion

The Mock SNMP Agent provides comprehensive testing capabilities for prometheus-snmp-exporter, enabling you to:

- **Validate configurations** before deploying to production
- **Test edge cases** like counter wraps, timeouts, and network issues
- **Performance test** with large MIB tables and high-frequency polling
- **Automate testing** in CI/CD pipelines
- **Debug issues** with detailed logging and REST API monitoring

By using these testing patterns and configurations, you can ensure your prometheus-snmp-exporter setup is robust, performant, and handles real-world network conditions effectively.

For additional examples and configurations, see:
- [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md) for command syntax
- [Configuration Guide](CONFIGURATION_GUIDE.md) for detailed YAML examples
- [Advanced Testing Guide](ADVANCED_TESTING_GUIDE.md) for scenario testing
- [Performance Results](PERFORMANCE_RESULTS.md) for benchmarking data
