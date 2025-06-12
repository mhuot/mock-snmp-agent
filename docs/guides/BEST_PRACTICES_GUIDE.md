# Mock SNMP Agent - Best Practices Guide

## Overview

This guide provides best practices for deploying, configuring, and using the Mock SNMP Agent effectively in production and testing environments.

## Configuration Best Practices

### 1. Environment-Specific Configuration

**Development Environment:**
```yaml
# config/development.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 50      # Low latency for fast iteration
      deviation: 25
    drops:
      enabled: false        # Disable drops for consistent testing
  logging:
    level: debug
    format: json
  metrics:
    enabled: true
    export_interval: 30
```

**Testing Environment:**
```yaml
# config/testing.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 100
      deviation: 50
    drops:
      enabled: true
      rate: 5              # Light packet loss simulation
    counter_wrap:
      enabled: true
      acceleration_factor: 100  # Faster wrap testing
  logging:
    level: info
    format: json
  metrics:
    enabled: true
```

**Production Testing:**
```yaml
# config/production.yaml
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 200     # Realistic network latency
      deviation: 100
    drops:
      enabled: true
      rate: 2               # Conservative packet loss
    resource_limits:
      enabled: true
      cpu_limit: 80
      memory_limit: 85
  logging:
    level: warn
    format: structured
```

### 2. Security Configuration

**SNMPv3 Security Setup:**
```yaml
# config/secure.yaml
snmp:
  version: v3
  security:
    users:
      - username: "test_user"
        auth_protocol: "SHA"
        auth_key: "strong_auth_key_12345"
        priv_protocol: "AES"
        priv_key: "strong_priv_key_67890"
    engine_id: "custom_engine_id"
```

**Community String Management:**
```yaml
snmp:
  communities:
    read_only: ["public", "monitoring"]
    read_write: ["private"]  # Use with caution
```

### 3. Performance Optimization

**High-Performance Configuration:**
```yaml
simulation:
  performance:
    max_concurrent_requests: 200
    response_buffer_size: 8192
    connection_pool_size: 50
  behaviors:
    delay:
      enabled: false        # Disable for maximum throughput
  logging:
    level: error            # Minimal logging overhead
    async: true
```

**Memory Optimization:**
```yaml
simulation:
  memory:
    max_cache_size: "100MB"
    cache_ttl: 3600
    garbage_collection: "aggressive"
```

## Deployment Patterns

### 1. Docker Deployment

**Single Agent Container:**
```dockerfile
# Dockerfile.simple
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 11611 8080
CMD ["python", "mock_snmp_agent.py", "--rest-api", "--config", "config/production.yaml"]
```

**Multi-Agent Orchestration:**
```yaml
# docker-compose.agents.yml
version: '3.8'
services:
  snmp-agent-1:
    build: .
    ports:
      - "11611:11611"
      - "8080:8080"
    environment:
      - AGENT_ID=agent-001
      - DEVICE_TYPE=router
    volumes:
      - ./config/router.yaml:/app/config/config.yaml

  snmp-agent-2:
    build: .
    ports:
      - "11612:11611"
      - "8081:8080"
    environment:
      - AGENT_ID=agent-002
      - DEVICE_TYPE=switch
    volumes:
      - ./config/switch.yaml:/app/config/config.yaml
```

### 2. Kubernetes Deployment

**Agent Deployment:**
```yaml
# k8s/snmp-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mock-snmp-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mock-snmp-agent
  template:
    metadata:
      labels:
        app: mock-snmp-agent
    spec:
      containers:
      - name: snmp-agent
        image: mock-snmp-agent:latest
        ports:
        - containerPort: 11611
          name: snmp
          protocol: UDP
        - containerPort: 8080
          name: api
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

**Service Configuration:**
```yaml
# k8s/snmp-agent-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mock-snmp-agent-service
spec:
  selector:
    app: mock-snmp-agent
  ports:
  - name: snmp
    port: 11611
    targetPort: 11611
    protocol: UDP
  - name: api
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Testing Strategies

### 1. Unit Testing

**Configuration Testing:**
```python
# tests/test_config_validation.py
def test_config_validation():
    config = load_config("config/testing.yaml")
    assert config['simulation']['behaviors']['delay']['enabled'] is True
    assert config['simulation']['behaviors']['delay']['global_delay'] > 0
```

**Behavior Testing:**
```python
# tests/test_simulation_behaviors.py
def test_delay_behavior():
    agent = MockSNMPAgent(config="config/delay_test.yaml")
    start_time = time.time()
    response = agent.get("1.3.6.1.2.1.1.1.0")
    response_time = time.time() - start_time
    assert response_time >= 0.1  # Expected delay
```

### 2. Integration Testing

**Load Testing Pattern:**
```python
# docs/examples/load_test_pattern.py
def run_load_test():
    """Structured load testing approach"""
    scenarios = [
        {"requests": 100, "workers": 10, "name": "light"},
        {"requests": 500, "workers": 50, "name": "medium"},
        {"requests": 1000, "workers": 100, "name": "heavy"}
    ]

    for scenario in scenarios:
        print(f"Running {scenario['name']} load test...")
        result = performance_test(**scenario)
        assert result['success_rate'] > 95
        assert result['avg_latency'] < 100  # ms
```

