# PRD Implementation Plan for Mock SNMP Agent

## Current State Analysis

### Already Implemented ✅
1. **SNMP Protocol Support**
   - SNMPv1, v2c, and v3 support via snmpsim
   - GET, GETNEXT, GETBULK operations
   - Basic community string support
   - Custom MIB definitions via .snmprec files

2. **Basic Infrastructure**
   - Python wrapper around snmpsim-lextudio
   - Command-line interface with basic options (host, port, data-dir)
   - Docker support
   - Test suite structure
   - Example scripts

### Missing from PRD ❌
1. **Simulation Behaviors**
   - Slow responses (configurable delays)
   - Intermittent responses (random drop percentage)
   - Packet loss simulation
   - Agent restart simulation
   - Dynamic MIB changes at runtime

2. **Configuration Management**
   - Configuration file support (YAML/JSON)
   - API for runtime configuration changes
   - Override specific MIB values via configuration

3. **Logging and Metrics**
   - Request/response logging
   - Metrics collection (counts, latencies, error rates)
   - Export capabilities for logs/metrics

4. **Enhanced Features**
   - Explicit SET operation support and examples
   - More predefined MIB sets
   - Better documentation of advanced features

## Implementation Strategy

### Phase 1: Configuration System (Priority: High)
**Timeline: 3-4 days**

#### Goals
- Add YAML/JSON configuration file support
- Create configuration schema and validation
- Enable dynamic .snmprec generation based on config

#### Tasks
1. Create `config.py` module for configuration handling
2. Add `--config` CLI option to mock_snmp_agent.py
3. Define configuration schema
4. Implement .snmprec file generation
5. Add configuration examples

#### Configuration Schema
```yaml
# config/example.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 100        # ms
      deviation: 50            # ms
      oid_specific:
        "1.3.6.1.2.1.1.1.0": 
          delay: 2000
          deviation: 1000
    
    drops:
      enabled: true
      rate: 10                 # percent
      
    packet_loss:
      enabled: true
      rate: 5                  # percent
      
    restart:
      enabled: false
      interval: 300            # seconds
      
  logging:
    enabled: true
    level: info
    file: "logs/snmp-agent.log"
    format: "json"
    
  metrics:
    enabled: true
    export:
      format: "prometheus"     # json, csv, prometheus
      interval: 60             # seconds
      file: "metrics/snmp-metrics.json"
```

### Phase 2: Simulation Behaviors (Priority: High)
**Timeline: 4-5 days**

#### Goals
- Implement all simulation behaviors using snmpsim's variation modules
- Add CLI options for quick behavior configuration
- Create behavior generator modules

#### Tasks
1. **Delay Behavior**
   - Create `behaviors/delay.py` to generate delay tags
   - Add `--delay` and `--delay-deviation` CLI options
   - Use snmpsim's built-in delay variation module

2. **Drop/Intermittent Responses**
   - Create `behaviors/drops.py` to generate error tags
   - Add `--drop-rate` CLI option
   - Use error variation module with probability

3. **Packet Loss**
   - Implement using delay module (wait=99999)
   - Add `--packet-loss` CLI option

4. **Agent Restart**
   - Create `behaviors/restart.py` for subprocess management
   - Add `--restart-interval` CLI option
   - Implement graceful restart with logging

5. **Dynamic MIB Changes**
   - Document writecache variation module usage
   - Add examples for runtime value modification
   - Create helper scripts for value updates

### Phase 3: Logging and Metrics (Priority: Medium)
**Timeline: 3-4 days**

#### Goals
- Comprehensive request/response logging
- Real-time metrics collection
- Multiple export formats

#### Tasks
1. **Logging Implementation**
   - Create `logging/logger.py` wrapper
   - Capture request details (timestamp, source, OIDs)
   - Log responses and errors
   - Support multiple formats (JSON, CSV, text)

2. **Metrics Collection**
   - Create `metrics/collector.py`
   - Track: request count, response times, error rates
   - Calculate: average latency, requests/second
   - Implement sliding window for real-time stats

3. **Export Functionality**
   - Support Prometheus exposition format
   - JSON metrics export
   - CSV export for analysis
   - Periodic automatic export

### Phase 4: Enhanced Features (Priority: Low)
**Timeline: 2-3 days**

#### Tasks
1. **SET Operation Examples**
   - Create comprehensive SET examples
   - Document writeable OIDs
   - Add persistence options

2. **Predefined MIB Sets**
   - Create `data/mibs/` directory
   - Add device-specific MIB sets:
     - cisco-router.snmprec
     - linux-server.snmprec
     - windows-server.snmprec
     - network-printer.snmprec
     - ups-device.snmprec

