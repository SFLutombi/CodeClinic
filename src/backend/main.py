"""
CodeClinic Backend - FastAPI Server
Main application entry point for the security assessment API
Simplified parallel scanning with single ZAP instance and thread-based workers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Optional
import logging

from models import ScanRequest, ScanResponse, CrawlRequest, PageSelectionRequest
from url_validator import URLValidator
from simple_scanner import SimpleParallelScanner

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
url_validator = URLValidator()

# Initialize simplified parallel scanning system
scanner = SimpleParallelScanner(max_workers=4)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CodeClinic API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "scanner_status": scanner.get_worker_status(),
        "version": "1.0.0"
    }

@app.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """
    Start a security scan for the provided URL
    Uses simplified parallel scanning with thread-based workers
    
    Args:
        request: ScanRequest containing URL and scan type
        
    Returns:
        ScanResponse with scan ID and initial status
    """
    try:
        # Convert Pydantic URL to string
        url_str = str(request.url)
        
        # Basic URL format validation only
        if not url_validator.is_valid_url(url_str):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        logger.info(f"Starting scan for URL: {url_str}")
        
        # Start scan using simplified scanner
        task_id = await scanner.start_scan(url_str, request.scan_type)
        message = "Scan initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get the current status of a scan"""
    try:
        # Get status from simplified scanner
        status = scanner.get_task_status(scan_id)
        if not status:
            raise HTTPException(status_code=404, detail="Scan not found")
        return status
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan status")


@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get the final scan results"""
    try:
        # Get task status from simplified scanner
        task_status = scanner.get_task_status(scan_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if task_status["status"] not in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Scan not yet completed")
        
        # Return results
        return {
            "id": scan_id,
            "status": task_status["status"],
            "progress": task_status["progress"],
            "vulnerabilities": task_status["results"].get("vulnerabilities", []) if task_status["results"] else [],
            "total_vulnerabilities": len(task_status["results"].get("vulnerabilities", [])) if task_status["results"] else 0,
            "scan_duration": task_status["results"].get("scan_duration", 0) if task_status["results"] else 0,
            "error": task_status.get("error")
        }
    except Exception as e:
        logger.error(f"Error getting scan results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan results")


@app.post("/crawl/start", response_model=ScanResponse)
async def start_crawl(request: CrawlRequest):
    """
    Start crawling a website to discover pages
    This is the first step in the improved workflow
    """
    try:
        # Convert Pydantic URL to string
        url_str = str(request.url)
        
        # Basic URL format validation only
        if not url_validator.is_valid_url(url_str):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        logger.info(f"Starting crawl for URL: {url_str}")
        
        # Start crawl using simplified scanner
        task_id = await scanner.start_crawl(url_str)
        message = "Crawl initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start crawl: {str(e)}")


@app.get("/crawl/{scan_id}/pages")
async def get_discovered_pages(scan_id: str):
    """Get the pages discovered during crawling"""
    try:
        # Get task status from simplified scanner
        task_status = scanner.get_task_status(scan_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Crawl not found")
        
        if task_status["status"] not in ["completed"]:
            raise HTTPException(status_code=400, detail="Crawl not yet completed")
        
        # Return discovered pages
        return {
            "scan_id": scan_id,
            "pages": task_status["results"].get("discovered_pages", []) if task_status["results"] else [],
            "total_pages": len(task_status["results"].get("discovered_pages", [])) if task_status["results"] else 0
        }
    except Exception as e:
        logger.error(f"Error getting discovered pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get discovered pages")


@app.post("/scan/start-selected", response_model=ScanResponse)
async def start_selected_scan(request: PageSelectionRequest):
    """
    Start scanning selected pages after crawling
    This is the second step in the improved workflow
    """
    try:
        # Start scan for selected pages using simplified scanner
        task_id = await scanner.start_scan_selected(request.scan_id, request.selected_pages)
        message = "Selected page scan initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting selected scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start selected scan: {str(e)}")


@app.get("/system/status")
async def get_system_status():
    """Get system-wide status and performance metrics"""
    try:
        return {
            "scanner_status": scanner.get_worker_status(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {"error": "Failed to get system status"}

@app.on_event("startup")
async def startup_event():
    """Initialize simplified parallel scanning system on startup"""
    try:
        logger.info("Starting CodeClinic with simplified parallel scanning...")
        
        # Initialize simplified scanner
        if await scanner.initialize():
            logger.info("✅ Simplified parallel scanning system initialized successfully")
            logger.info(f"🚀 Performance boost: {scanner.max_workers} worker threads ready")
        else:
            logger.warning("⚠️  Scanner initialization failed - using sequential mode")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize scanner: {str(e)}")
        logger.info("🔄 Falling back to sequential scanning mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down simplified parallel scanning system...")
        scanner.shutdown()
        logger.info("CodeClinic shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
