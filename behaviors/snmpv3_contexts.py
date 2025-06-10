#!/usr/bin/env python3
"""
SNMPv3 Context Handling Simulation

This module simulates SNMPv3 context-based MIB access, allowing different
OID trees and data sets to be served based on the context name in SNMPv3 requests.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ContextConfig:
    """Configuration for a single SNMPv3 context."""

    name: str
    description: str = ""
    oid_mappings: Dict[str, str] = field(default_factory=dict)  # OID -> value mappings
    allowed_users: Set[str] = field(default_factory=set)  # Users with access
    restricted_oids: Set[str] = field(default_factory=set)  # Blocked OID prefixes
    access_level: str = "read"  # "read", "write", "notify"

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.name:
            raise ValueError("Context name cannot be empty")

        if self.access_level not in ["read", "write", "notify"]:
            raise ValueError("Access level must be read, write, or notify")


class SNMPv3ContextManager:
    """
    Manages SNMPv3 contexts for different MIB views and access control.

    SNMPv3 contexts allow the same OID to return different values depending
    on the context name specified in the request. This is commonly used for:
    - Virtual routing instances (VRFs)
    - Bridge domains in switches
    - Multiple device instances
    - Partitioned MIB trees
    """

    def __init__(self):
        """Initialize context manager."""
        self.contexts: Dict[str, ContextConfig] = {}
        self.default_context = ""  # Empty string is default context
        self.logger = logging.getLogger(__name__)

        # Initialize with common default contexts
        self._setup_default_contexts()

    def _setup_default_contexts(self):
        """Set up commonly used default contexts."""

        # Default context (empty string)
        self.add_context(
            ContextConfig(
                name="",
                description="Default SNMP context",
                oid_mappings={
                    "1.3.6.1.2.1.1.1.0": "Default System Description",
                    "1.3.6.1.2.1.1.5.0": "default-system",
                    "1.3.6.1.2.1.1.6.0": "Default Location",
                },
                allowed_users={"public", "simulator", "monitor"},
                access_level="read",
            )
        )

        # VRF contexts (common in routers)
        self.add_context(
            ContextConfig(
                name="vrf-management",
                description="Management VRF context",
                oid_mappings={
                    "1.3.6.1.2.1.1.1.0": "Management VRF Router",
                    "1.3.6.1.2.1.1.5.0": "mgmt-router",
                    "1.3.6.1.2.1.1.6.0": "Management Network",
                    "1.3.6.1.2.1.4.1.0": "1",  # IP forwarding enabled
                    "1.3.6.1.2.1.4.3.0": "10",  # IP default TTL
                },
                allowed_users={"admin", "operator"},
                access_level="read",
            )
        )

        self.add_context(
            ContextConfig(
                name="vrf-customer-a",
                description="Customer A VRF context",
                oid_mappings={
                    "1.3.6.1.2.1.1.1.0": "Customer A Router Instance",
                    "1.3.6.1.2.1.1.5.0": "customer-a-router",
                    "1.3.6.1.2.1.1.6.0": "Customer A Site",
                    "1.3.6.1.2.1.4.1.0": "1",  # IP forwarding enabled
                    "1.3.6.1.2.1.4.3.0": "64",  # IP default TTL
                },
                allowed_users={"customer-a", "operator"},
                access_level="read",
            )
        )

        # Bridge domain contexts (common in switches)
        self.add_context(
            ContextConfig(
                name="bridge-domain-100",
                description="VLAN 100 bridge domain",
                oid_mappings={
                    "1.3.6.1.2.1.1.1.0": "Switch Bridge Domain 100",
                    "1.3.6.1.2.1.1.5.0": "switch-vlan100",
                    "1.3.6.1.2.1.17.1.1.0": "6",  # Bridge base num ports
                    "1.3.6.1.2.1.17.1.2.0": "2",  # Bridge type (transparent)
                },
                allowed_users={"switch-admin", "monitor"},
                access_level="read",
            )
        )

        # Firewall context
        self.add_context(
            ContextConfig(
                name="firewall-zone-dmz",
                description="DMZ firewall zone context",
                oid_mappings={
                    "1.3.6.1.2.1.1.1.0": "Firewall DMZ Zone",
                    "1.3.6.1.2.1.1.5.0": "fw-dmz",
                    "1.3.6.1.2.1.1.6.0": "DMZ Network Segment",
                },
                allowed_users={"security-admin", "monitor"},
                restricted_oids={"1.3.6.1.4.1"},  # Block enterprise MIBs
                access_level="read",
            )
        )

    def add_context(self, context: ContextConfig):
        """Add a new context.

        Args:
            context: Context configuration to add
        """
        self.contexts[context.name] = context
        self.logger.info(
            f"Added SNMPv3 context: '{context.name}' - {context.description}"
        )

    def remove_context(self, context_name: str) -> bool:
        """Remove a context.

        Args:
            context_name: Name of context to remove

        Returns:
            True if context was removed, False if not found
        """
        if context_name in self.contexts:
            del self.contexts[context_name]
            self.logger.info(f"Removed SNMPv3 context: '{context_name}'")
            return True
        return False

    def get_context_value(
        self, context_name: str, oid: str, user: str = None
    ) -> Optional[str]:
        """Get OID value for a specific context.

        Args:
            context_name: SNMPv3 context name
            oid: SNMP OID to query
            user: SNMPv3 user making the request

        Returns:
            OID value if found and accessible, None otherwise
        """
        # Use default context if context_name is None
        if context_name is None:
            context_name = self.default_context

        # Check if context exists
        if context_name not in self.contexts:
            self.logger.warning(f"Unknown context: '{context_name}'")
            return None

        context = self.contexts[context_name]

        # Check user access
        if user and context.allowed_users and user not in context.allowed_users:
            self.logger.warning(
                f"User '{user}' denied access to context '{context_name}'"
            )
            return None

        # Check restricted OIDs
        for restricted_prefix in context.restricted_oids:
            if oid.startswith(restricted_prefix):
                self.logger.warning(
                    f"OID '{oid}' restricted in context '{context_name}'"
                )
                return None

        # Look for exact match first
        if oid in context.oid_mappings:
            return context.oid_mappings[oid]

        # Look for prefix matches (for table entries)
        for mapped_oid, value in context.oid_mappings.items():
            if oid.startswith(mapped_oid):
                # Generate context-specific value for table entries
                return self._generate_context_value(context_name, oid, value)

        # No mapping found in this context
        return None

    def _generate_context_value(
        self, context_name: str, oid: str, base_value: str
    ) -> str:
        """Generate context-specific value for unmapped OIDs.

        Args:
            context_name: Context name
            oid: OID being queried
            base_value: Base value to modify

        Returns:
            Context-specific value
        """
        # For interface tables, modify based on context
        if oid.startswith("1.3.6.1.2.1.2.2.1"):
            if "vrf" in context_name:
                return f"{base_value}-{context_name}"
            elif "bridge" in context_name:
                return f"{base_value}-{context_name.split('-')[-1]}"  # Extract VLAN ID

        # For IP tables, provide context-specific data
        if oid.startswith("1.3.6.1.2.1.4"):
            if "management" in context_name:
                return "192.168.1.1"  # Management network
            elif "customer-a" in context_name:
                return "10.1.1.1"  # Customer A network

        return base_value

    def list_contexts(self) -> List[Dict[str, str]]:
        """List all available contexts.

        Returns:
            List of context information dictionaries
        """
        contexts = []
        for name, config in self.contexts.items():
            contexts.append(
                {
                    "name": name,
                    "description": config.description,
                    "access_level": config.access_level,
                    "oid_count": len(config.oid_mappings),
                    "user_count": len(config.allowed_users),
                    "restricted_count": len(config.restricted_oids),
                }
            )
        return contexts

    def validate_context_access(
        self, context_name: str, user: str, oid: str
    ) -> Tuple[bool, str]:
        """Validate if a user can access an OID in a specific context.

        Args:
            context_name: SNMPv3 context name
            user: SNMPv3 user
            oid: SNMP OID

        Returns:
            Tuple of (is_allowed, reason)
        """
        if context_name not in self.contexts:
            return False, f"Context '{context_name}' does not exist"

        context = self.contexts[context_name]

        # Check user access
        if context.allowed_users and user not in context.allowed_users:
            return False, f"User '{user}' not authorized for context '{context_name}'"

        # Check restricted OIDs
        for restricted_prefix in context.restricted_oids:
            if oid.startswith(restricted_prefix):
                return False, f"OID '{oid}' is restricted in context '{context_name}'"

        return True, "Access granted"

    def generate_snmprec_entries(self, context_name: str = None) -> List[str]:
        """Generate .snmprec entries for a specific context.

        Args:
            context_name: Context to generate entries for, or None for all

        Returns:
            List of .snmprec format entries
        """
        entries = []

        if context_name is None:
            # Generate for all contexts
            for ctx_name in self.contexts:
                entries.extend(self._generate_context_entries(ctx_name))
        else:
            # Generate for specific context
            if context_name in self.contexts:
                entries.extend(self._generate_context_entries(context_name))

        return entries

    def _generate_context_entries(self, context_name: str) -> List[str]:
        """Generate .snmprec entries for a single context.

        Args:
            context_name: Context name

        Returns:
            List of .snmprec entries
        """
        if context_name not in self.contexts:
            return []

        context = self.contexts[context_name]
        entries = [
            f"# SNMPv3 Context: {context_name}",
            f"# Description: {context.description}",
            "",
        ]

        # Add OID mappings
        for oid, value in sorted(context.oid_mappings.items()):
            # Determine SNMP type based on OID and value
            snmp_type = self._determine_snmp_type(oid, value)
            entries.append(f"{oid}|{snmp_type}|{value}")

        entries.append("")  # Blank line between contexts
        return entries

    def _determine_snmp_type(self, oid: str, value: str) -> str:
        """Determine SNMP type code for .snmprec format.

        Args:
            oid: SNMP OID
            value: Value string

        Returns:
            SNMP type code (4=string, 2=integer, etc.)
        """
        # System description, contact, location are strings
        if oid in ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.4.0", "1.3.6.1.2.1.1.6.0"]:
            return "4"  # OCTET STRING

        # System name is string
        if oid == "1.3.6.1.2.1.1.5.0":
            return "4"  # OCTET STRING

        # Try to detect integer values
        try:
            int(value)
            return "2"  # INTEGER
        except ValueError:
            pass

        # Default to string
        return "4"  # OCTET STRING


# Utility functions for easy context creation
def create_vrf_context(vrf_name: str, description: str = "") -> ContextConfig:
    """Create a VRF context configuration.

    Args:
        vrf_name: VRF name
        description: Optional description

    Returns:
        Context configuration for VRF
    """
    return ContextConfig(
        name=f"vrf-{vrf_name}",
        description=description or f"VRF {vrf_name} routing instance",
        oid_mappings={
            "1.3.6.1.2.1.1.1.0": f"Router VRF {vrf_name}",
            "1.3.6.1.2.1.1.5.0": f"router-vrf-{vrf_name}",
            "1.3.6.1.2.1.1.6.0": f"VRF {vrf_name} Location",
            "1.3.6.1.2.1.4.1.0": "1",  # IP forwarding enabled
        },
        allowed_users={"operator", "monitor"},
        access_level="read",
    )


def create_bridge_context(vlan_id: int, description: str = "") -> ContextConfig:
    """Create a bridge domain context configuration.

    Args:
        vlan_id: VLAN ID
        description: Optional description

    Returns:
        Context configuration for bridge domain
    """
    return ContextConfig(
        name=f"bridge-domain-{vlan_id}",
        description=description or f"Bridge domain for VLAN {vlan_id}",
        oid_mappings={
            "1.3.6.1.2.1.1.1.0": f"Switch Bridge VLAN {vlan_id}",
            "1.3.6.1.2.1.1.5.0": f"switch-vlan{vlan_id}",
            "1.3.6.1.2.1.17.1.1.0": "6",  # Bridge base num ports
            "1.3.6.1.2.1.17.1.2.0": "2",  # Bridge type (transparent)
        },
        allowed_users={"switch-admin", "monitor"},
        access_level="read",
    )


# Example usage and testing
if __name__ == "__main__":
    # Example: Create context manager
    context_mgr = SNMPv3ContextManager()

    # Add custom contexts
    context_mgr.add_context(create_vrf_context("production", "Production traffic VRF"))
    context_mgr.add_context(create_bridge_context(200, "Guest network VLAN"))

    # Test context access
    test_cases = [
        ("", "1.3.6.1.2.1.1.1.0", "public"),  # Default context
        ("vrf-management", "1.3.6.1.2.1.1.1.0", "operator"),  # Management VRF
        ("vrf-customer-a", "1.3.6.1.2.1.1.1.0", "customer-a"),  # Customer VRF
        ("bridge-domain-100", "1.3.6.1.2.1.1.1.0", "monitor"),  # Bridge domain
        ("firewall-zone-dmz", "1.3.6.1.4.1.9.1.1.0", "monitor"),  # Restricted OID
    ]

    print("SNMPv3 Context Access Test:")
    print("=" * 50)

    for context, oid, user in test_cases:
        value = context_mgr.get_context_value(context, oid, user)
        allowed, reason = context_mgr.validate_context_access(context, user, oid)

        status = "✅" if value else "❌"
        print(f"{status} Context: '{context}', User: '{user}'")
        print(f"    OID: {oid}")
        print(f"    Value: {value}")
        print(f"    Access: {allowed} - {reason}")
        print()

    print("Available Contexts:")
    print("=" * 50)
    for ctx in context_mgr.list_contexts():
        print(f"• {ctx['name'] or '(default)'}: {ctx['description']}")
        print(
            f"  OIDs: {ctx['oid_count']}, Users: {ctx['user_count']}, Restricted: {ctx['restricted_count']}"
        )
        print()
