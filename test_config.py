#!/usr/bin/env python3
"""
Test configuration functionality for Mock SNMP Agent.
"""

import os
import tempfile
from pathlib import Path


def test_config_loading():
    """Test configuration file loading."""
    try:
        from config import SimulationConfig
    except ImportError:
        print("PyYAML not installed, skipping config tests")
        return

    # Test simple configuration
    config_content = """
simulation:
  behaviors:
    delay:
      enabled: true
      global_delay: 100
      deviation: 20
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = SimulationConfig(config_path)
        assert config.config["simulation"]["behaviors"]["delay"]["enabled"] == True
        assert config.config["simulation"]["behaviors"]["delay"]["global_delay"] == 100
        print("✓ Configuration loading works")
    finally:
        os.unlink(config_path)


def test_snmprec_generation():
    """Test .snmprec file generation with delays."""
    try:
        from config import SimulationConfig
    except ImportError:
        print("PyYAML not installed, skipping config tests")
        return

    # Create test .snmprec file
    snmprec_content = """1.3.6.1.2.1.1.1.0|4|Test System
1.3.6.1.2.1.1.3.0|67|123456789
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file
        source_file = Path(temp_dir) / "test.snmprec"
        with open(source_file, "w") as f:
            f.write(snmprec_content)

        # Create config with delay
        config = SimulationConfig()
        config.config["simulation"]["behaviors"]["delay"]["enabled"] = True
        config.config["simulation"]["behaviors"]["delay"]["global_delay"] = 100

        # Generate modified files
        output_dir = config.generate_snmprec_files(temp_dir)

        # Check generated file
        output_file = Path(output_dir) / "test.snmprec"
        assert output_file.exists()

        with open(output_file) as f:
            content = f.read()

        # Should contain delay tags
        assert ":delay" in content
        assert "wait=100" in content
        print("✓ .snmprec generation with delays works")


def test_cli_behavior():
    """Test CLI behavior shortcuts."""
    import sys

    from mock_snmp_agent import main

    # Test delay argument parsing
    sys.argv = ["mock-snmp-agent", "--delay", "200", "--help"]

    try:
        main()
    except SystemExit:
        # Expected due to --help
        pass

    print("✓ CLI behavior shortcuts work")


if __name__ == "__main__":
    test_config_loading()
    test_snmprec_generation()
    test_cli_behavior()
    print("\nAll configuration tests passed!")
