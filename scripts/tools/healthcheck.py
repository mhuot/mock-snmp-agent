#!/usr/bin/env python3
"""
Health check script for Mock SNMP Agent containers.
"""

import os
import subprocess
import sys


def main():
    """Simple health check using snmpget."""
    port = os.environ.get("SNMP_PORT", "11611")

    try:
        result = subprocess.run(
            [
                "snmpget",
                "-v2c",
                "-c",
                "public",
                "-t",
                "3",
                "-r",
                "1",
                f"localhost:{port}",
                "1.3.6.1.2.1.1.1.0",
            ],
            capture_output=True,
            timeout=5,
        )

        if result.returncode == 0:
            sys.exit(0)  # Healthy
        else:
            sys.exit(1)  # Unhealthy

    except Exception:
        sys.exit(1)  # Unhealthy


if __name__ == "__main__":
    main()
