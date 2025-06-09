# Advanced Usage Guide

## Overview

This guide covers advanced features and usage patterns for the Mock SNMP Agent, including community string variations, SNMPv3 configuration, data file management, and integration with monitoring tools.

## Community Strings and Simulation Scenarios

The simulator supports multiple community strings for different simulation scenarios:

### Standard Communities

- **`public`**: Standard MIB-II data with typical system information
- **`private`**: Write access for SET operations (when enabled)

### Variation Communities

- **`variation/delay`**: Responses with configurable delays
- **`variation/error`**: Various SNMP error responses  
- **`variation/writecache`**: Writeable OIDs for SET operations
- **`variation/notification`**: Trap and inform generation

### Recorded Data Communities

- **`recorded/linux-full-walk`**: Real Linux system SNMP walk data
- **`recorded/winxp-full-walk`**: Real Windows XP system SNMP walk data
- **`recorded/cisco-router`**: Cisco router simulation data
- **`recorded/netgear-switch`**: Network switch simulation data

## Delay Simulation

Test slow network or processing scenarios using the `variation/delay` community string. For complete command syntax and examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#community-string-variations).

```bash
# Basic delay testing
snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Time the response to measure delay
time snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1
```

### Custom Delay Configuration

Configure specific delays for different OIDs:

```bash
# Start agent with custom delay configuration
python mock_snmp_agent.py --config config/custom_delays.yaml
```

```yaml
# config/custom_delays.yaml
simulation:
  delay:
    enabled: true
    global_delay: 100      # Base delay for all responses
    deviation: 20          # ±20ms random variation
    oid_specific:
      "1.3.6.1.2.1.1.1.0": 50    # Fast response for sysDescr
      "1.3.6.1.2.1.2.2.1": 500   # Slow response for interface table
      "1.3.6.1.2.1.25": 1000     # Very slow for host resources
```

## Error Simulation

Test error handling in your SNMP applications using the `variation/error` community string. For complete error testing commands, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#error-testing).

### Basic Error Testing

```bash
# Trigger authorization error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.1

# Trigger no-access error  
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1
```

### Advanced Error Configuration

```yaml
# config/error_scenarios.yaml
simulation:
  error_injection:
    enabled: true
    error_rate: 15         # 15% of requests return errors
    error_types:
      - "noSuchName"       # 40% of errors
      - "authorizationError" # 30% of errors  
      - "noAccess"         # 20% of errors
      - "genErr"           # 10% of errors
    
    # OID-specific errors
    oid_errors:
      "1.3.6.1.2.1.1.4.0": "noAccess"        # sysContact always fails
      "1.3.6.1.2.1.1.6.0": "authorizationError"  # sysLocation auth error
      "1.3.6.1.2.1.25.1": "resourceUnavailable"  # Host resources unavailable
```

## SET Operations

Test writeable OIDs and configuration changes:

### Basic SET Operations

```bash
# Set system description
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Modified system description"

# Read it back to verify
snmpget -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

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

# Verify interface operational status
snmpget -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.8.1
```

### Complex SET Operations

```bash
# Multiple SET operations in one command
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Production Router" \
    1.3.6.1.2.1.1.4.0 s "netops@company.com" \
    1.3.6.1.2.1.1.6.0 s "Network Operations Center"

# SET with different data types
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "String value" \
    1.3.6.1.2.1.1.3.0 t 123456789 \
    1.3.6.1.4.1.99999.1.1.0 i 42
```

## SNMPv3 Configuration

The simulator automatically configures SNMPv3 with sensible defaults and supports custom configurations.

### Default SNMPv3 Settings

- **Engine ID**: Auto-generated based on system
- **User**: `simulator`
- **Auth Protocol**: MD5
- **Auth Key**: `auctoritas`
- **Privacy Protocol**: DES
- **Privacy Key**: `privatus`

### Basic SNMPv3 Testing

