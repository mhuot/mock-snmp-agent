# Support

## Getting Help

If you need help with the Mock SNMP Agent, here are your options:

## 📖 Documentation

First, check our documentation:

- **README.md**: Installation, usage, and examples
- **CLAUDE.md**: Development setup and architecture
- **GitHub Issues**: Search existing issues for similar problems

## 🐛 Bug Reports

If you've found a bug:

1. Search existing [GitHub Issues](https://github.com/yourusername/mock-snmp-agent/issues)
2. If not found, [create a new issue](https://github.com/yourusername/mock-snmp-agent/issues/new)
3. Use the bug report template
4. Include:
   - Your environment (OS, Python version, Docker version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

## 💡 Feature Requests

For new features:

1. Check if someone else has requested it in [GitHub Issues](https://github.com/yourusername/mock-snmp-agent/issues)
2. If not, [create a feature request](https://github.com/yourusername/mock-snmp-agent/issues/new)
3. Describe the use case and expected behavior

## 🔧 Troubleshooting

### Common Issues

**Simulator won't start:**
- Check if another process is using the port
- Verify Python and package versions
- Check firewall settings

**No SNMP responses:**
- Confirm simulator is running: `ps aux | grep snmpsim`
- Test with correct port (default: 11611)
- Verify community string and OID

**Docker issues:**
- Ensure Docker is running
- Check port mappings (`-p 11611:161/udp`)
- Verify image build completed successfully

### Self-Service Diagnostics

Run these commands to help diagnose issues:

```bash
# Test basic functionality
python test_prd_requirements.py

# Check performance
python performance_test.py

# Verify installation
pip show snmpsim-lextudio

# Test SNMP tools
snmpget -v2c -c public localhost:11611 1.3.6.1.2.1.1.1.0
```

## 📋 When Creating Issues

Please include:

- **Environment**: OS, Python version, Docker version
- **Installation method**: Docker, pip, source
- **Command used**: Full command that triggered the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happened
- **Logs**: Any error messages or debug output
- **Configuration**: Any custom settings or data files

## 🕒 Response Times

- **Bug reports**: We aim to respond within 48 hours
- **Feature requests**: Response within 5 business days
- **Security issues**: See SECURITY.md for faster response

## 💝 Contributing

Want to help improve the project?

- See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for development setup
- Check [good first issue](https://github.com/yourusername/mock-snmp-agent/labels/good%20first%20issue) labels
- Help with documentation improvements
- Share your use cases and feedback

## 🌐 Community

- **GitHub Discussions**: For general questions and community interaction
- **Issues**: For bugs and feature requests
- **Pull Requests**: For code contributions

## ⚠️ What We Don't Support

- General SNMP protocol questions (use SNMP community resources)
- Issues with third-party SNMP tools (snmpget, snmpset, etc.)
- Production deployment support (this is a testing tool)
- Custom development or consulting services

## 📞 Emergency Support

This is an open-source testing tool. For urgent production issues, consider:

- Commercial SNMP simulation solutions
- Professional support from SNMP experts
- Enterprise network monitoring vendors

---

Thank you for using Mock SNMP Agent! We appreciate your feedback and contributions.
