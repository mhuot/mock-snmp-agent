# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅ Yes              |
| < 1.0   | ❌ No               |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it privately.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Contact the maintainers privately through GitHub's security advisory feature
3. Include detailed information about the vulnerability:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)

### What to Expect

- **Response Time**: We aim to respond within 48 hours
- **Investigation**: We will investigate and assess the severity
- **Fix Timeline**: Critical issues will be addressed within 7 days
- **Disclosure**: We will coordinate public disclosure after the fix is available

### Security Considerations for SNMP Simulators

This project simulates SNMP agents for testing purposes. Please note:

- **Not for Production**: This simulator is intended for development and testing only
- **Default Credentials**: Uses default SNMPv3 credentials for testing
- **Network Exposure**: Be cautious when exposing simulators on public networks
- **Data Sensitivity**: Avoid using real sensitive data in simulation datasets

### Best Practices

When using this simulator:

1. Run in isolated test environments
2. Use firewall rules to restrict access
3. Regularly update dependencies
4. Review custom data files for sensitive information
5. Don't use production credentials in test configurations

## Scope

This security policy applies to:

- The main simulator codebase
- Docker containers and configurations
- Test scripts and utilities
- Documentation and examples

## Recognition

We appreciate security researchers who help improve our project's security. With your permission, we will acknowledge your contribution in our security advisories.
