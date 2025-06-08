#!/usr/bin/env python3
"""
Performance test for SNMP simulator to verify PRD requirements:
- 1000 requests/second throughput
- <10ms latency target
"""

import subprocess
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed


def snmp_request(request_id):
    """Execute a single SNMP GET request and measure latency"""
    start_time = time.time()
    try:
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "public",
                "-t",
                "1",
                "-r",
                "0",
                "127.0.0.1:11611",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        success = result.returncode == 0 and "STRING:" in result.stdout
        return {
            "id": request_id,
            "latency_ms": latency_ms,
            "success": success,
            "error": result.stderr if not success else None,
        }
    except Exception as exc:
        end_time = time.time()
        return {
            "id": request_id,
            "latency_ms": (end_time - start_time) * 1000,
            "success": False,
            "error": str(exc),
        }


def performance_test(num_requests=100, max_workers=20):
    """Run performance test with specified parameters"""
    print(
        f"Performance Test: {num_requests} requests with {max_workers} concurrent workers"
    )
    print("=" * 60)

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        futures = [executor.submit(snmp_request, i) for i in range(num_requests)]

        # Collect results
        for future in as_completed(futures):
            results.append(future.result())

    end_time = time.time()

    # Analyze results
    successful_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]

    if successful_results:
        latencies = [r["latency_ms"] for r in successful_results]

        print("\nResults Summary:")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(failed_results)}")
        print(f"Success rate: {len(successful_results)/num_requests*100:.1f}%")
        print(f"Total time: {end_time - start_time:.2f}s")
        print(f"Throughput: {num_requests/(end_time - start_time):.1f} req/sec")

        print("\nLatency Statistics:")
        print(f"Mean: {statistics.mean(latencies):.2f}ms")
        print(f"Median: {statistics.median(latencies):.2f}ms")
        print(f"Min: {min(latencies):.2f}ms")
        print(f"Max: {max(latencies):.2f}ms")
        print(f"Std Dev: {statistics.stdev(latencies):.2f}ms")

        # Check PRD requirements
        print("\nPRD Requirements Check:")
        throughput = num_requests / (end_time - start_time)
        avg_latency = statistics.mean(latencies)
        throughput_pass = "✓ PASS" if throughput >= 1000 else "✗ FAIL"
        latency_pass = "✓ PASS" if avg_latency < 10 else "✗ FAIL"
        print(
            f"✓ Throughput target (1000 req/sec): {throughput_pass} ({throughput:.1f} req/sec)"
        )
        print(f"✓ Latency target (<10ms): {latency_pass} ({avg_latency:.2f}ms avg)")

        if failed_results:
            print("\nFirst 5 Errors:")
            for i, result in enumerate(failed_results[:5]):
                print(f"  {i+1}. Request {result['id']}: {result['error']}")
    else:
        print("No successful requests - check if simulator is running!")


if __name__ == "__main__":
    print("SNMP Simulator Performance Test")
    print("PRD Requirements: 1000 req/sec throughput, <10ms latency")
    print()

    # Run performance test
    performance_test(num_requests=100, max_workers=20)
