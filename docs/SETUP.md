> *This document serves as a template for you to write **setup** instructions for your project.* 

> Depending on the scale/complexity of your project, it may prove beneficial to have a **Python/Batch/Bash** script in the `scripts/` directory which *automatically sets-up* the project.

# Setup Instructions

Follow the steps below to set up and run CodeClinic - your security health assessment tool.

---

## 📦 Requirements

### Backend Requirements
- **Python 3.8+** (recommended: Python 3.10+)
- **pip** (Python package manager)
- **OWASP ZAP** (for security scanning)
  - Download from: https://www.zaproxy.org/download/
  - Or install via Docker: `docker run -d -p 8080:8080 owasp/zap2docker-stable`

### Frontend Requirements
- **Node.js 18+** (recommended: Node.js 20+)
- **npm** (comes with Node.js)

### Optional
- **Docker** (for containerized deployment)
- **Docker Compose** (for multi-container setup)

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
python -m venv venv

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

### 4. ZAP Setup (Required for Security Scanning)

#### Option A: Docker (Recommended)
```bash
# Run ZAP in Docker
docker run -d -p 8080:8080 --name zap owasp/zap2docker-stable
```

#### Option B: Local Installation
1. Download ZAP from https://www.zaproxy.org/download/
2. Extract and run ZAP
3. Ensure ZAP is running on `localhost:8080`

---

## ▶️ Running the Project

### 1. Start ZAP (if not using Docker)
Make sure OWASP ZAP is running on `localhost:8080`

### 2. Start the Backend Server
```bash
# From src/backend directory
python run.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at:
- **API Base**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Start the Frontend Application
```bash
# From src/frontend directory
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

### 4. Using the Application
1. Open http://localhost:3000 in your browser
2. Enter a website URL to scan
3. Choose scan type (Full Site or Selective Pages)
4. Wait for the scan to complete
5. Review the security health report

---

## 🐳 Docker Setup (Alternative)

### Using Docker Compose
```bash
# From project root
docker-compose up -d
```

This will start:
- ZAP scanner on port 8080
- Backend API on port 8000
- Frontend on port 3000

### Manual Docker Setup
```bash
# Start ZAP
docker run -d -p 8080:8080 --name zap owasp/zap2docker-stable

# Build and run backend
cd src/backend
docker build -t codeclinic-backend .
docker run -d -p 8000:8000 --name codeclinic-backend codeclinic-backend

# Build and run frontend
cd src/frontend
docker build -t codeclinic-frontend .
docker run -d -p 3000:3000 --name codeclinic-frontend codeclinic-frontend
```

---

## 🔧 Troubleshooting

### Common Issues

1. **ZAP Connection Error**
   - Ensure ZAP is running on port 8080
   - Check firewall settings
   - Verify ZAP API is accessible

2. **Backend Import Errors**
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt`

3. **Frontend Build Errors**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version: `node --version`

4. **CORS Issues**
   - Ensure backend is running on port 8000
   - Check frontend is running on port 3000
   - Verify CORS settings in backend

### Getting Help
- Check the API documentation at http://localhost:8000/docs
- Review the logs in the terminal
- Ensure all services are running on correct ports

---

## 📝 Development Notes

- Backend uses FastAPI with automatic API documentation
- Frontend uses Next.js with TypeScript and Tailwind CSS
- ZAP integration includes fallback mock data for demo purposes
- All components are designed with a medical clinic theme
