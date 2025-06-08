"""
Mock SNMP Agent

A comprehensive SNMP simulator for testing and development purposes,
using the official Lextudio SNMP simulator package.
"""

__version__ = "1.0.0"
__author__ = "Mock SNMP Agent Contributors"
__license__ = "Apache-2.0"

from .mock_snmp_agent import main

__all__ = ["main", "__version__"]
