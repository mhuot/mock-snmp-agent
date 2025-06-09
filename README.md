# Mock SNMP Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## 💡 What is this?

The Simple Network Management Protocol (SNMP) is widely used for monitoring network devices. However, effectively testing SNMP monitoring solutions often requires access to a diverse array of physical devices, which can be complex, costly, and difficult to manage.

The Mock SNMP Agent provides a **comprehensive, flexible, and robust SNMP simulator** designed to address this challenge. It allows developers and testers to **accurately simulate various network device behaviors, including critical errors, performance bottlenecks, and counter wraps**, without the need for physical hardware. Built on the official Lextudio SNMP simulator, this agent enhances testing capabilities with advanced configuration management, a powerful REST API, and real-time monitoring.

## ✨ Key Features & Why It's Unique

This simulator is **perfect for rigorously testing all 8 major SNMP monitoring challenges**, including:

- **Counter Wrap Validation**: 32-bit and 64-bit counter wrap simulation
- **Performance Testing**: Resource constraint and bulk operation testing  
- **Network Condition Simulation**: Delay, packet loss, and timeout scenarios
- **SNMP Monitoring Testing**: Validate handling of various SNMP agent behaviors
- **CI/CD Integration**: Docker-based testing infrastructure
- **Development Validation**: Comprehensive SNMP client application testing
- **Training Environments**: Educational and demonstration purposes

### Core Capabilities:
- **Multi-protocol**: SNMPv1, SNMPv2c, and SNMPv3 support (GET, GETNEXT, GETBULK, SET)
- **REST API & Real-time Monitoring**: Full HTTP API for control, WebSocket for live metrics/logs
- **Advanced Simulation Behaviors**: Configurable delays, error injection, dynamic OID values, agent restarts
- **Comprehensive Testing Infrastructure**: 78+ automated API tests, WebSocket integration, scenario testing, CI/CD ready
- **High Performance**: Tested at 240+ req/sec with ~70ms latency, scalable

## 🎯 Addressing the 8 Major SNMP Monitoring Challenges

The Mock SNMP Agent is specifically designed to simulate and validate solutions against common, critical SNMP monitoring issues:

1. **Counter Wraps (32-bit & 64-bit)**: Testing accurate handling of counter overflows
2. **Resource Exhaustion**: Simulating high CPU, memory, and concurrent request limits on devices
3. **Network Conditions**: Validating behavior under packet loss, high latency, and timeouts
4. **SNMP Agent Restarts/Unavailability**: Testing monitoring system resilience to agent downtime
5. **Error Responses**: Generating various SNMP error PDU types (e.g., `noSuchName`, `authorizationError`, `noAccess`)
6. **Bulk Operation Performance**: Stress testing GetBulk operations with large tables and high repetitions  
7. **Dynamic Value Changes**: Simulating real-time data fluctuations and OID modifications
8. **Authentication & Privacy Failures**: Validating secure SNMPv3 implementation under incorrect credentials

For detailed scenarios and how to test each of these challenges, see the [Advanced Testing Scenarios Guide](ADVANCED_TESTING_GUIDE.md).

## 🚀 Quick Start

The fastest way to get started is with Docker Compose.

### Prerequisites

1. **Python 3.8+** with pip (for local use or test dependencies)
2. **net-snmp tools** (for testing SNMP communication):
   ```bash
   # macOS
   brew install net-snmp
   # Ubuntu/Debian  
   sudo apt-get install snmp snmp-mibs-downloader
   # RHEL/CentOS
   sudo yum install net-snmp-utils
   ```

### Docker (Recommended) 🐳

1. **Clone this repository:**
   ```bash
   git clone https://github.com/mhuot/mock-snmp-agent.git
   cd mock-snmp-agent
   ```

2. **Start the agent with Docker Compose:**
   ```bash
   docker compose up -d
   ```

### Basic Usage

After starting the agent, you can test basic SNMP functionality:

```bash
# Test SNMPv2c GET
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Test SNMPv3 with authentication and privacy
snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
    -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```

For detailed installation options (local Python, extended Docker configs) and more advanced usage examples, see the Deeper Dives & Guides section below.

## 📚 Deeper Dives & Guides

Explore the full capabilities and documentation:

### **API Integration & Real-time Monitoring**
- **[REST API Documentation](REST_API_DOCUMENTATION.md)** - Comprehensive API reference and examples
- **[WebSocket Real-time Monitoring](REST_API_DOCUMENTATION.md#websocket-endpoints)** - Live metrics and activity streaming

### **Configuration & Advanced Testing**  
- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - Detailed YAML examples and configuration reference
- **[Advanced Testing Scenarios Guide](ADVANCED_TESTING_GUIDE.md)** - In-depth guide on testing the 8 major SNMP monitoring challenges
- **[Advanced Usage Guide](ADVANCED_USAGE_GUIDE.md)** - Community strings, SNMPv3 configuration, monitoring tool integration

### **Testing & Validation**
- **[API Testing Guide](API_TESTING_GUIDE.md)** - How to run the automated API test suite and interpret results
- **[Performance Results](PERFORMANCE_RESULTS.md)** - Detailed performance benchmarks and validation

### **Development & Deployment**
- **[Project Structure](PROJECT_STRUCTURE.md)** - A map of the codebase and component organization
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and debugging tips
- **[Advanced Deployments](ADVANCED_DEPLOYMENTS.md)** - Scaling and enterprise integration options

### **Examples & Integration**
- **[Examples Directory](examples/README.md)** - Usage examples and demonstrations
- **[React UI Project Plan](REACT_UI_PROJECT_PLAN.md)** - Web interface implementation roadmap

## ✅ Why Choose Mock SNMP Agent?

Mock SNMP Agent offers unparalleled value for network monitoring and SNMP client development:

- **Unmatched Simulation Depth**: Go beyond basic OID responses to simulate real-world issues like counter wraps, resource constraints, and network errors
- **Comprehensive Test Coverage**: Over 78 automated API tests ensure reliability, and scenarios validate critical monitoring challenges
- **Integrated API & Real-time Control**: Seamlessly control and monitor your simulations via REST API and WebSockets for dynamic testing
- **CI/CD Ready**: Dockerized environment and robust testing infrastructure enable easy integration into automated pipelines

## 🤝 Contributing & Support

- **Issues**: Report bugs and feature requests via [GitHub issues](https://github.com/mhuot/mock-snmp-agent/issues)
- **Contributing**: For development setup and contributing guidelines, see [CLAUDE.md](CLAUDE.md)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

This project uses the official snmpsim-lextudio package which is licensed under BSD.

## 🔗 Related Projects

- [snmpsim-lextudio](https://github.com/lextudio/snmpsim): Official SNMP simulator
- [snmpsim-data](https://github.com/lextudio/snmpsim-data): Additional device simulation data
- [snmpsim-control-plane](https://github.com/lextudio/snmpsim-control-plane): Enterprise management platform
- [pysnmp-lextudio](https://github.com/lextudio/pysnmp): SNMP library
- [net-snmp](http://www.net-snmp.org/): SNMP client tools