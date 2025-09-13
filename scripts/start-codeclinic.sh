#!/bin/bash

# CodeClinic Startup Script
# High-performance parallel scanning system with multiple ZAP workers

echo "🏥 Starting CodeClinic - Security Health Assessment Tool"
echo "========================================================"

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
        echo "   sudo ./scripts/start-codeclinic.sh"
        echo ""
        echo "5. Or fix permissions now:"
        echo "   sudo usermod -aG docker $USER && echo 'Please logout/login or restart'"
        echo ""
        echo "⚠️  The group change requires a new login session to take effect!"
        echo ""
        return 1
    fi
}

# Check if Docker Compose is installed
check_docker_compose() {
    print_status "Checking Docker Compose installation..."
    if command -v docker-compose &> /dev/null || /usr/local/bin/docker-compose --version &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose is installed"
        return 0
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_status "Visit: https://docs.docker.com/compose/install/"
        return 1
    fi
}

# Check if Redis is available
check_redis() {
    print_status "Checking Redis availability..."
    if docker ps | grep -q redis; then
        print_success "Redis is running"
        return 0
    else
        print_warning "Redis is not running. Starting Redis..."
        print_status "Downloading Redis image (this may take a moment)..."
        docker pull redis:7-alpine --quiet
        docker run -d --name codeclinic-redis -p 6379:6379 redis:7-alpine
        sleep 5
        if docker ps | grep -q redis; then
            print_success "Redis started successfully"
            return 0
        else
            print_error "Failed to start Redis"
            return 1
        fi
    fi
}

# Start ZAP workers
start_zap_workers() {
    print_status "Starting ZAP worker instances..."
    
    # Number of workers (default: 4)
    WORKERS=${1:-4}
    
    # Download ZAP image first
    print_status "Downloading ZAP image (this may take a moment)..."
    docker pull owasp/zap2docker-stable --quiet
    
    for i in $(seq 1 $WORKERS); do
        PORT=$((8080 + i - 1))
        print_status "Starting ZAP worker $i on port $PORT..."
        
        # Stop existing container if running
        docker stop codeclinic-zap-$i 2>/dev/null
        docker rm codeclinic-zap-$i 2>/dev/null
        
        # Start new ZAP instance
        docker run -d \
            --name codeclinic-zap-$i \
            -p $PORT:8080 \
            owasp/zap2docker-stable \
            zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true
        
        # Wait for ZAP to be ready
        print_status "Waiting for ZAP worker $i to be ready..."
        for j in {1..30}; do
            if curl -s http://localhost:$PORT/JSON/core/view/version/ > /dev/null 2>&1; then
                print_success "ZAP worker $i is ready"
                break
            fi
            sleep 2
        done
    done
}

# Install Python dependencies
install_dependencies() {
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
    print_status "Installing requirements..."
pip install -r requirements.txt

    print_success "Dependencies installed successfully"
    cd ../..
}

# Start the backend with parallel scanning
start_backend() {
    print_status "Starting CodeClinic backend with parallel scanning..."
    
    cd src/backend
    source venv/bin/activate
    
    # Set environment variables
    export REDIS_URL="redis://localhost:6379"
    export ZAP_WORKERS="4"
    export ZAP_PORTS="8080,8081,8082,8083"
    
    # Start the backend
    print_status "Starting FastAPI server..."
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

# Start the frontend
start_frontend() {
    print_status "Starting CodeClinic frontend..."
    
    cd src/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
    npm install
fi

    # Start the frontend
    print_status "Starting Next.js development server..."
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

# Test parallel scanning
test_parallel_scanning() {
    print_status "Testing parallel scanning system..."
    
    # Wait a moment for everything to be ready
    sleep 5
    
    # Test system status
    print_status "Checking system status..."
    curl -s http://localhost:8000/system/status | jq '.' || print_warning "Could not get system status"
    
    # Test health endpoint
    print_status "Checking health endpoint..."
    curl -s http://localhost:8000/health | jq '.' || print_warning "Could not get health status"
    
    print_success "Parallel scanning system is ready!"
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
    
    # Stop ZAP workers
    for i in {1..4}; do
        docker stop codeclinic-zap-$i 2>/dev/null
        docker rm codeclinic-zap-$i 2>/dev/null
    done
    
    # Stop Redis
    docker stop codeclinic-redis 2>/dev/null
    docker rm codeclinic-redis 2>/dev/null
    
    print_success "Cleanup complete"
}

# Main setup function
main() {
    print_status "Starting CodeClinic Parallel Scanning Setup"
    echo ""
    
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
    
    # Setup Redis
    if ! check_redis; then
        exit 1
    fi
    
    # Start ZAP workers
    start_zap_workers 4
    
    # Install dependencies
    install_dependencies
    
    # Start services
    start_backend
    start_frontend
    
    # Test the system
    test_parallel_scanning
    
    echo ""
    print_success "🎉 CodeClinic Parallel Scanning System is ready!"
    echo ""
    echo "📡 Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - System Status: http://localhost:8000/system/status"
    echo ""
    echo "🔍 ZAP Workers:"
    echo "  - Worker 1: http://localhost:8080"
    echo "  - Worker 2: http://localhost:8081"
    echo "  - Worker 3: http://localhost:8082"
    echo "  - Worker 4: http://localhost:8083"
    echo ""
    echo "🚀 Performance: Up to 4x faster scanning with parallel processing!"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
}

# Run main function
main "$@"
