# Troubleshooting Guide

## Overview

This guide covers common issues, debugging techniques, and solutions for the Mock SNMP Agent. Use this reference when encountering problems with installation, configuration, or operation.

## Common Issues

### 1. Installation and Setup Issues

#### Docker: "Unable to find image" error

**Problem:**
```bash
docker: Error response from daemon: Unable to find image 'mock-snmp-agent:latest'
```

**Solution:**
```bash
# Build the image first
docker build -t mock-snmp-agent .

# Then run
docker run -p 11611:161/udp mock-snmp-agent

# Or use Docker Compose
docker compose up -d
```

#### Python Package Installation Failures

**Problem:**
```bash
pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
```bash
# Update pip first
python -m pip install --upgrade pip

# Install in virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install with specific Python version
python3.8 -m pip install -r requirements.txt

# Clear pip cache if needed
pip cache purge
```

#### API Dependencies Missing

**Problem:**
```bash
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Install API dependencies
pip install fastapi uvicorn websockets pyyaml python-multipart

# Or install test dependencies
pip install -r requirements-test.txt

# Verify installation
python -c "import fastapi, uvicorn, websockets; print('OK')"
```

### 2. SNMP Connection Issues

#### "No Response" errors

**Problem:**
```bash
snmpget: Timeout (No Response from localhost:11611)
```

**Troubleshooting Steps:**

1. **Check if simulator is running:**
   ```bash
   # For local installation
   ps aux | grep mock_snmp_agent
   
   # For Docker
   docker ps
   docker logs <container_id>
   ```

2. **Verify correct port:**
   ```bash
   # Default port is 11611
   netstat -ln | grep 11611
   
   # Test with telnet
   telnet 127.0.0.1 11611
   ```

3. **Check firewall settings:**
   ```bash
   # macOS
   sudo pfctl -s rules | grep 11611
   
   # Linux (ufw)
   sudo ufw status
   
   # Linux (iptables)
   sudo iptables -L | grep 11611
   ```

4. **For Docker, ensure port mapping is correct:**
   ```bash
   # Correct UDP port mapping
   docker run -p 11611:161/udp mock-snmp-agent
   
   # Check port mapping
   docker port <container_name>
   ```

#### Connection Refused Errors

**Problem:**
```bash
snmpget: connect: Connection refused
```

**Solutions:**

1. **Check binding address:**
   ```bash
   # Agent should bind to correct interface
   python mock_snmp_agent.py --port 11611 --verbose
   
   # For external access, bind to all interfaces
   python mock_snmp_agent.py --host 0.0.0.0 --port 11611
   ```

2. **Verify no port conflicts:**
   ```bash
   # Check what's using the port
   lsof -i :11611
   
   # Use alternative port if needed
   python mock_snmp_agent.py --port 11612
   ```

### 3. SNMP Protocol Issues

#### "No Such Instance" errors

**Problem:**
```bash
SNMPv2-SMI::org = No Such Instance currently exists at this OID
```

**Troubleshooting:**

1. **Verify OID exists in simulation data:**
   ```bash
   # List available OIDs
   snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1
   
   # Check specific OID
   snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```
   
   For complete SNMP command syntax, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md).

2. **Use correct community string:**
   ```bash
   # Try different communities
   snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   snmpget -v2c -c variation/delay 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```
   
   For community string variations, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#community-string-variations).

3. **Check data file is properly loaded:**
   ```bash
   # Start with verbose output
   python mock_snmp_agent.py --verbose --port 11611
   
   # Check data directory
   ls -la data/
   ```

#### SNMPv3 Authentication Failures

**Problem:**
```bash
snmpget: Authentication failure (incorrect password, community or key)
```

**Solutions:**

1. **Verify SNMPv3 credentials:**
   ```bash
   # Use correct default credentials
   snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
       -n public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   
   # Test step by step
   # 1. No auth/priv
   snmpget -v3 -l noAuthNoPriv -u simulator 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   
   # 2. Auth only
   snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas \
       127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   
   # 3. Auth + Priv
   snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
       127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```
   
   For complete SNMPv3 command examples, see [SNMP Commands Reference](SNMP_COMMANDS_REFERENCE.md#snmpv3-commands).

2. **Check engine ID discovery:**
   ```bash
   # Force engine discovery
   snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
       -e 0x$(python -c "import hashlib; print(hashlib.md5(b'simulator').hexdigest()[:16])") \
       127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```

### 4. Performance Issues

#### Slow Response Times

**Problem:**
Responses taking longer than expected.

**Troubleshooting:**

1. **Check configuration for delays:**
   ```bash
   # Verify no artificial delays are configured
   grep -r "delay" config/
   
   # Check current configuration via API
   curl http://localhost:8080/config
   ```

2. **Monitor system resources:**
   ```bash
   # Check CPU/memory usage
   top -p $(pgrep -f mock_snmp_agent)
   
   # Monitor with API
   curl http://localhost:8080/metrics
   ```

3. **Test with minimal configuration:**
   ```yaml
   # config/minimal.yaml
   simulation:
     delay:
       enabled: false
     error_injection:
       enabled: false
   
   agent:
     endpoint: "127.0.0.1:11611"
   ```

#### High Memory Usage

**Problem:**
Agent consuming excessive memory.

**Solutions:**

1. **Check for memory leaks:**
   ```bash
   # Monitor memory over time
   while true; do
     ps -o pid,vsz,rss,comm -p $(pgrep -f mock_snmp_agent)
     sleep 10
   done
   ```

2. **Reduce simulation complexity:**
   ```yaml
   # Reduce bulk operation sizes
   simulation:
     bulk_operations:
       enabled: false
     
     resource_limits:
       enabled: true
       max_concurrent: 50  # Reduce from default
   ```

### 5. REST API Issues

#### API Server Won't Start

**Problem:**
```bash
Error: Address already in use
```

**Solutions:**

1. **Check port availability:**
   ```bash
   # Check if port 8080 is in use
   lsof -i :8080
   
   # Use different port
   python mock_snmp_agent.py --rest-api --api-port 8081
   ```

2. **Kill conflicting processes:**
   ```bash
   # Find and kill process using port
   sudo kill $(lsof -t -i:8080)
   
   # Or use alternative approach
   pkill -f "uvicorn.*8080"
   ```

#### WebSocket Connection Failures

**Problem:**
```bash
WebSocket connection failed: Connection refused
```

**Solutions:**

1. **Verify API server is running:**
   ```bash
   # Check API health
   curl http://localhost:8080/health
   
   # Check WebSocket endpoint
   curl -H "Upgrade: websocket" -H "Connection: Upgrade" \
        http://localhost:8080/ws/metrics
   ```

2. **Test WebSocket connection:**
   ```python
   import asyncio
   import websockets
   
   async def test_websocket():
       try:
           uri = "ws://localhost:8080/ws/metrics"
           async with websockets.connect(uri) as websocket:
               message = await websocket.recv()
               print(f"Received: {message}")
       except Exception as e:
           print(f"WebSocket error: {e}")
   
   asyncio.run(test_websocket())
   ```

### 6. Configuration Issues

#### Invalid YAML Syntax

**Problem:**
```bash
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Use online validator or
   python -c "import yaml; yaml.safe_load(open('config/test.yaml'))"
   ```

2. **Common YAML mistakes:**
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

#### Configuration Not Applied

**Problem:**
Configuration changes not taking effect.

**Solutions:**

1. **Restart agent after config changes:**
   ```bash
   # Stop agent
   pkill -f mock_snmp_agent
   
   # Start with new config
   python mock_snmp_agent.py --config config/updated.yaml
   ```

2. **Use dynamic configuration updates:**
   ```bash
   # Update via API (if enabled)
   curl -X PUT http://localhost:8080/config \
     -H "Content-Type: application/json" \
     -d '{"simulation": {"delay": {"enabled": true, "global_delay": 200}}}'
   ```

## Debugging Techniques

### 1. Enable Verbose Logging

```bash
# Start with maximum verbosity
python mock_snmp_agent.py --verbose --port 11611

