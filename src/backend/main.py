"""
CodeClinic Backend - FastAPI Server
Main application entry point for the security assessment API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from typing import List, Optional
import logging

from models import ScanRequest, ScanResponse, Vulnerability, ScanStatus
from zap_integration import ZAPScanner
from url_validator import URLValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CodeClinic API",
    description="Security assessment API for web applications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
zap_scanner = ZAPScanner()
url_validator = URLValidator()

# In-memory storage for scan results (in production, use Redis or database)
scan_results = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CodeClinic API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "zap_available": await zap_scanner.is_zap_available(),
        "version": "1.0.0"
    }

@app.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start a security scan for the provided URL
    
    Args:
        request: ScanRequest containing URL and scan type
        
    Returns:
        ScanResponse with scan ID and initial status
    """
    try:
        # Convert Pydantic URL to string
        url_str = str(request.url)
        
        # Validate URL
        if not url_validator.is_valid_url(url_str):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Check if URL is accessible
        if not await url_validator.is_accessible(url_str):
            raise HTTPException(status_code=400, detail="URL is not accessible")
        
        # Generate scan ID
        scan_id = f"scan_{len(scan_results) + 1}_{int(asyncio.get_event_loop().time())}"
        
        # Initialize scan result
        scan_results[scan_id] = {
            "id": scan_id,
            "url": url_str,
            "scan_type": request.scan_type,
            "status": "initializing",
            "vulnerabilities": [],
            "pages": [],
            "progress": 0
        }
        
        # Start background scan
        background_tasks.add_task(run_scan, scan_id, url_str, request.scan_type)
        
        return ScanResponse(
            scan_id=scan_id,
            status="started",
            message="Scan initiated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get the current status of a scan"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan_results[scan_id]

@app.get("/scan/{scan_id}/pages")
async def get_discovered_pages(scan_id: str):
    """Get discovered pages for selective scanning"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_data = scan_results[scan_id]
    if scan_data["status"] != "pages_discovered":
        raise HTTPException(status_code=400, detail="Pages not yet discovered")
    
    return {"pages": scan_data["pages"]}

@app.post("/scan/{scan_id}/select-pages")
async def select_pages_for_scan(scan_id: str, selected_pages: List[str]):
    """Select specific pages for scanning"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_data = scan_results[scan_id]
    scan_data["selected_pages"] = selected_pages
    scan_data["status"] = "scanning_selected_pages"
    
    # Continue with selected pages scan
    # This would trigger the actual ZAP scan
    
    return {"message": "Pages selected, scan continuing"}

@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get the final scan results"""
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_data = scan_results[scan_id]
    if scan_data["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Scan not yet completed")
    
    return scan_data

async def run_scan(scan_id: str, url: str, scan_type: str):
    """Background task to run the actual scan"""
    try:
        logger.info(f"Starting scan {scan_id} for URL: {url}")
        scan_results[scan_id]["status"] = "discovering_pages"
        scan_results[scan_id]["progress"] = 10
        
        # Discover pages
        logger.info(f"Discovering pages for {url}")
        pages = await zap_scanner.discover_pages(url)
        scan_results[scan_id]["pages"] = pages
        scan_results[scan_id]["status"] = "pages_discovered"
        scan_results[scan_id]["progress"] = 30
        
        # If full site scan, continue automatically
        if scan_type == "full_site":
            scan_results[scan_id]["status"] = "scanning"
            scan_results[scan_id]["progress"] = 50
            
            # Run ZAP scan
            logger.info(f"Running ZAP scan for {url}")
            vulnerabilities = await zap_scanner.run_scan(url, pages)
            scan_results[scan_id]["vulnerabilities"] = vulnerabilities
            scan_results[scan_id]["status"] = "completed"
            scan_results[scan_id]["progress"] = 100
            logger.info(f"Scan {scan_id} completed with {len(vulnerabilities)} vulnerabilities")
            
        # If selective scan, wait for page selection
        else:
            scan_results[scan_id]["status"] = "waiting_for_selection"
            
    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {str(e)}", exc_info=True)
        scan_results[scan_id]["status"] = "failed"
        scan_results[scan_id]["error"] = str(e)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
