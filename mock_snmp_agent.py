#!/usr/bin/env python3
"""
Mock SNMP Agent - Main module

This module provides a simple wrapper and entry point for the snmpsim-lextudio
SNMP simulator, making it easier to use as a testing tool.
"""

import sys
import subprocess
import os
import argparse
from pathlib import Path


def get_data_dir():
    """Get the data directory path."""
    # Try to find data directory in current working directory
    current_dir = Path.cwd()
    data_dir = current_dir / "data"

    if data_dir.exists():
        return str(data_dir)

    # Default to current directory if no data folder exists
    return str(current_dir)


def main():
    """Main entry point for mock-snmp-agent command."""
    parser = argparse.ArgumentParser(
        description="Mock SNMP Agent - Easy SNMP simulation for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mock-snmp-agent                     # Start on default port 11611
  mock-snmp-agent --port 1161         # Start on port 1161
  mock-snmp-agent --data-dir ./data   # Use custom data directory
  mock-snmp-agent --debug             # Enable debug output
  mock-snmp-agent --help              # Show this help

For advanced usage, use snmpsim-command-responder directly.
        """,
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=11611,
        help="UDP port to listen on (default: 11611)",
    )

    parser.add_argument(
        "--host",
        "-H",
        default="127.0.0.1",
        help="IP address to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--data-dir",
        "-d",
        default=None,
        help="Directory containing SNMP simulation data",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")

    args = parser.parse_args()

    # Determine data directory
    data_dir = args.data_dir if args.data_dir else get_data_dir()

    # Build command
    cmd = [
        "snmpsim-command-responder",
        f"--data-dir={data_dir}",
        f"--agent-udpv4-endpoint={args.host}:{args.port}",
    ]

    if args.debug:
        cmd.append("--debug=all")
    elif args.quiet:
        cmd.append("--quiet")

    # Set environment to suppress warnings
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"

    print(f"Starting Mock SNMP Agent on {args.host}:{args.port}")
    print(f"Data directory: {data_dir}")

    if not args.quiet:
        print(
            "Test with: snmpget -v2c -c public "
            f"{args.host}:{args.port} 1.3.6.1.2.1.1.1.0"
        )
        print("Press Ctrl+C to stop...")

    try:
        # Run the simulator
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nStopping Mock SNMP Agent...")
        return 0
    except FileNotFoundError:
        print("Error: snmpsim-command-responder not found!")
        print("Please install: pip install snmpsim-lextudio")
        return 1
    except subprocess.SubprocessError as exc:
        print(f"Error starting simulator: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
