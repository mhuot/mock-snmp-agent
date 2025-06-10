"""Basic functionality tests for Mock SNMP Agent."""

import subprocess
import time

import pytest


class TestBasicSNMP:
    """Test basic SNMP functionality."""

    def test_snmpv1_get(self, simulator_ready, snmp_endpoint):
        """Test SNMPv1 GET operation."""
        result = subprocess.run(
            [
                "snmpget",
                "-v1",
                "-c",
                snmp_endpoint["community"],
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"SNMPv1 GET failed: {result.stderr}"
        assert "SNMPv2-MIB::sysDescr.0" in result.stdout

    def test_snmpv2c_get(self, simulator_ready, snmp_endpoint):
        """Test SNMPv2c GET operation."""
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                snmp_endpoint["community"],
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"SNMPv2c GET failed: {result.stderr}"
        assert "SNMPv2-MIB::sysDescr.0" in result.stdout

    def test_snmpv2c_getnext(self, simulator_ready, snmp_endpoint):
        """Test SNMPv2c GETNEXT operation."""
        result = subprocess.run(
            [
                "snmpgetnext",
                "-v2c",
                "-c",
                snmp_endpoint["community"],
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"SNMPv2c GETNEXT failed: {result.stderr}"
        assert "SNMPv2-MIB::sysDescr.0" in result.stdout

    def test_snmpv2c_getbulk(self, simulator_ready, snmp_endpoint):
        """Test SNMPv2c GETBULK operation."""
        result = subprocess.run(
            [
                "snmpbulkget",
                "-v2c",
                "-c",
                snmp_endpoint["community"],
                "-Cn0",
                "-Cr3",
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"SNMPv2c GETBULK failed: {result.stderr}"
        # Should get multiple OIDs back
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 3, "GETBULK should return multiple OIDs"

    def test_snmpv3_noauth(self, simulator_ready, snmp_endpoint):
        """Test SNMPv3 with no authentication."""
        result = subprocess.run(
            [
                "snmpget",
                "-v3",
                "-l",
                "noAuthNoPriv",
                "-u",
                "simulator",
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"SNMPv3 noAuth failed: {result.stderr}"
        assert "SNMPv2-MIB::sysDescr.0" in result.stdout

    def test_invalid_community(self, simulator_ready, snmp_endpoint):
        """Test with invalid community string."""
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "invalid_community",
                "-t",
                "2",
                "-r",
                "1",  # Short timeout for faster test
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should timeout or return no response
        assert result.returncode != 0, "Invalid community should fail"

    def test_invalid_oid(self, simulator_ready, snmp_endpoint):
        """Test with non-existent OID."""
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                snmp_endpoint["community"],
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.999.999.999.0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should return "No Such Instance" or similar
        assert result.returncode == 0  # Command succeeds but returns no such instance
        assert "No Such Instance" in result.stdout or "No Such Object" in result.stdout


class TestVariationModules:
    """Test variation module functionality."""

    def test_delay_variation(self, simulator_ready, snmp_endpoint):
        """Test delay variation module."""
        start_time = time.time()

        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "variation/delay",
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.2.2.1.6.1",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        end_time = time.time()
        duration = end_time - start_time

        assert result.returncode == 0, f"Delay variation failed: {result.stderr}"
        # Should take more than 0.5 seconds due to delay simulation
        assert duration > 0.5, f"Expected delay but took only {duration:.2f}s"

    def test_error_variation(self, simulator_ready, snmp_endpoint):
        """Test error variation module."""
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "variation/error",
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.2.2.1.1.1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should return an error response or timeout
        assert result.returncode != 0 or "Error" in result.stderr

    def test_writecache_variation(self, simulator_ready, snmp_endpoint):
        """Test writecache variation module."""
        # Test SET operation
        set_result = subprocess.run(
            [
                "snmpset",
                "-v2c",
                "-c",
                "variation/writecache",
                f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                "1.3.6.1.2.1.1.1.0",
                "s",
                "Test Description",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if set_result.returncode == 0:  # SET succeeded
            # Verify the set value with GET
            get_result = subprocess.run(
                [
                    "snmpget",
                    "-v2c",
                    "-c",
                    "variation/writecache",
                    f"{snmp_endpoint['host']}:{snmp_endpoint['port']}",
                    "1.3.6.1.2.1.1.1.0",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert get_result.returncode == 0
            assert "Test Description" in get_result.stdout
