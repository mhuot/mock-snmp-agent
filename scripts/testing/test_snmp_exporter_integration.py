#!/usr/bin/env python3
"""
SNMP Exporter Integration Test

Tests the integration between Mock SNMP Agent and Prometheus SNMP Exporter
to validate that all PRD requirements for SNMP monitoring are met.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml


@dataclass
class IntegrationTestResult:
    """Integration test result data structure"""

    test_name: str
    status: str  # PASS, FAIL, SKIP
    details: str
    metrics_collected: int
    duration: float


class SNMPExporterIntegrationTester:
    """Tests Mock SNMP Agent integration with Prometheus SNMP Exporter"""

    def __init__(self):
        self.results: List[IntegrationTestResult] = []
        self.mock_agent_port = 11611
        self.api_port = 8080
        self.exporter_port = 9116
        self.mock_agent_process = None
        self.snmp_exporter_process = None

    def log_result(
        self,
        name: str,
        status: str,
        details: str,
        metrics: int = 0,
        duration: float = 0.0,
    ):
        """Log a test result"""
        result = IntegrationTestResult(name, status, details, metrics, duration)
        self.results.append(result)

        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_icon} {name}: {details}")
        if metrics > 0:
            print(f"   Metrics collected: {metrics}")

    def create_snmp_exporter_config(self) -> str:
        """Create a test snmp.yml configuration for the exporter"""
        config = {
            "auths": {
                "public_v2": {
                    "community": "public",
                    "security_level": "noAuthNoPriv",
                    "auth_protocol": "MD5",
                    "priv_protocol": "DES",
                    "version": 2,
                }
            },
            "modules": {
                "if_mib": {
                    "walk": [
                        "1.3.6.1.2.1.1",  # System MIB
                        "1.3.6.1.2.1.2.2.1",  # Interface MIB
                        "1.3.6.1.2.1.31.1.1",  # ifXTable
                    ],
                    "lookups": [
                        {
                            "old_index": "ifIndex",
                            "new_index": "ifName",
                            "oid": "1.3.6.1.2.1.2.2.1.2",  # ifDescr
                        }
                    ],
                    "overrides": {},
                },
                "system_mib": {
                    "walk": ["1.3.6.1.2.1.1"],
                    "lookups": [],
                    "overrides": {},
                },
                "counter_test": {
                    "walk": [
                        "1.3.6.1.2.1.2.2.1.10",  # ifInOctets
                        "1.3.6.1.2.1.2.2.1.16",  # ifOutOctets
                    ],
                    "lookups": [],
                    "overrides": {},
                },
            },
        }

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config, f, default_flow_style=False)
            return f.name

    def start_mock_agent(self) -> bool:
        """Start the Mock SNMP Agent"""
        print("🚀 Starting Mock SNMP Agent...")

        try:
            cmd = [
                sys.executable,
                "src/mock_snmp_agent.py",
                "--rest-api",
                "--api-port",
                str(self.api_port),
                "--port",
                str(self.mock_agent_port),
                "--config",
                "config/comprehensive.yaml",
            ]

            self.mock_agent_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Wait for agent to start
            for i in range(30):
                try:
                    response = requests.get(
                        f"http://127.0.0.1:{self.api_port}/health", timeout=1
                    )
                    if response.status_code == 200:
                        print("✅ Mock SNMP Agent started")
                        return True
                except:
                    time.sleep(1)

            print("❌ Failed to start Mock SNMP Agent")
            return False

        except Exception as e:
            print(f"❌ Error starting Mock SNMP Agent: {e}")
            return False

    def start_snmp_exporter(self, config_file: str) -> bool:
        """Start the SNMP Exporter"""
        print("🚀 Starting SNMP Exporter...")

        # Check if snmp_exporter is available
        which_result = subprocess.run(["which", "snmp_exporter"], capture_output=True)
        if which_result.returncode != 0:
            # Try to find it in common locations or download
            possible_paths = [
                "./snmp_exporter",
                "../snmp_exporter/snmp_exporter",
                "/usr/local/bin/snmp_exporter",
            ]

            exporter_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    exporter_path = path
                    break

            if not exporter_path:
                print("⚠️ SNMP Exporter not found - downloading...")
                if not self.download_snmp_exporter():
                    return False
                exporter_path = "./snmp_exporter"
        else:
            exporter_path = "snmp_exporter"

        try:
            cmd = [
                exporter_path,
                f"--config.file={config_file}",
                f"--web.listen-address=:{self.exporter_port}",
            ]

            self.snmp_exporter_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Wait for exporter to start
            for i in range(30):
                try:
                    response = requests.get(
                        f"http://127.0.0.1:{self.exporter_port}/metrics", timeout=1
                    )
                    if response.status_code == 200:
                        print("✅ SNMP Exporter started")
                        return True
                except:
                    time.sleep(1)

            print("❌ Failed to start SNMP Exporter")
            return False

        except Exception as e:
            print(f"❌ Error starting SNMP Exporter: {e}")
            return False

    def download_snmp_exporter(self) -> bool:
        """Download SNMP Exporter if not available"""
        try:
            import platform
            import tarfile
            import urllib.request

            # Determine architecture
            system = platform.system().lower()
            machine = platform.machine().lower()

            if machine in ["x86_64", "amd64"]:
                arch = "amd64"
            elif machine in ["arm64", "aarch64"]:
                arch = "arm64"
            else:
                print(f"❌ Unsupported architecture: {machine}")
                return False

            # Download URL
            version = "v0.21.0"  # Use a stable version
            filename = f"snmp_exporter-{version[1:]}.{system}-{arch}.tar.gz"
            url = f"https://github.com/prometheus/snmp_exporter/releases/download/{version}/{filename}"

            print(f"📥 Downloading SNMP Exporter from {url}")
            urllib.request.urlretrieve(url, filename)

            # Extract
            with tarfile.open(filename, "r:gz") as tar:
                tar.extractall()

            # Move binary
            extracted_dir = filename.replace(".tar.gz", "")
            os.rename(f"{extracted_dir}/snmp_exporter", "./snmp_exporter")
            os.chmod("./snmp_exporter", 0o755)

            # Cleanup
            os.remove(filename)
            os.rmdir(extracted_dir)

            print("✅ SNMP Exporter downloaded successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to download SNMP Exporter: {e}")
            return False

    def test_basic_scraping(self) -> None:
        """Test basic SNMP scraping functionality"""
        print("\n🔍 Testing Basic SNMP Scraping...")

        start_time = time.time()
        try:
            # Test system MIB scraping
            url = f"http://127.0.0.1:{self.exporter_port}/snmp?target=127.0.0.1:{self.mock_agent_port}&module=system_mib"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                metrics = response.text
                metric_lines = [
                    line
                    for line in metrics.split("\n")
                    if line and not line.startswith("#")
                ]

                # Check for expected metrics
                expected_metrics = ["snmp_up", "sysDescr", "sysUpTime"]
                found_metrics = []

                for expected in expected_metrics:
                    if any(expected in line for line in metric_lines):
                        found_metrics.append(expected)

                if len(found_metrics) >= 2:  # At least snmp_up and one system metric
                    self.log_result(
                        "Basic Scraping",
                        "PASS",
                        f"Successfully scraped system metrics",
                        len(metric_lines),
                        time.time() - start_time,
                    )
                else:
                    self.log_result(
                        "Basic Scraping",
                        "FAIL",
                        f"Missing expected metrics: {set(expected_metrics) - set(found_metrics)}",
                        len(metric_lines),
                        time.time() - start_time,
                    )
            else:
                self.log_result(
                    "Basic Scraping",
                    "FAIL",
                    f"HTTP error: {response.status_code}",
                    0,
                    time.time() - start_time,
                )

        except Exception as e:
            self.log_result(
                "Basic Scraping", "FAIL", str(e), 0, time.time() - start_time
            )

    def test_interface_metrics(self) -> None:
        """Test interface MIB scraping"""
        print("\n🌐 Testing Interface Metrics...")

        start_time = time.time()
        try:
            url = f"http://127.0.0.1:{self.exporter_port}/snmp?target=127.0.0.1:{self.mock_agent_port}&module=if_mib"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                metrics = response.text
                metric_lines = [
                    line
                    for line in metrics.split("\n")
                    if line and not line.startswith("#")
                ]

                # Check for interface metrics
                interface_metrics = ["ifIndex", "ifDescr", "ifType", "ifOperStatus"]
                found_interface_metrics = []

                for metric in interface_metrics:
                    if any(metric in line for line in metric_lines):
                        found_interface_metrics.append(metric)

                if len(found_interface_metrics) >= 2:
                    self.log_result(
                        "Interface Metrics",
                        "PASS",
                        f"Interface metrics collected: {found_interface_metrics}",
                        len(metric_lines),
                        time.time() - start_time,
                    )
                else:
                    self.log_result(
                        "Interface Metrics",
                        "FAIL",
                        "Insufficient interface metrics collected",
                        len(metric_lines),
                        time.time() - start_time,
                    )
            else:
                self.log_result(
                    "Interface Metrics",
                    "FAIL",
                    f"HTTP error: {response.status_code}",
                    0,
                    time.time() - start_time,
                )

        except Exception as e:
            self.log_result(
                "Interface Metrics", "FAIL", str(e), 0, time.time() - start_time
            )

    def test_counter_progression(self) -> None:
        """Test counter metrics and progression"""
        print("\n📊 Testing Counter Progression...")

        start_time = time.time()
        try:
            # Configure mock agent for counter progression
            config_data = {
                "behaviors": {
                    "counter_wrap": {"enabled": True, "acceleration_factor": 100}
                }
            }

            config_response = requests.post(
                f"http://127.0.0.1:{self.api_port}/api/v1/agents/configure",
                json=config_data,
                timeout=5,
            )

            if config_response.status_code != 200:
                self.log_result(
                    "Counter Progression",
                    "FAIL",
                    "Failed to configure counter behavior",
                    0,
                    time.time() - start_time,
                )
                return

            # Scrape counter metrics multiple times
            url = f"http://127.0.0.1:{self.exporter_port}/snmp?target=127.0.0.1:{self.mock_agent_port}&module=counter_test"

            counter_values = []
            for i in range(3):
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    metrics = response.text
                    # Extract counter values (simplified parsing)
                    for line in metrics.split("\n"):
                        if "ifInOctets" in line and not line.startswith("#"):
                            try:
                                value = float(line.split()[-1])
                                counter_values.append(value)
                                break
                            except:
                                pass
                time.sleep(2)  # Wait between scrapes

            if len(counter_values) >= 2:
                # Check if counters are progressing
                is_progressing = any(
                    counter_values[i] != counter_values[i - 1]
                    for i in range(1, len(counter_values))
                )

                if is_progressing:
                    self.log_result(
                        "Counter Progression",
                        "PASS",
                        f"Counters progressing: {counter_values}",
                        len(counter_values),
                        time.time() - start_time,
                    )
                else:
                    self.log_result(
                        "Counter Progression",
                        "FAIL",
                        f"Counters not progressing: {counter_values}",
                        len(counter_values),
                        time.time() - start_time,
                    )
            else:
                self.log_result(
                    "Counter Progression",
                    "FAIL",
                    "Insufficient counter samples collected",
                    len(counter_values),
                    time.time() - start_time,
                )

        except Exception as e:
            self.log_result(
                "Counter Progression", "FAIL", str(e), 0, time.time() - start_time
            )

    def test_response_time_simulation(self) -> None:
        """Test response time simulation impact"""
        print("\n⏱️ Testing Response Time Simulation...")

        start_time = time.time()
        try:
            # Configure delay behavior
            config_data = {
                "behaviors": {
                    "delay": {
                        "enabled": True,
                        "global_delay": 1000,  # 1 second delay
                        "deviation": 100,
                    }
                }
            }

            config_response = requests.post(
                f"http://127.0.0.1:{self.api_port}/api/v1/agents/configure",
                json=config_data,
                timeout=5,
            )

            if config_response.status_code != 200:
                self.log_result(
                    "Response Time Simulation",
                    "FAIL",
                    "Failed to configure delay behavior",
                    0,
                    time.time() - start_time,
                )
                return

            # Test scraping with delay
            url = f"http://127.0.0.1:{self.exporter_port}/snmp?target=127.0.0.1:{self.mock_agent_port}&module=system_mib"

            scrape_start = time.time()
            response = requests.get(url, timeout=60)
            scrape_duration = time.time() - scrape_start

            if response.status_code == 200 and scrape_duration > 1.0:
                self.log_result(
                    "Response Time Simulation",
                    "PASS",
                    f"Delay simulation working - scrape took {scrape_duration:.2f}s",
                    1,
                    time.time() - start_time,
                )
            else:
                self.log_result(
                    "Response Time Simulation",
                    "FAIL",
                    f"Delay not working - scrape took {scrape_duration:.2f}s",
                    0,
                    time.time() - start_time,
                )

            # Reset delay behavior
            reset_config = {"behaviors": {"delay": {"enabled": False}}}
            requests.post(
                f"http://127.0.0.1:{self.api_port}/api/v1/agents/configure",
                json=reset_config,
            )

        except Exception as e:
            self.log_result(
                "Response Time Simulation", "FAIL", str(e), 0, time.time() - start_time
            )

    def test_bulk_operations(self) -> None:
        """Test GETBULK operations efficiency"""
        print("\n📦 Testing Bulk Operations...")

        start_time = time.time()
        try:
            # Test interface table bulk retrieval
            url = f"http://127.0.0.1:{self.exporter_port}/snmp?target=127.0.0.1:{self.mock_agent_port}&module=if_mib"

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                metrics = response.text
                metric_lines = [
                    line
                    for line in metrics.split("\n")
                    if line and not line.startswith("#")
                ]

                # Check for multiple interface entries
                interface_indices = set()
                for line in metric_lines:
                    if "ifIndex=" in line:
                        try:
                            # Extract interface index from label
                            idx_part = [
                                part for part in line.split(",") if "ifIndex=" in part
                            ][0]
                            idx_value = idx_part.split("=")[1].strip('"')
                            interface_indices.add(idx_value)
                        except:
                            pass

                if len(interface_indices) >= 2:
                    self.log_result(
                        "Bulk Operations",
                        "PASS",
                        f"Bulk retrieval successful - {len(interface_indices)} interfaces",
                        len(metric_lines),
                        time.time() - start_time,
                    )
                else:
                    self.log_result(
                        "Bulk Operations",
                        "FAIL",
                        f"Insufficient bulk data - only {len(interface_indices)} interfaces",
                        len(metric_lines),
                        time.time() - start_time,
                    )
            else:
                self.log_result(
                    "Bulk Operations",
                    "FAIL",
                    f"HTTP error: {response.status_code}",
                    0,
                    time.time() - start_time,
                )

        except Exception as e:
            self.log_result(
                "Bulk Operations", "FAIL", str(e), 0, time.time() - start_time
            )

    def cleanup(self):
        """Clean up processes and temporary files"""
        if self.mock_agent_process:
            try:
                if os.name != "nt":
                    try:
                        os.killpg(
                            os.getpgid(self.mock_agent_process.pid), signal.SIGTERM
                        )
                    except (ProcessLookupError, OSError):
                        pass
                else:
                    self.mock_agent_process.terminate()

                try:
                    self.mock_agent_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name != "nt":
                        try:
                            os.killpg(
                                os.getpgid(self.mock_agent_process.pid), signal.SIGKILL
                            )
                        except (ProcessLookupError, OSError):
                            pass
                    else:
                        self.mock_agent_process.kill()
            except Exception:
                pass

        if self.snmp_exporter_process:
            try:
                if os.name != "nt":
                    try:
                        os.killpg(
                            os.getpgid(self.snmp_exporter_process.pid), signal.SIGTERM
                        )
                    except (ProcessLookupError, OSError):
                        pass
                else:
                    self.snmp_exporter_process.terminate()

                try:
                    self.snmp_exporter_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name != "nt":
                        try:
                            os.killpg(
                                os.getpgid(self.snmp_exporter_process.pid),
                                signal.SIGKILL,
                            )
                        except (ProcessLookupError, OSError):
                            pass
                    else:
                        self.snmp_exporter_process.kill()
            except Exception:
                pass

    def generate_report(self):
        """Generate integration test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])

        print(f"\n📊 SNMP Exporter Integration Test Report")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  • {result.test_name}: {result.details}")

        # Save detailed report
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "details": r.details,
                    "metrics_collected": r.metrics_collected,
                    "duration": r.duration,
                }
                for r in self.results
            ],
        }

        with open("snmp_exporter_integration_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: snmp_exporter_integration_report.json")

        return success_rate >= 80.0  # 80% success rate for integration tests

    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting SNMP Exporter Integration Tests")
        print("=" * 60)

        # Create SNMP exporter config
        config_file = self.create_snmp_exporter_config()

        try:
            # Start services
            if not self.start_mock_agent():
                return False

            if not self.start_snmp_exporter(config_file):
                return False

            # Run integration tests
            self.test_basic_scraping()
            self.test_interface_metrics()
            self.test_counter_progression()
            self.test_response_time_simulation()
            self.test_bulk_operations()

            # Generate report
            return self.generate_report()

        finally:
            # Cleanup
            self.cleanup()
            if os.path.exists(config_file):
                os.unlink(config_file)


def main():
    """Main function"""
    if not Path("src/mock_snmp_agent.py").exists():
        print("❌ src/mock_snmp_agent.py not found. Run from project root directory.")
        return 1

    tester = SNMPExporterIntegrationTester()
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
