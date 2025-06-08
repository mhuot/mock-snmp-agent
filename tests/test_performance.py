"""Performance tests for Mock SNMP Agent."""

import pytest
import subprocess
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestPerformance:
    """Test performance characteristics."""

    def snmp_request(self, request_id, endpoint):
        """Execute a single SNMP request."""
        start_time = time.time()
        try:
            result = subprocess.run(
                [
                    "snmpget",
                    "-v2c",
                    "-c",
                    endpoint["community"],
                    "-t",
                    "1",
                    "-r",
                    "0",
                    f"{endpoint['host']}:{endpoint['port']}",
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

    @pytest.mark.slow
    def test_basic_performance(self, simulator_ready, snmp_endpoint):
        """Test basic performance with small load."""
        num_requests = 10
        max_workers = 3

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.snmp_request, i, snmp_endpoint)
                for i in range(num_requests)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        end_time = time.time()

        # Analyze results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        # Basic assertions
        assert len(successful_results) > 0, "No successful requests"
        success_rate = len(successful_results) / num_requests
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2f}"

        # Performance metrics
        if successful_results:
            latencies = [r["latency_ms"] for r in successful_results]
            avg_latency = statistics.mean(latencies)
            throughput = num_requests / (end_time - start_time)

            # Log results for debugging
            print(f"\nPerformance Results:")
            print(f"  Requests: {num_requests}")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Failed: {len(failed_results)}")
            print(f"  Success rate: {success_rate:.1%}")
            print(f"  Avg latency: {avg_latency:.2f}ms")
            print(f"  Throughput: {throughput:.1f} req/sec")

            # Basic performance requirements
            assert avg_latency < 5000, f"Latency too high: {avg_latency:.2f}ms"
            assert throughput > 1, f"Throughput too low: {throughput:.1f} req/sec"

    @pytest.mark.slow
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-extensive", default=False),
        reason="Need --run-extensive option to run",
    )
    def test_extended_performance(self, simulator_ready, snmp_endpoint):
        """Test performance with higher load (requires --run-extensive)."""
        num_requests = 100
        max_workers = 10

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.snmp_request, i, snmp_endpoint)
                for i in range(num_requests)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        end_time = time.time()

        # Analyze results
        successful_results = [r for r in results if r["success"]]

        assert len(successful_results) > 0, "No successful requests"
        success_rate = len(successful_results) / num_requests
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.2f}"

        if successful_results:
            latencies = [r["latency_ms"] for r in successful_results]
            avg_latency = statistics.mean(latencies)
            throughput = num_requests / (end_time - start_time)

            print(f"\nExtended Performance Results:")
            print(f"  Requests: {num_requests}")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Success rate: {success_rate:.1%}")
            print(f"  Avg latency: {avg_latency:.2f}ms")
            print(f"  Throughput: {throughput:.1f} req/sec")

            # More demanding requirements for extended test
            assert avg_latency < 1000, f"Latency too high: {avg_latency:.2f}ms"
            assert throughput > 10, f"Throughput too low: {throughput:.1f} req/sec"

    def test_concurrent_access(self, simulator_ready, snmp_endpoint):
        """Test concurrent access from multiple clients."""

        def make_requests(client_id, num_requests):
            """Make multiple requests from one client."""
            results = []
            for i in range(num_requests):
                result = self.snmp_request(f"{client_id}-{i}", snmp_endpoint)
                results.append(result)
            return results

        # Simulate 3 clients making 5 requests each
        num_clients = 3
        requests_per_client = 5

        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [
                executor.submit(make_requests, client_id, requests_per_client)
                for client_id in range(num_clients)
            ]

            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Verify all requests
        successful_results = [r for r in all_results if r["success"]]
        total_requests = num_clients * requests_per_client

        assert len(all_results) == total_requests
        success_rate = len(successful_results) / total_requests
        assert (
            success_rate >= 0.8
        ), f"Concurrent access success rate too low: {success_rate:.2f}"


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-extensive",
        action="store_true",
        default=False,
        help="Run extensive performance tests",
    )