```bash
# Test with authentication and privacy
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test with authentication only (no privacy)
snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test without authentication (noAuthNoPriv)
snmpget -v3 -l noAuthNoPriv -u simulator \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### Custom SNMPv3 Configuration

```yaml
# config/snmpv3_custom.yaml
agent:
  snmpv3:
    enabled: true
    engine_id: "8000000001020304"  # Custom engine ID
    users:
      - username: "admin"
        auth_protocol: "SHA"
        auth_key: "admin_secret_key_123"
        priv_protocol: "AES"
        priv_key: "admin_priv_key_456"
        context: "admin_context"
      
      - username: "monitor"
        auth_protocol: "MD5"  
        auth_key: "monitor_auth_789"
        priv_protocol: "DES"
        priv_key: "monitor_priv_012"
        context: "public"
      
      - username: "readonly"
        auth_protocol: "SHA"
        auth_key: "readonly_key_345"
        priv_protocol: null  # No privacy
        priv_key: null
        context: "public"
      
      - username: "noauth"
        auth_protocol: null  # No authentication
        auth_key: null
        priv_protocol: null
        priv_key: null
        context: "public"
```

**Testing Custom Users:**

```bash
# Test admin user with SHA/AES
snmpget -v3 -l authPriv -u admin -a SHA -A admin_secret_key_123 \
    -x AES -X admin_priv_key_456 -n admin_context \
    127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test monitor user with MD5/DES
snmpget -v3 -l authPriv -u monitor -a MD5 -A monitor_auth_789 \
    -x DES -X monitor_priv_012 -n public \
    127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test readonly user (auth only)
snmpget -v3 -l authNoPriv -u readonly -a SHA -A readonly_key_345 \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

## Data Files and MIB Management

### Built-in Data Sources

The simulator uses data files from the snmpsim-lextudio package:

- **Standard communities**: MIB-II implementations
- **Variation modules**: Dynamic behavior simulation
- **Real device data**: Recorded SNMP walks from actual devices

### Custom Data Files

Create custom .snmprec files for specific device simulation:

```bash
# Create custom device data directory
mkdir -p data/custom

# Create a simple device simulation
cat > data/custom/router.snmprec << 'EOF'
1.3.6.1.2.1.1.1.0|4|Cisco IOS Router
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.9.1.122
1.3.6.1.2.1.1.3.0|67|12345678
1.3.6.1.2.1.1.4.0|4|admin@company.com
1.3.6.1.2.1.1.5.0|4|ROUTER-01
1.3.6.1.2.1.1.6.0|4|Data Center A
1.3.6.1.2.1.2.1.0|2|24
EOF

# Use custom data with specific community
python mock_snmp_agent.py --data-dir ./data/custom
```

### Dynamic Data Generation

Create data files with variation modules:

```python
#!/usr/bin/env python3
# generate_dynamic_data.py

import time
import random

def generate_interface_data(num_interfaces=24):
    """Generate dynamic interface table data."""
    data = []
    
    for i in range(1, num_interfaces + 1):
        # Interface description
        data.append(f"1.3.6.1.2.1.2.2.1.2.{i}|4|GigabitEthernet0/{i}")
        
        # Interface type (ethernetCsmacd = 6)
        data.append(f"1.3.6.1.2.1.2.2.1.3.{i}|2|6")
        
        # Interface MTU
        data.append(f"1.3.6.1.2.1.2.2.1.4.{i}|2|1500")
        
        # Interface speed (1 Gbps = 1000000000)
        data.append(f"1.3.6.1.2.1.2.2.1.5.{i}|66|1000000000")
        
        # Interface admin status (up = 1)
        data.append(f"1.3.6.1.2.1.2.2.1.7.{i}|2|1")
        
        # Interface operational status (up = 1, down = 2)
        status = 1 if random.random() > 0.1 else 2  # 90% up
        data.append(f"1.3.6.1.2.1.2.2.1.8.{i}|2|{status}")
        
        # Interface counters (random values)
        in_octets = random.randint(1000000, 4000000000)
        out_octets = random.randint(1000000, 4000000000)
        data.append(f"1.3.6.1.2.1.2.2.1.10.{i}|65|{in_octets}")
        data.append(f"1.3.6.1.2.1.2.2.1.16.{i}|65|{out_octets}")
    
    return data

if __name__ == "__main__":
    # Generate data for a 24-port switch
    interface_data = generate_interface_data(24)
    
    # Write to file
    with open("data/custom/switch24port.snmprec", "w") as f:
        # System information
        f.write("1.3.6.1.2.1.1.1.0|4|24-Port Gigabit Switch\\n")
        f.write("1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.99999.1.1\\n")
        f.write(f"1.3.6.1.2.1.1.3.0|67|{int(time.time() * 100)}\\n")
        f.write("1.3.6.1.2.1.1.4.0|4|netadmin@company.com\\n")
        f.write("1.3.6.1.2.1.1.5.0|4|SWITCH-24P-01\\n")
        f.write("1.3.6.1.2.1.1.6.0|4|Network Closet B\\n")
        f.write("1.3.6.1.2.1.2.1.0|2|24\\n")
        
        # Interface data
        for line in interface_data:
            f.write(line + "\\n")
        
    print("Generated switch24port.snmprec with 24 interfaces")
```

