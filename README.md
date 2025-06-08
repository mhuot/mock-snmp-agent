# Mock SNMP Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

A comprehensive SNMP simulator for testing and development purposes, using the official Lextudio SNMP simulator package. This project provides realistic SNMP agent simulation with various behaviors including delays, errors, and different response patterns.

**Perfect for:**
- Network monitoring tool development and testing
- SNMP client application validation
- CI/CD pipelines requiring SNMP endpoints
- Performance testing of SNMP-based systems
- Training and educational environments

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Advanced Usage](#advanced-usage)
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

### 🎭 Simulation Behaviors
- **Slow Response Simulation**: Configurable delays (tested up to 800ms+)
- **Error Simulation**: Various SNMP error responses (authorizationError, noAccess, etc.)
- **Packet Loss Simulation**: Simulate network issues and timeouts
- **Dynamic Values**: Runtime modification of OID values through writecache
- **Agent Restart Simulation**: Easy start/stop for testing reconnection scenarios

### ⚡ Performance
- **High Throughput**: Tested at 293+ req/sec with 60ms average latency
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
   git clone <repository-url>
   cd mock-snmp-agent
   ```

2. **Build and run with Docker Compose:**
   ```bash
   # Basic version
   docker-compose up -d
   
   # Extended version with additional device data
   docker-compose --profile extended up -d snmp-simulator-extended
   ```

3. **Or build and run manually:**
   ```bash
   docker build -t mock-snmp-agent .
   docker run -p 11611:161/udp mock-snmp-agent
   ```

4. **With custom data directory:**
   ```bash
   docker run -p 11611:161/udp \
              -v $(pwd)/custom-data:/usr/local/snmpsim/data \
              mock-snmp-agent
   ```

#### Option 2: Local Python Installation 🐍

1. **Clone this repository:**
   ```bash
   git clone <repository-url>
   cd snmpsim
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
   docker-compose up -d
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
       127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```

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
```

### Manual Testing Examples

```bash
# Test all protocol versions
snmpget -v1 -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    127.0.0.1:11611 1.3.6.1.2.1.1.1.0

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

1. **"No Response" errors:**
   - Check if simulator is running: `ps aux | grep snmpsim`
   - Verify correct port: default is 11611
   - Check firewall settings

2. **"No Such Instance" errors:**
   - Verify OID exists in simulation data
   - Use correct community string
   - Check data file is properly loaded

3. **Permission denied:**
   - Don't run as root unless binding to privileged ports (<1024)

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
├── README.md                 # This file
├── CLAUDE.md                 # Claude Code development guide
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker Compose configuration
├── .dockerignore             # Docker build exclusions
├── test_prd_requirements.py  # Comprehensive test suite
├── performance_test.py       # Performance testing script
├── data/                     # Custom simulation data (optional)
└── venv/                     # Python virtual environment (local only)
```

## Performance Results

Based on testing:
- **Throughput**: 293+ requests/second
- **Latency**: ~60ms average response time
- **Protocols**: SNMPv1, v2c, v3 all working
- **Operations**: GET, GETNEXT, GETBULK, SET all functional
- **Behaviors**: Delay, error, writecache simulations working

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