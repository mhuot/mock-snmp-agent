# SNMP Simulation Data

This directory contains custom SNMP simulation data files that override the built-in data from the snmpsim-lextudio package.

## File Formats Supported

- **`.snmprec`**: Native snmpsim recording format
- **`.snmpwalk`**: Standard snmpwalk output format  
- **`.sapwalk`**: SAP-specific walk format

## Community Name Mapping

The filename (without extension) becomes the SNMP community name:

- `public.snmprec` → community: `public`
- `private.snmprec` → community: `private`
- `mydevice.snmpwalk` → community: `mydevice`

## Creating Custom Data

### From Live SNMP Device

```bash
# Record from real device
snmpsim-record-commands \
    --agent-udpv4-endpoint=192.168.1.100 \
    --community=public \
    --output-file=./data/mydevice.snmprec

# Or use snmpwalk directly
snmpwalk -v2c -c public 192.168.1.100 1.3.6 > ./data/mydevice.snmpwalk
```

### Manual Creation

Create a `.snmprec` file with format: `OID|TYPE|VALUE`

```
1.3.6.1.2.1.1.1.0|4|My Custom Device Description
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.12345
1.3.6.1.2.1.1.3.0|67|123456
```

#### Type Codes
- `2`: INTEGER
- `4`: OCTET STRING  
- `6`: OBJECT IDENTIFIER
- `64`: IP ADDRESS
- `65`: COUNTER32
- `66`: GAUGE32
- `67`: TIMETICKS

## Variation Modules

Add special behaviors by using variation modules:

### Delay Simulation
```
# File: delay-test.snmprec
1.3.6.1.2.1.1.1.0|4:delay|value=Slow Response,wait=1000
```

### Error Simulation
```
# File: error-test.snmprec  
1.3.6.1.2.1.1.1.0|4:error|status=authorizationError
```

### Writeable Values
```
# File: writable-test.snmprec
1.3.6.1.2.1.1.1.0|4:writecache|value=Initial Value
```

## Usage

1. Place your data files in this directory
2. Restart the SNMP simulator
3. Query using the filename as community name:

```bash
snmpget -v2c -c mydevice 127.0.0.1:11611 1.3.6.1.2.1.1.1.0
```