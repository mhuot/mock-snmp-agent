#!/usr/bin/env python3
"""
Counter wrap demonstration for Mock SNMP Agent.

This example demonstrates the critical counter wrap testing capability,
which is one of the most important SNMP monitoring challenges.
"""

import subprocess
import time
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_counter_wrap_scenario():
    """Test counter wrap scenario with different interface speeds."""
    print("Counter Wrap Testing - The Most Critical SNMP Test")
    print("=" * 55)
    print()
    print("Counter wraps are a major cause of SNMP monitoring failures.")
    print("32-bit counters wrap at 4,294,967,295 and reset to 0.")
    print()
    print("Real-world wrap times:")
    print("  10 Mbps interface:  57.2 minutes")
    print("  100 Mbps interface: 5.7 minutes") 
    print("  1 Gbps interface:   34 seconds")
    print("  10 Gbps interface:  3.4 seconds")
    print()
    print("This demo uses 1000x acceleration for fast testing:")
    print("  10 Mbps:  3.4 seconds")
    print("  100 Mbps: 0.34 seconds")
    print("  1 Gbps:   0.034 seconds") 
    print("  10 Gbps:  0.0034 seconds")
    print()
    
    # Create counter wrap configuration
    config_content = """
simulation:
  behaviors:
    counter_wrap:
      enabled: true
      acceleration_factor: 1000
      interface_count: 4
      interface_speeds: ["10M", "100M", "1G", "10G"]
"""
    
    config_file = Path("config/counter_wrap_test.yaml")
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Starting agent with counter wrap simulation...")
    
    # Start agent with counter wrap config
    cmd = [
        sys.executable, "mock_snmp_agent.py",
        "--config", str(config_file),
        "--port", "11617",
        "--quiet"
    ]
    
    agent = subprocess.Popen(cmd)
    
    try:
        time.sleep(2)  # Let agent start
        
        print("\nTesting counter values over time...")
        print("Interface speeds: 10M, 100M, 1G, 10G")
        print("Time | Interface 1 (10M) | Interface 2 (100M) | Interface 3 (1G) | Interface 4 (10G)")
        print("-" * 85)
        
        start_time = time.time()
        
        for i in range(20):  # Monitor for 20 iterations
            current_time = time.time() - start_time
            
            # Query interface counters (ifInOctets)
            values = []
            for interface in range(1, 5):
                try:
                    result = subprocess.run([
                        "snmpget", "-v2c", "-c", "public", "-t", "1", "-r", "1",
                        "127.0.0.1:11617", f"1.3.6.1.2.1.2.2.1.10.{interface}"
                    ], capture_output=True, text=True, timeout=2)
                    
                    if result.returncode == 0:
                        # Extract counter value
                        output = result.stdout.strip()
                        if "=" in output:
                            value_part = output.split("=")[1].strip()
                            # Remove "Counter32: " prefix if present
                            if ":" in value_part:
                                value = value_part.split(":")[1].strip()
                            else:
                                value = value_part
                            values.append(int(value))
                        else:
                            values.append(0)
                    else:
                        values.append(0)
                        
                except (subprocess.TimeoutExpired, ValueError, IndexError):
                    values.append(0)
            
            # Format output
            print(f"{current_time:4.1f}s | {values[0]:>13,} | {values[1]:>14,} | {values[2]:>11,} | {values[3]:>12,}")
            
            # Check for wraps
            for j, value in enumerate(values):
                if i > 0 and value < 1000000:  # Likely wrapped
                    speed_names = ["10M", "100M", "1G", "10G"]
                    print(f"      *** WRAP DETECTED on Interface {j+1} ({speed_names[j]}) ***")
            
            time.sleep(0.5)  # Check every 0.5 seconds
        
        print("\nCounter wrap testing completed!")
        print("\nKey observations:")
        print("- Fastest interfaces (10G) wrap most frequently")
        print("- Counter values reset to 0 after reaching 4,294,967,295")
        print("- Monitoring systems must detect and handle counter wraps")
        print("- Delta calculations fail without proper wrap detection")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error during demo: {e}")
    finally:
        agent.terminate()
        agent.wait()
        
        # Clean up config file
        if config_file.exists():
            config_file.unlink()


def show_counter_math():
    """Show the mathematics behind counter wraps."""
    print("\nCounter Wrap Mathematics")
    print("=" * 25)
    print()
    print("32-bit counter maximum: 2^32 - 1 = 4,294,967,295")
    print()
    print("Interface Speed Analysis:")
    print()
    
    speeds = {
        "10 Mbps": 10_000_000,
        "100 Mbps": 100_000_000, 
        "1 Gbps": 1_000_000_000,
        "10 Gbps": 10_000_000_000
    }
    
    max_value = 2**32 - 1
    
    for name, bits_per_sec in speeds.items():
        bytes_per_sec = bits_per_sec // 8
        seconds_to_wrap = max_value / bytes_per_sec
        minutes_to_wrap = seconds_to_wrap / 60
        
        print(f"{name:>8}: {bytes_per_sec:>12,} bytes/sec")
        print(f"         Wrap time: {seconds_to_wrap:>7.1f} seconds ({minutes_to_wrap:.1f} minutes)")
        print()


def main():
    """Main demo function."""
    # Check if we have snmpget available
    try:
        subprocess.run(["snmpget", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Error: snmpget command not found!")
        print("Please install net-snmp tools:")
        print("  macOS: brew install net-snmp")
        print("  Ubuntu: sudo apt-get install snmp-utils")
        return 1
    
    show_counter_math()
    print("\n" + "="*60 + "\n")
    test_counter_wrap_scenario()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())