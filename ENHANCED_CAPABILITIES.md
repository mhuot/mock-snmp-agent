# Enhanced Mock SNMP Agent Capabilities

## Overview

The Mock SNMP Agent has been significantly enhanced with advanced simulation capabilities that address your specific requirements for **AgentX-style slow responses**, **SNMPv3 context handling**, and **endOfMibView response injection**.

## New Capabilities

### 🔧 AgentX-Style Response Simulation

**Status: ✅ FULLY IMPLEMENTED**

The agent now simulates AgentX (SNMP Extension Agent) behavior patterns commonly found in enterprise network devices where different subsystems are handled by separate subagents.

#### Features:
- **Subagent Registration Delays**: Simulates the delay when subagents register with the master agent
- **OID-Specific Delays**: Different response times based on MIB subsystem (interfaces, routing, hardware)
- **Connection Failures**: Simulates subagent disconnection and reconnection scenarios  
- **Master Agent Timeouts**: Occasional timeout conditions during subagent communication

#### Configuration Example:
```yaml
simulation:
  agentx_simulation:
    enabled: true
    registration_delays: true
    registration_delay_ms: 1500
    subagent_delays:
      "1.3.6.1.2.1.2": 200       # Interface agent - medium delay
      "1.3.6.1.2.1.25": 800      # Host resources - slow
      "1.3.6.1.4.1": 1200        # Enterprise MIBs - very slow
```

#### Testing:
```bash
# Test AgentX-style delays
python mock_snmp_agent.py --config config/enhanced_simulation.yaml

# Interface queries (medium delay ~200ms)
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.10.1

# Host resources (slow delay ~800ms)  
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.25.1.1.0

# Enterprise MIBs (very slow ~1200ms)
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.4.1.9.2.1.1.0
```

### 🔐 SNMPv3 Context Handling

**Status: ✅ FULLY IMPLEMENTED** 

The agent now supports SNMPv3 contexts, allowing different OID trees and values based on the context name in requests. This is essential for testing VRF-aware devices and multi-tenant systems.

#### Features:
- **Multiple Context Support**: VRF instances, bridge domains, firewall zones
- **Context-Based Access Control**: Different users authorized for different contexts
- **Context-Specific OID Values**: Same OID returns different values per context
- **Restricted OID Patterns**: Block access to certain MIB areas per context

#### Common Use Cases:
1. **VRF Testing**: Different routing instances with separate MIB views
2. **Bridge Domains**: VLAN-specific contexts in switches
3. **Firewall Zones**: Security zone isolation
4. **Multi-Tenant**: Customer-specific contexts

#### Configuration Example:
```yaml
simulation:
  snmpv3_contexts:
    enabled: true
    contexts:
      - name: "vrf-customer-a"
        description: "Customer A VRF instance"
        oid_mappings:
          "1.3.6.1.2.1.1.1.0": "Customer A Router Instance"
          "1.3.6.1.2.1.1.5.0": "customer-a-pe-01"
        allowed_users: ["customer-a", "operator"]
```

#### Testing:
```bash
# Default context
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# VRF context (requires context-aware SNMP client)
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n "vrf-customer-a" 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### 🚫 MIB Boundary Response Injection

**Status: ✅ FULLY IMPLEMENTED**

The agent can now inject proper SNMP exception responses including `endOfMibView`, `noSuchObject`, and `noSuchInstance` - critical for testing SNMP walk operations and error handling.

#### Features:
- **endOfMibView Responses**: Proper MIB walk termination at defined boundaries
- **noSuchObject Simulation**: Missing MIB objects that exist in specification but not implementation
- **noSuchInstance Handling**: Sparse table simulation with missing table entries
- **Configurable Boundaries**: Custom MIB view limits and missing object patterns

#### Configuration Example:
```yaml
simulation:
  mib_boundaries:
    enabled: true
    end_of_mib_view:
      mib_view_boundaries:
        "1.3.6.1.2.1.1": "1.3.6.1.2.1.1.9.0"      # System group ends here
    no_such_object:
      missing_objects:
        - "1.3.6.1.2.1.1.8.0"     # System services (unimplemented)
    no_such_instance:
      sparse_tables:
        "1.3.6.1.2.1.2.2.1": [3, 5, 7]  # Missing interface indices
```

#### Testing:
```bash
# Walk that encounters endOfMibView
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1

# Request missing object (noSuchObject)
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.8.0

# Request missing table instance (noSuchInstance)  
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.3
```

## Integration Examples

### Testing prometheus-snmp-exporter with Enhanced Features

```yaml
# snmp.yml for prometheus-snmp-exporter
modules:
  mock_device_enhanced:
    version: 2
    community: public
    walk:
      - 1.3.6.1.2.1.1     # Test endOfMibView handling
      - 1.3.6.1.2.1.2.2   # Test sparse tables
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

  mock_device_context:
    version: 3
    auth:
      username: simulator
      password: auctoritas
      protocol: MD5
    priv:
      password: privatus
      protocol: DES
    context_name: "vrf-customer-a"  # Test context handling
    walk:
      - 1.3.6.1.2.1.1
