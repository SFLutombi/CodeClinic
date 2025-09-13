#!/bin/bash

# CodeClinic Startup Script
# This script starts all required services for CodeClinic

echo "🏥 Starting CodeClinic - Security Health Assessment Tool"
echo "=================================================="

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Starting ZAP with Docker..."
    docker run -d -p 8080:8080 --name zap owasp/zap2docker-stable
    echo "✅ ZAP started on port 8080"
else
    echo "⚠️  Docker not found. Please ensure ZAP is running on localhost:8080"
    echo "   Download from: https://www.zaproxy.org/download/"
fi

# Start Backend
echo ""
echo "🐍 Starting Backend Server..."
cd src/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start backend in background
echo "🚀 Starting FastAPI server..."
python run.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Frontend
echo ""
echo "⚛️  Starting Frontend Application..."
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start frontend
echo "🚀 Starting Next.js development server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 CodeClinic is starting up!"
echo "=================================================="
echo "📡 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo "🔍 ZAP Scanner: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping CodeClinic services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    if command -v docker &> /dev/null; then
        docker stop zap 2>/dev/null
        docker rm zap 2>/dev/null
    fi
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
