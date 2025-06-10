#!/usr/bin/env python3
"""
ifXTable simulation for Mock SNMP Agent.

This module provides comprehensive ifXTable (RFC 2233) simulation with
64-bit high capacity counters and enhanced interface attributes.
"""

import time
import random
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .counter_wrap import CounterConfig, CounterWrapSimulator


class InterfaceType(Enum):
    """Standard interface types from IANAifType-MIB."""

    OTHER = 1
    REGULAR1822 = 2
    HDH1822 = 3
    DDNX25 = 4
    RFC877X25 = 5
    ETHERNET_CSMACD = 6
    ISO88023_CSMACD = 7
    ISO88024_TOKENBUS = 8
    ISO88025_TOKENRING = 9
    ISO88026_MAN = 10
    STARLAN = 11
    PROTEON_10MBIT = 12
    PROTEON_80MBIT = 13
    HYPERCHANNEL = 14
    FDDI = 15
    LAPB = 16
    SDLC = 17
    DS1 = 18
    E1 = 19
    BASICISDN = 20
    PRIMARYISDN = 21
    PROPPOINTTOPOINTSERIAL = 22
    PPP = 23
    SOFTWARELOOPBACK = 24
    EON = 25
    ETHERNET_3MBIT = 26
    NSIP = 27
    SLIP = 28
    ULTRA = 29
    DS3 = 30
    SIP = 31
    FRAMERELAY = 32
    RS232 = 33
    PARA = 34
    ARCNET = 35
    ARCNETPLUS = 36
    ATM = 37
    MIOX25 = 38
    SONET = 39
    X25PLE = 40
    ISO88022LLC = 41
    LOCALTALK = 42
    SMDSDXI = 43
    FRAMERELAYSERVICE = 44
    V35 = 45
    HSSI = 46
    HIPPI = 47
    MODEM = 48
    AAL5 = 49
    SONETPATH = 50
    SONETVT = 51
    SMDSICIP = 52
    PROPVIRTUAL = 53
    PROPMULTIPLEXOR = 54
    IEEE80212 = 55
    FIBRECHANNEL = 56
    HIPPIINTERFACE = 57
    FRAMERELAYINTERCONNECT = 58
    AFLANE8023 = 59
    AFLANE8025 = 60
    CCTEMUL = 61
    FASTETHER = 62
    ISDN = 63
    V11 = 64
    V36 = 65
    G703AT64K = 66
    G703AT2MB = 67
    QLLC = 68
    FASTETHERFX = 69
    CHANNEL = 70
    IEEE80211 = 71
    IBM370PARCHAN = 72
    ESCON = 73
    DLSW = 74
    ISDNS = 75
    ISDNU = 76
    LAPD = 77
    IPSWITCH = 78
    RSRB = 79
    ATMLOGICAL = 80
    DS0 = 81
    DS0BUNDLE = 82
    BSC = 83
    ASYNC = 84
    CNR = 85
    ISO88025DTR = 86
    EPLRS = 87
    ARAP = 88
    PROPCNLS = 89
    HOSTPAD = 90
    TERMPAD = 91
    FRAMERELAYMPI = 92
    X213 = 93
    ADSL = 94
    RADSL = 95
    SDSL = 96
    VDSL = 97
    ISO88025CRFPINT = 98
    MYRINET = 99
    VOICEEM = 100
    VOICEFXO = 101
    VOICEFXS = 102
    VOICEENCAP = 103
    VOICEOVERIP = 104
    ATMDXI = 105
    ATMFUNI = 106
    ATMIMA = 107
    PPPMULTILINKBUNDLE = 108
    IPOVERCDLC = 109
    IPOVERCLAW = 110
    STACKTOSTACK = 111
    VIRTUALIPADDRESS = 112
    MPC = 113
    IPOVERATM = 114
    ISO88025FIBER = 115
    TDLC = 116
    GIGABITETHERNET = 117
    HDLC = 118
    LAPF = 119
    V37 = 120
    X25MLP = 121
    X25HUNTGROUP = 122
    TRASNPHDLC = 123
    INTERLEAVE = 124
    FAST = 125
    IP = 126
    DOCSCABLEMACLAYER = 127
    DOCSCABLEDOWNSTREAM = 128
    DOCSCABLEUPSTREAM = 129
    A12MPPSWITCH = 130
    TUNNEL = 131
    COFFEE = 132
    CES = 133
    ATMSUBINTERFACE = 134
    L2VLAN = 135
    L3IPVLAN = 136
    L3IPXVLAN = 137
    DIGITALPOWERLINE = 138
    MEDIAMAILOVERIP = 139
    DTM = 140
    DCN = 141
    IPFORWARD = 142
    MSDSL = 143
    IEEE1394 = 144


