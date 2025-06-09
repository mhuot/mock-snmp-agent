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
import time
import threading
import shutil
import atexit
from pathlib import Path

try:
    from config import SimulationConfig
except ImportError:
    SimulationConfig = None


def get_data_dir():
    """Get the data directory path."""
    # Try to find data directory in current working directory
    current_dir = Path.cwd()
    data_dir = current_dir / "data"

    if data_dir.exists():
        return str(data_dir)

    # Default to current directory if no data folder exists
    return str(current_dir)


def run_with_restart(cmd, env, restart_interval, quiet=False):
    """Run simulator with periodic restarts.

    Args:
        cmd: Command to run
        env: Environment variables
        restart_interval: Seconds between restarts
        quiet: Suppress output

    Returns:
        Exit code
    """
    stop_event = threading.Event()
    process = None

    def signal_handler():
        nonlocal process
        stop_event.set()
        if process:
            process.terminate()

    # Set up signal handler
    import signal

    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

    restart_count = 0

    try:
        while not stop_event.is_set():
            if restart_count > 0 and not quiet:
                print(f"\nRestarting agent (restart #{restart_count})...")

            # Start the process
            process = subprocess.Popen(cmd, env=env)

            # Wait for restart interval or stop event
            start_time = time.time()
            while not stop_event.is_set():
                if process.poll() is not None:
                    # Process died unexpectedly
                    if not quiet:
                        print(f"Agent process died with code {process.returncode}")
                    return process.returncode

                elapsed = time.time() - start_time
                if elapsed >= restart_interval:
                    break

                # Check every 0.1 seconds
                time.sleep(0.1)

            if not stop_event.is_set():
                # Time for restart
                if not quiet:
                    print(f"Restart interval reached ({restart_interval}s)")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                restart_count += 1

        # Clean shutdown
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        if not quiet:
            print("\nStopping Mock SNMP Agent...")
        return 0

    except Exception as e:
        print(f"Error in restart handler: {e}")
        if process and process.poll() is None:
            process.kill()
        return 1


