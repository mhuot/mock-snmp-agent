# Mock SNMP Agent - Troubleshooting Guide

## Overview

This comprehensive guide covers common issues, debugging techniques, and solutions for the Mock SNMP Agent. Use this reference when encountering problems with installation, configuration, or operation.

## Quick Diagnostic Commands

Before diving into specific issues, run these quick diagnostic commands:

```bash
# Check if agent is running
ps aux | grep mock_snmp_agent
netstat -ln | grep 11611

# Test basic SNMP connectivity
snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0

# Check system resources
top -p $(pgrep -f mock_snmp_agent)

# Test API (if enabled)
curl http://localhost:8080/health
```

## Installation and Setup Issues

### Docker: "Unable to find image" Error

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

### Python Package Installation Failures

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

# Install API dependencies
pip install fastapi uvicorn websockets pyyaml python-multipart

# Or install test dependencies
pip install -r requirements-test.txt

# Verify installation
python -c "import fastapi, uvicorn, websockets; print('OK')"
```

### Agent Startup Issues

#### Agent Fails to Start

**Symptoms:**
- Command exits immediately
- No log output
- Port not listening

**Diagnosis Steps:**
```bash
# Check Python environment
python --version
pip list | grep -E "(snmpsim|fastapi|uvicorn)"

# Verify configuration syntax
python -c "import yaml; yaml.safe_load(open('config/simple.yaml'))"

# Check port availability
netstat -an | grep 11611
lsof -i :11611
```

**Solutions:**

1. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

2. **Port already in use:**
   ```bash
   # Find and kill process using port
   sudo lsof -ti:11611 | xargs kill -9
   # Or use different port
   python src/mock_snmp_agent.py --port 11612
   ```

3. **Permission issues:**
   ```bash
   # For ports < 1024, use sudo or higher port
   python src/mock_snmp_agent.py --port 11611  # OK
   python src/mock_snmp_agent.py --port 161    # Requires sudo
   ```

4. **Invalid configuration:**
   ```bash
   # Validate YAML syntax
   python -c "
   import yaml
   try:
       yaml.safe_load(open('config/your_config.yaml'))
       print('Configuration valid')
   except yaml.YAMLError as e:
       print(f'YAML Error: {e}')
   "
   ```

## SNMP Connection Issues

### "No Response" Errors

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
   sudo ufw allow 11611/udp

   # Linux (iptables)
   sudo iptables -L | grep 11611

   # Temporarily disable firewall for testing
   sudo ufw disable
   ```

4. **For Docker, ensure port mapping is correct:**
   ```bash
   # Correct UDP port mapping
   docker run -p 11611:161/udp mock-snmp-agent

   # Check port mapping
   docker port <container_name>
   ```

### Connection Refused Errors

**Problem:**
```bash
snmpget: connect: Connection refused
```

**Solutions:**

1. **Check binding address:**
   ```bash
   # Agent should bind to correct interface
   python src/mock_snmp_agent.py --port 11611 --verbose

   # For external access, bind to all interfaces
   python src/mock_snmp_agent.py --host 0.0.0.0 --port 11611
   ```

2. **Verify no port conflicts:**
   ```bash
   # Check what's using the port
   lsof -i :11611

   # Use alternative port if needed
   python src/mock_snmp_agent.py --port 11612
   ```

### Agent Starts But Doesn't Respond

**Diagnosis:**
```bash
# Test basic connectivity
snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0

# Check if agent is listening
netstat -an | grep 11611

# Verbose SNMP client debugging
snmpget -v2c -c public -d localhost:11611 1.3.6.1.2.1.1.1.0
```

**Solutions:**

1. **Wrong community string:**
   ```bash
   # Check configuration for correct community
   grep -r "community" config/
   # Try default community
   snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0
   ```

2. **Wrong IP binding:**
   ```bash
   # Agent might be binding to wrong interface
   python src/mock_snmp_agent.py --host 0.0.0.0 --port 11611
   ```

## SNMP Protocol Issues

### "No Such Instance" Errors

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
   python src/mock_snmp_agent.py --verbose --port 11611

   # Check data directory
   ls -la data/
   ```

### SNMPv3 Authentication Issues

#### Authentication Failures

**Problem:**
```bash
snmpget: Authentication failure (incorrect password, community or key)
```

**Symptoms:**
- "Authentication failure" errors
- "Unknown user name" messages
- Timeout with SNMPv3

**Diagnosis:**
```bash
# Test SNMPv3 with verbose output
snmpget -v3 -u simulator -a MD5 -A auctoritas -x DES -X privatus \
        -l authPriv -d localhost:11611 1.3.6.1.2.1.1.1.0
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