class AdminStatus(Enum):
    """Interface administrative status."""

    UP = 1
    DOWN = 2
    TESTING = 3


class OperStatus(Enum):
    """Interface operational status."""

    UP = 1
    DOWN = 2
    TESTING = 3
    UNKNOWN = 4
    DORMANT = 5
    NOTPRESENT = 6
    LOWERLAYERDOWN = 7


class LinkTrapEnable(Enum):
    """Link up/down trap enable status."""

    ENABLED = 1
    DISABLED = 2


@dataclass
class InterfaceDefinition:
    """Complete interface definition for ifXTable simulation."""

    # Basic interface properties
    index: int
    name: str
    alias: str = ""
    interface_type: InterfaceType = InterfaceType.ETHERNET_CSMACD
    speed_mbps: int = 1000
    mtu: int = 1500
    physical_address: str = ""

    # Administrative and operational status
    admin_status: AdminStatus = AdminStatus.UP
    oper_status: OperStatus = OperStatus.UP

    # ifXTable specific attributes
    link_trap_enable: LinkTrapEnable = LinkTrapEnable.ENABLED
    promiscuous_mode: bool = False
    connector_present: bool = True

    # Traffic simulation parameters
    utilization_pattern: str = "constant_low"
    base_utilization: float = 0.1  # 10% baseline
    traffic_ratios: Dict[str, float] = field(
        default_factory=lambda: {"unicast": 0.8, "multicast": 0.15, "broadcast": 0.05}
    )

    # Error simulation
    error_rates: Dict[str, float] = field(
        default_factory=lambda: {
            "input_errors": 0.0001,
            "output_errors": 0.0001,
            "input_discards": 0.0001,
            "output_discards": 0.0001,
        }
    )

    # State change simulation
    link_flap_enabled: bool = False
    link_flap_interval: int = 3600  # seconds
    link_down_duration: int = 30  # seconds

    def __post_init__(self):
        """Initialize calculated fields."""
        if not self.physical_address:
            # Generate a random MAC address
            mac = [
                0x02,
                0x00,
                0x00,
                random.randint(0x00, 0xFF),
                random.randint(0x00, 0xFF),
                random.randint(0x00, 0xFF),
            ]
            self.physical_address = ":".join(f"{x:02x}" for x in mac)

    def get_speed_bps(self) -> int:
        """Get interface speed in bits per second."""
        return self.speed_mbps * 1_000_000

    def get_speed_bytes_per_sec(self) -> int:
        """Get interface speed in bytes per second."""
        return self.get_speed_bps() // 8


