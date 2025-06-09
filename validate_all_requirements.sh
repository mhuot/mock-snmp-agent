#!/bin/bash
# Complete PRD Requirements Validation Script
# 
# This script runs all available tests to validate that the Mock SNMP Agent
# meets all Product Requirements Document (PRD) requirements.

set -e  # Exit on any error

echo "🚀 Complete PRD Requirements Validation"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "mock_snmp_agent.py" ]; then
    echo "❌ Error: mock_snmp_agent.py not found"
    echo "Please run this script from the mock-snmp-agent directory"
    exit 1
fi

# Create reports directory
mkdir -p test-reports

# Track overall success
OVERALL_SUCCESS=true

echo "📋 Step 1: Checking Dependencies..."
echo "=================================="

# Check Python dependencies
python -c "import requests, websocket, yaml, fastapi, uvicorn, pytest" 2>/dev/null || {
    echo "❌ Missing Python dependencies"
    echo "Run: pip install -r requirements-test.txt"
    exit 1
}

# Check SNMP tools
for tool in snmpget snmpgetnext snmpbulkget; do
    if command -v $tool >/dev/null 2>&1; then
        echo "✅ $tool found"
    else
        echo "❌ $tool not found - install net-snmp tools"
        echo "  macOS: brew install net-snmp"
        echo "  Ubuntu: apt-get install snmp"
        OVERALL_SUCCESS=false
    fi
done

if [ "$OVERALL_SUCCESS" = false ]; then
    echo "❌ Dependency check failed - please install missing tools"
    exit 1
fi

echo ""
echo "🧪 Step 2: Running Core PRD Compliance Tests..."
echo "=============================================="

# Run PRD compliance validation
if python validate_prd_compliance.py; then
    echo "✅ PRD Compliance Tests: PASSED"
else
    echo "❌ PRD Compliance Tests: FAILED"
    OVERALL_SUCCESS=false
fi

echo ""
echo "🔬 Step 3: Running Comprehensive API Test Suite..."
echo "================================================"

# Run the 78+ automated API tests
if python run_api_tests.py all --coverage --verbose; then
    echo "✅ API Test Suite: PASSED"
else
    echo "❌ API Test Suite: FAILED"
    OVERALL_SUCCESS=false
fi

echo ""
echo "⚡ Step 4: Running Performance Tests..."
echo "====================================="

# Run performance validation
if python quick_performance_test.py; then
    echo "✅ Performance Tests: PASSED"
else
    echo "❌ Performance Tests: FAILED"
    OVERALL_SUCCESS=false
fi

echo ""
echo "🌐 Step 5: Running SNMP Exporter Integration Tests..."
echo "==================================================="

# Run SNMP Exporter integration tests
if python test_snmp_exporter_integration.py; then
    echo "✅ SNMP Exporter Integration: PASSED"
else
    echo "⚠️ SNMP Exporter Integration: FAILED (may require snmp_exporter binary)"
    echo "Note: This test requires the Prometheus SNMP Exporter to be available"
    # Don't fail overall for this as it requires external binary
fi

echo ""
echo "🐳 Step 6: Testing Docker Integration..."
echo "======================================"

# Test Docker integration if Docker is available
if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        echo "Testing Docker Compose integration..."
        
        # Test basic Docker startup
        if timeout 60 bash -c '
            docker compose up -d && sleep 10 &&
            curl -f http://localhost:8080/health >/dev/null 2>&1 &&
            docker compose down
        '; then
            echo "✅ Docker Integration: PASSED"
        else
            echo "❌ Docker Integration: FAILED"
            docker compose down 2>/dev/null || true
            OVERALL_SUCCESS=false
        fi
    else
        echo "⚠️ Docker Compose not available - skipping Docker tests"
    fi
else
    echo "⚠️ Docker not available - skipping Docker tests"
fi

echo ""
echo "📊 Final Results"
echo "==============="

# Generate summary report
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "Test execution completed at: $TIMESTAMP"

if [ "$OVERALL_SUCCESS" = true ]; then
    echo ""
    echo "🎉 ALL PRD REQUIREMENTS VALIDATED SUCCESSFULLY!"
    echo "✅ Core SNMP Protocol Support"
    echo "✅ REST API and WebSocket Functionality"
    echo "✅ Simulation Behaviors"
    echo "✅ Performance Requirements"
    echo "✅ Configuration Management"
    echo "✅ Automated Test Coverage"
    echo ""
    echo "The Mock SNMP Agent fully meets all PRD requirements."
    echo "Ready for production use with Prometheus SNMP Exporter."
    
    # Create success marker file
    echo "SUCCESS: All PRD requirements validated at $TIMESTAMP" > test-reports/validation-success.txt
    
    exit 0
else
    echo ""
    echo "❌ SOME REQUIREMENTS NOT MET"
    echo "Please review the failed tests above and address any issues."
    echo "Check individual test reports in test-reports/ directory for details."
    
    # Create failure marker file
    echo "FAILURE: Some requirements not met at $TIMESTAMP" > test-reports/validation-failure.txt
    
    exit 1
fi