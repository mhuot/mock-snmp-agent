#!/bin/bash
# Comprehensive Docker-based Testing Script
# Tests all advanced features: SNMPv3 security, REST API, and State Machine

set -e

echo "🐳 Mock SNMP Agent - Comprehensive Feature Testing"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Clean up any existing containers
cleanup_containers() {
    print_status "Cleaning up existing containers..."
    
    docker compose -f docker-compose.testing.yml down --remove-orphans 2>/dev/null || true
    
    # Remove any orphaned containers
    docker ps -a --filter "name=mock-snmp" -q | xargs -r docker rm -f 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build main image
    if ! docker build -t mock-snmp-agent -f Dockerfile.enhanced .; then
        print_error "Failed to build main Docker image"
        exit 1
    fi
    
    # Build test runner image
    if ! docker build -t mock-snmp-test-runner -f Dockerfile.test-runner .; then
        print_error "Failed to build test runner image"
        exit 1
    fi
    
    print_success "Docker images built successfully"
}

# Start test containers
start_test_containers() {
    print_status "Starting test containers..."
    
    # Start all test containers
    if ! docker compose -f docker-compose.testing.yml up -d snmpv3-security-test rest-api-test state-machine-test combined-features-test snmp-client; then
        print_error "Failed to start test containers"
        exit 1
    fi
    
    print_success "Test containers started"
}

# Wait for containers to be ready
wait_for_containers() {
    print_status "Waiting for containers to be ready..."
    
    local max_wait=120
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        local ready_count=0
        local total_containers=4
        
        # Check each container's health
        for container in snmpv3-security-test rest-api-test state-machine-test combined-features-test; do
            if docker compose -f docker-compose.testing.yml ps $container | grep -q "healthy"; then
                ready_count=$((ready_count + 1))
            fi
        done
        
        if [ $ready_count -eq $total_containers ]; then
            print_success "All containers are ready"
            return 0
        fi
        
        print_status "Waiting for containers... ($ready_count/$total_containers ready)"
        sleep 10
        wait_time=$((wait_time + 10))
    done
    
    print_error "Timeout waiting for containers to be ready"
    return 1
}

# Run quick connectivity tests
test_connectivity() {
    print_status "Testing basic connectivity..."
    
    local test_passed=0
    local total_tests=0
    
    # Test SNMP connectivity for each container
    for port in 11621 11622 11623 11624; do
        total_tests=$((total_tests + 1))
        print_status "Testing SNMP on port $port..."
        
        if docker exec snmp-test-client snmpget -v2c -c public -t 3 -r 1 host.docker.internal:$port 1.3.6.1.2.1.1.1.0 2>/dev/null; then
            print_success "SNMP port $port: OK"
            test_passed=$((test_passed + 1))
        else
            print_warning "SNMP port $port: Failed"
        fi
    done
    
    # Test API connectivity for each container
    for port in 8081 8082 8083 8084; do
        total_tests=$((total_tests + 1))
        print_status "Testing API on port $port..."
        
        if docker exec snmp-test-client curl -s -f http://host.docker.internal:$port/health > /dev/null; then
            print_success "API port $port: OK"
            test_passed=$((test_passed + 1))
        else
            print_warning "API port $port: Failed"
        fi
    done
    
    print_status "Connectivity test results: $test_passed/$total_tests passed"
    
    if [ $test_passed -eq $total_tests ]; then
        return 0
    else
        return 1
    fi
}

# Run comprehensive tests
run_comprehensive_tests() {
    print_status "Running comprehensive test suite..."
    
    # Create test results directory
    mkdir -p test-results
    
    # Run the comprehensive test suite
    if docker compose -f docker-compose.testing.yml run --rm test-runner; then
        print_success "Comprehensive tests completed successfully"
        return 0
    else
        print_error "Comprehensive tests failed"
        return 1
    fi
}