## Monitoring Tool Integration

### Nagios/Icinga Integration

```bash
# Test Nagios check_snmp plugin
check_snmp -H 127.0.0.1 -p 11611 -C public -o 1.3.6.1.2.1.1.3.0

# Test with warning/critical thresholds
check_snmp -H 127.0.0.1 -p 11611 -C public -o 1.3.6.1.2.1.2.2.1.10.1 \
    -w 1000000 -c 2000000

# Test interface status check
check_snmp -H 127.0.0.1 -p 11611 -C public -o 1.3.6.1.2.1.2.2.1.8.1 \
    -r "^1$" -m "Interface is UP"
```

### Zabbix Integration

```xml
<!-- Zabbix template item for interface monitoring -->
<item>
    <name>Interface {#IFNAME} status</name>
    <key>snmp.get[1.3.6.1.2.1.2.2.1.8.{#SNMPINDEX}]</key>
    <snmp_community>public</snmp_community>
    <snmp_oid>1.3.6.1.2.1.2.2.1.8.{#SNMPINDEX}</snmp_oid>
    <port>11611</port>
    <value_type>3</value_type>
    <applications>
        <application>Network interfaces</application>
    </applications>
</item>
```

### PRTG Integration

```xml
<!-- PRTG custom sensor configuration -->
<prtg>
    <text>Interface Status Monitor</text>
    <result>
        <channel>Interface 1 Status</channel>
        <value>1</value>
        <unit>Custom</unit>
        <customunit>Status</customunit>
        <valueLookup>prtg.standardlookups.snmp.interfacestatus</valueLookup>
    </result>
</prtg>
```

## Advanced Scripting and Automation

### Bulk Testing Script

```bash
#!/bin/bash
# bulk_test.sh - Test multiple scenarios automatically

scenarios=("simple" "counter_wrap" "resource_limits" "error_injection")
port=11611

for scenario in "${scenarios[@]}"; do
    echo "Testing scenario: $scenario"
    
    # Start agent with scenario config
    python mock_snmp_agent.py --config "config/${scenario}.yaml" --port $port &
    agent_pid=$!
    
    # Wait for agent to start
    sleep 2
    
    # Run tests
    echo "Running SNMP tests..."
    snmpwalk -v2c -c public 127.0.0.1:$port 1.3.6.1.2.1.1 > "results/${scenario}_walk.txt"
    
    # Performance test
    echo "Running performance test..."
    time_start=$(date +%s%N)
    for i in {1..100}; do
        snmpget -v2c -c public 127.0.0.1:$port 1.3.6.1.2.1.1.1.0 >/dev/null 2>&1
    done
    time_end=$(date +%s%N)
    avg_time=$(( (time_end - time_start) / 100000000 ))
    echo "Average response time: ${avg_time}ms" > "results/${scenario}_perf.txt"
    
    # Stop agent
    kill $agent_pid
    wait $agent_pid 2>/dev/null
    
    echo "Scenario $scenario completed"
    echo "---"
done

echo "All tests completed. Results in results/ directory."
```

### Python Automation Example

