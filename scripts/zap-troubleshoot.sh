#!/bin/bash

# ZAP Troubleshooting Script
# Helps diagnose ZAP startup issues

echo "🔍 ZAP Troubleshooting Tool"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if ZAP container exists
check_zap_container() {
    print_status "Checking ZAP container status..."
    
    if docker ps -a | grep -q codeclinic-zap; then
        if docker ps | grep -q codeclinic-zap; then
            print_success "ZAP container is running"
            return 0
        else
            print_warning "ZAP container exists but is not running"
            return 1
        fi
    else
        print_error "ZAP container does not exist"
        return 1
    fi
}

# Check ZAP logs
check_zap_logs() {
    print_status "Checking ZAP container logs..."
    
    if docker ps -a | grep -q codeclinic-zap; then
        echo "--- Last 20 lines of ZAP logs ---"
        docker logs codeclinic-zap --tail 20 2>/dev/null || print_error "Could not retrieve logs"
        echo "--- End of logs ---"
        echo ""
    else
        print_error "No ZAP container found"
    fi
}

# Check ZAP connectivity
check_zap_connectivity() {
    print_status "Testing ZAP connectivity..."
    
    # Test version endpoint
    if curl -s http://localhost:8080/JSON/core/view/version/ > /dev/null 2>&1; then
        print_success "ZAP version endpoint is accessible"
        version=$(curl -s http://localhost:8080/JSON/core/view/version/ 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        print_status "ZAP version: $version"
    else
        print_error "ZAP version endpoint is not accessible"
    fi
    
    # Test status endpoint
    if curl -s http://localhost:8080/JSON/core/view/status/ > /dev/null 2>&1; then
        print_success "ZAP status endpoint is accessible"
        status=$(curl -s http://localhost:8080/JSON/core/view/status/ 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        print_status "ZAP status: $status"
    else
        print_error "ZAP status endpoint is not accessible"
    fi
}

# Check system resources
check_system_resources() {
    print_status "Checking system resources..."
    
    # Memory
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    used_mem=$((total_mem - available_mem))
    
    echo "Memory: ${used_mem}MB used / ${total_mem}MB total (${available_mem}MB available)"
    
    if [ "$available_mem" -lt 2048 ]; then
        print_warning "Low available memory (${available_mem}MB). ZAP requires at least 2GB RAM"
    else
        print_success "Sufficient memory available"
    fi
    
    # CPU load
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "CPU Load Average: $load_avg"
    
    # Disk space
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "Disk Usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 90 ]; then
        print_warning "High disk usage (${disk_usage}%)"
    fi
}

# Check Docker resources
check_docker_resources() {
    print_status "Checking Docker resources..."
    
    # Docker system info
    echo "Docker system info:"
    docker system df 2>/dev/null || print_error "Could not get Docker system info"
    echo ""
    
    # Check if ZAP container is consuming too much memory
    if docker ps | grep -q codeclinic-zap; then
        print_status "ZAP container resource usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" codeclinic-zap 2>/dev/null || print_warning "Could not get ZAP stats"
    fi
}

# Restart ZAP
restart_zap() {
    print_status "Restarting ZAP container..."
    
    # Stop existing container
    docker stop codeclinic-zap 2>/dev/null
    docker rm codeclinic-zap 2>/dev/null
    
    # Start new container
    docker run -d \
        --name codeclinic-zap \
        -p 8080:8080 \
        ghcr.io/zaproxy/zaproxy:stable \
        zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true
    
    print_status "Waiting for ZAP to start..."
    sleep 10
    
    # Check if it's running
    if docker ps | grep -q codeclinic-zap; then
        print_success "ZAP container restarted successfully"
        print_status "Wait 2-5 minutes for ZAP to fully initialize"
    else
        print_error "Failed to restart ZAP container"
    fi
}

# Main troubleshooting function
main() {
    echo "Starting ZAP troubleshooting..."
    echo ""
    
    # Check system resources first
    check_system_resources
    echo ""
    
    # Check Docker resources
    check_docker_resources
    echo ""
    
    # Check ZAP container
    if check_zap_container; then
        # Check connectivity
        check_zap_connectivity
        echo ""
    fi
    
    # Always show logs
    check_zap_logs
    echo ""
    
    # Provide recommendations
    print_status "Troubleshooting recommendations:"
    echo ""
    echo "1. If ZAP container is not running:"
    echo "   ./scripts/zap-troubleshoot.sh --restart"
    echo ""
    echo "2. If ZAP is running but not responding:"
    echo "   - Wait 2-5 minutes for full initialization"
    echo "   - Check system resources (RAM, CPU)"
    echo "   - Restart ZAP: ./scripts/zap-troubleshoot.sh --restart"
    echo ""
    echo "3. If system resources are low:"
    echo "   - Close other applications"
    echo "   - Increase Docker memory allocation"
    echo "   - Restart Docker: sudo systemctl restart docker"
    echo ""
    echo "4. For persistent issues:"
    echo "   - Check Docker logs: docker logs codeclinic-zap"
    echo "   - Try different ZAP version"
    echo "   - Check network connectivity"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    --restart)
        restart_zap
        ;;
    --logs)
        check_zap_logs
        ;;
    --resources)
        check_system_resources
        check_docker_resources
        ;;
    *)
        main
        ;;
esac
