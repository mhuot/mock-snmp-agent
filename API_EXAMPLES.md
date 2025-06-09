# Mock SNMP Agent API Examples

## Overview

This document provides practical examples for using the Mock SNMP Agent REST API in various scenarios including automated testing, monitoring integration, and CI/CD pipelines.

## Basic Usage Examples

### 1. Health Monitoring

```python
#!/usr/bin/env python3
"""
Monitor agent health and alert on issues
"""
import requests
import time
import logging

def check_agent_health(api_url="http://localhost:8080"):
    """Check agent health and return status"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'healthy': True,
                'uptime': data['uptime_seconds'],
                'endpoint': data['snmp_endpoint']
            }
        else:
            return {'healthy': False, 'error': f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {'healthy': False, 'error': str(e)}

def monitor_continuously():
    """Continuous health monitoring"""
    while True:
        health = check_agent_health()
        if health['healthy']:
            print(f"✓ Agent healthy - uptime: {health['uptime']:.0f}s")
        else:
            print(f"✗ Agent unhealthy: {health['error']}")
            # Send alert here
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_continuously()
```

### 2. Performance Metrics Collection

```python
#!/usr/bin/env python3
"""
Collect and analyze performance metrics
"""
import requests
import json
import csv
from datetime import datetime

class MetricsCollector:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        
    def get_metrics(self):
        """Fetch current metrics"""
        response = requests.get(f"{self.api_url}/metrics")
        if response.status_code == 200:
            return response.json()
        return None
    
    def collect_to_csv(self, filename="metrics.csv", interval=60, duration=3600):
        """Collect metrics to CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'requests_total', 'avg_response_time', 
                         'error_rate', 'memory_usage_mb']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            end_time = time.time() + duration
            while time.time() < end_time:
                metrics = self.get_metrics()
                if metrics:
                    row = {
                        'timestamp': datetime.now().isoformat(),
                        'requests_total': metrics.get('requests_total', 0),
                        'avg_response_time': metrics.get('avg_response_time_ms', 0),
                        'error_rate': metrics.get('error_rate_percent', 0),
                        'memory_usage_mb': metrics.get('memory_usage_mb', 0)
                    }
                    writer.writerow(row)
                    print(f"Collected: {row}")
                
                time.sleep(interval)

# Usage
collector = MetricsCollector()
collector.collect_to_csv("agent_metrics.csv", interval=30, duration=1800)
```

## Configuration Management Examples

### 3. Dynamic Configuration Updates

```python
#!/usr/bin/env python3
"""
Dynamically update agent configuration
"""
import requests
import yaml

class ConfigManager:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
    
    def get_current_config(self):
        """Get current configuration"""
        response = requests.get(f"{self.api_url}/config")
        return response.json() if response.status_code == 200 else None
    
    def update_behavior(self, behavior_name, parameters):
        """Update specific behavior configuration"""
        config_update = {
            "behaviors": {
                behavior_name: parameters
            }
        }
        
        response = requests.put(
            f"{self.api_url}/config", 
            json=config_update
        )
        
        if response.status_code == 200:
            print(f"Successfully updated {behavior_name}")
            return True
        else:
            print(f"Failed to update {behavior_name}: {response.text}")
            return False
    
    def enable_delay(self, delay_ms=100, deviation_ms=50):
        """Enable delay behavior with specific parameters"""
        return self.update_behavior("delay", {
            "enabled": True,
            "global_delay": delay_ms,
            "deviation": deviation_ms
        })
    
    def enable_packet_drops(self, drop_rate=5):
        """Enable packet drop simulation"""
        return self.update_behavior("drops", {
            "enabled": True,
            "rate": drop_rate
        })
    
    def disable_all_behaviors(self):
        """Disable all simulation behaviors for clean testing"""
        behaviors = ["delay", "drops", "counter_wrap", "resource_limits"]
        for behavior in behaviors:
            self.update_behavior(behavior, {"enabled": False})

# Usage examples
manager = ConfigManager()

# Test scenario 1: Clean baseline
manager.disable_all_behaviors()

# Test scenario 2: Network latency simulation
manager.enable_delay(delay_ms=200, deviation_ms=100)

# Test scenario 3: Unreliable network
manager.enable_packet_drops(drop_rate=10)
```

