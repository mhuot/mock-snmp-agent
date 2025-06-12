# Configuration Guide

## Overview

The Mock SNMP Agent supports advanced configuration through YAML/JSON files, enabling complex testing scenarios without code changes. This guide covers all configuration options and provides practical examples for different testing needs.

## Configuration File Usage

Create a YAML configuration file to define simulation behaviors:

```bash
# Run with configuration file
python src/mock_snmp_agent.py --config config/comprehensive.yaml --port 11611
```

## Configuration File Structure

```yaml
simulation:
  # Delay simulation settings
  delay:
    enabled: boolean
    global_delay: integer (milliseconds)
    deviation: integer (milliseconds)
    oid_specific:
      "OID": delay_ms

  # Packet loss simulation
  drop_rate: integer (percentage 0-100)
  packet_loss: integer (percentage 0-100)

  # Counter wrap simulation
  counter_wrap:
    enabled: boolean
    counters:
      "OID":
        acceleration: integer
        wrap_type: "32bit" | "64bit"
        initial_value: integer

  # Resource constraint simulation
  resource_limits:
    enabled: boolean
    cpu_limit: integer (percentage)
    memory_limit: integer (percentage)
    max_concurrent: integer
    queue_size: integer

  # Error injection
  error_injection:
    enabled: boolean
    error_rate: integer (percentage)
    error_types:
      - "noSuchName"
      - "authorizationError"
      - "noAccess"
      - "genErr"

  # Agent restart simulation
  restart:
    enabled: boolean
    interval: integer (seconds)
    downtime: integer (seconds)
    random_variation: integer (seconds)

# SNMP agent settings
agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
    - name: "private"
      access: "write"

  # SNMPv3 configuration
  snmpv3:
    enabled: boolean
    users:
      - username: "string"
        auth_protocol: "MD5" | "SHA"
        auth_key: "string"
        priv_protocol: "DES" | "AES"
        priv_key: "string"

# REST API settings (optional)
api:
  enabled: boolean
  port: integer
  host: "string"
  cors_origins: ["string"]
```

## Example Configurations

### Basic Delay Configuration

```yaml
# config/simple.yaml
simulation:
  delay:
    enabled: true
    global_delay: 500      # 500ms delay for all responses
    deviation: 100         # ±100ms random variation

  drop_rate: 5             # 5% packet drop rate
  packet_loss: 2           # 2% packet loss simulation

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
```

**Usage:**
```bash
python src/mock_snmp_agent.py --config config/simple.yaml
```

### Counter Wrap Testing Configuration

```yaml
# config/counter_wrap_test.yaml
simulation:
  counter_wrap:
    enabled: true
    counters:
      "1.3.6.1.2.1.2.2.1.10": # ifInOctets
        acceleration: 1000   # 1000x speed for testing
        wrap_type: "32bit"   # 32-bit counter
        initial_value: 4294967000  # Start near wrap
      "1.3.6.1.2.1.2.2.1.16": # ifOutOctets
        acceleration: 1000
        wrap_type: "32bit"
        initial_value: 4294967000
      "1.3.6.1.2.1.2.2.1.11": # ifInUcastPkts
        acceleration: 500
        wrap_type: "32bit"
        initial_value: 4294960000

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
```

**Usage:**
```bash
python src/mock_snmp_agent.py --config config/counter_wrap_test.yaml

# Monitor counter progression
watch -n 1 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.2.2.1.10.1'
```

For complete monitoring command examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#monitoring-and-watching-commands).

### Resource Constraint Testing Configuration

```yaml
# config/resource_limits.yaml
simulation:
  resource_limits:
    enabled: true
    cpu_limit: 80          # Simulate 80% CPU usage
    memory_limit: 90       # Simulate 90% memory usage
    max_concurrent: 50     # Max 50 concurrent requests
    queue_size: 100        # Request queue size

  # Add some delay under high load
  delay:
    enabled: true
    global_delay: 50
    deviation: 20

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
```

**Usage:**
```bash
python src/mock_snmp_agent.py --config config/resource_limits.yaml

# Generate high request load
for i in {1..100}; do
  snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0 &
done
```

For load testing command examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#load-testing-commands).

### Bulk Operation Testing Configuration