```python
#!/usr/bin/env python3
# automated_testing.py

import subprocess
import time
import requests
from pysnmp.hlapi import *

class SNMPTester:
    def __init__(self, host='127.0.0.1', port=11611, community='public'):
        self.host = host
        self.port = port
        self.community = community
        self.api_base = f"http://{host}:8080"
    
    def start_agent_with_config(self, config_file):
        """Start agent with specific configuration."""
        cmd = ['python', 'mock_snmp_agent.py', 
               '--config', config_file, 
               '--port', str(self.port),
               '--rest-api', '--api-port', '8080']
        return subprocess.Popen(cmd)
    
    def snmp_get(self, oid):
        """Perform SNMP GET operation."""
        for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(self.community),
            UdpTransportTarget((self.host, self.port)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False, maxRows=1):
            
            if errorIndication:
                return None, str(errorIndication)
            elif errorStatus:
                return None, f"{errorStatus.prettyPrint()} at {errorIndex}"
            else:
                for varBind in varBinds:
                    return varBind[1], None
    
    def test_scenario(self, config_file, tests):
        """Test a complete scenario."""
        print(f"Testing scenario: {config_file}")
        
        # Start agent
        agent_proc = self.start_agent_with_config(config_file)
        time.sleep(3)  # Wait for startup
        
        results = {}
        
        try:
            # Wait for API to be ready
            for _ in range(10):
                try:
                    response = requests.get(f"{self.api_base}/health", timeout=1)
                    if response.status_code == 200:
                        break
                except:
                    time.sleep(1)
            
            # Run tests
            for test_name, oid in tests.items():
                start_time = time.time()
                value, error = self.snmp_get(oid)
                end_time = time.time()
                
                results[test_name] = {
                    'value': str(value) if value else None,
                    'error': error,
                    'response_time': (end_time - start_time) * 1000  # ms
                }
            
            # Get API metrics
            try:
                response = requests.get(f"{self.api_base}/metrics")
                if response.status_code == 200:
                    results['api_metrics'] = response.json()
            except:
                pass
        
        finally:
            # Stop agent
            agent_proc.terminate()
            agent_proc.wait()
        
        return results

def main():
    tester = SNMPTester()
    
    # Define test scenarios
    scenarios = {
        'config/simple.yaml': {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'ifNumber': '1.3.6.1.2.1.2.1.0'
        },
        'config/counter_wrap.yaml': {
            'ifInOctets1': '1.3.6.1.2.1.2.2.1.10.1',
            'ifOutOctets1': '1.3.6.1.2.1.2.2.1.16.1'
        },
        'config/error_injection.yaml': {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',  # Configured to fail
            'sysLocation': '1.3.6.1.2.1.1.6.0'  # Configured to fail
        }
    }
    
    # Run all scenarios
    all_results = {}
    for config, tests in scenarios.items():
        results = tester.test_scenario(config, tests)
        all_results[config] = results
        
        # Print summary
        print(f"\\nResults for {config}:")
        for test_name, result in results.items():
            if test_name != 'api_metrics':
                status = "OK" if result['error'] is None else "ERROR"
                print(f"  {test_name}: {status} ({result['response_time']:.1f}ms)")
    
    # Save detailed results
    import json
    with open('test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\\nDetailed results saved to test_results.json")

if __name__ == "__main__":
    main()
```

## Performance Optimization

### Agent Performance Tuning

```yaml
# config/high_performance.yaml
simulation:
  # Minimal delays for maximum throughput
  delay:
    enabled: false
  
  # No error injection
  error_injection:
    enabled: false
  
  # High resource limits
  resource_limits:
    enabled: true
    max_concurrent: 1000
    queue_size: 5000

agent:
  # Optimize for performance
  performance:
    worker_threads: 8
    connection_pool_size: 200
    response_cache_size: 1000
    
# Enable API for monitoring performance
api:
  enabled: true
  port: 8080
```

### Client-Side Optimization

```bash
# Use connection reuse for multiple requests
snmpget -v2c -c public 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 \
    1.3.6.1.2.1.1.2.0 \
    1.3.6.1.2.1.1.3.0

# Use GetBulk for table data
snmpbulkget -v2c -c public -Cn0 -Cr25 127.0.0.1:11611 1.3.6.1.2.1.2.2.1

# Optimize timeout and retries
snmpget -v2c -c public -t 1 -r 2 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

For more examples and integration patterns, see the [Advanced Testing Scenarios Guide](ADVANCED_TESTING_GUIDE.md) and [REST API Documentation](REST_API_DOCUMENTATION.md).