# Enable debug output for underlying SNMP library
python mock_snmp_agent.py --debug --port 11611

# Use logging configuration
export PYTHONPATH=.
export SNMP_DEBUG=all
python mock_snmp_agent.py --port 11611
```

### 2. Network-Level Debugging

```bash
# Capture SNMP traffic with tcpdump
sudo tcpdump -i lo -p udp port 11611 -v

# Use Wireshark for detailed analysis
# Filter: udp.port == 11611

# Test with snmptranslate for OID validation
snmptranslate -On 1.3.6.1.2.1.1.1.0
snmptranslate -Of 1.3.6.1.2.1.1.1.0
```

### 3. API Debugging

```bash
# Enable FastAPI debug mode
export FASTAPI_ENV=development
python -m rest_api.server --port 8080 --debug

# Test API endpoints individually
curl -v http://localhost:8080/health
curl -v http://localhost:8080/metrics
curl -v http://localhost:8080/config

# Monitor API logs
tail -f api.log
```

### 4. Container Debugging

```bash
# Run container in interactive mode
docker run -it -p 11611:161/udp mock-snmp-agent /bin/bash

# Check container logs
docker logs <container_id> -f

# Execute commands in running container
docker exec -it <container_id> /bin/bash

# Check container networking
docker inspect <container_id> | grep IPAddress
```

## Diagnostic Tools

### Built-in Diagnostics

```bash
# Run built-in system check
python mock_snmp_agent.py --check-system

