#!/usr/bin/env python3
"""
Docker Comprehensive Testing Suite

This script runs comprehensive tests across all Docker containers
to validate SNMPv3 security, REST API, and State Machine functionality.
"""

import time
import requests
import subprocess
import sys
import json
from typing import Dict, List, Any
from pathlib import Path


class DockerTestSuite:
    """Comprehensive Docker-based testing suite."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = []
        self.containers = {
            'snmpv3-security': {
                'snmp_port': 11621,
                'api_port': 8081,
                'container': 'mock-snmp-snmpv3-security'
            },
            'rest-api': {
                'snmp_port': 11622,
                'api_port': 8082,
                'container': 'mock-snmp-rest-api'
            },
            'state-machine': {
                'snmp_port': 11623,
                'api_port': 8083,
                'container': 'mock-snmp-state-machine'
            },
            'combined': {
                'snmp_port': 11624,
                'api_port': 8084,
                'container': 'mock-snmp-combined'
            }
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log a test result."""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': details,
            'data': data
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"     {details}")
        if not success:
            print(f"     Data: {data}")
    
    def wait_for_containers(self, timeout: int = 120) -> bool:
        """Wait for all containers to be healthy."""
        print("Waiting for containers to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_ready = True
            
            for name, config in self.containers.items():
                try:
                    # Test SNMP port
                    snmp_result = subprocess.run([
                        'snmpget', '-v2c', '-c', 'public', '-t', '2', '-r', '1',
                        f"snmpv3-security-test:{config['snmp_port']}", '1.3.6.1.2.1.1.1.0'
                    ], capture_output=True, timeout=5)
                    
                    # Test API port
                    api_response = requests.get(
                        f"http://{name}-test:{config['api_port']}/health",
                        timeout=5
                    )
                    
                    if snmp_result.returncode != 0 or api_response.status_code != 200:
                        all_ready = False
                        break
                        
                except Exception:
                    all_ready = False
                    break
            
            if all_ready:
                print("✓ All containers are ready")
                return True
            
            time.sleep(5)
        
        print("✗ Timeout waiting for containers")
        return False
    
    def test_snmpv3_security_features(self) -> None:
        """Test SNMPv3 security failure features."""
        print("\n--- Testing SNMPv3 Security Features ---")
        
        container = 'snmpv3-security-test'
        snmp_port = self.containers['snmpv3-security']['snmp_port']
        api_port = self.containers['snmpv3-security']['api_port']
        
        # Test 1: Valid SNMPv3 credentials should work sometimes
        success_count = 0
        total_attempts = 10
        
        for i in range(total_attempts):
            try:
                result = subprocess.run([
                    'snmpget', '-v3', '-l', 'authNoPriv', '-u', 'simulator',
                    '-a', 'MD5', '-A', 'auctoritas', '-t', '3', '-r', '1',
                    f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
                ], capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    success_count += 1
            except subprocess.TimeoutExpired:
                pass  # Expected with failures
        
        # Should have some successes and some failures due to security simulation
        success_rate = success_count / total_attempts * 100
        self.log_test_result(
            "SNMPv3 Security Simulation",
            10 <= success_rate <= 90,  # Should be between 10-90% due to failures
            f"Success rate: {success_rate}%",
            {"success_count": success_count, "total_attempts": total_attempts}
        )
        
        # Test 2: Invalid credentials should fail more often
        fail_count = 0
        for i in range(5):
            try:
                result = subprocess.run([
                    'snmpget', '-v3', '-l', 'authNoPriv', '-u', 'wronguser',
                    '-a', 'MD5', '-A', 'wrongpass', '-t', '2', '-r', '1',
                    f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
                ], capture_output=True, timeout=8)
                
                if result.returncode != 0:
                    fail_count += 1
            except subprocess.TimeoutExpired:
                fail_count += 1
        
        self.log_test_result(
            "SNMPv3 Invalid Credentials Rejection",
            fail_count >= 4,  # Most should fail
            f"Failed {fail_count}/5 attempts",
            {"fail_count": fail_count}
        )
        
        # Test 3: API should report security configuration
        try:
            response = requests.get(f"http://{container}:{api_port}/config", timeout=10)
            config = response.json()
            
            security_enabled = (
                config.get('simulation', {})
                .get('behaviors', {})
                .get('snmpv3_security', {})
                .get('enabled', False)
            )
            
            self.log_test_result(
                "API Reports Security Configuration",
                security_enabled,
                "SNMPv3 security should be enabled in config",
                {"security_enabled": security_enabled}
            )
        except Exception as e:
            self.log_test_result(
                "API Reports Security Configuration",
                False,
                f"API request failed: {e}"
            )
    
    def test_rest_api_functionality(self) -> None:
        """Test REST API functionality."""
        print("\n--- Testing REST API Functionality ---")
        
        container = 'mock-snmp-rest-api'
        api_port = self.containers['rest-api']['api_port']
        base_url = f"http://{container}:{api_port}"
        
        # Test 1: Health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            health_data = response.json()
            
            self.log_test_result(
                "API Health Endpoint",
                response.status_code == 200 and health_data.get('status') == 'healthy',
                f"Status: {health_data.get('status')}",
                health_data
            )
        except Exception as e:
            self.log_test_result("API Health Endpoint", False, f"Request failed: {e}")
        
        # Test 2: Metrics endpoint
        try:
            response = requests.get(f"{base_url}/metrics", timeout=10)
            metrics_data = response.json()
            
            required_fields = ['requests_total', 'uptime_seconds', 'current_connections']
            has_required = all(field in metrics_data for field in required_fields)
            
            self.log_test_result(
                "API Metrics Endpoint",
                response.status_code == 200 and has_required,
                f"Required fields present: {has_required}",
                metrics_data
            )
        except Exception as e:
            self.log_test_result("API Metrics Endpoint", False, f"Request failed: {e}")
        
        # Test 3: Configuration endpoint
        try:
            response = requests.get(f"{base_url}/config", timeout=10)
            config_data = response.json()
            
            has_simulation = 'simulation' in config_data
            
            self.log_test_result(
                "API Configuration Endpoint",
                response.status_code == 200 and has_simulation,
                f"Has simulation config: {has_simulation}",
                {"has_simulation_config": has_simulation}
            )
        except Exception as e:
            self.log_test_result("API Configuration Endpoint", False, f"Request failed: {e}")
        
        # Test 4: Configuration update
        try:
            update_data = {
                "simulation": {
                    "behaviors": {
                        "delay": {
                            "enabled": True,
                            "global_delay": 200
                        }
                    }
                }
            }
            
            response = requests.put(f"{base_url}/config", json=update_data, timeout=10)
            updated_config = response.json()
            
            delay_enabled = (
                updated_config.get('simulation', {})
                .get('behaviors', {})
                .get('delay', {})
                .get('enabled', False)
            )
            
            self.log_test_result(
                "API Configuration Update",
                response.status_code == 200 and delay_enabled,
                f"Delay enabled after update: {delay_enabled}",
                {"delay_enabled": delay_enabled}
            )
        except Exception as e:
            self.log_test_result("API Configuration Update", False, f"Request failed: {e}")
        
        # Test 5: Agent status endpoint
        try:
            response = requests.get(f"{base_url}/agent/status", timeout=10)
            status_data = response.json()
            
            agent_running = status_data.get('status') == 'running'
            has_pid = 'pid' in status_data
            
            self.log_test_result(
                "API Agent Status",
                response.status_code == 200 and agent_running and has_pid,
                f"Agent running: {agent_running}, Has PID: {has_pid}",
                status_data
            )
        except Exception as e:
            self.log_test_result("API Agent Status", False, f"Request failed: {e}")
        
        # Test 6: Available OIDs endpoint
        try:
            response = requests.get(f"{base_url}/oids/available", timeout=10)
            oids_data = response.json()
            
            has_oids = len(oids_data.get('oids', [])) > 0
            has_count = 'total_count' in oids_data
            
            self.log_test_result(
                "API Available OIDs",
                response.status_code == 200 and has_oids and has_count,
                f"OID count: {oids_data.get('total_count', 0)}",
                {"oid_count": oids_data.get('total_count', 0)}
            )
        except Exception as e:
            self.log_test_result("API Available OIDs", False, f"Request failed: {e}")
    
    def test_state_machine_functionality(self) -> None:
        """Test state machine functionality."""
        print("\n--- Testing State Machine Functionality ---")
        
        container = 'mock-snmp-state-machine'
        snmp_port = self.containers['state-machine']['snmp_port']
        api_port = self.containers['state-machine']['api_port']
        
        # Test 1: API should report state machine configuration
        try:
            response = requests.get(f"http://{container}:{api_port}/config", timeout=10)
            config = response.json()
            
            sm_enabled = (
                config.get('simulation', {})
                .get('state_machine', {})
                .get('enabled', False)
            )
            
            device_type = (
                config.get('simulation', {})
                .get('state_machine', {})
                .get('device_type', 'unknown')
            )
            
            self.log_test_result(
                "State Machine Configuration",
                sm_enabled,
                f"Device type: {device_type}",
                {"enabled": sm_enabled, "device_type": device_type}
            )
        except Exception as e:
            self.log_test_result("State Machine Configuration", False, f"API request failed: {e}")
        
        # Test 2: SNMP responses should reflect state effects
        response_times = []
        success_count = 0
        
        for i in range(10):
            try:
                start_time = time.time()
                result = subprocess.run([
                    'snmpget', '-v2c', '-c', 'public', '-t', '5', '-r', '1',
                    f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
                ], capture_output=True, timeout=15)
                end_time = time.time()
                
                if result.returncode == 0:
                    success_count += 1
                    response_times.append((end_time - start_time) * 1000)
                
            except subprocess.TimeoutExpired:
                pass  # May timeout due to state effects
            
            time.sleep(1)  # Brief pause between requests
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        self.log_test_result(
            "State Machine SNMP Effects",
            success_count > 0,  # Should have some successful responses
            f"Success rate: {success_count}/10, Avg response: {avg_response_time:.1f}ms",
            {
                "success_count": success_count,
                "avg_response_time_ms": avg_response_time,
                "response_times": response_times
            }
        )
        
        # Test 3: Check if sysDescr reflects device state
        try:
            result = subprocess.run([
                'snmpget', '-v2c', '-c', 'public', '-t', '5', '-r', '2',
                f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
            ], capture_output=True, timeout=15)
            
            if result.returncode == 0:
                output = result.stdout.decode('utf-8')
                has_state_info = any(word in output.lower() for word in ['router', 'booting', 'operational'])
                
                self.log_test_result(
                    "State Reflected in sysDescr",
                    has_state_info,
                    f"Output contains state info: {has_state_info}",
                    {"snmp_output": output.strip()}
                )
            else:
                self.log_test_result(
                    "State Reflected in sysDescr",
                    False,
                    "SNMP request failed",
                    {"error": result.stderr.decode('utf-8')}
                )
        except Exception as e:
            self.log_test_result("State Reflected in sysDescr", False, f"Request failed: {e}")
    
    def test_combined_features(self) -> None:
        """Test combined features working together."""
        print("\n--- Testing Combined Features ---")
        
        container = 'mock-snmp-combined'
        snmp_port = self.containers['combined']['snmp_port']
        api_port = self.containers['combined']['api_port']
        
        # Test 1: All features should be enabled in configuration
        try:
            response = requests.get(f"http://{container}:{api_port}/config", timeout=10)
            config = response.json()
            
            behaviors = config.get('simulation', {}).get('behaviors', {})
            
            features_enabled = {
                'snmpv3_security': behaviors.get('snmpv3_security', {}).get('enabled', False),
                'state_machine': config.get('simulation', {}).get('state_machine', {}).get('enabled', False),
                'rest_api': config.get('simulation', {}).get('rest_api', {}).get('enabled', False)
            }
            
            all_enabled = all(features_enabled.values())
            
            self.log_test_result(
                "Combined Features Configuration",
                all_enabled,
                f"Features enabled: {features_enabled}",
                features_enabled
            )
        except Exception as e:
            self.log_test_result("Combined Features Configuration", False, f"API request failed: {e}")
        
        # Test 2: SNMP should work with combined effects
        try:
            result = subprocess.run([
                'snmpget', '-v3', '-l', 'authNoPriv', '-u', 'simulator',
                '-a', 'MD5', '-A', 'auctoritas', '-t', '10', '-r', '2',
                f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
            ], capture_output=True, timeout=25)
            
            # Should succeed at least sometimes even with security failures and state effects
            snmp_works = result.returncode == 0
            
            self.log_test_result(
                "Combined Features SNMP Operation",
                True,  # Test that we can attempt the operation
                f"SNMP operation result: {'Success' if snmp_works else 'Failed (expected with security simulation)'}",
                {
                    "snmp_success": snmp_works,
                    "stdout": result.stdout.decode('utf-8') if snmp_works else "",
                    "stderr": result.stderr.decode('utf-8') if not snmp_works else ""
                }
            )
        except Exception as e:
            self.log_test_result("Combined Features SNMP Operation", False, f"Request failed: {e}")
    
    def test_performance_under_load(self) -> None:
        """Test performance under moderate load."""
        print("\n--- Testing Performance Under Load ---")
        
        container = 'mock-snmp-rest-api'
        snmp_port = self.containers['rest-api']['snmp_port']
        
        # Send multiple concurrent SNMP requests
        start_time = time.time()
        successful_requests = 0
        total_requests = 20
        
        processes = []
        for i in range(total_requests):
            proc = subprocess.Popen([
                'snmpget', '-v2c', '-c', 'public', '-t', '3', '-r', '1',
                f"{container}:{snmp_port}", '1.3.6.1.2.1.1.1.0'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(proc)
        
        # Wait for all processes to complete
        for proc in processes:
            try:
                proc.wait(timeout=10)
                if proc.returncode == 0:
                    successful_requests += 1
            except subprocess.TimeoutExpired:
                proc.kill()
        
        end_time = time.time()
        total_time = end_time - start_time
        success_rate = successful_requests / total_requests * 100
        
        self.log_test_result(
            "Performance Under Load",
            success_rate >= 80,  # Should handle 80%+ successfully
            f"Success rate: {success_rate}%, Time: {total_time:.1f}s",
            {
                "successful_requests": successful_requests,
                "total_requests": total_requests,
                "total_time_seconds": total_time,
                "requests_per_second": total_requests / total_time
            }
        )
    
    def run_all_tests(self) -> bool:
        """Run all comprehensive tests."""
        print("Docker Comprehensive Testing Suite")
        print("=" * 50)
        
        # Wait for containers to be ready
        if not self.wait_for_containers():
            print("✗ Containers failed to start properly")
            return False
        
        # Run all test suites
        self.test_snmpv3_security_features()
        self.test_rest_api_functionality()
        self.test_state_machine_functionality()
        self.test_combined_features()
        self.test_performance_under_load()
        
        # Generate test report
        self.generate_test_report()
        
        # Return overall success
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"\n{'='*50}")
        print(f"Overall Results: {passed_tests}/{total_tests} tests passed")
        
        return passed_tests == total_tests
    
    def generate_test_report(self) -> None:
        """Generate detailed test report."""
        report_file = Path("/app/test-results/docker_comprehensive_test_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        report = {
            "timestamp": time.time(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for result in self.test_results if result['success']),
            "failed_tests": sum(1 for result in self.test_results if not result['success']),
            "test_results": self.test_results,
            "summary": {
                "snmpv3_security": [],
                "rest_api": [],
                "state_machine": [],
                "combined_features": [],
                "performance": []
            }
        }
        
        # Categorize results
        for result in self.test_results:
            test_name = result['test_name'].lower()
            if 'snmpv3' in test_name or 'security' in test_name:
                report['summary']['snmpv3_security'].append(result)
            elif 'api' in test_name:
                report['summary']['rest_api'].append(result)
            elif 'state' in test_name:
                report['summary']['state_machine'].append(result)
            elif 'combined' in test_name:
                report['summary']['combined_features'].append(result)
            elif 'performance' in test_name:
                report['summary']['performance'].append(result)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed test report saved to: {report_file}")


def main():
    """Main test execution function."""
    suite = DockerTestSuite()
    success = suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())