# SNMP Commands Reference

## Overview

This reference provides common SNMP command examples used throughout the Mock SNMP Agent documentation. All commands assume the agent is running on `127.0.0.1:11611` unless otherwise specified.

## Basic SNMP Commands

### SNMPv1 and SNMPv2c Commands

```bash
# Basic SNMPv2c GET operation
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# SNMPv1 GET operation
snmpget -v1 -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# GETNEXT operation
snmpgetnext -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1

# GETBULK operation
snmpbulkget -v2c -c public -Cn0 -Cr3 127.0.0.1:11611 1.3.6.1.2.1.1

# Large GETBULK operation
snmpbulkget -v2c -c public -Cn0 -Cr50 127.0.0.1:11611 1.3.6.1.2.1.2.2.1

# SNMP walk
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1
```

### SNMPv3 Commands

```bash
# SNMPv3 with authentication and privacy (default credentials)
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# SNMPv3 with authentication only (no privacy)
snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# SNMPv3 without authentication or privacy
snmpget -v3 -l noAuthNoPriv -u simulator \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

## Community String Variations

### Standard Communities
```bash
# Public community (standard data)
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Private community (if write access enabled)
snmpset -v2c -c private 127.0.0.1:11611 1.3.6.1.2.1.1.4.0 s "admin@example.com"
```

### Variation Communities
```bash
# Delay simulation community
snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Error simulation community
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Writeable cache community
snmpget -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Invalid community (for testing error handling)
snmpget -v2c -c invalid 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### Recorded Data Communities
```bash
# Linux system data
snmpget -v2c -c recorded/linux-full-walk 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Windows XP system data
snmpget -v2c -c recorded/winxp-full-walk 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

## SET Operations

### Basic SET Operations
```bash
# Set system description
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Modified system description"

# Set system contact
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.4.0 s "admin@example.com"

# Set system location
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.6.0 s "Data Center A, Rack 15"
```

### Interface Configuration
```bash
# Set interface description
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.2.2.1.2.1 s "WAN Interface to ISP"

# Set interface admin status (1=up, 2=down)
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.2.2.1.7.1 i 1
```

### Multiple SET Operations
```bash
# Set multiple values in one command
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Production Router" \
    1.3.6.1.2.1.1.4.0 s "netops@company.com" \
    1.3.6.1.2.1.1.6.0 s "Network Operations Center"
```

## Common OID References

### System Information OIDs
```bash
# System description
1.3.6.1.2.1.1.1.0

# System object ID
1.3.6.1.2.1.1.2.0

# System uptime
1.3.6.1.2.1.1.3.0

# System contact
1.3.6.1.2.1.1.4.0

# System name
1.3.6.1.2.1.1.5.0

# System location
1.3.6.1.2.1.1.6.0
```

### Interface Table OIDs
```bash
# Number of interfaces
1.3.6.1.2.1.2.1.0

# Interface description (index 1)
1.3.6.1.2.1.2.2.1.2.1

# Interface type (index 1)
1.3.6.1.2.1.2.2.1.3.1

# Interface admin status (index 1)
1.3.6.1.2.1.2.2.1.7.1

# Interface operational status (index 1)
1.3.6.1.2.1.2.2.1.8.1

# Interface input octets (index 1)
1.3.6.1.2.1.2.2.1.10.1

# Interface output octets (index 1)
1.3.6.1.2.1.2.2.1.16.1
```

## Performance and Timing Options

### Timeout and Retry Options
```bash
# Set timeout to 1 second, 2 retries
snmpget -v2c -c public -t 1 -r 2 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Set timeout to 3 seconds, 1 retry
snmpget -v2c -c public -t 3 -r 1 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### Timing Commands
```bash
# Time a command execution
time snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Time a command with delay simulation
time snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1
```

## Monitoring and Watching Commands

### Continuous Monitoring
```bash
# Monitor counter progression (for counter wrap testing)
watch -n 1 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.2.2.1.10.1'

# Monitor system uptime
watch -n 5 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.3.0'
```

### Load Testing Commands
```bash
# Generate multiple concurrent requests
for i in {1..100}; do
  snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0 &
done

# Progressive timeout testing
for delay in 100 500 1000 2000 5000; do
  echo "Testing ${delay}ms delay..."
  time snmpget -v2c -c public -t 3 localhost:11611 1.3.6.1.2.1.1.1.0
done
```

## Troubleshooting Commands

### Connection Testing
```bash
# Test basic connectivity
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test with timeout
timeout 10 snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test UDP connectivity
nc -u 127.0.0.1 11611
```

### Error Testing
```bash
# Trigger authorization error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.1

# Trigger no-access error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1

# Test invalid OID
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.99.99.99.0
```

## Usage in Different Contexts

### Development Testing
Reference these commands from:
- [Advanced Testing Scenarios Guide](ADVANCED_TESTING_GUIDE.md)
- [Advanced Usage Guide](ADVANCED_USAGE_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Configuration Validation
Use these commands to test configurations from:
- [Configuration Guide](CONFIGURATION_GUIDE.md)

### API Integration
Combine with REST API calls as shown in:
- [REST API Documentation](REST_API_DOCUMENTATION.md)
- [API Testing Guide](API_TESTING_GUIDE.md)

## Notes

- Replace `127.0.0.1:11611` with your actual agent address and port
- Default SNMPv3 credentials are: user=`simulator`, auth=`auctoritas`, priv=`privatus`
- Use appropriate community strings based on your testing scenario
- Add `-v` flag for verbose output when troubleshooting
- Ensure the Mock SNMP Agent is running before executing commands