```

### Network Monitoring Tool Testing

```bash
# Test suite for SNMP monitoring tools
#!/bin/bash

echo "Testing AgentX-style delays..."
time snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.25.1.1.0  # Should be slow

echo "Testing context handling..."
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n "vrf-management" 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

echo "Testing MIB boundaries..."
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1 | grep -c "No Such Instance"
```

## REST API Enhancements

The enhanced capabilities include extended REST API endpoints:

```bash
# Get AgentX subagent status
curl http://localhost:8080/api/agentx/status

# List available SNMPv3 contexts
curl http://localhost:8080/api/contexts/

# Get MIB boundary statistics
curl http://localhost:8080/api/boundaries/stats
```

## Performance Impact

| Feature | Performance Impact | Use Cases |
|---------|-------------------|-----------|
| AgentX Simulation | Medium (controlled delays) | Testing subagent-based devices |
| SNMPv3 Contexts | Low (context lookup) | VRF testing, multi-tenant |
| MIB Boundaries | Very Low (pattern matching) | Walk termination, error handling |

## Configuration Templates

### Enterprise Router Simulation
```yaml
# Simulates Cisco/Juniper router with AgentX subagents
simulation:
  agentx_simulation:
    enabled: true
    subagent_delays:
      "1.3.6.1.2.1.2": 150       # Fast interface queries
      "1.3.6.1.2.1.4": 200       # Medium IP table queries
      "1.3.6.1.4.1.9": 800       # Slow Cisco enterprise queries
```

### Data Center Switch Simulation
```yaml
# Simulates switch with bridge domains and sparse interfaces
simulation:
  snmpv3_contexts:
    enabled: true
    contexts:
      - name: "bridge-domain-100"
      - name: "bridge-domain-200"
  mib_boundaries:
    no_such_instance:
      sparse_tables:
        "1.3.6.1.2.1.2.2.1": [5, 7, 11, 13]  # Missing switch ports
```

### Firewall/Security Device Simulation
```yaml
# Simulates firewall with security contexts and restricted MIBs
simulation:
  snmpv3_contexts:
    contexts:
      - name: "firewall-zone-dmz"
        restricted_oids: ["1.3.6.1.4.1"]  # Block enterprise MIBs
  mib_boundaries:
    no_such_object:
      missing_object_patterns:
        - "1.3.6.1.2.1.25"  # Block host resources for security
```

## Testing Checklist

### ✅ AgentX-Style Response Testing
- [ ] Verify different delays by MIB subsystem
- [ ] Test subagent registration timeouts
- [ ] Validate connection failure handling
- [ ] Measure realistic delay patterns

### ✅ SNMPv3 Context Testing  
- [ ] Test multiple context access
- [ ] Verify context-based access control
- [ ] Validate context-specific OID values
- [ ] Test restricted OID patterns

### ✅ MIB Boundary Testing
- [ ] Verify endOfMibView at walk boundaries
- [ ] Test noSuchObject for missing MIB objects
- [ ] Validate noSuchInstance for sparse tables
- [ ] Test SNMP walk termination

### ✅ Integration Testing
- [ ] Test with prometheus-snmp-exporter
- [ ] Validate with various SNMP monitoring tools
- [ ] Test SNMP library error handling
- [ ] Performance test under load

## Migration from Basic to Enhanced

Existing configurations remain compatible. To enable enhanced features:

1. **Add enhanced behaviors to existing config:**
```yaml
# Add to existing simulation block
simulation:
  # ... existing config ...
  agentx_simulation:
    enabled: true
  snmpv3_contexts:
    enabled: true
  mib_boundaries:
    enabled: true
```

2. **Use enhanced configuration template:**
```bash
# Start with enhanced capabilities
python mock_snmp_agent.py --config config/enhanced_simulation.yaml
```

3. **Enable via REST API:**
```bash
# Enable at runtime
curl -X PUT http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"simulation": {"agentx_simulation": {"enabled": true}}}'
```

## Summary

The Mock SNMP Agent now provides comprehensive advanced simulation capabilities that directly address your requirements:

✅ **AgentX-style slow responses** - Full implementation with configurable subagent delays  
✅ **SNMPv3 context handling** - Complete context support with access control  
✅ **endOfMibView response injection** - Comprehensive MIB boundary simulation  

These enhancements make the Mock SNMP Agent suitable for testing complex enterprise network monitoring scenarios, including VRF-aware devices, multi-tenant systems, and realistic AgentX-based network equipment.

The implementation maintains backward compatibility while providing powerful new testing capabilities for advanced SNMP monitoring system validation.