@dataclass
class InterfaceCounters:
    """Current counter values for an interface."""

    # 32-bit counters (from basic ifTable)
    in_octets: int = 0
    in_ucast_pkts: int = 0
    in_non_ucast_pkts: int = 0
    in_discards: int = 0
    in_errors: int = 0
    in_unknown_protos: int = 0
    out_octets: int = 0
    out_ucast_pkts: int = 0
    out_non_ucast_pkts: int = 0
    out_discards: int = 0
    out_errors: int = 0

    # ifXTable specific counters
    in_multicast_pkts: int = 0
    in_broadcast_pkts: int = 0
    out_multicast_pkts: int = 0
    out_broadcast_pkts: int = 0

    # 64-bit high capacity counters
    hc_in_octets: int = 0
    hc_in_ucast_pkts: int = 0
    hc_in_multicast_pkts: int = 0
    hc_in_broadcast_pkts: int = 0
    hc_out_octets: int = 0
    hc_out_ucast_pkts: int = 0
    hc_out_multicast_pkts: int = 0
    hc_out_broadcast_pkts: int = 0

    # Timestamps
    last_update: float = field(default_factory=time.time)
    last_state_change: float = field(default_factory=time.time)


class TrafficPatternEngine:
    """Generates realistic traffic patterns for interface simulation."""

    PATTERNS = {
        "constant_low": {"utilization": 0.1, "variance": 0.02},
        "constant_medium": {"utilization": 0.5, "variance": 0.05},
        "constant_high": {"utilization": 0.8, "variance": 0.1},
        "business_hours": {
            "peak_hours": [9, 10, 11, 14, 15, 16],
            "peak_utilization": 0.8,
            "baseline_utilization": 0.15,
            "variance": 0.1,
        },
        "bursty": {
            "burst_interval": 300,  # seconds
            "burst_duration": 60,  # seconds
            "burst_utilization": 0.95,
            "idle_utilization": 0.05,
            "variance": 0.15,
        },
        "server_load": {
            "base_utilization": 0.3,
            "peak_multiplier": 3.0,
            "peak_probability": 0.1,
            "variance": 0.2,
        },
    }

    def __init__(self):
        self.last_burst_time = {}
        self.burst_active = {}

    def get_current_utilization(self, interface_index: int, pattern_name: str) -> float:
        """Calculate current utilization based on pattern and time."""
        if pattern_name not in self.PATTERNS:
            return 0.1  # Default fallback

        pattern = self.PATTERNS[pattern_name]
        current_time = time.time()
        current_hour = int((current_time % 86400) // 3600)  # Hour of day (0-23)

        if pattern_name == "business_hours":
            if current_hour in pattern["peak_hours"]:
                base_util = pattern["peak_utilization"]
            else:
                base_util = pattern["baseline_utilization"]
            variance = random.uniform(-pattern["variance"], pattern["variance"])
            return max(0, min(1, base_util + variance))

        elif pattern_name == "bursty":
            if interface_index not in self.last_burst_time:
                self.last_burst_time[interface_index] = current_time
                self.burst_active[interface_index] = False

            time_since_last = current_time - self.last_burst_time[interface_index]

            if not self.burst_active[interface_index]:
                if time_since_last >= pattern["burst_interval"]:
                    self.burst_active[interface_index] = True
                    self.last_burst_time[interface_index] = current_time
                util = pattern["idle_utilization"]
            else:
                if time_since_last >= pattern["burst_duration"]:
                    self.burst_active[interface_index] = False
                    self.last_burst_time[interface_index] = current_time
                util = pattern["burst_utilization"]

            variance = random.uniform(-pattern["variance"], pattern["variance"])
            return max(0, min(1, util + variance))

        elif pattern_name == "server_load":
            base_util = pattern["base_utilization"]
            if random.random() < pattern["peak_probability"]:
                base_util *= pattern["peak_multiplier"]
            variance = random.uniform(-pattern["variance"], pattern["variance"])
            return max(0, min(1, base_util + variance))

        else:  # constant patterns
            base_util = pattern["utilization"]
            variance = random.uniform(-pattern["variance"], pattern["variance"])
            return max(0, min(1, base_util + variance))


class IfXTableSimulator:
    """Complete ifXTable simulation with all 18 OIDs and dynamic behavior."""

    def __init__(self):
        self.interfaces: Dict[int, InterfaceDefinition] = {}
        self.counters: Dict[int, InterfaceCounters] = {}
        self.counter_simulator = CounterWrapSimulator()
        self.traffic_engine = TrafficPatternEngine()
        self.simulation_start_time = time.time()

    def add_interface(self, interface_def: InterfaceDefinition) -> None:
        """Add an interface to the simulation."""
        self.interfaces[interface_def.index] = interface_def
        self.counters[interface_def.index] = InterfaceCounters()

        # Add 64-bit counters to the counter wrap simulator
        speed_bytes_per_sec = interface_def.get_speed_bytes_per_sec()

        # High capacity in/out octets (most important)
        hc_in_config = CounterConfig(
            oid=f"1.3.6.1.2.1.31.1.1.1.6.{interface_def.index}",  # ifHCInOctets
            counter_type="64bit",
            increment_rate=int(
                speed_bytes_per_sec * interface_def.base_utilization * 0.6
            ),
            acceleration_factor=1,
        )
        self.counter_simulator.add_counter(hc_in_config)

        hc_out_config = CounterConfig(
            oid=f"1.3.6.1.2.1.31.1.1.1.10.{interface_def.index}",  # ifHCOutOctets
            counter_type="64bit",
            increment_rate=int(
                speed_bytes_per_sec * interface_def.base_utilization * 0.4
            ),
            acceleration_factor=1,
        )
        self.counter_simulator.add_counter(hc_out_config)

        # Add other 64-bit packet counters
        packet_rate = (
            speed_bytes_per_sec // 1500
        )  # Assume 1500 byte average packet size

        for counter_type, oid_suffix in [
            ("hc_in_ucast", 7),
            ("hc_in_mcast", 8),
            ("hc_in_bcast", 9),
            ("hc_out_ucast", 11),
            ("hc_out_mcast", 12),
            ("hc_out_bcast", 13),
        ]:
            if "in" in counter_type:
                traffic_ratio = interface_def.traffic_ratios.get(
                    counter_type.replace("hc_in_", "").replace("cast", "cast"), 0.1
                )
                rate = int(
                    packet_rate * interface_def.base_utilization * 0.6 * traffic_ratio
                )
            else:
                traffic_ratio = interface_def.traffic_ratios.get(
                    counter_type.replace("hc_out_", "").replace("cast", "cast"), 0.1
                )
                rate = int(
                    packet_rate * interface_def.base_utilization * 0.4 * traffic_ratio
                )

            counter_config = CounterConfig(
                oid=f"1.3.6.1.2.1.31.1.1.1.{oid_suffix}.{interface_def.index}",
                counter_type="64bit",
                increment_rate=max(1, rate),
                acceleration_factor=1,
            )
            self.counter_simulator.add_counter(counter_config)

    def get_interface_counter_value(
        self, interface_index: int, counter_oid: str
    ) -> int:
        """Get current counter value for an interface with dynamic updates."""
        if interface_index not in self.interfaces:
            return 0

        interface_def = self.interfaces[interface_index]
        current_time = time.time()

        # Apply traffic pattern to get current utilization
        current_util = self.traffic_engine.get_current_utilization(
            interface_index, interface_def.utilization_pattern
        )

        # Update counter rates based on current utilization
        self._update_counter_rates(interface_index, current_util)

        # Get value from counter simulator
        return self.counter_simulator.get_current_value(counter_oid)

    def _update_counter_rates(self, interface_index: int, utilization: float) -> None:
        """Update counter increment rates based on current utilization."""
        interface_def = self.interfaces[interface_index]
        speed_bytes_per_sec = interface_def.get_speed_bytes_per_sec()

        # Update HC octets counters
        in_rate = int(speed_bytes_per_sec * utilization * 0.6)  # 60% in
        out_rate = int(speed_bytes_per_sec * utilization * 0.4)  # 40% out

        in_oid = f"1.3.6.1.2.1.31.1.1.1.6.{interface_index}"
        out_oid = f"1.3.6.1.2.1.31.1.1.1.10.{interface_index}"

        if in_oid in self.counter_simulator.counters:
            self.counter_simulator.counters[in_oid].increment_rate = in_rate
        if out_oid in self.counter_simulator.counters:
            self.counter_simulator.counters[out_oid].increment_rate = out_rate

    def simulate_link_flap(self, interface_index: int, down_duration: int = 30) -> bool:
        """Simulate interface link going down and back up."""
        if interface_index not in self.interfaces:
            return False

        interface_def = self.interfaces[interface_index]

        # Change operational status to down
        original_status = interface_def.oper_status
        interface_def.oper_status = OperStatus.DOWN

        # Reset counters during downtime (in real scenario)
        # For simulation, we'll just pause counter increments
        self._pause_interface_counters(interface_index)

        # Schedule return to up status
        def restore_interface():
            time.sleep(down_duration)
            interface_def.oper_status = original_status
            self._resume_interface_counters(interface_index)

        # In a real implementation, this would be handled by a background task
        # For now, we'll just log the event
        print(f"Interface {interface_index} link flap: down for {down_duration}s")

        return True

    def _pause_interface_counters(self, interface_index: int) -> None:
        """Pause counter increments for an interface."""
        for oid in list(self.counter_simulator.counters.keys()):
            if oid.endswith(f".{interface_index}"):
                self.counter_simulator.counters[oid].increment_rate = 0

    def _resume_interface_counters(self, interface_index: int) -> None:
        """Resume counter increments for an interface."""
        if interface_index not in self.interfaces:
            return

        interface_def = self.interfaces[interface_index]
        current_util = self.traffic_engine.get_current_utilization(
            interface_index, interface_def.utilization_pattern
        )
        self._update_counter_rates(interface_index, current_util)

    def change_interface_speed(self, interface_index: int, new_speed_mbps: int) -> bool:
        """Change interface speed (simulate auto-negotiation)."""
        if interface_index not in self.interfaces:
            return False

        interface_def = self.interfaces[interface_index]
        old_speed = interface_def.speed_mbps
        interface_def.speed_mbps = new_speed_mbps

        # Update counter rates for new speed
        current_util = self.traffic_engine.get_current_utilization(
            interface_index, interface_def.utilization_pattern
        )
        self._update_counter_rates(interface_index, current_util)

        print(
            f"Interface {interface_index} speed changed: {old_speed}Mbps -> {new_speed_mbps}Mbps"
        )
        return True

    def get_interface_state(self, interface_index: int) -> Dict[str, Any]:
        """Get complete interface state including counters and metadata."""
        if interface_index not in self.interfaces:
            return {}

        interface_def = self.interfaces[interface_index]
        current_time = time.time()

        # Get current counter values
        counter_values = {}
        for oid_suffix, counter_name in [
            (1, "ifName"),
            (2, "ifInMulticastPkts"),
            (3, "ifInBroadcastPkts"),
            (4, "ifOutMulticastPkts"),
            (5, "ifOutBroadcastPkts"),
            (6, "ifHCInOctets"),
            (7, "ifHCInUcastPkts"),
            (8, "ifHCInMulticastPkts"),
            (9, "ifHCInBroadcastPkts"),
            (10, "ifHCOutOctets"),
            (11, "ifHCOutUcastPkts"),
            (12, "ifHCOutMulticastPkts"),
            (13, "ifHCOutBroadcastPkts"),
            (14, "ifLinkUpDownTrapEnable"),
            (15, "ifHighSpeed"),
            (16, "ifPromiscuousMode"),
            (17, "ifConnectorPresent"),
            (18, "ifAlias"),
        ]:
            oid = f"1.3.6.1.2.1.31.1.1.1.{oid_suffix}.{interface_index}"
            if "HC" in counter_name:
                counter_values[counter_name] = self.get_interface_counter_value(
                    interface_index, oid
                )
            else:
                counter_values[counter_name] = self._get_interface_attribute(
                    interface_def, counter_name
                )

        current_util = self.traffic_engine.get_current_utilization(
            interface_index, interface_def.utilization_pattern
        )

        return {
            "interface_index": interface_index,
            "interface_def": interface_def,
            "current_utilization": current_util,
            "counters": counter_values,
            "simulation_time": current_time - self.simulation_start_time,
        }

    def _get_interface_attribute(
        self, interface_def: InterfaceDefinition, attribute_name: str
    ) -> Any:
        """Get non-counter interface attribute values."""
        mapping = {
            "ifName": interface_def.name,
            "ifAlias": interface_def.alias,
            "ifHighSpeed": interface_def.speed_mbps,
            "ifLinkUpDownTrapEnable": interface_def.link_trap_enable.value,
            "ifPromiscuousMode": 1 if interface_def.promiscuous_mode else 2,
            "ifConnectorPresent": 1 if interface_def.connector_present else 2,
            "ifInMulticastPkts": 0,  # Would calculate from 64-bit counters
            "ifInBroadcastPkts": 0,
            "ifOutMulticastPkts": 0,
            "ifOutBroadcastPkts": 0,
        }
        return mapping.get(attribute_name, 0)

    def generate_ifxtable_snmprec(self, output_file: Path) -> None:
        """Generate .snmprec file with complete ifXTable entries."""
        lines = []

        for interface_index, interface_def in self.interfaces.items():
            # ifXTable entries (1.3.6.1.2.1.31.1.1.1.X.index)
            base_oid = f"1.3.6.1.2.1.31.1.1.1"

            # 1. ifName (DisplayString)
            lines.append(f"{base_oid}.1.{interface_index}|4|{interface_def.name}\n")

            # 2-5. Multicast/Broadcast packet counters (use numeric variation for dynamic values)
            for oid_suffix, counter_type in [
                (2, "in_mcast"),
                (3, "in_bcast"),
                (4, "out_mcast"),
                (5, "out_bcast"),
            ]:
                packet_rate = interface_def.get_speed_bytes_per_sec() // 1500
                if "in" in counter_type:
                    base_rate = int(packet_rate * interface_def.base_utilization * 0.6)
                else:
                    base_rate = int(packet_rate * interface_def.base_utilization * 0.4)

                if "mcast" in counter_type:
                    rate = int(
                        base_rate * interface_def.traffic_ratios.get("multicast", 0.15)
                    )
                else:  # broadcast
                    rate = int(
                        base_rate * interface_def.traffic_ratios.get("broadcast", 0.05)
                    )

                lines.append(
                    f"{base_oid}.{oid_suffix}.{interface_index}|65:numeric|function=counter,rate={rate},max=4294967295\n"
                )

            # 6-13. High capacity 64-bit counters (use 64-bit gauge for now)
            hc_counter_values = {
                6: int(interface_def.base_utilization * 1000000000),  # ifHCInOctets
                7: int(interface_def.base_utilization * 100000),      # ifHCInUcastPkts  
                8: int(interface_def.base_utilization * 10000),       # ifHCInMulticastPkts
                9: int(interface_def.base_utilization * 1000),        # ifHCInBroadcastPkts
                10: int(interface_def.base_utilization * 800000000),  # ifHCOutOctets
                11: int(interface_def.base_utilization * 80000),      # ifHCOutUcastPkts
                12: int(interface_def.base_utilization * 8000),       # ifHCOutMulticastPkts
                13: int(interface_def.base_utilization * 800),        # ifHCOutBroadcastPkts
            }
            for oid_suffix in [6, 7, 8, 9, 10, 11, 12, 13]:
                value = hc_counter_values.get(oid_suffix, 0)
                lines.append(
                    f"{base_oid}.{oid_suffix}.{interface_index}|70|{value}\n"
                )

            # 14. ifLinkUpDownTrapEnable (INTEGER)
            lines.append(
                f"{base_oid}.14.{interface_index}|2|{interface_def.link_trap_enable.value}\n"
            )

            # 15. ifHighSpeed (Gauge32) - Interface speed in Mbps
            lines.append(
                f"{base_oid}.15.{interface_index}|66|{interface_def.speed_mbps}\n"
            )

            # 16. ifPromiscuousMode (TruthValue)
            promiscuous_val = 1 if interface_def.promiscuous_mode else 2
            lines.append(f"{base_oid}.16.{interface_index}|2|{promiscuous_val}\n")

            # 17. ifConnectorPresent (TruthValue)
            connector_val = 1 if interface_def.connector_present else 2
            lines.append(f"{base_oid}.17.{interface_index}|2|{connector_val}\n")

            # 18. ifAlias (DisplayString)
            lines.append(f"{base_oid}.18.{interface_index}|4|{interface_def.alias}\n")

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"Generated ifXTable .snmprec with {len(self.interfaces)} interfaces")


