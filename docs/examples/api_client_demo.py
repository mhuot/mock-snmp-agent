#!/usr/bin/env python3
"""
REST API Client Demonstration

This script demonstrates how to use the Mock SNMP Agent REST API
for programmatic control and monitoring.

Usage:
    python examples/api_client_demo.py

Prerequisites:
    - Mock SNMP Agent running with REST API enabled
    - requests library: pip install requests
"""

import json
import sys
import time
from typing import Any, Dict

import requests


class MockSNMPAgentAPIClient:
    """Client for Mock SNMP Agent REST API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", api_key: str = None):
        """Initialize the API client.

        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

        # Set timeouts
        self.session.timeout = 10

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            JSON response data

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e.response, "text"):
                print(f"Response: {e.response.text}")
            raise

    def get_health(self) -> Dict[str, Any]:
        """Get agent health status."""
        return self._make_request("GET", "/health")

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return self._make_request("GET", "/metrics")

    def get_configuration(self) -> Dict[str, Any]:
        """Get current agent configuration."""
        return self._make_request("GET", "/config")

    def update_configuration(self, config_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent configuration.

        Args:
            config_update: Configuration updates to apply

        Returns:
            Updated configuration
        """
        return self._make_request("PUT", "/config", json=config_update)

    def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed agent status."""
        return self._make_request("GET", "/agent/status")

    def restart_agent(
        self, force: bool = False, timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Restart the SNMP agent.

        Args:
            force: Force restart even if agent is healthy
            timeout_seconds: Timeout for restart operation

        Returns:
            Restart operation result
        """
        data = {"force": force, "timeout_seconds": timeout_seconds}
        return self._make_request("POST", "/agent/restart", json=data)

    def get_available_oids(self) -> Dict[str, Any]:
        """Get list of available OIDs."""
        return self._make_request("GET", "/oids/available")

    def get_api_info(self) -> Dict[str, Any]:
        """Get API information."""
        return self._make_request("GET", "/")


def demonstrate_api_usage():
    """Demonstrate various API operations."""
    print("Mock SNMP Agent REST API Demonstration")
    print("=" * 50)

    # Initialize client
    client = MockSNMPAgentAPIClient()

    try:
        # 1. Check API connectivity
        print("\n1. Testing API connectivity...")
        api_info = client.get_api_info()
        print(f"✓ Connected to {api_info['name']} v{api_info['version']}")
        print(f"  Available endpoints: {len(api_info['endpoints'])}")

        # 2. Check agent health
        print("\n2. Checking agent health...")
        health = client.get_health()
        print(f"✓ Agent status: {health['status']}")
        print(f"  Uptime: {health['uptime_seconds']:.1f} seconds")
        print(f"  SNMP endpoint: {health['snmp_endpoint']}")

        # 3. Get current metrics
        print("\n3. Getting performance metrics...")
        metrics = client.get_metrics()
        print(f"✓ Total requests: {metrics['requests_total']}")
        print(f"  Successful: {metrics['requests_successful']}")
        print(f"  Failed: {metrics['requests_failed']}")
        print(f"  Average response time: {metrics['avg_response_time_ms']:.1f}ms")
        print(f"  Current connections: {metrics['current_connections']}")

        # 4. Get agent status
        print("\n4. Getting detailed agent status...")
        status = client.get_agent_status()
        print(f"✓ Agent status: {status['status']}")
        print(f"  Process ID: {status['pid']}")
        print(f"  Data directory: {status['data_directory']}")
        print(f"  Active behaviors: {', '.join(status['active_behaviors']) or 'None'}")

        # 5. Get available OIDs
        print("\n5. Getting available OIDs...")
        oids = client.get_available_oids()
        print(f"✓ Total OIDs available: {oids['total_count']}")
        print(f"  Data sources: {', '.join(oids['data_sources'])}")
        if oids["oids"]:
            print(f"  Sample OIDs: {', '.join(oids['oids'][:5])}")
            if len(oids["oids"]) > 5:
                print(f"    ... and {len(oids['oids']) - 5} more")

        # 6. Get current configuration
        print("\n6. Getting current configuration...")
        config = client.get_configuration()
        print(f"✓ Configuration retrieved (timestamp: {config['timestamp']})")

        behaviors = config["simulation"].get("behaviors", {})
        enabled_behaviors = [
            name
            for name, conf in behaviors.items()
            if isinstance(conf, dict) and conf.get("enabled", False)
        ]
        print(f"  Enabled behaviors: {', '.join(enabled_behaviors) or 'None'}")

        # 7. Demonstrate configuration update
        print("\n7. Testing configuration update...")

        # Enable delay behavior
        config_update = {
            "simulation": {
                "behaviors": {
                    "delay": {"enabled": True, "global_delay": 100, "deviation": 25}
                }
            }
        }

        print("  Enabling delay behavior (100ms ± 25ms)...")
        updated_config = client.update_configuration(config_update)
        print("✓ Configuration updated successfully")

        delay_config = updated_config["simulation"]["behaviors"]["delay"]
        print(f"  Delay enabled: {delay_config['enabled']}")
        print(f"  Global delay: {delay_config['global_delay']}ms")
        print(f"  Deviation: {delay_config['deviation']}ms")

        # 8. Test SNMP request with delay
        print("\n8. Testing SNMP request with new delay...")
        print("  (This would require separate SNMP client to test actual delay)")
        print(
            "  You can test with: snmpget -v2c -c public 127.0.0.1:11611 1.3.6.1.2.1.1.1.0"
        )

        # 9. Disable delay behavior
        print("\n9. Disabling delay behavior...")
        config_update = {"simulation": {"behaviors": {"delay": {"enabled": False}}}}

        client.update_configuration(config_update)
        print("✓ Delay behavior disabled")

        # 10. Final metrics check
        print("\n10. Final metrics check...")
        final_metrics = client.get_metrics()
        print(f"✓ Total requests after demo: {final_metrics['requests_total']}")

        print(f"\n{'='*50}")
        print("🎉 API demonstration completed successfully!")
        print(f"\nAPI Documentation: http://127.0.0.1:8080/docs")
        print(f"Interactive API: http://127.0.0.1:8080/redoc")

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API server!")
        print("\nPlease start the Mock SNMP Agent with REST API enabled:")
        print("  python mock_snmp_agent.py --config config/api_config.yaml")
        return False

    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

    return True


def test_snmpv3_security_api():
    """Demonstrate SNMPv3 security configuration via API."""
    print("\n" + "=" * 50)
    print("SNMPv3 Security Configuration via API")
    print("=" * 50)

    client = MockSNMPAgentAPIClient()

    try:
        # Enable SNMPv3 security failures
        security_config = {
            "simulation": {
                "behaviors": {
                    "snmpv3_security": {
                        "enabled": True,
                        "time_window_failures": {
                            "enabled": True,
                            "clock_skew_seconds": 250,
                            "failure_rate": 20,
                        },
                        "authentication_failures": {
                            "enabled": True,
                            "wrong_credentials_rate": 15,
                        },
                    }
                }
            }
        }

        print("Enabling SNMPv3 security failures...")
        client.update_configuration(security_config)
        print("✓ SNMPv3 security failures enabled")

        # Check updated configuration
        config = client.get_configuration()
        security = config["simulation"]["behaviors"]["snmpv3_security"]

        print(f"  Time window failures: {security['time_window_failures']['enabled']}")
        print(
            f"  Clock skew: {security['time_window_failures']['clock_skew_seconds']} seconds"
        )
        print(f"  Auth failures: {security['authentication_failures']['enabled']}")
        print(
            f"  Wrong credentials rate: {security['authentication_failures']['wrong_credentials_rate']}%"
        )

        print("\nTest SNMPv3 with these commands:")
        print("  # Should work (valid credentials):")
        print(
            "  snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas 127.0.0.1:11611 1.3.6.1.2.1.1.1.0"
        )
        print("  # May fail due to simulated failures:")
        print(
            "  snmpget -v3 -l authNoPriv -u wronguser -a MD5 -A wrongpass 127.0.0.1:11611 1.3.6.1.2.1.1.1.0"
        )

        return True

    except Exception as e:
        print(f"✗ SNMPv3 security configuration failed: {e}")
        return False


def main():
    """Main demonstration function."""
    print("Starting Mock SNMP Agent REST API Client Demo...")

    success = demonstrate_api_usage()

    if success:
        # Also demonstrate SNMPv3 security API
        test_snmpv3_security_api()

    if success:
        print("\n🎉 All API demonstrations completed successfully!")
        return 0
    else:
        print("\n❌ API demonstration failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
