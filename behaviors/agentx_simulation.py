#!/usr/bin/env python3
"""
AgentX-Style Response Simulation

This module simulates AgentX (SNMP Extension Agent) behavior patterns,
including subagent delays, registration timeouts, and master-agent
communication latencies commonly seen in network devices.
"""

import random
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AgentXConfig:
    """Configuration for AgentX-style simulation."""
    
    # Subagent registration delays
    registration_enabled: bool = False
    registration_delay_ms: int = 1000
    registration_timeout_rate: int = 5  # Percentage
    
    # Master agent communication delays
    master_agent_delays: bool = False
    base_delay_ms: int = 200
    timeout_threshold_ms: int = 5000
    
    # Subagent-specific delays by OID tree
    subagent_delays: Dict[str, int] = None
    
    # Connection state simulation
    connection_failures: bool = False
    disconnection_rate: int = 2  # Percentage
    reconnection_delay_ms: int = 3000


class AgentXSimulator:
    """
    Simulates AgentX (SNMP Extension Agent) behavior patterns.
    
    AgentX is commonly used in network devices where different subsystems
    (interfaces, routing, security) are handled by separate subagents that
    register with a master SNMP agent.
    """
    
    def __init__(self, config: AgentXConfig = None):
        """Initialize AgentX simulator.
        
        Args:
            config: AgentX configuration object
        """
        self.config = config or AgentXConfig()
        self.logger = logging.getLogger(__name__)
        
        # Default subagent delay mappings (common network device patterns)
        self.default_subagent_delays = {
            "1.3.6.1.2.1.1": 50,        # System - fast (master agent)
            "1.3.6.1.2.1.2": 200,       # Interfaces - medium delay
            "1.3.6.1.2.1.4": 300,       # IP - medium delay  
            "1.3.6.1.2.1.6": 150,       # TCP - fast
            "1.3.6.1.2.1.7": 150,       # UDP - fast
            "1.3.6.1.2.1.11": 400,      # SNMP stats - slow
            "1.3.6.1.2.1.25": 800,      # Host resources - very slow
            "1.3.6.1.2.1.47": 600,      # Entity MIB - slow (hardware info)
            "1.3.6.1.4.1": 1000,        # Enterprise MIBs - slowest
        }
        
        # Merge with configured delays
        if self.config.subagent_delays:
            self.default_subagent_delays.update(self.config.subagent_delays)
        
        # Subagent state tracking
        self.subagent_states = {}
        self.last_registration_times = {}
        
    def get_agentx_delay(self, oid: str) -> int:
        """Calculate AgentX-style delay for an OID.
        
        Args:
            oid: SNMP OID being queried
            
        Returns:
            Delay in milliseconds
        """
        # Find best matching subagent based on OID prefix
        best_match = ""
        base_delay = self.config.base_delay_ms
        
        for prefix, delay in self.default_subagent_delays.items():
            if oid.startswith(prefix) and len(prefix) > len(best_match):
                best_match = prefix
                base_delay = delay
        
        # Simulate subagent registration delays
        if self.config.registration_enabled:
            if self._is_subagent_registering(best_match):
                registration_delay = self.config.registration_delay_ms
                self.logger.debug(f"AgentX registration delay for {best_match}: {registration_delay}ms")
                return registration_delay
        
        # Simulate connection failures
        if self.config.connection_failures:
            if random.randint(1, 100) <= self.config.disconnection_rate:
                self.logger.debug(f"AgentX subagent disconnection for {best_match}")
                return self.config.reconnection_delay_ms
        
        # Add random variation to simulate real subagent behavior
        variation = random.randint(-50, 200)  # -50ms to +200ms variation
        final_delay = max(10, base_delay + variation)  # Minimum 10ms
        
        # Simulate occasional timeouts
        if self.config.master_agent_delays:
            if random.randint(1, 1000) <= 5:  # 0.5% chance of timeout
                timeout_delay = random.randint(self.config.timeout_threshold_ms, 
                                             self.config.timeout_threshold_ms + 2000)
                self.logger.warning(f"AgentX timeout simulation for {oid}: {timeout_delay}ms")
                return timeout_delay
        
        return final_delay
    
    def _is_subagent_registering(self, subagent_prefix: str) -> bool:
        """Check if a subagent is currently in registration phase.
        
        Args:
            subagent_prefix: OID prefix identifying the subagent
            
        Returns:
            True if subagent is registering
        """
        current_time = time.time()
        
        # Check if this is first access to this subagent
        if subagent_prefix not in self.last_registration_times:
            # Simulate initial registration
            if random.randint(1, 100) <= self.config.registration_timeout_rate:
                self.last_registration_times[subagent_prefix] = current_time
                return True
        
        # Check for re-registration (every 5-10 minutes)
        last_reg = self.last_registration_times.get(subagent_prefix, 0)
        if current_time - last_reg > random.randint(300, 600):  # 5-10 minutes
            if random.randint(1, 100) <= self.config.registration_timeout_rate:
                self.last_registration_times[subagent_prefix] = current_time
                return True
        
        return False
    
    def get_subagent_info(self) -> Dict[str, Dict]:
        """Get information about simulated subagents.
        
        Returns:
            Dictionary with subagent information
        """
        subagent_info = {}
        
        for prefix, delay in self.default_subagent_delays.items():
            subagent_name = self._get_subagent_name(prefix)
            subagent_info[prefix] = {
                "name": subagent_name,
                "base_delay_ms": delay,
                "last_registration": self.last_registration_times.get(prefix),
                "status": "registered" if prefix in self.last_registration_times else "unknown"
            }
        
        return subagent_info
    
    def _get_subagent_name(self, oid_prefix: str) -> str:
        """Get friendly name for subagent based on OID prefix.
        
        Args:
            oid_prefix: OID prefix
            
        Returns:
            Human-readable subagent name
        """
        names = {
            "1.3.6.1.2.1.1": "System Agent",
            "1.3.6.1.2.1.2": "Interface Agent", 
            "1.3.6.1.2.1.4": "IP Agent",
            "1.3.6.1.2.1.6": "TCP Agent",
            "1.3.6.1.2.1.7": "UDP Agent",
            "1.3.6.1.2.1.11": "SNMP Agent",
            "1.3.6.1.2.1.25": "Host Resources Agent",
            "1.3.6.1.2.1.47": "Entity Agent",
            "1.3.6.1.4.1": "Enterprise Agent",
        }
        return names.get(oid_prefix, f"Subagent {oid_prefix}")
    
    def simulate_subagent_restart(self, oid_prefix: str = None):
        """Simulate a subagent restart.
        
        Args:
            oid_prefix: Specific subagent to restart, or None for random
        """
        if oid_prefix is None:
            # Pick random subagent
            oid_prefix = random.choice(list(self.default_subagent_delays.keys()))
        
        if oid_prefix in self.last_registration_times:
            del self.last_registration_times[oid_prefix]
        
        self.logger.info(f"Simulated restart of subagent: {self._get_subagent_name(oid_prefix)}")
    
    def generate_snmprec_entries(self) -> List[str]:
        """Generate .snmprec entries for AgentX simulation.
        
        Returns:
            List of .snmprec format entries
        """
        entries = []
        
        # Add entries that demonstrate different subagent delays
        entries.extend([
            "# AgentX Subagent Simulation Data",
            "# System Agent (fast response)",
            "1.3.6.1.2.1.1.1.0|4|Router with AgentX subagents",
            "1.3.6.1.2.1.1.3.0|67|12345600",
            "",
            "# Interface Agent (medium delay)",
            "1.3.6.1.2.1.2.1.0|2|24",
            "1.3.6.1.2.1.2.2.1.1.1|2|1",
            "1.3.6.1.2.1.2.2.1.2.1|4|FastEthernet0/1",
            "1.3.6.1.2.1.2.2.1.10.1|65|1234567890",
            "",
            "# Host Resources Agent (slow response)",
            "1.3.6.1.2.1.25.1.1.0|67|12345600",
            "1.3.6.1.2.1.25.2.2.0|2|4",
            "",
            "# Enterprise Agent (very slow)",
            "1.3.6.1.4.1.9.2.1.1.0|4|Cisco IOS Software",
            "1.3.6.1.4.1.9.2.1.8.0|2|1",
        ])
        
        return entries


