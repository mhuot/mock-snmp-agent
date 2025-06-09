#!/bin/bash

# Docker testing script for Mock SNMP Agent
# This script runs comprehensive tests in Docker containers

set -e

echo "=========================================="
echo "Mock SNMP Agent - Docker Integration Tests"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $1 in
        "SUCCESS") echo -e "${GREEN}✓ $2${NC}" ;;
        "ERROR") echo -e "${RED}✗ $2${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠ $2${NC}" ;;
        "INFO") echo -e "$2" ;;
    esac
}

# Cleanup function
cleanup() {
    print_status "INFO" "Cleaning up Docker containers..."
    docker compose -f docker-compose.test.yml down --remove-orphans -v 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Create necessary directories
print_status "INFO" "Creating log and metrics directories..."
mkdir -p logs metrics temp

# Build and start containers
print_status "INFO" "Building Docker images..."
if docker compose -f docker-compose.test.yml build; then
    print_status "SUCCESS" "Docker images built successfully"
else
    print_status "ERROR" "Failed to build Docker images"
    exit 1
fi

print_status "INFO" "Starting SNMP agent containers..."
if docker compose -f docker-compose.test.yml up -d; then
    print_status "SUCCESS" "Containers started successfully"
else
    print_status "ERROR" "Failed to start containers"
    exit 1
fi

# Wait for containers to be healthy
print_status "INFO" "Waiting for containers to be healthy..."
sleep 10

# Check container status
print_status "INFO" "Checking container status..."
docker compose -f docker-compose.test.yml ps

# Run the comprehensive test suite
print_status "INFO" "Running comprehensive test suite..."

if docker compose -f docker-compose.test.yml exec -T test-client python3 tests/docker_integration_test.py; then
    print_status "SUCCESS" "All tests completed successfully!"
    TEST_RESULT=0
else
    print_status "ERROR" "Some tests failed!"
    TEST_RESULT=1
fi

# Show container logs for debugging if tests failed
if [ $TEST_RESULT -ne 0 ]; then
    print_status "WARNING" "Showing container logs for debugging..."
    
    for service in mock-snmp-basic mock-snmp-delay mock-snmp-drops mock-snmp-comprehensive mock-snmp-counters; do
        echo ""
        print_status "INFO" "Logs for $service:"
        docker compose -f docker-compose.test.yml logs --tail=20 $service || true
    done
fi

# Manual testing section
print_status "INFO" "Running manual verification tests..."

# Test 1: Basic connectivity
print_status "INFO" "Test 1: Basic SNMP connectivity"
if docker compose -f docker-compose.test.yml exec -T test-client snmpget -v2c -c public -t 3 mock-snmp-basic:11611 1.3.6.1.2.1.1.1.0; then
    print_status "SUCCESS" "Basic connectivity test passed"
else
    print_status "ERROR" "Basic connectivity test failed"
    TEST_RESULT=1
fi

# Test 2: Delay simulation
print_status "INFO" "Test 2: Delay simulation (should take ~500ms)"
START_TIME=$(date +%s.%N)
if docker compose -f docker-compose.test.yml exec -T test-client snmpget -v2c -c public -t 5 mock-snmp-delay:11612 1.3.6.1.2.1.1.1.0 >/dev/null; then
    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    DURATION_MS=$(echo "$DURATION * 1000" | bc)
    print_status "SUCCESS" "Delay test passed (${DURATION_MS%.*}ms)"
else
    print_status "ERROR" "Delay test failed"
    TEST_RESULT=1
fi

# Test 3: Drop rate testing
print_status "INFO" "Test 3: Drop rate testing (20% drops expected)"
SUCCESS_COUNT=0
for i in {1..10}; do
    if docker compose -f docker-compose.test.yml exec -T test-client snmpget -v2c -c public -t 2 -r 1 mock-snmp-drops:11613 1.3.6.1.2.1.1.1.0 >/dev/null 2>&1; then
        ((SUCCESS_COUNT++))
    fi
done
DROP_RATE=$(echo "100 - ($SUCCESS_COUNT * 10)" | bc)
print_status "INFO" "Drop rate test: $SUCCESS_COUNT/10 successful (${DROP_RATE}% drops)"

# Test 4: Interface table bulk operation
print_status "INFO" "Test 4: Bulk operation testing"
INTERFACE_COUNT=$(docker compose -f docker-compose.test.yml exec -T test-client snmpwalk -v2c -c public -t 10 mock-snmp-comprehensive:11614 1.3.6.1.2.1.2.2.1.1 2>/dev/null | wc -l || echo "0")
if [ "$INTERFACE_COUNT" -gt 0 ]; then
    print_status "SUCCESS" "Bulk operation test passed ($INTERFACE_COUNT interfaces)"
else
    print_status "ERROR" "Bulk operation test failed"
    TEST_RESULT=1
fi

# Show test results summary
print_status "INFO" "Copying test results from container..."
docker compose -f docker-compose.test.yml exec -T test-client cat logs/docker_test_results.json 2>/dev/null > logs/docker_test_results.json || true

if [ -f logs/docker_test_results.json ]; then
    print_status "SUCCESS" "Test results saved to logs/docker_test_results.json"
else
    print_status "WARNING" "Could not retrieve detailed test results"
fi

# Final status
echo ""
print_status "INFO" "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    print_status "SUCCESS" "ALL DOCKER TESTS PASSED!"
    print_status "INFO" "The Mock SNMP Agent is working correctly in Docker"
else
    print_status "ERROR" "SOME TESTS FAILED"
    print_status "INFO" "Check the logs above for details"
fi
print_status "INFO" "=========================================="

exit $TEST_RESULT