2. **User configuration:**
   ```yaml
   # Ensure correct SNMPv3 user setup
   snmp:
     v3_users:
       - username: simulator
         auth_protocol: MD5
         auth_key: auctoritas
         priv_protocol: DES
         priv_key: privatus
   ```

3. **Time synchronization:**
   ```bash
   # SNMPv3 requires time sync
   ntpdate -s time.nist.gov
   ```

4. **Check engine ID discovery:**
   ```bash
   # Force engine discovery
   snmpget -v3 -l authPriv -u simulator -a MD5 -A auctoritas -x DES -X privatus \
       -e 0x$(python -c "import hashlib; print(hashlib.md5(b'simulator').hexdigest()[:16])") \
       127.0.0.1:11611 1.3.6.1.2.1.1.1.0
   ```

## Performance Issues

### High Response Latency

**Symptoms:**
- SNMP requests take >10ms consistently
- Timeouts under load
- Slow API responses

**Diagnosis:**
```bash
# Run performance test
python scripts/testing/performance_test.py --quick

# Check system resources
top
htop
iostat 1

# Monitor during operation
top -p $(pgrep -f mock_snmp_agent)
```

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

**Solutions:**

1. **System resource constraints:**
   ```bash
   # Increase system limits if needed
   ulimit -n 65536  # File descriptors
   ```

2. **Optimize configuration:**
   ```yaml
   # Optimize for performance
   simulation:
     behaviors:
       delay:
         enabled: false    # Disable artificial delays
     logging:
       level: error        # Reduce logging overhead
   ```

3. **Network issues:**
   ```bash
   # Test local network latency
   ping localhost
   # Check UDP buffer sizes
   sysctl net.core.rmem_default net.core.wmem_default
   ```

### Low Throughput

**Diagnosis:**
```bash
# Test sustained load
python docs/examples/load_testing.py

# Monitor network utilization
iftop
nethogs
```

**Solutions:**

1. **Increase worker threads:**
   ```python
   # In mock_snmp_agent.py configuration
   max_workers = 100  # Increase from default
   ```

2. **Optimize Python GIL:**
   ```bash
   # Use multiple processes instead of threads
   python src/mock_snmp_agent.py --processes 4
   ```

### High Memory Usage

**Problem:**
Agent consuming excessive memory.

**Symptoms:**
- Memory usage grows over time
- Eventually crashes with OOM
- Slow garbage collection

**Diagnosis:**
```bash
# Check for memory leaks
while true; do
  ps -o pid,vsz,rss,comm -p $(pgrep -f mock_snmp_agent)
  sleep 10
done

# Python memory profiling
pip install memory-profiler
python -m memory_profiler src/mock_snmp_agent.py

# Monitor memory usage
ps -o pid,vsz,rss,comm -p $(pgrep -f mock_snmp_agent)
```

**Solutions:**

1. **Reduce simulation complexity:**
   ```yaml
   # Reduce bulk operation sizes
   simulation:
     bulk_operations:
       enabled: false

     resource_limits:
       enabled: true
       max_concurrent: 50  # Reduce from default
   ```

2. **Enable garbage collection:**
   ```python
   import gc
   gc.set_threshold(700, 10, 10)  # Tune thresholds
   gc.collect()  # Force collection
   ```

3. **Limit cache sizes:**
   ```yaml
   simulation:
     cache:
       max_size: "100MB"
       ttl: 3600
   ```

4. **Connection cleanup:**
   ```python
   # Ensure proper connection cleanup
   with SNMPClient() as client:
       response = client.get(oid)
   ```

## REST API Issues

### API Server Won't Start

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
   python src/mock_snmp_agent.py --rest-api --api-port 8081
   ```

2. **Kill conflicting processes:**
   ```bash
   # Find and kill process using port
   sudo kill $(lsof -t -i:8080)

   # Or use alternative approach
   pkill -f "uvicorn.*8080"
   ```

### API Not Responding

**Diagnosis:**
```bash
# Test API endpoint
curl -v http://localhost:8080/health