3. **MIB Conversion Tools**
   - Add `--convert-mib` option
   - Wrapper for mib2rec functionality
   - Batch MIB conversion support

## Technical Implementation Details

### Using snmpsim's Variation Modules

1. **Delay Module**
   ```
   OID|TAG:delay|value=X,wait=Y,deviation=Z
   1.3.6.1.2.1.1.1.0|4:delay|value=Test System,wait=1000,deviation=500
   ```

2. **Error Module**
   ```
   OID|TAG:error|op=X,value=Y
   1.3.6.1.2.1.1.2.0|6:error|op=set,value=authorizationError
   ```

3. **Writecache Module**
   ```
   OID|TAG:writecache|value=X,file=Y
   1.3.6.1.2.1.1.4.0|4:writecache|value=Initial,file=/tmp/cache.db
   ```

### CLI Enhancements

```bash
# Current
mock-snmp-agent --port 1161

# Enhanced
mock-snmp-agent --port 1161 --config config.yaml
mock-snmp-agent --port 1161 --delay 100 --delay-deviation 50
mock-snmp-agent --port 1161 --drop-rate 10 --packet-loss 5
mock-snmp-agent --port 1161 --restart-interval 300
mock-snmp-agent --port 1161 --log-file agent.log --metrics-export prometheus
```

## File Structure After Implementation

```
mock-snmp-agent/
├── mock_snmp_agent.py      # Enhanced main module
├── config.py               # Configuration handler
├── behaviors/              # Behavior generators
│   ├── __init__.py
│   ├── delay.py           # Delay behavior generator
│   ├── drops.py           # Drop/error generator
│   ├── restart.py         # Restart manager
│   └── dynamic.py         # Dynamic value handler
├── logging/               
│   ├── __init__.py
│   ├── logger.py          # Request/response logger
│   └── formatters.py      # Log formatters
├── metrics/               
│   ├── __init__.py
│   ├── collector.py       # Metrics collector
│   └── exporters.py       # Export handlers
├── utils/                 
│   ├── __init__.py
│   ├── snmprec.py        # .snmprec file utilities
│   └── validation.py      # Config validation
├── data/
│   ├── public.snmprec     # Default data
│   ├── examples/          # Example .snmprec files
│   │   ├── delay.snmprec
│   │   ├── errors.snmprec
│   │   └── dynamic.snmprec
│   └── mibs/             # Predefined MIB sets
│       ├── cisco-router.snmprec
│       ├── linux-server.snmprec
│       └── windows-server.snmprec
├── config/               # Configuration examples
│   ├── simple.yaml
│   ├── advanced.yaml
│   ├── testing.yaml
│   └── schema.json
├── examples/             # Usage examples
│   ├── config_example.py
│   ├── slow_responses.py
│   ├── packet_loss.py
│   ├── dynamic_values.py
│   └── full_simulation.py
├── tests/
│   ├── test_config.py
│   ├── test_behaviors.py
│   ├── test_logging.py
│   └── test_metrics.py
└── docs/
    ├── configuration.md
    ├── behaviors.md
    ├── logging.md
    └── advanced.md
```

## Testing Strategy

### Unit Tests
- Configuration parsing and validation
- Behavior generation logic
- Metrics calculation
- Log formatting

### Integration Tests
- End-to-end simulation scenarios
- Configuration file loading
- Behavior activation
- Metrics export

### Performance Tests
- Verify 1000 req/sec capability
- Measure impact of logging/metrics
- Test under various behavior scenarios

## Success Criteria

1. **Functionality**
   - All PRD simulation behaviors working
   - Configuration file support complete
   - Logging and metrics operational

2. **Performance**
   - Maintains 1000 req/sec capability
   - Average latency under 10ms (normal mode)
   - Minimal memory footprint

3. **Usability**
   - Simple configuration
   - Clear documentation
   - Helpful error messages

## Implementation Order

1. **Week 1**: Configuration System
   - config.py module
   - CLI integration
   - Basic tests

2. **Week 2**: Simulation Behaviors
   - Delay implementation
   - Drop/error behaviors
   - Restart capability

3. **Week 3**: Logging & Metrics
   - Request logging
   - Metrics collection
   - Export functionality

4. **Week 4**: Polish & Documentation
   - Enhanced examples
   - Comprehensive tests
   - Documentation

This plan leverages snmpsim's existing capabilities while adding the configuration and management layer that makes it easy to use for testing scenarios as specified in the PRD.