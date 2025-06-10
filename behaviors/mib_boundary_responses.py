#!/usr/bin/env python3
"""
MIB Boundary Response Simulation

This module simulates SNMP MIB boundary conditions including endOfMibView,
noSuchObject, and noSuchInstance responses. These are critical for testing
SNMP walk operations and table boundary detection.
"""

import random
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class SNMPExceptionType(Enum):
    """SNMP exception types for MIB boundary responses."""
    END_OF_MIB_VIEW = "endOfMibView"
    NO_SUCH_OBJECT = "noSuchObject"
    NO_SUCH_INSTANCE = "noSuchInstance"


@dataclass
class MIBBoundaryConfig:
    """Configuration for MIB boundary response simulation."""
    
    # EndOfMibView configuration
    enable_end_of_mib_view: bool = True
    mib_view_boundaries: Dict[str, str] = None  # OID prefix -> last valid OID
    
    # NoSuchObject configuration  
    enable_no_such_object: bool = True
    missing_objects: Set[str] = None  # Specific OIDs that don't exist
    missing_object_patterns: Set[str] = None  # OID patterns that don't exist
    
    # NoSuchInstance configuration
    enable_no_such_instance: bool = True
    missing_instances: Set[str] = None  # Table entries that don't exist
    sparse_tables: Dict[str, List[int]] = None  # Table OID -> missing indices
    
    # Random boundary injection
    random_boundaries: bool = False
    boundary_injection_rate: int = 5  # Percentage
    
    def __post_init__(self):
        """Initialize default values."""
        if self.mib_view_boundaries is None:
            self.mib_view_boundaries = {}
        if self.missing_objects is None:
            self.missing_objects = set()
        if self.missing_object_patterns is None:
            self.missing_object_patterns = set()
        if self.missing_instances is None:
            self.missing_instances = set()
        if self.sparse_tables is None:
            self.sparse_tables = {}