def main():
    """Main entry point for mock-snmp-agent command."""
    parser = argparse.ArgumentParser(
        description="Mock SNMP Agent - Easy SNMP simulation for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mock-snmp-agent                          # Start on default port 11611
  mock-snmp-agent --port 1161              # Start on port 1161
  mock-snmp-agent --data-dir ./data        # Use custom data directory
  mock-snmp-agent --config config.yaml     # Use configuration file
  mock-snmp-agent --delay 100              # Add 100ms delay to responses
  mock-snmp-agent --drop-rate 10           # Drop 10% of requests
  mock-snmp-agent --restart-interval 300   # Restart every 5 minutes
  mock-snmp-agent --help                   # Show this help

Simulation behaviors:
  --delay MS                    Add delay to all responses (milliseconds)
  --delay-deviation MS          Random delay variation (+/- milliseconds)
  --drop-rate PERCENT           Drop percentage of requests (0-100)
  --packet-loss PERCENT         Simulate packet loss (0-100)
  --restart-interval SECONDS    Restart agent periodically

SNMPv3 security failure simulation:
  --snmpv3-auth-failures PERCENT     Authentication failures (0-100)
  --snmpv3-clock-skew SECONDS         Time window violations (>150 seconds)
  --snmpv3-engine-failures PERCENT   Engine discovery failures (0-100)

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

    # Configuration file support
    parser.add_argument(
        "--config",
        "-c",
        help="Configuration file (YAML or JSON) for simulation behaviors",
    )

    # Behavior shortcuts (override config file)
    parser.add_argument(
        "--delay",
        type=int,
        metavar="MS",
        help="Add delay to all responses (milliseconds)",
    )

    parser.add_argument(
        "--delay-deviation",
        type=int,
        metavar="MS",
        help="Random delay variation (requires --delay)",
    )

    parser.add_argument(
        "--drop-rate",
        type=float,
        metavar="PERCENT",
        help="Drop percentage of requests (0-100)",
    )

    parser.add_argument(
        "--packet-loss",
        type=float,
        metavar="PERCENT",
        help="Simulate packet loss percentage (0-100)",
    )

    parser.add_argument(
        "--restart-interval",
        type=int,
        metavar="SECONDS",
        help="Restart agent every N seconds",
    )

    # SNMPv3 Security failure options
    parser.add_argument(
        "--snmpv3-auth-failures",
        type=float,
        metavar="PERCENT",
        help="Enable SNMPv3 authentication failures (0-100 percent)",
    )

    parser.add_argument(
        "--snmpv3-clock-skew",
        type=int,
        metavar="SECONDS",
        help="Enable time window violations with clock skew (seconds > 150)",
    )

    parser.add_argument(
        "--snmpv3-engine-failures",
        type=float,
        metavar="PERCENT",
        help="Enable engine discovery failures (0-100 percent)",
    )

    args = parser.parse_args()

    # Load configuration
    config = None
    temp_data_dir = None

    if args.config:
        if not SimulationConfig:
            print("Error: PyYAML not installed. Install with: pip install pyyaml")
            return 1

        try:
            config = SimulationConfig(args.config)
            print(f"Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return 1
    elif any(
        [
            args.delay and args.delay > 0,
            args.drop_rate,
            args.packet_loss,
            args.snmpv3_auth_failures,
            args.snmpv3_clock_skew,
            args.snmpv3_engine_failures,
        ]
    ):
        # Create config from CLI arguments
        if not SimulationConfig:
            print("Error: PyYAML not installed. Install with: pip install pyyaml")
            return 1

        config = SimulationConfig()

        # Apply CLI overrides
        if args.delay is not None and args.delay > 0:
            config.config["simulation"]["behaviors"]["delay"]["enabled"] = True
            config.config["simulation"]["behaviors"]["delay"][
                "global_delay"
            ] = args.delay
            if args.delay_deviation:
                config.config["simulation"]["behaviors"]["delay"][
                    "deviation"
                ] = args.delay_deviation

        if args.drop_rate is not None and args.drop_rate > 0:
            config.config["simulation"]["behaviors"]["drops"]["enabled"] = True
            config.config["simulation"]["behaviors"]["drops"]["rate"] = args.drop_rate

        if args.packet_loss is not None and args.packet_loss > 0:
            config.config["simulation"]["behaviors"]["packet_loss"]["enabled"] = True
            config.config["simulation"]["behaviors"]["packet_loss"][
                "rate"
            ] = args.packet_loss

        # Apply SNMPv3 security failure CLI overrides
        if any(
            [
                args.snmpv3_auth_failures,
                args.snmpv3_clock_skew,
                args.snmpv3_engine_failures,
            ]
        ):
            config.config["simulation"]["behaviors"]["snmpv3_security"][
                "enabled"
            ] = True

            if args.snmpv3_auth_failures is not None and args.snmpv3_auth_failures > 0:
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "authentication_failures"
                ]["enabled"] = True
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "authentication_failures"
                ]["wrong_credentials_rate"] = args.snmpv3_auth_failures

            if args.snmpv3_clock_skew is not None and args.snmpv3_clock_skew > 150:
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "time_window_failures"
                ]["enabled"] = True
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "time_window_failures"
                ]["clock_skew_seconds"] = args.snmpv3_clock_skew

            if (
                args.snmpv3_engine_failures is not None
                and args.snmpv3_engine_failures > 0
            ):
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "engine_discovery_failures"
                ]["enabled"] = True
                config.config["simulation"]["behaviors"]["snmpv3_security"][
                    "engine_discovery_failures"
                ]["wrong_engine_id_rate"] = args.snmpv3_engine_failures

    # Determine data directory
    data_dir = args.data_dir if args.data_dir else get_data_dir()

    # Generate modified .snmprec files if config is provided
    if config:
        temp_data_dir = config.generate_snmprec_files(data_dir)
        data_dir = temp_data_dir
        # Register cleanup
        atexit.register(lambda: shutil.rmtree(temp_data_dir, ignore_errors=True))

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

    # Add config-based CLI arguments
    if config:
        cmd.extend(config.get_cli_args())

    # Set environment to suppress warnings
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"

    print(f"Starting Mock SNMP Agent on {args.host}:{args.port}")
    print(f"Data directory: {data_dir}")

    if config:
        behaviors = config.config["simulation"]["behaviors"]
        enabled = []
        if behaviors["delay"]["enabled"]:
            enabled.append(f"delay ({behaviors['delay']['global_delay']}ms)")
        if behaviors["drops"]["enabled"]:
            enabled.append(f"drops ({behaviors['drops']['rate']}%)")
        if behaviors["packet_loss"]["enabled"]:
            enabled.append(f"packet loss ({behaviors['packet_loss']['rate']}%)")
        if enabled:
            print(f"Behaviors: {', '.join(enabled)}")

    if not args.quiet:
        print(
            "Test with: snmpget -v2c -c public "
            f"{args.host}:{args.port} 1.3.6.1.2.1.1.1.0"
        )
        print("Press Ctrl+C to stop...")

    # Handle restart behavior
    restart_interval = args.restart_interval
    if config and not restart_interval:
        restart_enabled, restart_interval = config.should_restart()
        if not restart_enabled:
            restart_interval = None

    if restart_interval:
        print(f"Agent will restart every {restart_interval} seconds")
        return run_with_restart(cmd, env, restart_interval, args.quiet)
    else:
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
