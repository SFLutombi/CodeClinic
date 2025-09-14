
> *This document serves as a template for you to write **setup** instructions for your project.* 

> Depending on the scale/complexity of your project, it may prove beneficial to have a **Python/Batch/Bash** script in the `scripts/` directory which *automatically sets-up* the project.

# Setup Instructions

Follow the steps below to set up and run CodeClinic - your security health assessment tool with simplified parallel scanning.

---

## 📦 Requirements

### Backend Requirements
- **Python 3.8+** (recommended: Python 3.10+)
- **pip** (Python package manager)
- **Redis** (for task coordination and caching)

### Frontend Requirements
- **Node.js 18+** (recommended: Node.js 20+)
- **npm** (comes with Node.js)

### Infrastructure Requirements
- **Docker** (for ZAP and Redis containers)
- **Docker Compose** (recommended for easy setup)
- **OWASP ZAP** (automatically started via Docker)

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/SFLutombi/CodeClinic
cd CodeClinic
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd src/backend

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd src/frontend

# Install Node.js dependencies
npm install
```

### 4. Infrastructure Setup

#### Option A: Docker Compose (Recommended)
```bash
# Start all services with one command
docker-compose up -d

# This starts:
# - Redis (port 6379)
# - ZAP (port 8080)
# - Backend API (port 8000)
# - Frontend (port 3000)
```

#### Option B: Manual Docker Setup
```bash
# Start Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Start ZAP
docker run -d -p 8080:8080 --name zap ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true
```

---

## ▶️ Running the Project

### Option 1: Automated Startup Script (Recommended)
```bash
# Start all services with one command
./scripts/start-codeclinic.sh

# This script will:
# - Check Docker installation and permissions
# - Start Redis container
# - Start ZAP with proper API configuration
# - Install Python dependencies
# - Start backend and frontend services
# - Run system tests
```

### Option 2: Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 3: Manual Setup
```bash
# 1. Start infrastructure (if not using Docker Compose)
docker run -d -p 6379:6379 --name redis redis:7-alpine
docker run -d -p 8080:8080 --name zap ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true

# 2. Start Backend
cd src/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 run.py

# 3. Start Frontend (in another terminal)
cd src/frontend
npm run dev
```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **ZAP Interface**: http://localhost:8080

### Using the Application
1. Open http://localhost:3000 in your browser
2. Enter a website URL to scan
3. Choose scan type (Full Site or Selective Pages)
4. Wait for the scan to complete (real ZAP scanning)
5. Review the security health report with actual vulnerabilities

---

## 🐳 Docker Architecture

### Simplified Container Setup
The new architecture uses a simplified approach:

```yaml
services:
  redis:     # Task coordination and caching
  zap:       # Single ZAP instance (replaces 4 workers)
  backend:   # FastAPI application
  frontend:  # Next.js application
```

### Benefits of New Architecture
- **Simpler Setup**: One ZAP container instead of four
- **Better Performance**: Thread-based parallelism
- **Lower Resource Usage**: Reduced memory and CPU requirements
- **Easier Debugging**: Fewer moving parts
- **Real Scanning**: Actual ZAP API integration, no mock data

---

## 🔧 Troubleshooting

### Common Issues

1. **ZAP Connection Error**
   - Ensure ZAP container is running: `docker ps | grep zap`
   - Check ZAP is accessible: `curl http://localhost:8080/JSON/core/view/version/`
   - Use troubleshooting script: `./scripts/zap-troubleshoot.sh`
   - Restart ZAP container: `./scripts/zap-troubleshoot.sh --restart`

2. **Redis Connection Error**
   - Ensure Redis container is running: `docker ps | grep redis`
   - Check Redis connectivity: `docker exec codeclinic-redis redis-cli ping`
   - Restart Redis container: `docker restart codeclinic-redis`

3. **Backend Import Errors**
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt`
   - Check Python version: `python3 --version`

4. **Frontend Build Errors**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version: `node --version`
   - Update dependencies: `npm update`

5. **Docker Compose Issues**
   - Check all services: `docker-compose ps`
   - View logs: `docker-compose logs [service-name]`
   - Restart all services: `docker-compose restart`

6. **Startup Script Issues**
   - ZAP takes 2-5 minutes to initialize (this is normal)
   - If ZAP fails to start: `./scripts/zap-troubleshoot.sh`
   - Check system resources: `./scripts/zap-troubleshoot.sh --resources`
   - View ZAP logs: `./scripts/zap-troubleshoot.sh --logs`

### Getting Help
- Check the API documentation at http://localhost:8000/docs
- Review container logs: `docker-compose logs -f`
- Ensure all services are running on correct ports
- Check health endpoints: http://localhost:8000/health

---

## 📝 Development Notes

- **Backend**: FastAPI with automatic API documentation and real ZAP integration
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Scanning**: Real OWASP ZAP API integration with thread-based parallelism
- **Architecture**: Simplified single-ZAP instance with Redis coordination
- **Theme**: Medical clinic-inspired UI for security assessment
