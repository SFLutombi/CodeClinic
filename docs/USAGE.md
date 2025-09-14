# CodeClinic Usage Guide

Welcome to CodeClinic - your security health assessment tool! This guide will help you get started with scanning web applications for security vulnerabilities.

---

## ▶️ Quick Start

### 1. Start the Application
```bash
# Start all services with Docker Compose
docker-compose up -d

# Or start manually (see SETUP.md for details)
```

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🖥️ How to Use CodeClinic

### Step 1: Enter Target URL
1. Open http://localhost:3000 in your browser
2. Enter the URL of the website you want to scan
3. Choose scan type:
   - **Full Site**: Comprehensive scan of the entire website
   - **Selective Pages**: Scan specific pages only

### Step 2: Start the Scan
1. Click "Start Security Assessment"
2. The system will:
   - Validate the URL
   - Set up the target in ZAP
   - Begin spider scanning to discover pages
   - Start active vulnerability scanning

### Step 3: Monitor Progress
- Watch real-time progress updates
- See current scanning phase (Spider → Active Scan → Results)
- Monitor discovered pages and vulnerabilities

### Step 4: Review Results
Once scanning completes, you'll see:

#### 🏥 Vitals Dashboard
- **Overall Health Score**: 0-100 security rating
- **Severity Breakdown**: High, Medium, Low, and Informational issues
- **Visual Health Indicators**: Color-coded status (🟢 Excellent, 🔵 Good, 🟡 Fair, 🟠 Poor, 🔴 Critical)

#### 🧪 Lab Results
- **Detailed Vulnerability List**: Each finding with:
  - Vulnerability type and severity
  - Affected URL and parameters
  - Evidence of the issue
  - Recommended solutions
  - CWE ID and confidence level

---

## 🔍 Understanding Scan Results

### Vulnerability Types
- **XSS (Cross-Site Scripting)**: Script injection vulnerabilities
- **SQL Injection**: Database query manipulation
- **CSRF (Cross-Site Request Forgery)**: Unauthorized action execution
- **Insecure Headers**: Missing security headers
- **SSL/TLS Issues**: Encryption and certificate problems
- **Authentication Issues**: Login and session vulnerabilities

### Severity Levels
- **High**: Critical security issues requiring immediate attention
- **Medium**: Important security concerns that should be addressed
- **Low**: Minor security issues and best practice violations
- **Informational**: General security recommendations

### Health Score Calculation
- **100-80**: Excellent security posture
- **79-60**: Good security with minor issues
- **59-40**: Fair security requiring attention
- **39-20**: Poor security with significant vulnerabilities
- **19-0**: Critical security issues requiring urgent remediation

---

## 🎥 Demo

Check out the Demos: 
- [Demo Video](../demo/demo.mp4)
- [Demo Presentation](../demo/demo.pptx)

---

## 📌 Important Notes

### ⚠️ Ethical Usage
- **Only scan websites you own or have explicit permission to test**
- **Do not use this tool for malicious purposes**
- **Respect robots.txt and rate limiting**

### 🔧 Technical Notes
- **Real ZAP Integration**: All scans use actual OWASP ZAP security testing
- **Parallel Processing**: Thread-based workers for efficient scanning
- **Progress Tracking**: Real-time updates via Redis coordination
- **Comprehensive Results**: Full vulnerability details with remediation guidance

### 🚀 Performance Tips
- **Full Site Scans**: Can take 5-15 minutes depending on site size
- **Selective Scans**: Faster for testing specific pages
- **Resource Usage**: Single ZAP instance with thread-based parallelism
- **Concurrent Scans**: Multiple scans can run simultaneously

### 🛠️ Troubleshooting
- **Scan Timeouts**: Large sites may need longer scan times
- **Connection Issues**: Ensure target URL is accessible
- **ZAP Errors**: Check ZAP container logs for detailed error information
- **Redis Issues**: Verify Redis container is running and accessible

---

## 📊 API Usage

For developers wanting to integrate with CodeClinic:

### Start a Scan
```bash
curl -X POST "http://localhost:8000/scan/start" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "scan_type": "full_site"}'
```

### Check Scan Status
```bash
curl "http://localhost:8000/scan/{scan_id}/status"
```

### Get Results
```bash
curl "http://localhost:8000/scan/{scan_id}/results"
```

### System Status
```bash
curl "http://localhost:8000/system/status"
```

For complete API documentation, visit: http://localhost:8000/docs