```yaml
# config/bulk_test.yaml
simulation:
  # Large table simulation
  bulk_operations:
    enabled: true
    large_tables:
      "1.3.6.1.2.1.2.2": # Interface table
        entries: 1000     # 1000 interface entries
        response_delay: 10 # 10ms per entry
      "1.3.6.1.2.1.4.20": # IP address table
        entries: 500
        response_delay: 5

  # Simulate memory pressure during bulk ops
  resource_limits:
    enabled: true
    memory_limit: 85

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
```

**Usage:**
```bash
python src/mock_snmp_agent.py --config config/bulk_test.yaml

# Test large GetBulk operations
snmpbulkget -v2c -c public -Cn0 -Cr50 localhost:11611 1.3.6.1.2.1.2.2.1
```

### Network Condition Simulation

```yaml
# config/network_conditions.yaml
simulation:
  delay:
    enabled: true
    global_delay: 200      # Base 200ms latency
    deviation: 50          # ±50ms jitter
    oid_specific:
      "1.3.6.1.2.1.1.1.0": 100   # Fast response for sysDescr
      "1.3.6.1.2.1.2.2.1": 500   # Slow response for interface table

  drop_rate: 10            # 10% packet drop
  packet_loss: 5           # 5% additional packet loss

  # Intermittent connectivity issues
  restart:
    enabled: true
    interval: 300          # Restart every 5 minutes
    downtime: 30           # 30 seconds down
    random_variation: 60   # ±60 seconds variation

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
```

### Error Injection Configuration

```yaml
# config/error_injection.yaml
simulation:
  error_injection:
    enabled: true
    error_rate: 20         # 20% of requests return errors
    error_types:
      - "noSuchName"       # 40% of errors
      - "authorizationError" # 30% of errors
      - "noAccess"         # 20% of errors
      - "genErr"           # 10% of errors

    # OID-specific error configuration
    oid_errors:
      "1.3.6.1.2.1.1.4.0": "noAccess"     # sysContact always fails
      "1.3.6.1.2.1.1.6.0": "authorizationError" # sysLocation auth error

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
    - name: "private"
      access: "write"
```

### SNMPv3 Security Testing

```yaml
# config/snmpv3_security.yaml
simulation:
  # Simulate authentication delays
  delay:
    enabled: true
    global_delay: 100
    deviation: 50

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"

  snmpv3:
    enabled: true
    users:
      - username: "testuser"
        auth_protocol: "MD5"
        auth_key: "authkey123"
        priv_protocol: "DES"
        priv_key: "privkey123"
      - username: "shauser"
        auth_protocol: "SHA"
        auth_key: "shakey456"
        priv_protocol: "AES"
        priv_key: "aeskey456"
      - username: "noauth"
        auth_protocol: null
        auth_key: null
        priv_protocol: null
        priv_key: null
```

**Usage:**
```bash
python src/mock_snmp_agent.py --config config/snmpv3_security.yaml

# Test valid authentication
snmpget -v3 -l authPriv -u testuser -a MD5 -A authkey123 -x DES -X privkey123 \
    localhost:11611 1.3.6.1.2.1.1.1.0

# Test authentication failure
snmpget -v3 -l authPriv -u testuser -a MD5 -A wrongkey -x DES -X privkey123 \
    localhost:11611 1.3.6.1.2.1.1.1.0
```

For complete SNMPv3 command examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#snmpv3-commands).

### Comprehensive Testing Configuration

```yaml
# config/comprehensive.yaml
simulation:
  # Enable all simulation types with moderate settings
  delay:
    enabled: true
    global_delay: 100
    deviation: 25
    oid_specific:
      "1.3.6.1.2.1.2.2.1": 200  # Interface table slower

  drop_rate: 2             # Light packet loss
  packet_loss: 1

  counter_wrap:
    enabled: true
    counters:
      "1.3.6.1.2.1.2.2.1.10":
        acceleration: 100
        wrap_type: "32bit"

  resource_limits:
    enabled: true
    cpu_limit: 70
    memory_limit: 80
    max_concurrent: 75

  error_injection:
    enabled: true
    error_rate: 5          # Light error injection
    error_types: ["noSuchName", "genErr"]

  restart:
    enabled: true
    interval: 600          # Restart every 10 minutes
    downtime: 15           # 15 seconds down
    random_variation: 120  # ±2 minutes variation

agent:
  endpoint: "127.0.0.1:11611"
  communities:
    - name: "public"
      access: "read"
    - name: "private"
      access: "write"

  snmpv3:
    enabled: true
    users:
      - username: "simulator"
        auth_protocol: "MD5"
        auth_key: "auctoritas"
        priv_protocol: "DES"
        priv_key: "privatus"

# Enable REST API for monitoring
api:
  enabled: true
  port: 8080
  host: "0.0.0.0"
  cors_origins: ["*"]
```

