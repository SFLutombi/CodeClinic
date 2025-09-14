
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

### Optional AI Features
- **Google Gemini API Key** (for AI-powered vulnerability explanations)
- **Supabase Account** (for user authentication and data persistence)

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

# Optional: Install AI dependencies
pip install google-generativeai supabase

# Create .env file with your API keys (optional)
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
echo "SUPABASE_URL=your_supabase_url_here" >> .env
echo "SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key_here" >> .env
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd src/frontend

# Install Node.js dependencies
npm install

# Optional: Create .env.local file for additional features
echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here" > .env.local
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here" >> .env.local
echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here" >> .env.local
echo "CLERK_SECRET_KEY=your_clerk_secret_key_here" >> .env.local
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

### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 2: Manual Setup
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

## 🎯 Features

### Basic Mode (No AI/Database)
- ✅ Real OWASP ZAP security scanning
- ✅ Interactive security health dashboard
- ✅ Vulnerability analysis and reporting
- ✅ Medical clinic-inspired UI
- ✅ Page selection and targeted scanning

### Advanced Mode (With AI/Database)
- ✅ AI-powered vulnerability explanations (Gemini API)
- ✅ User authentication and progress tracking
- ✅ Interactive quiz system
- ✅ Leaderboard and rankings
- ✅ XP and badge system

---

## 🐳 Docker Architecture

### Simplified Container Setup
The architecture uses a simplified approach:

```yaml
services:
  redis:     # Task coordination and caching
  zap:       # Single ZAP instance (replaces 4 workers)
  backend:   # FastAPI application
  frontend:  # Next.js application
```

### Benefits of Architecture
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

6. **AI Features Not Working**
   - **Error: `Gemini API not available`**
     - Add your Gemini API key to the `.env` file
     - Install with: `pip install google-generativeai`
   - **Error: `Supabase client not available`**
     - This is expected if you haven't set up Supabase yet
     - The backend will work without database features
     - Install with: `pip install supabase`

### Getting Help
- Check the API documentation at http://localhost:8000/docs
- Review container logs: `docker-compose logs -f`
- Ensure all services are running on correct ports
- Check health endpoints: http://localhost:8000/health

---

## 📝 Environment Variables

### Backend (.env) - Optional
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
```

### Frontend (.env.local) - Optional
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
```

---

## 📝 Development Notes

- **Backend**: FastAPI with automatic API documentation and real ZAP integration
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Scanning**: Real OWASP ZAP API integration with thread-based parallelism
- **Architecture**: Simplified single-ZAP instance with Redis coordination
- **Theme**: Medical clinic-inspired UI for security assessment
- **AI Integration**: Optional Gemini API for intelligent vulnerability explanations
