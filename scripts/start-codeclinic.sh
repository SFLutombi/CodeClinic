#!/bin/bash

# CodeClinic Startup Script
# Simplified parallel scanning system with single ZAP instance and thread-based workers

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

# Check Docker resources
check_docker_resources() {
    print_status "Checking Docker resource allocation..."
    
    # Check available memory
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    
    print_status "System memory: ${total_mem}MB total, ${available_mem}MB available"
    
    if [ "$available_mem" -lt 2048 ]; then
        print_warning "Low available memory (${available_mem}MB). ZAP requires at least 2GB RAM"
        print_status "Consider closing other applications or increasing system RAM"
    else
        print_success "Sufficient memory available for ZAP"
    fi
    
    # Check Docker stats if available
    if docker stats --no-stream --format "table {{.MemUsage}}" codeclinic-zap 2>/dev/null | grep -q "MB\|GB"; then
        print_status "ZAP memory usage: $(docker stats --no-stream --format "{{.MemUsage}}" codeclinic-zap 2>/dev/null || echo "Unknown")"
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
        
        # Remove existing container if it exists
        docker stop codeclinic-redis 2>/dev/null
        docker rm codeclinic-redis 2>/dev/null
        
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

start_zap() {
    print_status "Starting ZAP instance..."
    
    print_status "Downloading ZAP image (this may take a moment)..."
    docker pull ghcr.io/zaproxy/zaproxy:stable > /dev/null 2>&1
    
    docker stop codeclinic-zap 2>/dev/null
    docker rm codeclinic-zap 2>/dev/null
    
    print_status "Starting ZAP on port 8080..."
    docker run -d \
        --name codeclinic-zap \
        -p 8080:8080 \
        ghcr.io/zaproxy/zaproxy:stable \
        zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
    
    print_status "Waiting for ZAP to be ready..."
    print_warning "ZAP is a heavyweight security scanner that can take 2-5 minutes to initialize on first startup"
    print_status "Please be patient - this is normal behavior"
    
    ready=false
    total_attempts=150  # 150 attempts × 2 seconds = 5 minutes
    for j in {1..150}; do
        # Show progress every 30 seconds (15 attempts)
        if [ $((j % 15)) -eq 0 ]; then
            elapsed=$((j * 2))
            print_status "Still waiting for ZAP... (${elapsed}s elapsed)"
        fi
        
        # Test multiple ZAP endpoints to ensure it's fully ready
        if curl -s http://localhost:8080/JSON/core/view/version/ > /dev/null 2>&1 && \
           curl -s http://localhost:8080/JSON/core/view/status/ > /dev/null 2>&1; then
            print_success "ZAP is ready after $((j * 2)) seconds"
            ready=true
            break
        fi
        
        # Also check if container is still running
        if ! docker ps | grep -q codeclinic-zap; then
            print_error "ZAP container stopped unexpectedly"
            print_status "Checking ZAP logs..."
            docker logs codeclinic-zap 2>/dev/null || print_warning "Could not retrieve ZAP logs"
            exit 1
        fi
        
        sleep 2
    done

    if [ "$ready" = false ]; then
        print_error "ZAP did not become ready after 5 minutes"
        print_status "This might be due to:"
        echo "  - Insufficient system resources (RAM/CPU)"
        echo "  - Network connectivity issues"
        echo "  - Docker resource constraints"
        echo ""
        print_status "Checking ZAP container status..."
        docker ps | grep codeclinic-zap || print_warning "ZAP container is not running"
        print_status "Checking ZAP logs..."
        docker logs codeclinic-zap --tail 20 2>/dev/null || print_warning "Could not retrieve ZAP logs"
        echo ""
        print_status "You can try:"
        echo "  1. Increase Docker memory allocation (4GB+ recommended)"
        echo "  2. Restart Docker service: sudo systemctl restart docker"
        echo "  3. Try again: ./scripts/start-codeclinic.sh"
        exit 1
    fi
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

# Start the backend with simplified parallel scanning
start_backend() {
    print_status "Starting CodeClinic backend with simplified parallel scanning..."
    
    cd src/backend
    source venv/bin/activate
    
    # Set environment variables
    export REDIS_URL="redis://localhost:6379"
    export ZAP_HOST="localhost"
    export ZAP_PORT="8080"
    
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

# Test simplified scanning system
test_scanning_system() {
    print_status "Testing simplified scanning system..."
    
    # Wait a moment for everything to be ready
    sleep 5
    
    # Test system status
    print_status "Checking system status..."
    curl -s http://localhost:8000/system/status | jq '.' || print_warning "Could not get system status"
    
    # Test health endpoint
    print_status "Checking health endpoint..."
    curl -s http://localhost:8000/health | jq '.' || print_warning "Could not get health status"
    
    print_success "Simplified scanning system is ready!"
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
    
    # Stop ZAP
    docker stop codeclinic-zap 2>/dev/null
    docker rm codeclinic-zap 2>/dev/null
    
    # Stop Redis
    docker stop codeclinic-redis 2>/dev/null
    docker rm codeclinic-redis 2>/dev/null
    
    print_success "Cleanup complete"
}

# Main setup function
main() {
    print_status "Starting CodeClinic Simplified Parallel Scanning Setup"
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
    
    # Check system resources
    check_docker_resources
    
    # Setup Redis
    if ! check_redis; then
        exit 1
    fi
    
    # Start single ZAP instance
    start_zap
    
    # Check ZAP resource usage
    print_status "Checking ZAP resource usage..."
    sleep 5  # Give ZAP a moment to settle
    check_docker_resources
    
    # Install dependencies
    install_dependencies
    
    # Start services
    start_backend
    start_frontend
    
    # Test the system
    test_scanning_system
    
    echo ""
    print_success "🎉 CodeClinic Simplified Parallel Scanning System is ready!"
    echo ""
    echo "📡 Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - System Status: http://localhost:8000/system/status"
    echo ""
    echo "🔍 ZAP Instance:"
    echo "  - ZAP: http://localhost:8080"
    echo ""
    echo "🚀 Performance: Thread-based parallel processing with single ZAP instance!"
    echo "💡 Benefits: Simpler setup, lower resource usage, real vulnerability scanning"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM

    # Wait for user to stop
    wait
}

# Run main function
main "$@"