def create_sample_interfaces(num_interfaces: int = 5) -> List[InterfaceDefinition]:
    """Create sample interface definitions for testing."""
    interfaces = []

    interface_types = [
        ("GigabitEthernet", InterfaceType.GIGABITETHERNET, 1000),
        ("TenGigabitEthernet", InterfaceType.GIGABITETHERNET, 10000),
        ("FastEthernet", InterfaceType.ETHERNET_CSMACD, 100),
        ("Ethernet", InterfaceType.ETHERNET_CSMACD, 10),
    ]

    patterns = [
        "business_hours",
        "constant_medium",
        "bursty",
        "server_load",
        "constant_low",
    ]

    for i in range(1, num_interfaces + 1):
        type_info = interface_types[i % len(interface_types)]
        pattern = patterns[i % len(patterns)]

        interface = InterfaceDefinition(
            index=i,
            name=f"{type_info[0]}{i//10}/{i%10}",
            alias=f"Interface {i} - {pattern.replace('_', ' ').title()}",
            interface_type=type_info[1],
            speed_mbps=type_info[2],
            utilization_pattern=pattern,
            base_utilization=random.uniform(0.05, 0.3),
            link_flap_enabled=(i % 3 == 0),  # Every 3rd interface has link flap
        )
        interfaces.append(interface)

    return interfaces


