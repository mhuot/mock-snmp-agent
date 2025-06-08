#!/usr/bin/env python3
"""
Load Testing Example

This example demonstrates how to perform load testing against the Mock SNMP Agent
to measure performance characteristics under various loads.
"""

import subprocess
import sys
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class SNMPLoadTester:
    """SNMP Load Testing utility."""
    
    def __init__(self, host="127.0.0.1", port=11611, community="public"):
        self.host = host
        self.port = port
        self.community = community
        self.endpoint = f"{host}:{port}"
    
    def single_request(self, request_id, oid="1.3.6.1.2.1.1.1.0"):
        """Execute a single SNMP GET request."""
        start_time = time.time()
        try:
            result = subprocess.run([
                "snmpget", "-v2c", "-c", self.community,
                "-t", "5", "-r", "0",  # 5 second timeout, no retries
                self.endpoint, oid
            ], capture_output=True, text=True, timeout=10, check=False)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            success = result.returncode == 0 and "STRING:" in result.stdout
            return {
                'id': request_id,
                'latency_ms': latency_ms,
                'success': success,
                'error': result.stderr if not success else None,
                'timestamp': start_time
            }
        except Exception as exc:
            end_time = time.time()
            return {
                'id': request_id,
                'latency_ms': (end_time - start_time) * 1000,
                'success': False,
                'error': str(exc),
                'timestamp': start_time
            }
    
    def load_test(self, num_requests=100, max_workers=10, oid="1.3.6.1.2.1.1.1.0"):
        """Perform load test with specified parameters."""
        print(f"Load Test Configuration:")
        print(f"  Target: {self.endpoint}")
        print(f"  Community: {self.community}")
        print(f"  Requests: {num_requests}")
        print(f"  Concurrent workers: {max_workers}")
        print(f"  OID: {oid}")
        print()
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            futures = [
                executor.submit(self.single_request, i, oid) 
                for i in range(num_requests)
            ]
            
            # Collect results with progress indication
            completed = 0
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if completed % 10 == 0 or completed == num_requests:
                    print(f"  Progress: {completed}/{num_requests} requests completed")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        return self.analyze_results(results, total_duration)
    
    def analyze_results(self, results, total_duration):
        """Analyze load test results."""
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        analysis = {
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'total_duration': total_duration,
            'throughput': len(results) / total_duration if total_duration > 0 else 0,
            'latencies': [],
            'latency_stats': {}
        }
        
        if successful_results:
            latencies = [r['latency_ms'] for r in successful_results]
            analysis['latencies'] = latencies
            analysis['latency_stats'] = {
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'p95': self.percentile(latencies, 95),
                'p99': self.percentile(latencies, 99),
                'std_dev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        
        # Error analysis
        error_types = {}
        for result in failed_results:
            error = result['error'] or 'Unknown error'
            error_types[error] = error_types.get(error, 0) + 1
        
        analysis['error_types'] = error_types
        
        return analysis
    
    @staticmethod
    def percentile(data, percentile):
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def print_results(self, analysis):
        """Print load test results."""
        print(f"\n{'='*60}")
        print(f"LOAD TEST RESULTS")
        print(f"{'='*60}")
        
        # Overall metrics
        print(f"\nOverall Metrics:")
        print(f"  Total requests: {analysis['total_requests']}")
        print(f"  Successful: {analysis['successful_requests']}")
        print(f"  Failed: {analysis['failed_requests']}")
        print(f"  Success rate: {analysis['success_rate']:.1%}")
        print(f"  Total duration: {analysis['total_duration']:.2f}s")
        print(f"  Throughput: {analysis['throughput']:.1f} req/sec")
        
        # Latency statistics
        if analysis['latency_stats']:
            stats = analysis['latency_stats']
            print(f"\nLatency Statistics (milliseconds):")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  Min: {stats['min']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
            print(f"  95th percentile: {stats['p95']:.2f}ms")
            print(f"  99th percentile: {stats['p99']:.2f}ms")
            print(f"  Std deviation: {stats['std_dev']:.2f}ms")
        
        # Error analysis
        if analysis['error_types']:
            print(f"\nError Analysis:")
            for error, count in analysis['error_types'].items():
                print(f"  {error}: {count} occurrences")
        
        # Performance assessment
        print(f"\nPerformance Assessment:")
        throughput_status = "✓ GOOD" if analysis['throughput'] >= 50 else "⚠ LOW"
        print(f"  Throughput: {throughput_status}")
        
        if analysis['latency_stats']:
            avg_latency = analysis['latency_stats']['mean']
            latency_status = "✓ GOOD" if avg_latency < 100 else "⚠ HIGH"
            print(f"  Average latency: {latency_status}")
            
            success_status = "✓ GOOD" if analysis['success_rate'] >= 0.95 else "⚠ LOW"
            print(f"  Success rate: {success_status}")


def test_basic_load():
    """Test basic load with moderate concurrency."""
    print("=== Basic Load Test ===")
    tester = SNMPLoadTester()
    analysis = tester.load_test(num_requests=50, max_workers=5)
    tester.print_results(analysis)
    return analysis['success_rate'] >= 0.8


def test_high_concurrency():
    """Test with high concurrency."""
    print(f"\n{'='*60}")
    print("=== High Concurrency Test ===")
    tester = SNMPLoadTester()
    analysis = tester.load_test(num_requests=100, max_workers=20)
    tester.print_results(analysis)
    return analysis['success_rate'] >= 0.7


def test_sustained_load():
    """Test sustained load over time."""
    print(f"\n{'='*60}")
    print("=== Sustained Load Test ===")
    tester = SNMPLoadTester()
    
    # Run multiple rounds
    rounds = 3
    round_results = []
    
    for round_num in range(1, rounds + 1):
        print(f"\nRound {round_num}/{rounds}:")
        analysis = tester.load_test(num_requests=30, max_workers=5)
        round_results.append(analysis)
        
        if round_num < rounds:
            print("  Waiting 2 seconds before next round...")
            time.sleep(2)
    
    # Aggregate results
    total_requests = sum(r['total_requests'] for r in round_results)
    total_successful = sum(r['successful_requests'] for r in round_results)
    overall_success_rate = total_successful / total_requests
    
    print(f"\nSustained Load Summary:")
    print(f"  Rounds: {rounds}")
    print(f"  Total requests: {total_requests}")
    print(f"  Total successful: {total_successful}")
    print(f"  Overall success rate: {overall_success_rate:.1%}")
    
    return overall_success_rate >= 0.8


def test_different_oids():
    """Test load with different OIDs."""
    print(f"\n{'='*60}")
    print("=== Different OIDs Test ===")
    
    oids = [
        ("1.3.6.1.2.1.1.1.0", "System Description"),
        ("1.3.6.1.2.1.1.3.0", "System Uptime"),
        ("1.3.6.1.2.1.1.5.0", "System Name"),
    ]
    
    tester = SNMPLoadTester()
    overall_success = True
    
    for oid, description in oids:
        print(f"\nTesting {description} ({oid}):")
        analysis = tester.load_test(num_requests=20, max_workers=5, oid=oid)
        
        print(f"  Success rate: {analysis['success_rate']:.1%}")
        print(f"  Throughput: {analysis['throughput']:.1f} req/sec")
        if analysis['latency_stats']:
            print(f"  Avg latency: {analysis['latency_stats']['mean']:.2f}ms")
        
        if analysis['success_rate'] < 0.8:
            overall_success = False
    
    return overall_success


def main():
    """Run all load tests."""
    print("SNMP Load Testing Example")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if simulator is running
    print("Checking if simulator is running...")
    tester = SNMPLoadTester()
    result = tester.single_request(0)
    
    if not result['success']:
        print("✗ Simulator not responding!")
        print("\nPlease start the Mock SNMP Agent:")
        print("  python mock_snmp_agent.py")
        print("  # or")
        print("  docker-compose up -d")
        sys.exit(1)
    
    print("✓ Simulator is running")
    print()
    
    # Run tests
    tests = [
        ("Basic Load", test_basic_load),
        ("High Concurrency", test_high_concurrency),
        ("Sustained Load", test_sustained_load),
        ("Different OIDs", test_different_oids),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✓ {test_name} test PASSED")
                passed += 1
            else:
                print(f"\n✗ {test_name} test FAILED")
        except Exception as e:
            print(f"\n✗ {test_name} test ERROR: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n🎉 All load tests passed!")
        print("\nRecommendations:")
        print("- Simulator handles concurrent load well")
        print("- Suitable for testing SNMP applications")
        print("- Consider higher loads for stress testing")
        sys.exit(0)
    else:
        print("\n⚠️  Some load tests failed")
        print("\nRecommendations:")
        print("- Check system resources")
        print("- Reduce concurrency levels")
        print("- Monitor simulator logs")
        sys.exit(1)


if __name__ == "__main__":
    main()