class MIBBoundarySimulator:
    """
    Simulates SNMP MIB boundary conditions and exception responses.
    
    This simulator helps test SNMP management applications' handling of:
    - endOfMibView: Indicates end of MIB tree during walks
    - noSuchObject: Object exists in MIB but not implemented
    - noSuchInstance: Object type exists but specific instance doesn't
    """
    
    def __init__(self, config: MIBBoundaryConfig = None):
        """Initialize MIB boundary simulator.
        
        Args:
            config: Boundary configuration object
        """
        self.config = config or MIBBoundaryConfig()
        self.logger = logging.getLogger(__name__)
        
        # Set up default MIB boundaries and missing objects
        self._setup_default_boundaries()
    
    def _setup_default_boundaries(self):
        """Set up common MIB boundary conditions."""
        
        # Default MIB view boundaries (common ending points)
        default_boundaries = {
            "1.3.6.1.2.1.1": "1.3.6.1.2.1.1.9.0",      # System group ends
            "1.3.6.1.2.1.2.2.1": "1.3.6.1.2.1.2.2.1.22", # Interface table columns
            "1.3.6.1.2.1.4": "1.3.6.1.2.1.4.34",        # IP group ends
            "1.3.6.1.2.1.6": "1.3.6.1.2.1.6.19",        # TCP group ends
            "1.3.6.1.2.1.7": "1.3.6.1.2.1.7.7",         # UDP group ends
            "1.3.6.1.2.1.25": "1.3.6.1.2.1.25.7",       # Host resources ends
        }
        
        # Merge with configured boundaries
        for prefix, boundary in default_boundaries.items():
            if prefix not in self.config.mib_view_boundaries:
                self.config.mib_view_boundaries[prefix] = boundary
        
        # Default missing objects (common unimplemented MIB objects)
        default_missing = {
            "1.3.6.1.2.1.1.8.0",     # System services (often not implemented)
            "1.3.6.1.2.1.2.2.1.21",  # Interface specific (deprecated)
            "1.3.6.1.2.1.4.12.0",    # IP forwarding timeout (rarely implemented)
            "1.3.6.1.2.1.6.14.0",    # TCP max connections (often not set)
            "1.3.6.1.2.1.25.3.8",    # Host disk access (varies by system)
        }
        
        self.config.missing_objects.update(default_missing)
        
        # Default missing object patterns
        default_patterns = {
            "1.3.6.1.2.1.10",        # Transmission group (device-specific)
            "1.3.6.1.2.1.13",        # AppleTalk (obsolete)
            "1.3.6.1.2.1.19",        # Character devices (rarely used)
            "1.3.6.1.4.1.99999",     # Non-existent enterprise
        }
        
        self.config.missing_object_patterns.update(default_patterns)
        
        # Default sparse table configurations
        default_sparse = {
            "1.3.6.1.2.1.2.2.1": [3, 5, 7, 9],      # Missing interface indices
            "1.3.6.1.2.1.4.20.1": [2, 4, 6],        # Missing IP address entries
            "1.3.6.1.2.1.4.21.1": [1, 3, 5, 8],     # Missing route entries
        }
        
        for table_oid, missing_indices in default_sparse.items():
            if table_oid not in self.config.sparse_tables:
                self.config.sparse_tables[table_oid] = missing_indices
    
    def check_boundary_condition(self, oid: str) -> Optional[SNMPExceptionType]:
        """Check if an OID should return a boundary condition.
        
        Args:
            oid: SNMP OID to check
            
        Returns:
            Exception type if boundary condition detected, None otherwise
        """
        # Check for endOfMibView
        if self.config.enable_end_of_mib_view:
            end_condition = self._check_end_of_mib_view(oid)
            if end_condition:
                return end_condition
        
        # Check for noSuchObject
        if self.config.enable_no_such_object:
            no_object = self._check_no_such_object(oid)
            if no_object:
                return no_object
        
        # Check for noSuchInstance
        if self.config.enable_no_such_instance:
            no_instance = self._check_no_such_instance(oid)
            if no_instance:
                return no_instance
        
        # Random boundary injection
        if self.config.random_boundaries:
            if random.randint(1, 100) <= self.config.boundary_injection_rate:
                return random.choice(list(SNMPExceptionType))
        
        return None
    
    def _check_end_of_mib_view(self, oid: str) -> Optional[SNMPExceptionType]:
        """Check if OID should return endOfMibView.
        
        Args:
            oid: SNMP OID to check
            
        Returns:
            SNMPExceptionType.END_OF_MIB_VIEW if at boundary, None otherwise
        """
        for prefix, boundary_oid in self.config.mib_view_boundaries.items():
            if oid.startswith(prefix):
                # Check if we're past the boundary
                if self._compare_oids(oid, boundary_oid) > 0:
                    self.logger.debug(f"endOfMibView: {oid} beyond boundary {boundary_oid}")
                    return SNMPExceptionType.END_OF_MIB_VIEW
        
        # Check for walks beyond defined MIB areas
        if oid.startswith("1.3.6.1.2.1.99"):  # Non-standard area
            return SNMPExceptionType.END_OF_MIB_VIEW
        
        return None
    
    def _check_no_such_object(self, oid: str) -> Optional[SNMPExceptionType]:
        """Check if OID should return noSuchObject.
        
        Args:
            oid: SNMP OID to check
            
        Returns:
            SNMPExceptionType.NO_SUCH_OBJECT if object missing, None otherwise
        """
        # Check exact matches
        if oid in self.config.missing_objects:
            self.logger.debug(f"noSuchObject: {oid} in missing objects list")
            return SNMPExceptionType.NO_SUCH_OBJECT
        
        # Check pattern matches
        for pattern in self.config.missing_object_patterns:
            if oid.startswith(pattern):
                self.logger.debug(f"noSuchObject: {oid} matches pattern {pattern}")
                return SNMPExceptionType.NO_SUCH_OBJECT
        
        return None
    
    def _check_no_such_instance(self, oid: str) -> Optional[SNMPExceptionType]:
        """Check if OID should return noSuchInstance.
        
        Args:
            oid: SNMP OID to check
            
        Returns:
            SNMPExceptionType.NO_SUCH_INSTANCE if instance missing, None otherwise
        """
        # Check exact instance matches
        if oid in self.config.missing_instances:
            self.logger.debug(f"noSuchInstance: {oid} in missing instances list")
            return SNMPExceptionType.NO_SUCH_INSTANCE
        
        # Check sparse table configurations
        for table_prefix, missing_indices in self.config.sparse_tables.items():
            if oid.startswith(table_prefix):
                # Extract index from OID
                index = self._extract_table_index(oid, table_prefix)
                if index is not None and index in missing_indices:
                    self.logger.debug(f"noSuchInstance: {oid} index {index} missing from table")
                    return SNMPExceptionType.NO_SUCH_INSTANCE
        
        return None
    
    def _extract_table_index(self, oid: str, table_prefix: str) -> Optional[int]:
        """Extract table index from OID.
        
        Args:
            oid: Full OID
            table_prefix: Table prefix OID
            
        Returns:
            Table index if extractable, None otherwise
        """
        if not oid.startswith(table_prefix):
            return None
        
        # Remove table prefix and extract index
        suffix = oid[len(table_prefix):]
        if suffix.startswith("."):
            suffix = suffix[1:]
        
        # For simple cases, index is the last component
        parts = suffix.split(".")
        if parts:
            try:
                return int(parts[-1])
            except ValueError:
                pass
        
        return None
    
    def _compare_oids(self, oid1: str, oid2: str) -> int:
        """Compare two OIDs lexicographically.
        
        Args:
            oid1: First OID
            oid2: Second OID
            
        Returns:
            -1 if oid1 < oid2, 0 if equal, 1 if oid1 > oid2
        """
        # Convert to integer lists for proper comparison
        try:
            parts1 = [int(x) for x in oid1.split(".") if x]
            parts2 = [int(x) for x in oid2.split(".") if x]
            
            # Pad shorter OID with zeros
            max_len = max(len(parts1), len(parts2))
            parts1.extend([0] * (max_len - len(parts1)))
            parts2.extend([0] * (max_len - len(parts2)))
            
            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            
            return 0
            
        except ValueError:
            # Fallback to string comparison
            if oid1 < oid2:
                return -1
            elif oid1 > oid2:
                return 1
            else:
                return 0
    
    def get_next_valid_oid(self, oid: str) -> Optional[str]:
        """Get the next valid OID after the given OID.
        
        Args:
            oid: Current OID
            
        Returns:
            Next valid OID or None if endOfMibView
        """
        # Simple implementation - increment last component
        parts = oid.split(".")
        if parts:
            try:
                last = int(parts[-1])
                parts[-1] = str(last + 1)
                next_oid = ".".join(parts)
                
                # Check if next OID has boundary condition
                boundary = self.check_boundary_condition(next_oid)
                if boundary == SNMPExceptionType.END_OF_MIB_VIEW:
                    return None
                elif boundary in [SNMPExceptionType.NO_SUCH_OBJECT, 
                                 SNMPExceptionType.NO_SUCH_INSTANCE]:
                    # Recursively find next valid OID
                    return self.get_next_valid_oid(next_oid)
                
                return next_oid
            except ValueError:
                pass
        
        return None
    
    def generate_boundary_snmprec_entries(self) -> List[str]:
        """Generate .snmprec entries that demonstrate boundary conditions.
        
        Returns:
            List of .snmprec format entries with boundary examples
        """
        entries = [
            "# MIB Boundary Condition Examples",
            "# These entries demonstrate endOfMibView, noSuchObject, and noSuchInstance",
            "",
            "# Normal objects (before boundaries)",
            "1.3.6.1.2.1.1.1.0|4|System with MIB boundaries",
            "1.3.6.1.2.1.1.3.0|67|12345600",
            "1.3.6.1.2.1.1.9.0|2|77",  # Last object in system group
            "",
            "# Interface table with sparse entries",
            "1.3.6.1.2.1.2.1.0|2|10",  # 10 interfaces total
            "1.3.6.1.2.1.2.2.1.1.1|2|1",   # Interface 1 exists
            "1.3.6.1.2.1.2.2.1.1.2|2|2",   # Interface 2 exists
            "# Interface 3 missing (noSuchInstance)",
            "1.3.6.1.2.1.2.2.1.1.4|2|4",   # Interface 4 exists
            "",
            "# IP address table (sparse)",
            "1.3.6.1.2.1.4.20.1.1.192.168.1.1|1|192.168.1.1",  # IP address exists
            "# 192.168.1.2 missing (noSuchInstance)",
            "1.3.6.1.2.1.4.20.1.1.192.168.1.3|1|192.168.1.3",  # IP address exists
            "",
            "# Enterprise MIB area (demonstrates noSuchObject)",
            "# 1.3.6.1.4.1.99999.* would return noSuchObject",
            "",
            "# End of defined MIB areas - beyond this is endOfMibView",
            "# Requests beyond 1.3.6.1.2.1.99 should return endOfMibView",
        ]
        
        # Add entries for missing objects (commented to show what's missing)
        entries.extend([
            "",
            "# Missing objects (would return noSuchObject):",
        ])
        
        for missing_oid in sorted(self.config.missing_objects):
            entries.append(f"# {missing_oid} - noSuchObject")
        
        # Add sparse table information
        entries.extend([
            "",
            "# Sparse table indices (would return noSuchInstance):",
        ])
        
        for table_oid, missing_indices in self.config.sparse_tables.items():
            entries.append(f"# {table_oid}.* indices {missing_indices} - noSuchInstance")
        
        return entries
    
    def create_walk_test_data(self, start_oid: str, max_objects: int = 50) -> List[Tuple[str, str, str]]:
        """Create test data for SNMP walk operations with boundaries.
        
        Args:
            start_oid: Starting OID for walk
            max_objects: Maximum objects to return
            
        Returns:
            List of (oid, type, value) tuples, including boundary conditions
        """
        results = []
        current_oid = start_oid
        
        for i in range(max_objects):
            boundary = self.check_boundary_condition(current_oid)
            
            if boundary == SNMPExceptionType.END_OF_MIB_VIEW:
                # End the walk
                results.append((current_oid, "endOfMibView", ""))
                break
            elif boundary == SNMPExceptionType.NO_SUCH_OBJECT:
                # Skip to next OID
                current_oid = self.get_next_valid_oid(current_oid)
                if current_oid is None:
                    break
                continue
            elif boundary == SNMPExceptionType.NO_SUCH_INSTANCE:
                # Skip to next OID  
                current_oid = self.get_next_valid_oid(current_oid)
                if current_oid is None:
                    break
                continue
            
            # Normal object - generate test data
            if current_oid.endswith(".1.0"):
                value = f"Test string for {current_oid}"
                snmp_type = "4"  # OCTET STRING
            elif current_oid.endswith(".3.0"):
                value = str(12345600 + i)
                snmp_type = "67"  # TIMETICKS
            else:
                value = str(i + 1)
                snmp_type = "2"  # INTEGER
            
            results.append((current_oid, snmp_type, value))
            
            # Get next OID
            current_oid = self.get_next_valid_oid(current_oid)
            if current_oid is None:
                results.append((current_oid or "endOfMibView", "endOfMibView", ""))
                break
        
        return results