# Check if API server started
netstat -an | grep 8080
```

**Solutions:**

1. **API not enabled:**
   ```bash
   # Start with API enabled
   python src/mock_snmp_agent.py --rest-api --api-port 8080
   ```

2. **Port conflicts:**
   ```bash
   # Use different port
   python src/mock_snmp_agent.py --rest-api --api-port 8081
   ```

### WebSocket Connection Failures

**Problem:**
```bash
WebSocket connection failed: Connection refused
```

**Diagnosis:**
```bash
# Test WebSocket
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     --header "Sec-WebSocket-Version: 13" \
     http://localhost:8080/ws/metrics
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

3. **Check WebSocket implementation:**
   ```python
   # Verify WebSocket manager is running
   from src.rest_api.websocket import ConnectionManager
   manager = ConnectionManager()
   print(f"Active connections: {len(manager.active_connections)}")
   ```

## Configuration Issues

### Invalid YAML Syntax

**Problem:**
```bash
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Use online validator or
   python -c "import yaml; yaml.safe_load(open('config/test.yaml'))"

   # Use yamllint if available
   yamllint config.yaml
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

### Configuration Not Loading

**Problem:**
Configuration changes not taking effect.

**Symptoms:**
- Default values used instead of config
- Error messages about missing files
- YAML parsing errors

**Solutions:**

1. **File path issues:**
   ```bash
   # Use absolute paths
   python src/mock_snmp_agent.py --config /full/path/to/config.yaml

   # Check current directory
   pwd
   ls -la config/
   ```

2. **Restart agent after config changes:**
   ```bash
   # Stop agent
   pkill -f mock_snmp_agent

   # Start with new config
   python src/mock_snmp_agent.py --config config/updated.yaml
   ```

3. **Use dynamic configuration updates:**
   ```bash
   # Update via API (if enabled)
   curl -X PUT http://localhost:8080/config \
     -H "Content-Type: application/json" \
     -d '{"simulation": {"delay": {"enabled": true, "global_delay": 200}}}'
   ```

4. **Schema validation:**
   ```python
   # Custom validation script
   def validate_config(config_file):
       with open(config_file) as f:
           config = yaml.safe_load(f)

       required_keys = ['simulation', 'logging']
       for key in required_keys:
           if key not in config:
               raise ValueError(f"Missing required key: {key}")
   ```

## Data File Issues

### MIB Data Not Loading

**Symptoms:**
- "No such object" errors
- Empty SNMP walks
- Missing OIDs

**Diagnosis:**
```bash
# Check data files
ls -la data/
file data/*.snmprec

# Validate .snmprec format
head -n 10 data/public.snmprec
```

**Solutions:**

1. **Invalid .snmprec format:**
   ```bash
   # Correct format: OID|TYPE|VALUE
   echo "1.3.6.1.2.1.1.1.0|4|Test System" > data/test.snmprec
   ```

2. **File permissions:**
   ```bash
   chmod 644 data/*.snmprec
   ```

3. **Encoding issues:**
   ```bash
   # Ensure UTF-8 encoding
   file -i data/public.snmprec
   iconv -f ISO-8859-1 -t UTF-8 data/public.snmprec > data/public_utf8.snmprec
   ```

## Docker Issues

### Container Won't Start

**Diagnosis:**
```bash
# Check container logs
docker logs mock-snmp-agent

# Test container locally
docker run -it --rm mock-snmp-agent:latest bash
```

**Solutions:**

1. **Build issues:**
   ```bash
   # Rebuild with no cache
   docker build --no-cache -t mock-snmp-agent .

   # Check Dockerfile syntax
   docker build --dry-run .
   ```

2. **Port mapping:**
   ```bash
   # Correct port mapping
   docker run -p 11611:11611/udp -p 8080:8080 mock-snmp-agent
   ```

3. **Volume mounting:**
   ```bash
   # Mount configuration
   docker run -v $(pwd)/config:/app/config mock-snmp-agent
   ```

### Cannot Connect to Containerized Agent

**Solutions:**

1. **Network issues:**
   ```bash
   # Test from host
   snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0

   # Test from another container
   docker run --network container:mock-snmp-agent alpine ping localhost
   ```

2. **Firewall/networking:**
   ```bash
   # Check Docker networking
   docker network ls
   docker inspect bridge
   ```

## Debugging Techniques

### Enable Verbose Logging

```bash
# Start with maximum verbosity
python src/mock_snmp_agent.py --verbose --port 11611

# Enable debug output for underlying SNMP library
python src/mock_snmp_agent.py --debug --port 11611

# Use logging configuration
export PYTHONPATH=.
export SNMP_DEBUG=all
python src/mock_snmp_agent.py --port 11611
```

### Network-Level Debugging

```bash
# Capture SNMP traffic with tcpdump
sudo tcpdump -i lo -p udp port 11611 -v

# Use Wireshark for detailed analysis
# Filter: udp.port == 11611

# Test with snmptranslate for OID validation
snmptranslate -On 1.3.6.1.2.1.1.1.0
snmptranslate -Of 1.3.6.1.2.1.1.1.0

# Monitor network connections
ss -un | grep 11611
```

### API Debugging

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

### Container Debugging

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

### Performance Profiling

```bash
# CPU profiling
python -m cProfile -o profile.stats src/mock_snmp_agent.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"

# Memory profiling
python -m memory_profiler src/mock_snmp_agent.py
```

## Diagnostic Tools

### Built-in Diagnostics

```bash
# Run built-in system check
python src/mock_snmp_agent.py --check-system

# Validate configuration
python src/mock_snmp_agent.py --config config/test.yaml --validate

# Test SNMP functionality
python scripts/testing/test_prd_requirements.py --basic

# Run performance test
python scripts/testing/performance_test.py
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

### Log Analysis

```bash
# Real-time log monitoring
tail -f logs/snmp-agent.log

# Search for errors
grep -i error logs/snmp-agent.log

# Analyze request patterns
awk '/SNMP request/ {print $1, $2, $8}' logs/snmp-agent.log
```

## Recovery Procedures

### Service Recovery

```bash
#!/bin/bash
# recovery_script.sh

# Stop existing processes
pkill -f mock_snmp_agent

# Wait for cleanup
sleep 5

# Restart with fresh configuration
python src/mock_snmp_agent.py --config config/production.yaml --port 11611 &

# Verify startup
sleep 10
snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0
```

### Data Recovery

```bash
# Backup current state
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# Restore from backup
cp -r data_backup_20231201_120000/ data/

# Regenerate indexes
rm -rf /tmp/snmpsim/
python src/mock_snmp_agent.py --rebuild-indexes
```

## Monitoring and Health Checks

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

# Test SNMP response
if snmpget -v2c -c public -t 5 localhost:11611 1.3.6.1.2.1.1.1.0 >/dev/null 2>&1; then
    echo "SNMP: OK"
else
    echo "SNMP: FAIL"
    exit 1
fi

# Test API response
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "API: OK"
else
    echo "API: FAIL"
    exit 1
fi
```

### Log Monitoring

```bash
# Monitor for errors
tail -F logs/snmp-agent.log | grep -i --line-buffered error | \
while read line; do
    echo "ERROR DETECTED: $line"
    # Send alert
    curl -X POST "https://hooks.slack.com/..." -d "{'text':'SNMP Agent Error: $line'}"
done
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
python src/mock_snmp_agent.py --log-file /var/log/snmp/agent.log
```

## Collect Diagnostic Information

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

## Resources and Documentation

- **GitHub Issues**: Report bugs and feature requests
- **API Documentation**: [REST_API_DOCUMENTATION.md](../api/REST_API_DOCUMENTATION.md)
- **Configuration Guide**: [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- **Testing Guide**: [API_TESTING_GUIDE.md](../api/API_TESTING_GUIDE.md)
- **Advanced Usage**: [ADVANCED_USAGE_GUIDE.md](ADVANCED_USAGE_GUIDE.md)
- **SNMP Commands Reference**: [SNMP_COMMANDS_REFERENCE.md](SNMP_COMMANDS_REFERENCE.md)

## Frequently Asked Questions

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

## Contact and Support

### Information to Include in Bug Reports

- Operating system and version
- Python version and installed packages (`pip list`)
- Network configuration
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs. actual behavior
- Output from diagnostic script above

### Log Files to Include

- Application logs: `logs/snmp-agent.log`
- System logs: `/var/log/syslog` or `journalctl -u snmp-agent`
- Configuration: `config/*.yaml`
- Performance data: Output from `scripts/testing/performance_test.py`

If your issue isn't covered here, please create a GitHub issue with diagnostic information and detailed error messages.