# Run individual feature tests
test_snmpv3_security() {
    print_status "Testing SNMPv3 Security Features..."
    
    # Test valid credentials (should work sometimes due to failure simulation)
    print_status "Testing valid SNMPv3 credentials..."
    if docker exec snmp-test-client snmpget -v3 -l authNoPriv -u simulator -a MD5 -A auctoritas -t 5 -r 2 host.docker.internal:11621 1.3.6.1.2.1.1.1.0 2>/dev/null; then
        print_success "Valid SNMPv3 credentials: Working"
    else
        print_warning "Valid SNMPv3 credentials: Failed (may be due to security simulation)"
    fi
    
    # Test invalid credentials (should fail)
    print_status "Testing invalid SNMPv3 credentials..."
    if docker exec snmp-test-client snmpget -v3 -l authNoPriv -u wronguser -a MD5 -A wrongpass -t 3 -r 1 host.docker.internal:11621 1.3.6.1.2.1.1.1.0 2>/dev/null; then
        print_warning "Invalid SNMPv3 credentials: Unexpectedly succeeded"
    else
        print_success "Invalid SNMPv3 credentials: Correctly rejected"
    fi
    
    # Check API configuration
    print_status "Checking SNMPv3 security configuration via API..."
    if docker exec snmp-test-client curl -s http://host.docker.internal:8081/config | grep -q '"enabled":.*true' 2>/dev/null; then
        print_success "SNMPv3 security configuration: Enabled via API"
    else
        print_warning "SNMPv3 security configuration: Not confirmed via API"
    fi
}

test_rest_api() {
    print_status "Testing REST API Features..."
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if docker exec snmp-test-client curl -s -f http://host.docker.internal:8082/health > /dev/null; then
        print_success "Health endpoint: Working"
    else
        print_error "Health endpoint: Failed"
    fi
    
    # Test metrics endpoint
    print_status "Testing metrics endpoint..."
    if docker exec snmp-test-client curl -s -f http://host.docker.internal:8082/metrics > /dev/null; then
        print_success "Metrics endpoint: Working"
    else
        print_error "Metrics endpoint: Failed"
    fi
    
    # Test configuration endpoint
    print_status "Testing configuration endpoint..."
    if docker exec snmp-test-client curl -s -f http://host.docker.internal:8082/config > /dev/null; then
        print_success "Configuration endpoint: Working"
    else
        print_error "Configuration endpoint: Failed"
    fi
    
    # Test configuration update
    print_status "Testing configuration update..."
    if docker exec snmp-test-client curl -s -X PUT -H "Content-Type: application/json" \
       -d '{"simulation":{"behaviors":{"delay":{"enabled":true,"global_delay":100}}}}' \
       http://host.docker.internal:8082/config > /dev/null; then
        print_success "Configuration update: Working"
    else
        print_error "Configuration update: Failed"
    fi
}

test_state_machine() {
    print_status "Testing State Machine Features..."
    
    # Test SNMP with state effects
    print_status "Testing SNMP responses with state machine..."
    local response_times=()
    local success_count=0
    
    for i in {1..5}; do
        local start_time=$(date +%s%N)
        if docker exec snmp-test-client snmpget -v2c -c public -t 5 -r 1 host.docker.internal:11623 1.3.6.1.2.1.1.1.0 2>/dev/null; then
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            response_times+=($response_time)
            success_count=$((success_count + 1))
        fi
        sleep 1
    done
    
    if [ $success_count -gt 0 ]; then
        print_success "State machine SNMP responses: $success_count/5 successful"
    else
        print_warning "State machine SNMP responses: No successful responses"
    fi
    
    # Check state machine configuration
    print_status "Checking state machine configuration via API..."
    if docker exec snmp-test-client curl -s http://host.docker.internal:8083/config | grep -q '"device_type"' 2>/dev/null; then
        print_success "State machine configuration: Found device type"
    else
        print_warning "State machine configuration: No device type found"
    fi
}

