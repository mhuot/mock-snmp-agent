#!/usr/bin/env python3
"""
Test suite for SNMPv3 Security Failure Simulation

This module tests the SNMPv3 security failure simulation functionality
including configuration, failure generation, and integration.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules to test
from behaviors.snmpv3_security import (
    SNMPv3SecuritySimulator,
    SecurityFailureConfig,
    create_security_config_from_dict,
)


class TestSecurityFailureConfig:
    """Test SecurityFailureConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SecurityFailureConfig()

        assert config.time_window_enabled is False
        assert config.clock_skew_seconds == 200
        assert config.time_window_failure_rate == 15

        assert config.auth_failures_enabled is False
        assert config.wrong_credentials_rate == 10
        assert config.unsupported_auth_rate == 5
        assert config.unknown_user_rate == 8

        assert config.privacy_failures_enabled is False
        assert config.decryption_error_rate == 7
        assert config.unsupported_privacy_rate == 3

        assert config.engine_failures_enabled is False
        assert config.wrong_engine_id_rate == 12
        assert config.boot_counter_issues_rate == 5

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SecurityFailureConfig(
            time_window_enabled=True,
            clock_skew_seconds=300,
            auth_failures_enabled=True,
            wrong_credentials_rate=25,
        )

        assert config.time_window_enabled is True
        assert config.clock_skew_seconds == 300
        assert config.auth_failures_enabled is True
        assert config.wrong_credentials_rate == 25

        # Defaults should still apply
        assert config.time_window_failure_rate == 15
        assert config.privacy_failures_enabled is False


class TestCreateSecurityConfigFromDict:
    """Test configuration creation from dictionary."""

    def test_empty_dict(self):
        """Test with empty dictionary."""
        config = create_security_config_from_dict({})

        # Should use all defaults
        assert config.time_window_enabled is False
        assert config.auth_failures_enabled is False
        assert config.privacy_failures_enabled is False
        assert config.engine_failures_enabled is False

    def test_full_config_dict(self):
        """Test with complete configuration dictionary."""
        config_dict = {
            "snmpv3_security": {
                "time_window_failures": {
                    "enabled": True,
                    "clock_skew_seconds": 250,
                    "failure_rate": 20,
                },
                "authentication_failures": {
                    "enabled": True,
                    "wrong_credentials_rate": 15,
                    "unsupported_auth_rate": 8,
                    "unknown_user_rate": 12,
                },
                "privacy_failures": {
                    "enabled": True,
                    "decryption_error_rate": 10,
                    "unsupported_privacy_rate": 5,
                },
                "engine_discovery_failures": {
                    "enabled": True,
                    "wrong_engine_id_rate": 18,
                    "boot_counter_issues_rate": 7,
                },
            }
        }

        config = create_security_config_from_dict(config_dict)

        assert config.time_window_enabled is True
        assert config.clock_skew_seconds == 250
        assert config.time_window_failure_rate == 20

        assert config.auth_failures_enabled is True
        assert config.wrong_credentials_rate == 15
        assert config.unsupported_auth_rate == 8
        assert config.unknown_user_rate == 12

        assert config.privacy_failures_enabled is True
        assert config.decryption_error_rate == 10
        assert config.unsupported_privacy_rate == 5

        assert config.engine_failures_enabled is True
        assert config.wrong_engine_id_rate == 18
        assert config.boot_counter_issues_rate == 7

    def test_partial_config_dict(self):
        """Test with partial configuration dictionary."""
        config_dict = {
            "snmpv3_security": {
                "time_window_failures": {"enabled": True, "failure_rate": 25}
            }
        }

        config = create_security_config_from_dict(config_dict)

        assert config.time_window_enabled is True
        assert config.time_window_failure_rate == 25
        assert config.clock_skew_seconds == 200  # Default

        # Other sections should use defaults
        assert config.auth_failures_enabled is False
        assert config.privacy_failures_enabled is False
        assert config.engine_failures_enabled is False