### 4. Test Scenario Automation

```python
#!/usr/bin/env python3
"""
Automated test scenario execution
"""
import requests
import time
import json

class ScenarioRunner:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
    
    def create_scenario(self, scenario_config):
        """Create a new test scenario"""
        response = requests.post(
            f"{self.api_url}/simulation/scenarios",
            json=scenario_config
        )
        
        if response.status_code == 201:
            scenario_id = response.json()['id']
            print(f"Created scenario: {scenario_id}")
            return scenario_id
        else:
            print(f"Failed to create scenario: {response.text}")
            return None
    
    def execute_scenario(self, scenario_id):
        """Execute a test scenario"""
        response = requests.post(
            f"{self.api_url}/simulation/execute",
            json={"scenario_id": scenario_id}
        )
        
        if response.status_code == 200:
            execution_id = response.json()['execution_id']
            print(f"Started execution: {execution_id}")
            return execution_id
        else:
            print(f"Failed to start scenario: {response.text}")
            return None
    
    def wait_for_completion(self, execution_id, timeout=300):
        """Wait for scenario completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.api_url}/simulation/executions/{execution_id}"
            )
            
            if response.status_code == 200:
                status = response.json()['status']
                if status == 'completed':
                    return response.json()
                elif status == 'failed':
                    print(f"Scenario failed: {response.json()['error']}")
                    return None
                
            time.sleep(10)
        
        print("Scenario timed out")
        return None
    
    def run_performance_test(self):
        """Complete performance test scenario"""
        scenario = {
            "name": "Performance Baseline Test",
            "description": "Test agent performance without simulation behaviors",
            "duration_seconds": 120,
            "behaviors": [
                {
                    "name": "delay",
                    "enabled": False
                },
                {
                    "name": "drops", 
                    "enabled": False
                }
            ],
            "success_criteria": {
                "max_response_time_ms": 10,
                "min_success_rate": 99
            }
        }
        
        # Create and execute scenario
        scenario_id = self.create_scenario(scenario)
        if scenario_id:
            execution_id = self.execute_scenario(scenario_id)
            if execution_id:
                result = self.wait_for_completion(execution_id)
                if result:
                    print("Performance test completed successfully!")
                    print(f"Results: {json.dumps(result['results'], indent=2)}")
                    return result
        
        return None

# Usage
runner = ScenarioRunner()
result = runner.run_performance_test()
```

## WebSocket Examples

### 5. Real-time Monitoring

```python
#!/usr/bin/env python3
"""
Real-time monitoring using WebSockets
"""
import asyncio
import websockets
import json

async def monitor_metrics():
    """Monitor real-time metrics"""
    uri = "ws://localhost:8080/ws/metrics"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to metrics stream")
            
            async for message in websocket:
                data = json.loads(message)
                print(f"Metrics update: {data['timestamp']} - "
                      f"Requests: {data.get('requests_total', 0)}, "
                      f"Latency: {data.get('avg_response_time_ms', 0):.2f}ms")
                
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    except Exception as e:
        print(f"Error: {e}")

async def monitor_logs():
    """Monitor real-time logs"""
    uri = "ws://localhost:8080/ws/logs"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to log stream")
            
            async for message in websocket:
                log_entry = json.loads(message)
                level = log_entry.get('level', 'INFO')
                msg = log_entry.get('message', '')
                timestamp = log_entry.get('timestamp', '')
                
                print(f"[{level}] {timestamp}: {msg}")
                
    except Exception as e:
        print(f"Log monitoring error: {e}")

async def monitor_snmp_activity():
    """Monitor SNMP request/response activity"""
    uri = "ws://localhost:8080/ws/activity"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to SNMP activity stream")
            
            async for message in websocket:
                activity = json.loads(message)
                req_type = activity.get('type', 'unknown')
                oid = activity.get('oid', '')
                response_time = activity.get('response_time_ms', 0)
                
                print(f"SNMP {req_type}: {oid} ({response_time:.2f}ms)")
                
    except Exception as e:
        print(f"Activity monitoring error: {e}")

# Run all monitors concurrently
async def main():
    await asyncio.gather(
        monitor_metrics(),
        monitor_logs(),
        monitor_snmp_activity()
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Integration Examples

### 6. Prometheus Integration

```python
#!/usr/bin/env python3
"""
Export metrics to Prometheus format
"""
import requests
import time

