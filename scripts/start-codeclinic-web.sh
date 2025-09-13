#!/bin/bash

# CodeClinic Web-Ready Startup Script
# No Docker permissions required - uses direct Python/Node.js

echo "🌐 Starting CodeClinic - Web-Ready Mode"
echo "========================================"

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

# Check Python
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        print_success "Python 3 is installed"
        return 0
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

# Check Node.js
check_node() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        print_success "Node.js is installed"
        return 0
    else
        print_error "Node.js is not installed"
        return 1
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    cd src/backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
    cd ../..
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    cd src/frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    print_success "Node.js dependencies installed"
    cd ../..
}

# Start backend (without Docker)
start_backend() {
    print_status "Starting backend server..."
    cd src/backend
    source venv/bin/activate
    
    # Set environment variables for web mode
    export REDIS_URL="redis://localhost:6379"
    export ZAP_WORKERS="1"  # Single worker for web mode
    export WEB_MODE="true"
    
    # Start backend
    python run.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend started successfully"
            break
        fi
        sleep 2
    done
    
    cd ../..
}

# Start frontend
start_frontend() {
    print_status "Starting frontend application..."
    cd src/frontend
    
    # Start frontend
    npm run dev &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    print_status "Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend started successfully"
            break
        fi
        sleep 2
    done
    
    cd ../..
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    
    # Stop backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # Stop frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    print_success "Cleanup complete"
}

# Main function
main() {
    print_status "Starting CodeClinic in Web-Ready Mode"
    echo ""
    
    # Check prerequisites
    if ! check_python; then
        exit 1
    fi
    
    if ! check_node; then
        exit 1
    fi
    
    # Install dependencies
    install_python_deps
    install_node_deps
    
    # Start services
    start_backend
    start_frontend
    
    echo ""
    print_success "🎉 CodeClinic is running in Web-Ready Mode!"
    echo ""
    echo "📡 Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "💡 Note: This mode uses sequential scanning (no Docker required)"
    echo "   For parallel scanning, use: ./scripts/start-codeclinic.sh"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Wait for user to stop
    wait
}

# Run main function
main "$@"