## CLI Quick Options

For rapid testing, use CLI flags without configuration files:

```bash
# Quick delay testing
python src/mock_snmp_agent.py --delay 1000 --drop-rate 10

# Combined quick options
python src/mock_snmp_agent.py --delay 500 --drop-rate 5 --restart-interval 300

# Override config file settings
python src/mock_snmp_agent.py --config config/base.yaml --delay 2000
```

### Available CLI Flags

```bash
# Delay options
--delay MILLISECONDS          # Global response delay
--deviation MILLISECONDS      # Random delay variation

# Network simulation
--drop-rate PERCENTAGE        # Packet drop rate (0-100)
--packet-loss PERCENTAGE      # Additional packet loss

# Agent behavior
--restart-interval SECONDS    # Automatic restart interval
--port PORT                   # SNMP agent port (default: 11611)

# API options
--rest-api                    # Enable REST API
--api-port PORT               # REST API port (default: 8080)

# Configuration
--config FILENAME             # Load configuration file
--verbose                     # Enable verbose logging
--quiet                       # Suppress most output
```

## Configuration Validation

The agent validates configuration files on startup:

```bash
# Test configuration file
python src/mock_snmp_agent.py --config config/test.yaml --validate-only

# Check configuration with verbose output
python src/mock_snmp_agent.py --config config/test.yaml --verbose
```

### Common Configuration Errors

**Invalid YAML syntax:**
```yaml
# Wrong - missing quotes around OID
simulation:
  counter_wrap:
    counters:
      1.3.6.1.2.1.1.1.0: 1000  # Should be quoted

# Correct
simulation:
  counter_wrap:
    counters:
      "1.3.6.1.2.1.1.1.0": 1000
```

**Invalid value ranges:**
```yaml
# Wrong - percentage > 100
simulation:
  drop_rate: 150  # Must be 0-100

# Wrong - negative delay
delay:
  global_delay: -100  # Must be >= 0
```

## Environment Variable Substitution

Configuration files support environment variable substitution:

```yaml
# config/production.yaml
agent:
  endpoint: "${SNMP_ENDPOINT:-127.0.0.1:11611}"

api:
  enabled: true
  port: "${API_PORT:-8080}"
  host: "${API_HOST:-0.0.0.0}"

simulation:
  delay:
    global_delay: "${RESPONSE_DELAY:-100}"
```

**Usage:**
```bash
export SNMP_ENDPOINT="0.0.0.0:161"
export API_PORT="9090"
export RESPONSE_DELAY="500"

python src/mock_snmp_agent.py --config config/production.yaml
```

## Dynamic Configuration Updates

When REST API is enabled, configurations can be updated dynamically:

```bash
# Update delay configuration
curl -X PUT http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {
      "delay": {
        "enabled": true,
        "global_delay": 250,
        "deviation": 50
      }
    }
  }'

# Get current configuration
curl http://localhost:8080/config
```

## Best Practices

### Configuration Organization

```
config/
├── environments/
│   ├── development.yaml
│   ├── testing.yaml
│   └── production.yaml
├── scenarios/
│   ├── counter_wrap.yaml
│   ├── high_latency.yaml
│   ├── resource_limits.yaml
│   └── bulk_operations.yaml
└── templates/
    ├── base.yaml
    └── snmpv3.yaml
```

### Version Control

- Keep configuration files in version control
- Use descriptive names for scenario configurations
- Document configuration changes in commit messages
- Use environment variables for deployment-specific values

### Testing Configurations

```bash
# Test configuration syntax
python -c "import yaml; yaml.safe_load(open('config/test.yaml'))"

# Validate with agent
python src/mock_snmp_agent.py --config config/test.yaml --validate-only

# Dry run with verbose output
python src/mock_snmp_agent.py --config config/test.yaml --dry-run --verbose
```

For more advanced configuration examples and integration with monitoring tools, see the [Advanced Testing Scenarios Guide](ADVANCED_TESTING_GUIDE.md).