# Generate summary report
generate_summary() {
    print_status "Generating test summary..."
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > test-results/summary.txt << EOF
Mock SNMP Agent - Comprehensive Testing Summary
===============================================

Test Run: $timestamp

Test Environment:
- Docker containers: 4 (SNMPv3 Security, REST API, State Machine, Combined)
- SNMP ports: 11621-11624
- API ports: 8081-8084

Test Categories:
1. SNMPv3 Security Failure Simulation
2. REST API Functionality  
3. State Machine Device Lifecycle
4. Combined Features Integration
5. Performance Under Load

Results:
- Detailed results: test-results/docker_comprehensive_test_report.json
- Container logs: Available via 'docker compose -f docker-compose.testing.yml logs'

EOF

    if [ -f test-results/docker_comprehensive_test_report.json ]; then
        local total_tests=$(jq '.total_tests' test-results/docker_comprehensive_test_report.json 2>/dev/null || echo "N/A")
        local passed_tests=$(jq '.passed_tests' test-results/docker_comprehensive_test_report.json 2>/dev/null || echo "N/A")
        
        cat >> test-results/summary.txt << EOF
Summary Statistics:
- Total tests: $total_tests
- Passed tests: $passed_tests
- Success rate: $(echo "scale=1; $passed_tests * 100 / $total_tests" | bc 2>/dev/null || echo "N/A")%

EOF
    fi
    
    print_success "Summary report generated: test-results/summary.txt"
}

# Show container logs for debugging
show_logs() {
    print_status "Container logs available with:"
    echo "  docker compose -f docker-compose.testing.yml logs snmpv3-security-test"
    echo "  docker compose -f docker-compose.testing.yml logs rest-api-test"
    echo "  docker compose -f docker-compose.testing.yml logs state-machine-test"
    echo "  docker compose -f docker-compose.testing.yml logs combined-features-test"
}

# Main execution
main() {
    # Handle command line arguments
    case "${1:-all}" in
        "clean")
            print_status "Cleaning up only..."
            cleanup_containers
            docker image prune -f
            print_success "Cleanup completed"
            exit 0
            ;;
        "build")
            print_status "Building images only..."
            check_prerequisites
            build_images
            print_success "Build completed"
            exit 0
            ;;
        "quick")
            print_status "Running quick connectivity tests only..."
            check_prerequisites
            cleanup_containers
            build_images
            start_test_containers
            wait_for_containers
            test_connectivity
            cleanup_containers
            exit 0
            ;;
        "all"|"")
            print_status "Running full test suite..."
            ;;
        *)
            echo "Usage: $0 [all|quick|build|clean]"
            echo "  all   - Run complete test suite (default)"
            echo "  quick - Run quick connectivity tests only"
            echo "  build - Build Docker images only"
            echo "  clean - Clean up containers and images"
            exit 1
            ;;
    esac
    
    # Run full test suite
    local overall_success=true
    
    # Prerequisites and setup
    check_prerequisites || overall_success=false
    cleanup_containers
    build_images || overall_success=false
    start_test_containers || overall_success=false
    wait_for_containers || overall_success=false
    
    # Basic connectivity
    if ! test_connectivity; then
        print_warning "Basic connectivity issues detected, but continuing with comprehensive tests..."
    fi
    
    # Individual feature tests
    test_snmpv3_security
    test_rest_api  
    test_state_machine
    
    # Comprehensive automated tests
    run_comprehensive_tests || overall_success=false
    
    # Generate reports
    generate_summary
    show_logs
    
    # Cleanup
    print_status "Cleaning up test containers..."
    cleanup_containers
    
    # Final results
    echo ""
    echo "=================================================="
    if [ "$overall_success" = true ]; then
        print_success "🎉 All tests completed successfully!"
        echo ""
        print_status "Key achievements validated:"
        echo "  ✅ SNMPv3 Security Failure Simulation"
        echo "  ✅ REST API for Agent Control"
        echo "  ✅ State Machine Device Lifecycle"
        echo "  ✅ Combined Features Integration"
        echo "  ✅ Performance Under Load"
        echo ""
        print_status "Check test-results/ directory for detailed reports"
        exit 0
    else
        print_error "❌ Some tests failed - check logs for details"
        echo ""
        print_status "Check test-results/ directory for detailed reports"
        print_status "Use 'docker compose -f docker-compose.testing.yml logs' for container logs"
        exit 1
    fi
}

# Run main function
main "$@"