# Validate configuration
python mock_snmp_agent.py --config config/test.yaml --validate

# Test SNMP functionality
python test_basic.py

# Run performance test
python performance_test.py
```

### External Tools

```bash
# SNMP tools
snmpwalk -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1
snmpstatus -v2c -c public 127.0.0.1:11611

# Network tools
nc -u 127.0.0.1 11611  # Test UDP connectivity
nmap -sU -p 11611 127.0.0.1  # UDP port scan

# System tools
htop  # Monitor system resources
ss -ulpn | grep 11611  # Check UDP sockets
```

## Log File Analysis

### Common Log Messages

**Normal Operation:**
```
INFO: SNMP agent started on 127.0.0.1:11611
INFO: REST API server started on 0.0.0.0:8080
INFO: Configuration loaded from config/simple.yaml
```

**Warning Messages:**
```
WARNING: High request rate detected: 500 req/sec
WARNING: Memory usage above 80%: 85%
WARNING: Configuration file not found, using defaults
```

**Error Messages:**
```
ERROR: Failed to bind to port 11611: Address already in use
ERROR: Invalid OID in configuration: not.valid.oid
ERROR: SNMPv3 authentication failed for user: baduser
```

### Log File Locations

```bash
# Default log locations
./mock_snmp_agent.log      # Main agent log
./api.log                  # REST API log
./debug.log                # Debug output

# Configure custom log location
python mock_snmp_agent.py --log-file /var/log/snmp/agent.log
```

## Getting Help

### Collect Diagnostic Information

Before reporting issues, collect this information:

```bash
#!/bin/bash
# diagnostic_info.sh

echo "=== System Information ==="
uname -a
python --version
pip --version

echo "=== Docker Information ==="
docker --version
docker compose version

echo "=== Python Packages ==="
pip list | grep -E "(snmpsim|fastapi|uvicorn|websockets)"

echo "=== Network Configuration ==="
netstat -ln | grep 11611
ss -ulpn | grep 11611

echo "=== Process Information ==="
ps aux | grep -E "(mock_snmp|snmpsim)"

echo "=== Log Files ==="
ls -la *.log 2>/dev/null || echo "No log files found"

echo "=== Configuration ==="
find . -name "*.yaml" -o -name "*.yml" | head -5

echo "=== Test Results ==="
timeout 10 snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0 2>&1
```

### Resources

- **GitHub Issues**: Report bugs and feature requests
- **API Documentation**: [REST_API_DOCUMENTATION.md](REST_API_DOCUMENTATION.md)
- **Configuration Guide**: [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- **Testing Guide**: [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)
- **Advanced Usage**: [ADVANCED_USAGE_GUIDE.md](ADVANCED_USAGE_GUIDE.md)

### Frequently Asked Questions

**Q: Can I run multiple agents on the same machine?**
A: Yes, use different ports: `--port 11611`, `--port 11612`, etc.

**Q: How do I simulate a specific device type?**
A: Use device-specific data files or create custom .snmprec files. See [ADVANCED_USAGE_GUIDE.md](ADVANCED_USAGE_GUIDE.md).

**Q: Can I modify OID values at runtime?**
A: Yes, use SET operations with `variation/writecache` community or the REST API.

**Q: How do I test SNMPv3 with custom credentials?**
A: Create a custom configuration file with SNMPv3 users. See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

**Q: Why are my counter wraps not working?**
A: Check acceleration settings and ensure you're monitoring the correct OIDs. Use the REST API to verify configuration.

**Q: How do I integrate with monitoring tools?**
A: See monitoring tool examples in [ADVANCED_USAGE_GUIDE.md](ADVANCED_USAGE_GUIDE.md).

If your issue isn't covered here, please create a GitHub issue with diagnostic information and detailed error messages.