# Utility functions for easy configuration
def create_sparse_interface_table(num_interfaces: int, missing_indices: List[int]) -> MIBBoundaryConfig:
    """Create configuration for sparse interface table.
    
    Args:
        num_interfaces: Total number of interfaces
        missing_indices: List of missing interface indices
        
    Returns:
        MIB boundary configuration
    """
    return MIBBoundaryConfig(
        enable_no_such_instance=True,
        sparse_tables={
            "1.3.6.1.2.1.2.2.1": missing_indices
        }
    )


def create_limited_mib_view(mib_boundaries: Dict[str, str]) -> MIBBoundaryConfig:
    """Create configuration for limited MIB view.
    
    Args:
        mib_boundaries: Dictionary of OID prefix -> boundary OID
        
    Returns:
        MIB boundary configuration
    """
    return MIBBoundaryConfig(
        enable_end_of_mib_view=True,
        mib_view_boundaries=mib_boundaries
    )


# Example usage and testing
if __name__ == "__main__":
    # Example: Create boundary simulator
    config = MIBBoundaryConfig(
        enable_end_of_mib_view=True,
        enable_no_such_object=True,
        enable_no_such_instance=True,
        random_boundaries=False,
        sparse_tables={
            "1.3.6.1.2.1.2.2.1": [3, 5, 7],  # Missing interface indices
        }
    )
    
    simulator = MIBBoundarySimulator(config)
    
    # Test various OIDs
    test_oids = [
        "1.3.6.1.2.1.1.1.0",      # Normal object
        "1.3.6.1.2.1.1.8.0",      # Missing object
        "1.3.6.1.2.1.2.2.1.1.3",  # Missing instance
        "1.3.6.1.2.1.99.1.0",     # Beyond MIB view
        "1.3.6.1.4.1.99999.1.0",  # Non-existent enterprise
    ]
    
    print("MIB Boundary Condition Test:")
    print("=" * 40)
    
    for oid in test_oids:
        boundary = simulator.check_boundary_condition(oid)
        if boundary:
            print(f"❌ {oid}: {boundary.value}")
        else:
            print(f"✅ {oid}: Normal response")
    
    print("\nWalk Test (starting from 1.3.6.1.2.1.1):")
    print("=" * 40)
    
    walk_data = simulator.create_walk_test_data("1.3.6.1.2.1.1.1.0", 10)
    for oid, snmp_type, value in walk_data:
        if snmp_type == "endOfMibView":
            print(f"🛑 {oid}: endOfMibView")
        else:
            print(f"📄 {oid}: {value}")