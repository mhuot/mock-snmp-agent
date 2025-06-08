# Contributing to Mock SNMP Agent

We welcome contributions to the Mock SNMP Agent project! This document provides guidelines for contributing.

## 🤝 How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Search existing issues before creating a new one
- Provide detailed information about your environment and the issue
- Include steps to reproduce the problem

### Feature Requests

- Use the GitHub issue tracker for feature requests
- Describe the feature and its use case
- Be open to discussion about implementation approaches

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear, descriptive messages
6. Push to your fork and create a pull request

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/mock-snmp-agent.git
   cd mock-snmp-agent
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests:**
   ```bash
   python test_prd_requirements.py
   python performance_test.py
   ```

## 📝 Code Style

- Follow PEP 8 conventions
- Use `pylint` to check code quality
- Format code with `black` if available
- Write self-documenting code with clear variable names
- Add comments for complex logic, avoid obvious comments
- Ensure all code passes WCAG AAA standards where applicable

## 🧪 Testing

- Add tests for new features
- Ensure all existing tests pass
- Include both unit tests and integration tests
- Test on multiple Python versions if possible

## 📋 Code Review Process

1. All submissions require review
2. Maintainers will review for:
   - Code quality and style
   - Test coverage
   - Documentation updates
   - Backward compatibility
3. Address feedback promptly
4. Squash commits before merge if requested

## 🚀 Release Process

- We use semantic versioning (MAJOR.MINOR.PATCH)
- Releases are tagged in GitHub
- Release notes are maintained in the changelog

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (Apache License 2.0).

## 💬 Communication

- Use GitHub issues for bug reports and feature requests
- Be respectful and constructive in all interactions
- Follow the project's code of conduct

## 🎯 Areas for Contribution

- Bug fixes and improvements
- Additional simulation behaviors
- Performance optimizations
- Documentation improvements
- Test coverage expansion
- Docker and deployment enhancements

Thank you for contributing to Mock SNMP Agent!