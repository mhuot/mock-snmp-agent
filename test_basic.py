#!/usr/bin/env python
"""Simple test to verify basic snmpsim functionality"""

import subprocess
import time
import os

# Start simulator in background
env = os.environ.copy()
env["PYTHONWARNINGS"] = "ignore"

print("Starting SNMP simulator...")
with subprocess.Popen(
    [
        "snmpsim-command-responder",
        "--data-dir=./data",
        "--agent-udpv4-endpoint=127.0.0.1:11611",
        "--quiet",
    ],
    env=env,
) as sim:

    # Give it time to start
    time.sleep(5)

    try:
        print("\nTesting SNMP GET...")
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", "public", "localhost:11611", "1.3.6.1.2.1.1.1.0"],
            capture_output=True,
            text=True,
            check=False,
        )

        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"Return code: {result.returncode}")

    finally:
        print("\nStopping simulator...")
        sim.terminate()
        sim.wait()
        print("Done!")
