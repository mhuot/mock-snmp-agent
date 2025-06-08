# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SNMP Simulator (snmpsim) is a pure-Python tool that simulates SNMP agents. It can act as multiple virtual SNMP-enabled devices, responding to SNMP queries based on recorded data, MIB files, or dynamic variation modules.

## Common Development Commands

### Setup Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### Installation
```bash
# Install in development mode (after activating venv)
pip install -e .

# Install all dependencies for development
pip install -r requirements.txt -r devel-requirements.txt
```

### Running the Simulator
```bash
# Start the full-featured SNMP simulator
snmpsim-command-responder --data-dir=./data --agent-udpv4-endpoint=127.0.0.1:1024

# Start the lightweight simulator
snmpsim-command-responder-lite --data-dir=./data --agent-udpv4-endpoint=127.0.0.1:1163
```

### Testing
```bash
# Run the complete test suite
bash runtests.sh
```

### Linting
```bash
# Run pylint on the codebase
pylint snmpsim
```

## High-Level Architecture

### Core Command Entry Points
- `snmpsim/commands/responder.py` - Main SNMP simulator with full features
- `snmpsim/commands/responder_lite.py` - Lightweight simulator for high-scale deployments
- `snmpsim/commands/cmd2rec.py` - Records SNMP interactions to .snmprec files
- `snmpsim/commands/mib2rec.py` - Converts MIB files to simulation data
- `snmpsim/commands/pcap2rec.py` - Extracts SNMP data from packet captures

### Key Components
- **Controller** (`controller.py`) - Central MIB instrumentation controller that manages SNMP object access
- **Data Management** (`datafile.py`) - Handles loading and indexing of simulation data files
- **Grammar Modules** (`grammar/`) - Parsers for different data formats (snmprec, walk, sap, mvc)
- **Variation Modules** (`variation.py` + `/variation/`) - Plugin system for dynamic SNMP responses

### Data Flow
1. SNMP requests arrive at network endpoints (`endpoints.py`)
2. Controller routes requests to appropriate data files based on community/context
3. Data files provide static responses or invoke variation modules for dynamic behavior
4. Responses are formatted and sent back via pysnmp

### Simulation Data Format (.snmprec)
```
OID|TYPE|VALUE
1.3.6.1.2.1.1.1.0|4|Linux System
1.3.6.1.2.1.1.3.0|67|233425120
```

### Variation Module Interface
Variation modules in `/variation/` implement dynamic behavior by providing:
- `init()` - Called once when module loads
- `record()` - Called during recording phase (optional)
- `variate()` - Called to generate dynamic responses

## Key Development Patterns

1. **Multi-Protocol Support**: Code must handle SNMPv1, v2c, and v3 with various security models
2. **Data Source Abstraction**: All data sources (files, databases, etc.) implement common interfaces
3. **Plugin Architecture**: New functionality should be added as variation modules when possible
4. **Performance Considerations**: The simulator may handle thousands of virtual agents - avoid blocking operations
5. **Python Compatibility**: Maintain compatibility with Python 2.7 and 3.x