if __name__ == "__main__":
    # Demo usage
    simulator = IfXTableSimulator()

    # Create sample interfaces
    sample_interfaces = create_sample_interfaces(8)

    print("Creating ifXTable simulation with interfaces:")
    for interface in sample_interfaces:
        simulator.add_interface(interface)
        print(
            f"  {interface.index}: {interface.name} ({interface.speed_mbps}Mbps, {interface.utilization_pattern})"
        )

    print(
        f"\nSimulating {len(simulator.interfaces)} interfaces with 64-bit counters..."
    )

    # Show current state for first few interfaces
    for i in range(1, min(4, len(sample_interfaces) + 1)):
        state = simulator.get_interface_state(i)
        if state:
            print(f"\nInterface {i} ({state['interface_def'].name}):")
            print(f"  Current utilization: {state['current_utilization']:.1%}")
            print(f"  HC In Octets: {state['counters']['ifHCInOctets']:,}")
            print(f"  HC Out Octets: {state['counters']['ifHCOutOctets']:,}")
            print(f"  High Speed: {state['counters']['ifHighSpeed']} Mbps")

    # Generate sample .snmprec file
    output_path = Path("data/ifxtable_sample.snmprec")
    output_path.parent.mkdir(exist_ok=True)
    simulator.generate_ifxtable_snmprec(output_path)
    print(f"\nGenerated sample ifXTable data: {output_path}")
