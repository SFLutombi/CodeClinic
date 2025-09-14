#!/bin/bash

# CodeClinic Docker Compose Startup Script
# Simple one-command startup using Docker Compose

echo "🏥 Starting CodeClinic with Docker Compose"
echo "=========================================="

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

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        return 0
    else
        print_error "Docker is not installed. Please install Docker first."
        print_status "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi
}

# Check Docker permissions
check_docker_permissions() {
    print_status "Checking Docker permissions..."
    if docker ps > /dev/null 2>&1; then
        print_success "Docker permissions OK"
        return 0
    else
        print_error "Docker permission denied!"
        echo ""
        echo "🔧 DOCKER PERMISSIONS FIX REQUIRED:"
        echo "=================================="
        echo ""
        echo "1. Add your user to docker group:"
        echo "   sudo usermod -aG docker $USER"
        echo ""
        echo "2. Log out and log back in (or restart your computer)"
        echo ""
        echo "3. Or start a new terminal session and try again"
        echo ""
        echo "4. Quick fix - run with sudo (not recommended):"
        echo "   sudo ./scripts/start-docker.sh"
        echo ""
        return 1
    fi
}

# Check if Docker Compose is installed
check_docker_compose() {
    print_status "Checking Docker Compose installation..."
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose is installed"
        return 0
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_status "Visit: https://docs.docker.com/compose/install/"
        return 1
    fi
}

# Start services with Docker Compose
start_services() {
    print_status "Starting CodeClinic services with Docker Compose..."
    
    # Stop any existing containers
    print_status "Stopping any existing containers..."
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null
    
    # Start services
    print_status "Starting all services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are running
    if docker ps | grep -q codeclinic; then
        print_success "All services started successfully!"
        return 0
    else
        print_error "Failed to start services"
        return 1
    fi
}

# Test services
test_services() {
    print_status "Testing services..."
    
    # Test backend health
    print_status "Testing backend health..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
            break
        fi
        sleep 2
    done
    
    # Test frontend
    print_status "Testing frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is accessible"
            break
        fi
        sleep 2
    done
    
    # Test ZAP
    print_status "Testing ZAP..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/JSON/core/view/version/ > /dev/null 2>&1; then
            print_success "ZAP is ready"
            break
        fi
        sleep 2
    done
}

# Cleanup function
cleanup() {
    print_status "Stopping CodeClinic services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    print_success "Services stopped"
}

# Main function
main() {
    # Check prerequisites
    if ! check_docker; then
        exit 1
    fi
    
    if ! check_docker_permissions; then
        exit 1
    fi
    
    if ! check_docker_compose; then
        exit 1
    fi
    
    # Start services
    if ! start_services; then
        exit 1
    fi
    
    # Test services
    test_services
    
    echo ""
    print_success "🎉 CodeClinic is ready!"
    echo ""
    echo "📡 Services:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - ZAP: http://localhost:8080"
    echo ""
    echo "🚀 Features:"
    echo "  - Real ZAP vulnerability scanning"
    echo "  - Thread-based parallel processing"
    echo "  - Medical clinic-themed UI"
    echo "  - Comprehensive security reports"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM

    # Wait for user to stop
    wait
}

# Run main function
main "$@"