def export_prometheus_metrics(api_url="http://localhost:8080", output_file="metrics.prom"):
    """Export current metrics in Prometheus format"""
    
    response = requests.get(f"{api_url}/metrics")
    if response.status_code != 200:
        print("Failed to fetch metrics")
        return
    
    metrics = response.json()
    timestamp = int(time.time() * 1000)
    
    prom_metrics = [
        f"# HELP snmp_requests_total Total number of SNMP requests",
        f"# TYPE snmp_requests_total counter",
        f"snmp_requests_total {metrics.get('requests_total', 0)} {timestamp}",
        f"",
        f"# HELP snmp_response_time_ms Average response time in milliseconds", 
        f"# TYPE snmp_response_time_ms gauge",
        f"snmp_response_time_ms {metrics.get('avg_response_time_ms', 0)} {timestamp}",
        f"",
        f"# HELP snmp_error_rate Error rate percentage",
        f"# TYPE snmp_error_rate gauge", 
        f"snmp_error_rate {metrics.get('error_rate_percent', 0)} {timestamp}",
        f"",
        f"# HELP snmp_agent_memory_mb Memory usage in megabytes",
        f"# TYPE snmp_agent_memory_mb gauge",
        f"snmp_agent_memory_mb {metrics.get('memory_usage_mb', 0)} {timestamp}"
    ]
    
    with open(output_file, 'w') as f:
        f.write('\\n'.join(prom_metrics))
    
    print(f"Metrics exported to {output_file}")

# Usage
export_prometheus_metrics()
```

### 7. CI/CD Pipeline Integration

```python
#!/usr/bin/env python3
"""
CI/CD pipeline integration for automated testing
"""
import requests
import sys
import time
import json

