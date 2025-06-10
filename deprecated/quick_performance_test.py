#!/usr/bin/env python3
"""
Quick Performance Test for SNMP simulator
Validates basic PRD requirements quickly
"""

import statistics
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def snmp_request(request_id):
    """Execute a single SNMP GET request"""
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
            timeout=3,
            check=False,
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        success = result.returncode == 0 and "STRING:" in result.stdout

        return {"id": request_id, "latency_ms": latency_ms, "success": success}
    except Exception as exc:
        return {
            "id": request_id,
            "latency_ms": 5000,  # Timeout
            "success": False,
            "error": str(exc),
        }


def quick_test(num_requests=50, max_workers=10):
    """Run quick performance test"""
    print(f"Quick Performance Test: {num_requests} requests with {max_workers} workers")
    print("=" * 60)

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(snmp_request, i) for i in range(num_requests)]
        for future in as_completed(futures):
            results.append(future.result())

    end_time = time.time()

    # Analyze results
    successful_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]

    if successful_results:
        latencies = [r["latency_ms"] for r in successful_results]
        throughput = num_requests / (end_time - start_time)
        avg_latency = statistics.mean(latencies)

        print(f"\nResults:")
        print(f"Total requests: {num_requests}")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(failed_results)}")
        print(f"Success rate: {len(successful_results)/num_requests*100:.1f}%")
        print(f"Throughput: {throughput:.1f} req/sec")
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Min latency: {min(latencies):.2f}ms")
        print(f"Max latency: {max(latencies):.2f}ms")

        # PRD requirements check
        print(f"\nPRD Requirements:")
        latency_ok = avg_latency < 10
        print(
            f"Latency target (<10ms): {'✓ PASS' if latency_ok else '✗ FAIL'} ({avg_latency:.2f}ms)"
        )
        print(f"Throughput capability: {throughput:.1f} req/sec")

        if len(successful_results) < num_requests * 0.9:
            print("⚠ Warning: High failure rate detected")

        return {
            "throughput": throughput,
            "avg_latency": avg_latency,
            "success_rate": len(successful_results) / num_requests * 100,
        }
    else:
        print("❌ No successful requests - check if simulator is running!")
        return None


if __name__ == "__main__":
    # Test basic performance
    result = quick_test(num_requests=50, max_workers=10)

    if result and result["success_rate"] > 90:
        print(f"\n✅ Basic performance validated:")
        print(f"   - Latency: {result['avg_latency']:.2f}ms")
        print(f"   - Throughput: {result['throughput']:.1f} req/sec")
        print(f"   - Success rate: {result['success_rate']:.1f}%")
    else:
        print(f"\n❌ Performance test failed or incomplete")