def create_agentx_config(
    registration_delays: bool = True,
    connection_failures: bool = False,
    custom_delays: Dict[str, int] = None
) -> AgentXConfig:
    """Create AgentX configuration with common settings.
    
    Args:
        registration_delays: Enable subagent registration delays
        connection_failures: Enable connection failure simulation
        custom_delays: Custom delay mappings by OID prefix
        
    Returns:
        AgentX configuration object
    """
    return AgentXConfig(
        registration_enabled=registration_delays,
        registration_delay_ms=1500,
        registration_timeout_rate=10,
        master_agent_delays=True,
        base_delay_ms=100,
        connection_failures=connection_failures,
        disconnection_rate=3,
        reconnection_delay_ms=2000,
        subagent_delays=custom_delays or {}
    )


# Example usage and testing
if __name__ == "__main__":
    # Example: Create AgentX simulator
    config = create_agentx_config(
        registration_delays=True,
        connection_failures=True,
        custom_delays={
            "1.3.6.1.4.1.9": 2000,  # Cisco enterprise MIB - very slow
            "1.3.6.1.2.1.47": 1500, # Entity MIB - slow hardware queries
        }
    )
    
    simulator = AgentXSimulator(config)
    
    # Test different OIDs
    test_oids = [
        "1.3.6.1.2.1.1.1.0",      # System - should be fast
        "1.3.6.1.2.1.2.2.1.10.1", # Interface - medium delay
        "1.3.6.1.2.1.25.1.1.0",   # Host resources - slow
        "1.3.6.1.4.1.9.2.1.1.0",  # Cisco enterprise - very slow
    ]
    
    print("AgentX Delay Simulation Test:")
    print("=" * 40)
    
    for oid in test_oids:
        delay = simulator.get_agentx_delay(oid)
        print(f"OID {oid}: {delay}ms delay")
    
    print("\nSubagent Information:")
    print("=" * 40)
    
    for prefix, info in simulator.get_subagent_info().items():
        print(f"{info['name']} ({prefix}): {info['base_delay_ms']}ms base delay")