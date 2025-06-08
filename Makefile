# Makefile for Mock SNMP Agent

.PHONY: help install install-dev test test-fast test-all lint format clean build docs docker docker-test

# Default target
help:
	@echo "Mock SNMP Agent - Make targets:"
	@echo ""
	@echo "  install       Install package and dependencies"
	@echo "  install-dev   Install package with development dependencies"
	@echo "  test          Run fast tests"
	@echo "  test-fast     Run tests excluding slow ones"
	@echo "  test-all      Run all tests including slow ones"
	@echo "  lint          Run code quality checks"
	@echo "  format        Format code with black"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build package"
	@echo "  docker        Build Docker image"
	@echo "  docker-test   Test Docker image"
	@echo ""

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev,test]

# Testing targets
test: test-fast

test-fast:
	pytest -m "not slow" -v

test-all:
	pytest -v

test-extensive:
	pytest --run-extensive -v

# Code quality targets
lint:
	@echo "Running pylint..."
	pylint *.py tests/ --fail-under=8.0
	@echo "Running bandit security scan..."
	bandit -r . -f json -o bandit-report.json --severity-level medium || true
	@echo "Running safety check..."
	safety check || true

format:
	@echo "Formatting code with black..."
	black *.py tests/

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

build: clean
	python -m build

# Docker targets
docker:
	docker build -t mock-snmp-agent .

docker-extended:
	docker build -f Dockerfile.extended -t mock-snmp-agent:extended .

docker-test: docker
	@echo "Testing Docker image..."
	docker run --rm -d --name test-snmp -p 11611:161/udp mock-snmp-agent
	sleep 5
	snmpget -v2c -c public -t 5 -r 1 localhost:11611 1.3.6.1.2.1.1.1.0 || true
	docker stop test-snmp

# Development helpers
dev-setup: install-dev
	@echo "Development environment set up!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code quality"

# Legacy test commands for backward compatibility
test-basic:
	python test_basic.py

test-prd:
	python test_prd_requirements.py

test-performance:
	python performance_test.py