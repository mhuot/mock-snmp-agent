# Mock SNMP Agent - Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues when deploying and operating the Mock SNMP Agent.

## Common Issues and Solutions

### 1. Agent Startup Issues

#### Problem: Agent fails to start
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

**Common Solutions:**
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
   python mock_snmp_agent.py --port 11612
   ```

3. **Permission issues:**
   ```bash
   # For ports < 1024, use sudo or higher port
   python mock_snmp_agent.py --port 11611  # OK
   python mock_snmp_agent.py --port 161    # Requires sudo
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

#### Problem: Agent starts but doesn't respond to SNMP requests
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

2. **Firewall blocking:**
   ```bash
   # Temporarily disable firewall (Linux)
   sudo ufw disable
   # Or add rule
   sudo ufw allow 11611/udp
   ```

3. **Wrong IP binding:**
   ```bash
   # Agent might be binding to wrong interface
   python mock_snmp_agent.py --host 0.0.0.0 --port 11611
   ```

### 2. Performance Issues

#### Problem: High response latency
**Symptoms:**
- SNMP requests take >10ms consistently
- Timeouts under load
- Slow API responses

**Diagnosis:**
```bash
# Run performance test
python performance_test.py --quick

# Check system resources
top
htop
iostat 1
```

**Solutions:**
1. **System resource constraints:**
   ```bash
   # Monitor during operation
   top -p $(pgrep -f mock_snmp_agent)

   # Increase system limits if needed
   ulimit -n 65536  # File descriptors
   ```

2. **Suboptimal configuration:**
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

#### Problem: Low throughput
**Diagnosis:**
```bash
# Test sustained load
python examples/load_testing.py

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
   python mock_snmp_agent.py --processes 4
   ```

### 3. Memory Issues

#### Problem: Memory leaks
**Symptoms:**
- Memory usage grows over time
- Eventually crashes with OOM
- Slow garbage collection

**Diagnosis:**
```bash
# Monitor memory usage
ps -o pid,vsz,rss,comm -p $(pgrep -f mock_snmp_agent)

# Python memory profiling
pip install memory-profiler
python -m memory_profiler mock_snmp_agent.py
```

**Solutions:**
1. **Enable garbage collection:**
   ```python
   import gc
   gc.set_threshold(700, 10, 10)  # Tune thresholds
   gc.collect()  # Force collection
   ```

2. **Limit cache sizes:**
   ```yaml
   simulation:
     cache:
       max_size: "100MB"
       ttl: 3600
   ```

3. **Connection cleanup:**
   ```python
   # Ensure proper connection cleanup
   with SNMPClient() as client:
       response = client.get(oid)
   ```

### 4. Configuration Issues

#### Problem: Configuration not loading
**Symptoms:**
- Default values used instead of config
- Error messages about missing files
- YAML parsing errors

**Solutions:**
1. **File path issues:**
   ```bash
   # Use absolute paths
   python mock_snmp_agent.py --config /full/path/to/config.yaml

   # Check current directory
   pwd
   ls -la config/
   ```

2. **YAML syntax errors:**
   ```bash
   # Validate YAML
   python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

   # Use online YAML validator
   yamllint config.yaml
   ```

3. **Schema validation:**
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

### 5. API Issues

#### Problem: REST API not responding
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
   python mock_snmp_agent.py --rest-api --api-port 8080
   ```

2. **Port conflicts:**
   ```bash
   # Use different port
   python mock_snmp_agent.py --rest-api --api-port 8081
   ```

#### Problem: WebSocket connections failing
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
1. **Check WebSocket implementation:**
   ```python
   # Verify WebSocket manager is running
   from rest_api.websocket import WebSocketManager
   manager = WebSocketManager()
   print(f"Active connections: {len(manager.active_connections)}")
   ```

### 6. Data File Issues

#### Problem: MIB data not loading
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

### 7. Docker Issues

#### Problem: Container won't start
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

#### Problem: Cannot connect to containerized agent
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

### 8. SNMPv3 Issues

#### Problem: Authentication failures
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
1. **User configuration:**
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

2. **Time synchronization:**
   ```bash
   # SNMPv3 requires time sync
   ntpdate -s time.nist.gov
   ```

## Diagnostic Tools

### 1. Log Analysis
```bash
# Real-time log monitoring
tail -f logs/snmp-agent.log

# Search for errors
grep -i error logs/snmp-agent.log

# Analyze request patterns
awk '/SNMP request/ {print $1, $2, $8}' logs/snmp-agent.log
```

### 2. Network Debugging
```bash
# Capture SNMP traffic
tcpdump -i any port 11611 -w snmp_capture.pcap

# Analyze with Wireshark
wireshark snmp_capture.pcap

# Monitor network connections
ss -un | grep 11611
```

### 3. Performance Profiling
```bash
# CPU profiling
python -m cProfile -o profile.stats mock_snmp_agent.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"

# Memory profiling
python -m memory_profiler mock_snmp_agent.py
```

## Recovery Procedures

### 1. Service Recovery
```bash
#!/bin/bash
# recovery_script.sh

# Stop existing processes
pkill -f mock_snmp_agent

# Wait for cleanup
sleep 5

# Restart with fresh configuration
python mock_snmp_agent.py --config config/production.yaml --port 11611 &

# Verify startup
sleep 10
snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0
```

### 2. Data Recovery
```bash
# Backup current state
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# Restore from backup
cp -r data_backup_20231201_120000/ data/

# Regenerate indexes
rm -rf /tmp/snmpsim/
python mock_snmp_agent.py --rebuild-indexes
```

## Monitoring and Alerting

### 1. Health Checks
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

### 2. Log Monitoring
```bash
# Monitor for errors
tail -F logs/snmp-agent.log | grep -i --line-buffered error | \
while read line; do
    echo "ERROR DETECTED: $line"
    # Send alert
    curl -X POST "https://hooks.slack.com/..." -d "{'text':'SNMP Agent Error: $line'}"
done
```

## Contact and Escalation

### 1. Documentation Resources
- [API Documentation](REST_API_DOCUMENTATION.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Best Practices](BEST_PRACTICES_GUIDE.md)

### 2. Log Files to Include in Bug Reports
- Application logs: `logs/snmp-agent.log`
- System logs: `/var/log/syslog` or `journalctl -u snmp-agent`
- Configuration: `config/*.yaml`
- Performance data: Output from `performance_test.py`

### 3. Information to Gather
- Operating system and version
- Python version and installed packages
- Network configuration
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs. actual behavior

This troubleshooting guide covers the most common issues encountered when deploying and operating the Mock SNMP Agent. For additional support, please refer to the project documentation or create an issue with detailed diagnostic information.