class CIPipelineIntegration:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        
    def wait_for_agent_ready(self, timeout=60):
        """Wait for agent to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✓ Agent is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(5)
        
        print("✗ Agent failed to become ready")
        return False
    
    def run_smoke_tests(self):
        """Run basic smoke tests"""
        tests = [
            ("Health check", self._test_health),
            ("Metrics endpoint", self._test_metrics),
            ("Configuration endpoint", self._test_config),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result, None))
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status}: {test_name}")
            except Exception as e:
                results.append((test_name, False, str(e)))
                print(f"✗ ERROR: {test_name} - {e}")
        
        # Summary
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        print(f"\\nSummary: {passed}/{total} tests passed")
        
        return passed == total
    
    def _test_health(self):
        response = requests.get(f"{self.api_url}/health")
        return response.status_code == 200
    
    def _test_metrics(self):
        response = requests.get(f"{self.api_url}/metrics")
        return response.status_code == 200
    
    def _test_config(self):
        response = requests.get(f"{self.api_url}/config")
        return response.status_code == 200
    
    def performance_gate(self, max_latency_ms=50, min_success_rate=95):
        """Performance gate for CI/CD"""
        print(f"Performance gate: latency < {max_latency_ms}ms, success rate > {min_success_rate}%")
        
        # Run quick performance test
        scenario = {
            "name": "CI Performance Gate",
            "description": "Quick performance validation",
            "duration_seconds": 60,
            "behaviors": [],  # No simulation behaviors
            "success_criteria": {
                "max_response_time_ms": max_latency_ms,
                "min_success_rate": min_success_rate
            }
        }
        
        # Execute scenario
        response = requests.post(f"{self.api_url}/simulation/execute", json=scenario)
        if response.status_code != 200:
            print("✗ Failed to start performance test")
            return False
        
        execution_id = response.json()['execution_id']
        
        # Wait for completion
        for _ in range(12):  # 2 minutes max
            response = requests.get(f"{self.api_url}/simulation/executions/{execution_id}")
            if response.status_code == 200:
                status = response.json()['status']
                if status == 'completed':
                    results = response.json()['results']
                    avg_latency = results.get('avg_response_time_ms', float('inf'))
                    success_rate = results.get('success_rate_percent', 0)
                    
                    latency_ok = avg_latency <= max_latency_ms
                    success_ok = success_rate >= min_success_rate
                    
                    print(f"Results: {avg_latency:.2f}ms latency, {success_rate:.1f}% success rate")
                    
                    if latency_ok and success_ok:
                        print("✓ Performance gate PASSED")
                        return True
                    else:
                        print("✗ Performance gate FAILED")
                        return False
                elif status == 'failed':
                    print("✗ Performance test failed")
                    return False
            
            time.sleep(10)
        
        print("✗ Performance test timed out")
        return False

def main():
    """Main CI/CD integration function"""
    ci = CIPipelineIntegration()
    
    # Step 1: Wait for agent
    if not ci.wait_for_agent_ready():
        sys.exit(1)
    
    # Step 2: Smoke tests
    if not ci.run_smoke_tests():
        sys.exit(1)
    
    # Step 3: Performance gate
    if not ci.performance_gate():
        sys.exit(1)
    
    print("\\n🎉 All CI checks passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Advanced Usage

### 8. Load Testing Orchestration

```python
#!/usr/bin/env python3
"""
Orchestrate complex load testing scenarios
"""
import requests
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

class LoadTestOrchestrator:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        
    async def distributed_load_test(self, agents, total_requests=10000, duration=300):
        """Distribute load across multiple agent instances"""
        
        requests_per_agent = total_requests // len(agents)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for agent_url in agents:
                task = self._load_test_agent(session, agent_url, requests_per_agent, duration)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Aggregate results
            total_requests_sent = sum(r['requests_sent'] for r in results)
            total_successful = sum(r['successful'] for r in results)
            avg_latency = sum(r['avg_latency'] * r['successful'] for r in results) / total_successful
            
            print(f"\\nDistributed Load Test Results:")
            print(f"Total requests: {total_requests_sent}")
            print(f"Successful: {total_successful}")
            print(f"Success rate: {total_successful/total_requests_sent*100:.1f}%")
            print(f"Average latency: {avg_latency:.2f}ms")
            
            return {
                'total_requests': total_requests_sent,
                'successful': total_successful,
                'success_rate': total_successful/total_requests_sent*100,
                'avg_latency': avg_latency
            }
    
    async def _load_test_agent(self, session, agent_url, requests, duration):
        """Load test single agent"""
        print(f"Starting load test on {agent_url}")
        
        # Configure for high performance
        config = {
            "behaviors": {
                "delay": {"enabled": False},
                "drops": {"enabled": False}
            }
        }
        
        await session.put(f"{agent_url}/config", json=config)
        
        # Run load test
        start_time = time.time()
        requests_sent = 0
        successful = 0
        total_latency = 0
        
        while time.time() - start_time < duration and requests_sent < requests:
            req_start = time.time()
            
            async with session.get(f"{agent_url}/metrics") as response:
                if response.status == 200:
                    successful += 1
                    total_latency += (time.time() - req_start) * 1000
                
                requests_sent += 1
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        avg_latency = total_latency / successful if successful > 0 else 0
        
        return {
            'agent_url': agent_url,
            'requests_sent': requests_sent,
            'successful': successful,
            'avg_latency': avg_latency
        }

# Usage
async def run_distributed_test():
    orchestrator = LoadTestOrchestrator()
    
    # List of agent instances
    agents = [
        "http://localhost:8080",
        "http://localhost:8081", 
        "http://localhost:8082"
    ]
    
    results = await orchestrator.distributed_load_test(
        agents=agents,
        total_requests=50000,
        duration=600
    )
    
    print(f"Final results: {results}")

if __name__ == "__main__":
    asyncio.run(run_distributed_test())
```

These examples demonstrate practical usage patterns for the Mock SNMP Agent API, from basic monitoring to complex CI/CD integration and distributed load testing scenarios.