### 3. Monitoring Integration

**Prometheus Metrics:**
```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: 'mock-snmp-agent'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Grafana Dashboard:**
```json
{
  "dashboard": {
    "title": "Mock SNMP Agent Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{"expr": "rate(snmp_requests_total[5m])"}]
      },
      {
        "title": "Response Latency",
        "targets": [{"expr": "histogram_quantile(0.95, snmp_response_duration_seconds_bucket)"}]
      }
    ]
  }
}
```

## Operational Guidelines

### 1. Monitoring and Alerting

**Key Metrics to Monitor:**
- Request rate (requests/second)
- Response latency (p50, p95, p99)
- Error rate (percentage)
- Memory usage
- CPU utilization
- Active connections

**Alert Thresholds:**
```yaml
alerts:
  high_latency:
    condition: "avg_latency > 100ms for 5 minutes"
    severity: "warning"

  high_error_rate:
    condition: "error_rate > 5% for 2 minutes"
    severity: "critical"

  memory_usage:
    condition: "memory_usage > 80% for 10 minutes"
    severity: "warning"
```

### 2. Logging Best Practices

**Structured Logging:**
```python
# Use structured logging for better analysis
logger.info("SNMP request processed", extra={
    "request_id": request_id,
    "oid": requested_oid,
    "response_time_ms": response_time * 1000,
    "client_ip": client_address,
    "community": community_string
})
```

**Log Rotation:**
```yaml
logging:
  rotation:
    max_size: "100MB"
    backup_count: 5
    when: "midnight"
```

### 3. Capacity Planning

**Resource Requirements by Load:**

| Load Level | Requests/sec | CPU Cores | Memory | Network |
|------------|-------------|----------|--------|---------|
| Light      | 0-100       | 1        | 256MB  | 10Mbps  |
| Medium     | 100-500     | 2        | 512MB  | 50Mbps  |
| Heavy      | 500-1000    | 4        | 1GB    | 100Mbps |
| Extreme    | 1000+       | 8        | 2GB    | 200Mbps |

**Scaling Guidelines:**
- Horizontal scaling: Use multiple agent instances with load balancer
- Vertical scaling: Increase CPU/memory for single high-performance instance
- Geographic distribution: Deploy agents closer to test clients

## Security Best Practices

### 1. Access Control

**Network Security:**
```bash
# Firewall rules for production
sudo ufw allow from 192.168.1.0/24 to any port 11611
sudo ufw allow from 10.0.0.0/8 to any port 8080
sudo ufw deny 11611
sudo ufw deny 8080
```

**Authentication:**
- Always use SNMPv3 in production environments
- Rotate authentication keys regularly
- Use strong encryption protocols (AES, SHA)
- Implement IP-based access controls

### 2. Data Protection

**Sensitive Information:**
```yaml
# Never log sensitive data
logging:
  exclude_fields:
    - "auth_key"
    - "priv_key"
    - "community"
  sanitize: true
```

**Configuration Security:**
```bash
# Secure configuration files
chmod 600 config/*.yaml
chown app:app config/*.yaml
```

## Troubleshooting Common Issues

### 1. Performance Issues

**Symptom:** High latency responses
**Solutions:**
- Check system resource utilization
- Reduce logging verbosity
- Disable unnecessary simulation behaviors
- Optimize configuration cache settings

**Symptom:** Low throughput
**Solutions:**
- Increase worker pool size
- Optimize network buffer sizes
- Check for network bottlenecks
- Scale horizontally with multiple instances

### 2. Configuration Issues

**Symptom:** Agent fails to start
**Solutions:**
- Validate YAML syntax
- Check file permissions
- Verify required dependencies
- Review startup logs

### 3. Memory Leaks

**Prevention:**
- Enable garbage collection monitoring
- Set maximum cache sizes
- Implement connection timeouts
- Regular memory profiling

## Maintenance Procedures

### 1. Regular Maintenance

**Daily:**
- Monitor performance metrics
- Check error logs
- Verify agent responsiveness

**Weekly:**
- Rotate log files
- Update configuration if needed
- Performance trend analysis

**Monthly:**
- Security key rotation
- Dependency updates
- Capacity planning review

### 2. Backup and Recovery

**Configuration Backup:**
```bash
#!/bin/bash
# backup_config.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "config_backup_$DATE.tar.gz" config/
aws s3 cp "config_backup_$DATE.tar.gz" s3://backup-bucket/snmp-agent/
```

**Disaster Recovery:**
- Document deployment procedures
- Maintain configuration version control
- Test recovery procedures regularly
- Implement automated failover

## Performance Tuning

### 1. Operating System Tuning

**Linux Network Tuning:**
```bash
# /etc/sysctl.conf
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.ipv4.udp_mem = 102400 873800 16777216
net.core.netdev_max_backlog = 5000
```

### 2. Application Tuning

**Python Optimization:**
```python
# Use optimized Python settings
import sys
sys.setswitchinterval(0.001)  # Reduce context switching

# Enable garbage collection optimization
import gc
gc.set_threshold(700, 10, 10)
```

This guide provides comprehensive best practices for deploying and managing the Mock SNMP Agent effectively across different environments and use cases.
