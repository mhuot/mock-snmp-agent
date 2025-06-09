# Mock SNMP Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

A comprehensive SNMP simulator for testing and development purposes, featuring advanced simulation behaviors for comprehensive SNMP monitoring validation. Built on the official Lextudio SNMP simulator with enhanced configuration management and testing capabilities.

**Perfect for:**
- **SNMP Monitoring Testing**: Test all 8 major SNMP monitoring issues
- **Counter Wrap Validation**: 32-bit and 64-bit counter wrap simulation
- **Performance Testing**: Resource constraint and bulk operation testing  
- **Network Condition Simulation**: Delay, packet loss, and timeout scenarios
- **CI/CD Integration**: Docker-based testing infrastructure
- **Development Validation**: SNMP client application testing
- **Training Environments**: Educational and demonstration purposes

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Configuration System](#-configuration-system)
- [Advanced Testing Scenarios](#-advanced-testing-scenarios)
- [Docker Testing](#-docker-testing)
- [Testing](#testing)
- [Data Files](#data-files)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Performance Results](#performance-results)
- [Advanced Deployments](#advanced-deployments)
- [Related Projects](#related-projects)

## ✨ Features

### 🔌 Core SNMP Support
- **Multi-protocol**: SNMPv1, SNMPv2c, and SNMPv3 support
- **All Operations**: GET, GETNEXT, GETBULK, and SET operations
- **Authentication**: SNMPv3 with MD5/SHA authentication and DES/AES privacy
- **Community-based**: Multiple community strings for different simulation scenarios

### 🎭 Advanced Simulation Behaviors
- **Slow Response Simulation**: Configurable delays (tested up to 800ms+)
- **Error Simulation**: Various SNMP error responses (authorizationError, noAccess, etc.)
- **Packet Loss Simulation**: Simulate network issues and timeouts
- **Dynamic Values**: Runtime modification of OID values through writecache
- **Agent Restart Simulation**: Easy start/stop for testing reconnection scenarios
- **Counter Wrap Testing**: 32-bit and 64-bit counter wrap simulation with acceleration
- **Resource Constraints**: CPU and memory limit simulation for realistic device behavior
- **Bulk Operation Testing**: Large table simulation and GetBulk stress testing
- **Configuration-Driven**: YAML/JSON configuration for complex testing scenarios

### ⚡ Performance
- **High Throughput**: Tested at 240+ req/sec with ~70ms average latency
- **Concurrent Handling**: Multi-threaded request processing
- **Scalable**: Supports multiple simultaneous SNMP clients

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** with pip
2. **net-snmp tools** for testing:
   ```bash
   # macOS
   brew install net-snmp
   
   # Ubuntu/Debian
   sudo apt-get install snmp snmp-mibs-downloader
   
   # RHEL/CentOS
   sudo yum install net-snmp-utils
   ```

### 📦 Installation

Choose one of the following deployment methods:

#### Option 1: Docker (Recommended) 🐳

1. **Clone this repository:**
   ```bash
   git clone https://github.com/mhuot/mock-snmp-agent.git
   cd mock-snmp-agent
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t mock-snmp-agent .
   ```

3. **Run with Docker Compose (recommended):**
   ```bash
   # Basic version
   docker compose up -d
   
   # Extended version with additional device data
   docker compose --profile extended up -d snmp-simulator-extended
   ```

4. **Or run manually:**
   ```bash
   docker run -p 11611:161/udp mock-snmp-agent
   ```

5. **With custom data directory:**
   ```bash
   docker run -p 11611:161/udp \
              -v $(pwd)/custom-data:/usr/local/snmpsim/data \
              mock-snmp-agent
   ```

#### Option 2: Local Python Installation 🐍

1. **Clone this repository:**
   ```bash
   git clone https://github.com/mhuot/mock-snmp-agent.git
   cd mock-snmp-agent
   ```

2. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the official snmpsim package:**
   ```bash
   pip install snmpsim-lextudio==1.1.1
   
   # Optional: Install additional device simulation data
   pip install snmpsim-data
   ```

### Basic Usage

#### Docker Usage

1. **Start with Docker Compose:**
   ```bash
   docker compose up -d
   ```

2. **Or run the container directly:**
   ```bash
   docker run -p 11611:161/udp mock-snmp-agent
   ```

#### Local Installation Usage

1. **Start the SNMP simulator:**
   ```bash
   snmpsim-command-responder \
       --data-dir=./data \
       --agent-udpv4-endpoint=127.0.0.1:11611 \
       --quiet
   ```

2. **Test basic functionality:**
   ```bash
   # SNMPv2c GET
   snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   
   # SNMPv1 GET
   snmpget -v1 -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   
   # GETNEXT
   snmpgetnext -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1
   
   # GETBULK
   snmpbulkget -v2c -c public -Cn0 -Cr3 127.0.0.1:11611 1.3.6.1.2.1.1
   
   # SNMPv3 with authentication and privacy
   snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
       -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```

## 🔧 Configuration System

The Mock SNMP Agent supports advanced configuration through YAML/JSON files, enabling complex testing scenarios without code changes.

### Configuration File Usage

Create a YAML configuration file to define simulation behaviors:

```bash
# Run with configuration file
python mock_snmp_agent.py --config config/comprehensive.yaml --port 11611
```

### Example Configurations

#### Basic Delay Configuration
```yaml
# config/simple.yaml
simulation:
  delay:
    global_delay: 500      # 500ms delay for all responses
    deviation: 100         # ±100ms random variation
  
  drop_rate: 5             # 5% packet drop rate
  packet_loss: 2           # 2% packet loss simulation
```

#### Counter Wrap Testing
```yaml
# config/counter_wrap_test.yaml
simulation:
  counter_wrap:
    enabled: true
    counters:
      "1.3.6.1.2.1.2.2.1.10": # ifInOctets
        acceleration: 1000   # 1000x speed for testing
        wrap_type: "32bit"   # 32-bit counter
      "1.3.6.1.2.1.2.2.1.16": # ifOutOctets  
        acceleration: 1000
        wrap_type: "32bit"
```

#### Resource Constraint Testing
```yaml
# config/resource_limits.yaml
simulation:
  resource_limits:
    enabled: true
    cpu_limit: 80          # Simulate 80% CPU usage
    memory_limit: 90       # Simulate 90% memory usage
    max_concurrent: 50     # Max 50 concurrent requests
```

### CLI Quick Options

For rapid testing, use CLI flags without configuration files:

```bash
# Quick delay testing
python mock_snmp_agent.py --delay 1000 --drop-rate 10

# Counter wrap testing
python mock_snmp_agent.py --config config/counter_wrap_test.yaml

# Resource constraint testing  
python mock_snmp_agent.py --config config/resource_limits.yaml

# Restart simulation
python mock_snmp_agent.py --restart-interval 300
```

## 🧪 Advanced Testing Scenarios

The Mock SNMP Agent enables comprehensive testing of the 8 major SNMP monitoring issues:

### 1. Counter Wrap Testing

Test 32-bit counter wrap scenarios critical for network monitoring:

```bash
# Start agent with counter wrap acceleration
python mock_snmp_agent.py --config config/counter_wrap_test.yaml

# Monitor counter progression
watch -n 1 'snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.2.2.1.10.1'

# Observe wrap from 4294967295 to 0
```

**Key Testing Points:**
- Counter wrap detection at 2^32-1 (4,294,967,295)
- Multiple wraps between polling intervals
- Relationship preservation between related counters
- Acceleration factors for different interface speeds

### 2. Resource Constraint Testing

Simulate device resource exhaustion scenarios:

```bash
# Test under CPU constraints
python mock_snmp_agent.py --config config/resource_limits.yaml

# Generate high request load
for i in {1..100}; do
  snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0 &
done
```

**Resource Limits Tested:**
- CPU utilization above 80%
- Memory usage above 90%  
- Concurrent request limits (50+ simultaneous)
- Request queue overflow conditions

### 3. Bulk Operation Testing

Test large SNMP responses and GetBulk operations:

```bash
# Test large GetBulk operations
snmpbulkget -v2c -c public -Cn0 -Cr50 localhost:11611 1.3.6.1.2.1.2.2.1

# Test with bulk operation configuration
python mock_snmp_agent.py --config config/bulk_test.yaml
```

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

## 🐳 Docker Testing

Comprehensive Docker testing infrastructure for isolated testing environments.

### Docker Test Scenarios

Run all test scenarios with Docker:

```bash
# Run comprehensive Docker tests
docker compose -f docker-compose.test.yml up

# Individual test scenarios
docker compose -f docker-compose.test.yml up delay-test
docker compose -f docker-compose.test.yml up counter-wrap-test
docker compose -f docker-compose.test.yml up resource-limit-test
docker compose -f docker-compose.test.yml up bulk-operation-test
docker compose -f docker-compose.test.yml up comprehensive-test
```

### Quick Docker Test

For rapid validation without long build times:

```bash
# Run quick Docker functionality test
python quick_docker_test.py
```

This creates a minimal Docker image and tests:
- Basic SNMP functionality
- Delay behavior
- Container networking
- Port mapping

### Docker Test Infrastructure

The testing setup includes:
- **5 test scenarios** covering all major simulation behaviors
- **Automated testing scripts** with result validation
- **Performance benchmarking** within containers
- **Network isolation** for consistent testing

## Advanced Usage

### Community Strings and Simulation Data

The simulator supports multiple community strings for different simulation scenarios:

- **`public`**: Standard MIB-II data with typical system information
- **`variation/delay`**: Responses with configurable delays
- **`variation/error`**: Various SNMP error responses
- **`variation/writecache`**: Writeable OIDs for SET operations
- **`recorded/linux-full-walk`**: Real Linux system SNMP walk data
- **`recorded/winxp-full-walk`**: Real Windows XP system SNMP walk data

### Delay Simulation

Test slow network or processing scenarios:

```bash
# This will respond after ~800ms delay
snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1

# Time the response
time snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1
```

### Error Simulation

Test error handling in your SNMP applications:

```bash
# Trigger authorization error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.1.1

# Trigger no-access error
snmpget -v2c -c variation/error 127.0.0.1:11611 1.3.6.1.2.1.2.2.1.6.1
```

### SET Operations

Test writeable OIDs:

```bash
# Set a value
snmpset -v2c -c variation/writecache 127.0.0.1:11611 \
    1.3.6.1.2.1.1.1.0 s "Modified system description"

# Read it back
snmpget -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

### SNMPv3 Configuration

The simulator automatically configures SNMPv3 with these defaults:
- **Engine ID**: Auto-generated
- **User**: `simulator`
- **Auth Protocol**: MD5
- **Auth Key**: `auctoritas`
- **Privacy Protocol**: DES
- **Privacy Key**: `privatus`

## Testing

### Run Comprehensive Tests

```bash
# Run all PRD requirement tests
python3 test_prd_requirements.py

# Run performance tests
python3 performance_test.py

# Run pytest test suite
pytest tests/ -v

# Run Docker integration tests
python3 tests/docker_integration_test.py

# Quick Docker validation
python3 quick_docker_test.py
```

### Manual Testing Examples

```bash
# Test all protocol versions
snmpget -v1 -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test different operations
snmpgetnext -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1
snmpbulkget -v2c -c public -Cn0 -Cr5 127.0.0.1:11611 1.3.6.1.2.1.1
snmpset -v2c -c variation/writecache 127.0.0.1:11611 1.3.6.1.2.1.1.1.0 s "Test"
```

## Data Files

The simulator uses the built-in data files from the snmpsim-lextudio package, including:

- **Standard communities**: `public`, various recorded datasets
- **Variation modules**: `delay`, `error`, `writecache`, `notification`
- **Real device data**: Linux and Windows system walks

## Troubleshooting

### Common Issues

1. **Docker: "Unable to find image" error:**
   ```bash
   # Build the image first
   docker build -t mock-snmp-agent .
   # Then run
   docker run -p 11611:161/udp mock-snmp-agent
   ```

2. **"No Response" errors:**
   - Check if simulator is running: `ps aux | grep snmpsim` or `docker ps`
   - Verify correct port: default is 11611
   - Check firewall settings
   - For Docker: ensure port mapping is correct (`-p 11611:161/udp`)

3. **"No Such Instance" errors:**
   - Verify OID exists in simulation data
   - Use correct community string
   - Check data file is properly loaded

4. **Permission denied:**
   - Don't run as root unless binding to privileged ports (<1024)
   - For Docker: no special permissions needed

### Debugging

Enable debug output:
```bash
snmpsim-command-responder \
    --debug all \
    --data-dir=./data \
    --agent-udpv4-endpoint=127.0.0.1:11611
```

## Project Structure

```
mock-snmp-agent/
├── README.md                      # This documentation
├── CLAUDE.md                      # Claude Code development guide
├── mock_snmp_agent.py             # Enhanced main module with CLI options
├── config.py                      # Configuration management system
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation script
├── behaviors/                     # Advanced simulation behaviors
│   ├── __init__.py
│   ├── counter_wrap.py            # Counter wrap simulation
│   ├── resource_limits.py         # CPU/memory constraint simulation
│   └── bulk_operations.py         # Large table and GetBulk testing
├── config/                        # Configuration examples
│   ├── simple.yaml                # Basic delay configuration
│   ├── advanced.yaml              # All features demonstration
│   ├── comprehensive.yaml         # Testing all 8 SNMP issues
│   ├── counter_wrap_test.yaml     # Counter wrap focus
│   ├── resource_limits.yaml       # Resource constraint testing
│   └── bulk_test.yaml             # Bulk operation testing
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── test_basic_functionality.py # Core functionality tests
│   ├── test_performance.py        # Performance validation
│   └── docker_integration_test.py # Docker testing automation
├── docker-compose.test.yml        # Docker test scenarios
├── docker-compose.yml             # Basic Docker setup
├── Dockerfile                     # Standard container
├── Dockerfile.enhanced            # Production-ready container
├── quick_docker_test.py           # Fast Docker validation
├── test_prd_requirements.py       # PRD compliance testing
├── performance_test.py            # Performance benchmarking
├── test_basic.py                  # Basic functionality tests
├── data/                          # Simulation data files
├── .dockerignore                  # Docker build optimizations
└── venv/                          # Python virtual environment (local)
```

## Performance Results

### Core Performance
- **Throughput**: 240+ requests/second baseline
- **Latency**: ~70ms average response time (normal mode)
- **Protocols**: SNMPv1, v2c, v3 all validated
- **Operations**: GET, GETNEXT, GETBULK, SET all functional

### Advanced Features Performance
- **Counter Wrap Simulation**: 1000x acceleration factor tested
- **Resource Constraints**: Handles 100+ concurrent requests under limits
- **Bulk Operations**: Successfully processes GetBulk with 200+ repetitions
- **Configuration Loading**: Sub-second YAML/JSON configuration parsing
- **Docker Performance**: Minimal overhead in containerized environments

### Simulation Behaviors Validated
- ✅ **Delay Simulation**: Configurable delays 100ms-5000ms
- ✅ **Packet Loss**: 1-20% loss rates tested
- ✅ **Counter Wrap**: 32-bit and 64-bit wrap detection
- ✅ **Resource Limits**: CPU 80%+ and Memory 90%+ constraints
- ✅ **Bulk Testing**: Large table simulation (1000+ entries)
- ✅ **Error Injection**: Various SNMP error responses
- ✅ **Dynamic Values**: Runtime OID modification via writecache

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

This project uses the official snmpsim-lextudio package which is licensed under BSD.

## Support

- **Issues**: Report bugs and feature requests via GitHub issues
- **Testing**: Run `python3 test_prd_requirements.py` to verify functionality
- **Documentation**: Check CLAUDE.md for development setup

## Advanced Deployments

### Additional Device Data

For more realistic device simulations, install the optional data package:

```bash
pip install snmpsim-data
setup-snmpsim-data ./data
```

This provides pre-recorded SNMP walks from various real-world devices (routers, switches, UPS systems, etc.).

### Enterprise Control Plane

For large-scale deployments with multiple simulator instances, consider the [snmpsim-control-plane](https://github.com/lextudio/snmpsim-control-plane):

- **REST API**: Remote simulator management
- **Virtual Labs**: Organize simulators into logical groups  
- **Metrics Collection**: Performance monitoring and reporting
- **Distributed Management**: Scale across multiple servers

Example use cases:
- Network testing labs with dozens of simulated devices
- CI/CD pipelines requiring automated SNMP testing
- Training environments with isolated simulator groups

## Related Projects

- [snmpsim-lextudio](https://github.com/lextudio/snmpsim): Official SNMP simulator
- [snmpsim-data](https://github.com/lextudio/snmpsim-data): Additional device simulation data
- [snmpsim-control-plane](https://github.com/lextudio/snmpsim-control-plane): Enterprise management platform
- [pysnmp-lextudio](https://github.com/lextudio/pysnmp): SNMP library
- [net-snmp](http://www.net-snmp.org/): SNMP client tools