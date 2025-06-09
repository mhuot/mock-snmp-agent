#!/usr/bin/env python3
"""
Docker integration tests for Mock SNMP Agent.

This script tests all functionality in a containerized environment
to validate the complete system works as expected.
"""

import subprocess
import time
import json
import sys
from typing import Dict, List, Tuple
from pathlib import Path


class DockerSNMPTester:
    """Comprehensive Docker-based SNMP testing."""
    
    def __init__(self):
        self.test_results = {}
        self.agents = {
            "basic": {"host": "mock-snmp-basic", "port": 11611},
            "delay": {"host": "mock-snmp-delay", "port": 11612}, 
            "drops": {"host": "mock-snmp-drops", "port": 11613},
            "comprehensive": {"host": "mock-snmp-comprehensive", "port": 11614},
            "counters": {"host": "mock-snmp-counters", "port": 11615}
        }
    
    def wait_for_agents(self, timeout: int = 60) -> bool:
        """Wait for all SNMP agents to be ready."""
        print("Waiting for SNMP agents to start...")
        
        start_time = time.time()
        ready_agents = set()
        
        while len(ready_agents) < len(self.agents) and (time.time() - start_time) < timeout:
            for name, config in self.agents.items():
                if name in ready_agents:
                    continue
                    
                try:
                    result = subprocess.run([
                        "snmpget", "-v2c", "-c", "public", "-t", "2", "-r", "1",
                        f"{config['host']}:{config['port']}", "1.3.6.1.2.1.1.1.0"
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        ready_agents.add(name)
                        print(f"  ✓ {name} agent ready")
                    
                except subprocess.TimeoutExpired:
                    pass
            
            if len(ready_agents) < len(self.agents):
                time.sleep(2)
        
        success = len(ready_agents) == len(self.agents)
        if success:
            print(f"All {len(self.agents)} agents ready!")
        else:
            print(f"Only {len(ready_agents)}/{len(self.agents)} agents ready")
            
        return success
    
    def test_basic_functionality(self) -> Dict:
        """Test basic SNMP functionality."""
        print("\n" + "="*50)
        print("Testing Basic SNMP Functionality")
        print("="*50)
        
        results = {}
        agent = self.agents["basic"]
        
        # Test basic GET
        print("Testing SNMP GET...")
        result = self._snmp_get(agent, "1.3.6.1.2.1.1.1.0")
        results["basic_get"] = result["success"]
        
        if result["success"]:
            print(f"  ✓ GET successful: {result['value']}")
        else:
            print(f"  ✗ GET failed: {result['error']}")
        
        # Test multiple OIDs
        print("Testing multiple OIDs...")
        oids = [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.3.0",  # sysUpTime
            "1.3.6.1.2.1.1.5.0",  # sysName
        ]
        
        success_count = 0
        for oid in oids:
            result = self._snmp_get(agent, oid)
            if result["success"]:
                success_count += 1
        
        results["multiple_oids"] = success_count == len(oids)
        print(f"  {'✓' if results['multiple_oids'] else '✗'} {success_count}/{len(oids)} OIDs successful")
        
        return results
    
    def test_delay_functionality(self) -> Dict:
        """Test delay simulation."""
        print("\n" + "="*50)
        print("Testing Delay Simulation (500ms)")
        print("="*50)
        
        results = {}
        agent = self.agents["delay"]
        
        # Test response timing
        print("Measuring response times...")
        times = []
        
        for i in range(5):
            start_time = time.time()
            result = self._snmp_get(agent, "1.3.6.1.2.1.1.1.0", timeout=10)
            end_time = time.time()
            
            if result["success"]:
                response_time = (end_time - start_time) * 1000  # ms
                times.append(response_time)
                print(f"  Response {i+1}: {response_time:.0f}ms")
            else:
                print(f"  Response {i+1}: Failed - {result['error']}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"  Average response time: {avg_time:.0f}ms")
            
            # Should be around 500ms (allowing for some variance)
            results["delay_working"] = 400 <= avg_time <= 800
            results["avg_response_time"] = avg_time
        else:
            results["delay_working"] = False
            results["avg_response_time"] = 0
        
        return results
    
    def test_drop_functionality(self) -> Dict:
        """Test drop rate simulation."""
        print("\n" + "="*50)
        print("Testing Drop Rate Simulation (20%)")
        print("="*50)
        
        results = {}
        agent = self.agents["drops"]
        
        # Test multiple requests to see drop rate
        print("Testing drop rate with 20 requests...")
        successes = 0
        failures = 0
        
        for i in range(20):
            result = self._snmp_get(agent, "1.3.6.1.2.1.1.1.0", timeout=3)
            if result["success"]:
                successes += 1
            else:
                failures += 1
        
        drop_rate = (failures / 20) * 100
        print(f"  Successes: {successes}/20")
        print(f"  Failures: {failures}/20") 
        print(f"  Actual drop rate: {drop_rate:.1f}%")
        print(f"  Expected drop rate: ~20%")
        
        # Allow some variance in drop rate (10-30%)
        results["drop_rate_working"] = 10 <= drop_rate <= 40
        results["actual_drop_rate"] = drop_rate
        
        return results
    
    def test_comprehensive_functionality(self) -> Dict:
        """Test comprehensive configuration."""
        print("\n" + "="*50)
        print("Testing Comprehensive Configuration")
        print("="*50)
        
        results = {}
        agent = self.agents["comprehensive"]
        
        # Test if agent responds
        print("Testing comprehensive agent response...")
        result = self._snmp_get(agent, "1.3.6.1.2.1.1.1.0", timeout=10)
        results["comprehensive_responsive"] = result["success"]
        
        if result["success"]:
            print("  ✓ Comprehensive agent responding")
        else:
            print(f"  ✗ Comprehensive agent not responding: {result['error']}")
        
        # Test bulk operation (interface table)
        print("Testing bulk operation (interface table)...")
        bulk_result = self._snmp_walk(agent, "1.3.6.1.2.1.2.2.1.1")  # ifIndex
        results["bulk_operations"] = bulk_result["success"]
        
        if bulk_result["success"]:
            count = len(bulk_result["values"])
            print(f"  ✓ Retrieved {count} interface entries")
            results["interface_count"] = count
        else:
            print(f"  ✗ Bulk operation failed: {bulk_result['error']}")
            results["interface_count"] = 0
        
        return results
    
    def test_counter_wrap_functionality(self) -> Dict:
        """Test counter wrap simulation."""
        print("\n" + "="*50)
        print("Testing Counter Wrap Simulation")
        print("="*50)
        
        results = {}
        agent = self.agents["counters"]
        
        # Test counter values over time
        print("Monitoring counter values for wrap detection...")
        
        initial_values = {}
        wrap_detected = False
        
        # Get initial values
        for interface in range(1, 5):
            oid = f"1.3.6.1.2.1.2.2.1.10.{interface}"  # ifInOctets
            result = self._snmp_get(agent, oid, timeout=5)
            if result["success"]:
                try:
                    initial_values[interface] = int(result["value"])
                except ValueError:
                    initial_values[interface] = 0
            else:
                initial_values[interface] = 0
        
        print(f"  Initial counter values: {initial_values}")
        
        # Monitor for 10 seconds looking for wraps
        for iteration in range(20):
            time.sleep(0.5)
            
            current_values = {}
            for interface in range(1, 5):
                oid = f"1.3.6.1.2.1.2.2.1.10.{interface}"
                result = self._snmp_get(agent, oid, timeout=2)
                if result["success"]:
                    try:
                        current_values[interface] = int(result["value"])
                    except ValueError:
                        current_values[interface] = 0
                else:
                    current_values[interface] = 0
            
            # Check for wraps (value significantly decreased)
            for interface in range(1, 5):
                if interface in initial_values and interface in current_values:
                    if current_values[interface] < initial_values[interface] / 2:
                        print(f"  ✓ Counter wrap detected on interface {interface}!")
                        print(f"    {initial_values[interface]:,} → {current_values[interface]:,}")
                        wrap_detected = True
            
            if wrap_detected:
                break
        
        results["counter_wrap_detected"] = wrap_detected
        if not wrap_detected:
            print("  ⚠ No counter wraps detected in 10 seconds")
            print("    (This may be normal if acceleration is low)")
        
        return results
    
    def _snmp_get(self, agent: Dict, oid: str, timeout: int = 5) -> Dict:
        """Execute SNMP GET command."""
        try:
            result = subprocess.run([
                "snmpget", "-v2c", "-c", "public", 
                "-t", str(timeout), "-r", "1",
                f"{agent['host']}:{agent['port']}", oid
            ], capture_output=True, text=True, timeout=timeout + 2)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "=" in output:
                    value_part = output.split("=", 1)[1].strip()
                    # Remove type prefix if present
                    if ":" in value_part:
                        value = value_part.split(":", 1)[1].strip()
                    else:
                        value = value_part
                    
                    return {"success": True, "value": value}
                else:
                    return {"success": False, "error": "No value in response"}
            else:
                return {"success": False, "error": result.stderr.strip()}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _snmp_walk(self, agent: Dict, oid: str, timeout: int = 10) -> Dict:
        """Execute SNMP WALK command."""
        try:
            result = subprocess.run([
                "snmpwalk", "-v2c", "-c", "public",
                "-t", str(timeout), "-r", "1",
                f"{agent['host']}:{agent['port']}", oid
            ], capture_output=True, text=True, timeout=timeout + 5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                values = []
                for line in lines:
                    if "=" in line:
                        values.append(line.strip())
                
                return {"success": True, "values": values}
            else:
                return {"success": False, "error": result.stderr.strip()}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return results."""
        print("Mock SNMP Agent - Docker Integration Tests")
        print("=" * 60)
        
        # Wait for agents to be ready
        if not self.wait_for_agents():
            print("Failed to start all agents - aborting tests")
            return {"overall_success": False, "error": "Agents not ready"}
        
        # Run all tests
        all_results = {}
        
        try:
            all_results["basic"] = self.test_basic_functionality()
            all_results["delay"] = self.test_delay_functionality()
            all_results["drops"] = self.test_drop_functionality()
            all_results["comprehensive"] = self.test_comprehensive_functionality()
            all_results["counters"] = self.test_counter_wrap_functionality()
            
        except KeyboardInterrupt:
            print("\nTests interrupted by user")
            all_results["interrupted"] = True
        
        # Calculate overall success
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, dict):
                for test_name, success in results.items():
                    if isinstance(success, bool):
                        total_tests += 1
                        if success:
                            passed_tests += 1
        
        overall_success = passed_tests == total_tests
        all_results["overall_success"] = overall_success
        all_results["test_summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / max(total_tests, 1)) * 100
        }
        
        return all_results
    
    def print_summary(self, results: Dict) -> None:
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if "test_summary" in results:
            summary = results["test_summary"]
            print(f"Total tests: {summary['total_tests']}")
            print(f"Passed: {summary['passed_tests']}")
            print(f"Success rate: {summary['success_rate']:.1f}%")
            print()
        
        # Print detailed results
        for category, category_results in results.items():
            if category in ["overall_success", "test_summary", "interrupted"]:
                continue
                
            print(f"{category.upper()}:")
            if isinstance(category_results, dict):
                for test_name, result in category_results.items():
                    if isinstance(result, bool):
                        status = "✓" if result else "✗"
                        print(f"  {status} {test_name}")
                    elif isinstance(result, (int, float)):
                        print(f"    {test_name}: {result}")
            print()
        
        overall = results.get("overall_success", False)
        print(f"OVERALL RESULT: {'✓ PASS' if overall else '✗ FAIL'}")


def main():
    """Main test runner."""
    tester = DockerSNMPTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Save results to file
    results_file = Path("/app/logs/docker_test_results.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Exit with appropriate code
    return 0 if results.get("overall_success", False) else 1


if __name__ == "__main__":
    sys.exit(main())