class TestSNMPv3SecuritySimulator:
    """Test SNMPv3SecuritySimulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.default_config = SecurityFailureConfig()
        self.enabled_config = SecurityFailureConfig(
            time_window_enabled=True,
            auth_failures_enabled=True,
            privacy_failures_enabled=True,
            engine_failures_enabled=True,
        )

    def test_initialization(self):
        """Test simulator initialization."""
        simulator = SNMPv3SecuritySimulator(self.default_config)

        assert simulator.config == self.default_config
        assert "time_window" in simulator.error_codes
        assert "auth_failure" in simulator.error_codes
        assert simulator.error_codes["time_window"] == "notInTimeWindow"

    def test_should_trigger_failure_disabled(self):
        """Test failure triggering when failures are disabled."""
        simulator = SNMPv3SecuritySimulator(self.default_config)

        # All failure types should be disabled
        assert not simulator.should_trigger_failure("time_window", 100)
        assert not simulator.should_trigger_failure("auth", 100)
        assert not simulator.should_trigger_failure("privacy", 100)
        assert not simulator.should_trigger_failure("engine", 100)

    @patch("behaviors.snmpv3_security.random.randint")
    def test_should_trigger_failure_enabled(self, mock_randint):
        """Test failure triggering when failures are enabled."""
        simulator = SNMPv3SecuritySimulator(self.enabled_config)

        # Mock random to always trigger failure
        mock_randint.return_value = 1

        assert simulator.should_trigger_failure("time_window", 15)
        assert simulator.should_trigger_failure("auth", 10)
        assert simulator.should_trigger_failure("privacy", 7)
        assert simulator.should_trigger_failure("engine", 12)

        # Mock random to never trigger failure
        mock_randint.return_value = 100

        assert not simulator.should_trigger_failure("time_window", 15)
        assert not simulator.should_trigger_failure("auth", 10)

    def test_generate_time_window_failure_disabled(self):
        """Test time window failure generation when disabled."""
        simulator = SNMPv3SecuritySimulator(self.default_config)

        result = simulator.generate_time_window_failure("1.3.6.1.2.1.1.1.0")
        assert result is None

    @patch("behaviors.snmpv3_security.random.randint")
    def test_generate_time_window_failure_enabled(self, mock_randint):
        """Test time window failure generation when enabled."""
        config = SecurityFailureConfig(time_window_enabled=True)
        simulator = SNMPv3SecuritySimulator(config)

        # Mock to trigger failure
        mock_randint.return_value = 1

        result = simulator.generate_time_window_failure("1.3.6.1.2.1.1.1.0")

        assert result is not None
        assert "1.3.6.1.2.1.1.1.0" in result
        assert "error" in result
        assert "notInTimeWindow" in result

    @patch("behaviors.snmpv3_security.random.randint")
    def test_generate_auth_failure_enabled(self, mock_randint):
        """Test authentication failure generation when enabled."""
        config = SecurityFailureConfig(auth_failures_enabled=True)
        simulator = SNMPv3SecuritySimulator(config)

        # Mock to trigger failure
        mock_randint.return_value = 1

        result = simulator.generate_auth_failure("1.3.6.1.2.1.1.1.0")

        assert result is not None
        assert "1.3.6.1.2.1.1.1.0" in result
        assert "error" in result
        # Should contain one of the auth error types
        assert any(
            error in result
            for error in ["authenticationFailure", "wrongDigest", "unknownUserName"]
        )

    @patch("behaviors.snmpv3_security.random.randint")
    def test_generate_privacy_failure_enabled(self, mock_randint):
        """Test privacy failure generation when enabled."""
        config = SecurityFailureConfig(privacy_failures_enabled=True)
        simulator = SNMPv3SecuritySimulator(config)

        # Mock to trigger failure
        mock_randint.return_value = 1

        result = simulator.generate_privacy_failure("1.3.6.1.2.1.1.1.0")

        assert result is not None
        assert "1.3.6.1.2.1.1.1.0" in result
        assert "error" in result
        # Should contain one of the privacy error types
        assert any(error in result for error in ["decryptionError", "wrongLength"])

    @patch("behaviors.snmpv3_security.random.randint")
    def test_generate_engine_failure_enabled(self, mock_randint):
        """Test engine discovery failure generation when enabled."""
        config = SecurityFailureConfig(engine_failures_enabled=True)
        simulator = SNMPv3SecuritySimulator(config)

        # Mock to trigger failure
        mock_randint.return_value = 1

        result = simulator.generate_engine_failure("1.3.6.1.2.1.1.1.0")

        assert result is not None
        assert "1.3.6.1.2.1.1.1.0" in result
        assert "error" in result
        assert "unknownEngineID" in result

    def test_generate_security_failures(self):
        """Test security failure generation for multiple OIDs."""
        config = SecurityFailureConfig(
            time_window_enabled=True, time_window_failure_rate=100  # Always trigger
        )
        simulator = SNMPv3SecuritySimulator(config)

        test_oids = ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0", "1.3.6.1.2.1.1.3.0"]

        with patch("behaviors.snmpv3_security.random.randint", return_value=1):
            failures = simulator.generate_security_failures(test_oids)

        # Should generate failures for all OIDs
        assert len(failures) >= len(test_oids)

        # All failures should be valid .snmprec format
        for failure in failures:
            parts = failure.split("|")
            assert len(parts) == 3
            assert parts[0] in test_oids  # OID should be from test set
            assert "error" in parts[1]  # Should be error tag

    def test_create_security_test_data(self):
        """Test security test data file creation."""
        config = SecurityFailureConfig(time_window_enabled=True)
        simulator = SNMPv3SecuritySimulator(config)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".snmprec", delete=False
        ) as f:
            temp_file = f.name

        try:
            with patch("behaviors.snmpv3_security.random.randint", return_value=1):
                simulator.create_security_test_data(temp_file)

            # Verify file was created
            assert Path(temp_file).exists()

            # Read and verify content
            with open(temp_file, "r") as f:
                content = f.read()

            # Should contain header comments
            assert "SNMPv3 Security Failure Test Data" in content

            # Should contain both normal and failure entries
            lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]
            assert len(lines) > 0

            # Verify .snmprec format
            for line in lines:
                if "|" in line:
                    parts = line.split("|")
                    assert len(parts) == 3

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_get_security_statistics(self):
        """Test security statistics generation."""
        config = SecurityFailureConfig(
            time_window_enabled=True,
            auth_failures_enabled=True,
            privacy_failures_enabled=False,
            engine_failures_enabled=True,
        )
        simulator = SNMPv3SecuritySimulator(config)

        stats = simulator.get_security_statistics()

        assert "enabled_failures" in stats
        assert "failure_rates" in stats
        assert "total_failure_types" in stats

        # Should show 3 enabled failure types
        assert stats["total_failure_types"] == 3
        assert "time_window_violations" in stats["enabled_failures"]
        assert "authentication_failures" in stats["enabled_failures"]
        assert "engine_discovery_failures" in stats["enabled_failures"]
        assert "privacy_failures" not in stats["enabled_failures"]

        # Should have failure rates for enabled types
        assert "time_window" in stats["failure_rates"]
        assert "auth" in stats["failure_rates"]
        assert "engine" in stats["failure_rates"]


class TestIntegration:
    """Integration tests for SNMPv3 security simulation."""

    def test_full_configuration_integration(self):
        """Test complete configuration and simulation flow."""
        config_dict = {
            "snmpv3_security": {
                "time_window_failures": {
                    "enabled": True,
                    "clock_skew_seconds": 300,
                    "failure_rate": 20,
                },
                "authentication_failures": {
                    "enabled": True,
                    "wrong_credentials_rate": 15,
                },
            }
        }

        # Create config from dict
        config = create_security_config_from_dict(config_dict)

        # Create simulator
        simulator = SNMPv3SecuritySimulator(config)

        # Test statistics
        stats = simulator.get_security_statistics()
        assert stats["total_failure_types"] == 2

        # Test failure generation
        test_oids = ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.2.0"]

        with patch("behaviors.snmpv3_security.random.randint", return_value=1):
            failures = simulator.generate_security_failures(test_oids)

        # Should generate some failures
        assert len(failures) > 0

        # Verify failure format
        for failure in failures:
            parts = failure.split("|")
            assert len(parts) == 3
            assert parts[0] in test_oids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
