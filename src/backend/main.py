"""
CodeClinic Backend - FastAPI Server
Main application entry point for the security assessment API
Now with high-performance parallel scanning capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from typing import List, Optional
import logging
import uuid

from models import ScanRequest, ScanResponse, Vulnerability, ScanStatus
from zap_integration import ZAPScanner
from url_validator import URLValidator
from parallel_scanner import ParallelScanner
from redis_coordinator import RedisCoordinator, ScanStatus as RedisScanStatus
from worker_pool import WorkerPool

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

# Initialize parallel scanning system
redis_coordinator = RedisCoordinator()
parallel_scanner = ParallelScanner()
worker_pool = WorkerPool(redis_coordinator)

# Global flag for parallel scanning availability
parallel_scanning_enabled = False

# Legacy in-memory storage for fallback mode
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
        "parallel_scanning": parallel_scanning_enabled,
        "worker_pool_status": worker_pool.get_worker_status() if parallel_scanning_enabled else None,
        "version": "1.0.0"
    }

@app.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start a security scan for the provided URL
    Now supports high-performance parallel scanning
    
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
        scan_id = f"scan_{int(asyncio.get_event_loop().time())}_{uuid.uuid4().hex[:8]}"
        
        # Choose scanning method based on availability
        if parallel_scanning_enabled:
            # Use parallel scanning
            background_tasks.add_task(run_parallel_scan, scan_id, url_str, request.scan_type)
            message = "Parallel scan initiated successfully"
        else:
            # Fallback to sequential scanning
            background_tasks.add_task(run_sequential_scan, scan_id, url_str, request.scan_type)
            message = "Sequential scan initiated successfully"
        
        return ScanResponse(
            scan_id=scan_id,
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
        if parallel_scanning_enabled:
            # Get status from Redis coordinator
            progress = await redis_coordinator.get_scan_progress(scan_id)
            if not progress or progress.get("status") == "unknown":
                raise HTTPException(status_code=404, detail="Scan not found")
            return progress
        else:
            # Fallback to in-memory storage (legacy)
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            return scan_results[scan_id]
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan status")

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
    try:
        if parallel_scanning_enabled:
            # Get results from Redis coordinator
            progress = await redis_coordinator.get_scan_progress(scan_id)
            if not progress or progress.get("status") == "unknown":
                raise HTTPException(status_code=404, detail="Scan not found")
            
            if progress.get("status") not in ["completed", "failed"]:
                raise HTTPException(status_code=400, detail="Scan not yet completed")
            
            # Get vulnerabilities
            vulnerabilities = await redis_coordinator.get_scan_results(scan_id)
            
            return {
                "id": scan_id,
                "status": progress.get("status"),
                "progress": progress.get("progress", 0),
                "vulnerabilities": vulnerabilities,
                "total_vulnerabilities": len(vulnerabilities),
                "completed_pages": progress.get("completed_pages", 0),
                "total_pages": progress.get("total_pages", 0)
            }
        else:
            # Fallback to in-memory storage (legacy)
    if scan_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_data = scan_results[scan_id]
    if scan_data["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Scan not yet completed")
    
    return scan_data
    except Exception as e:
        logger.error(f"Error getting scan results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan results")

async def run_parallel_scan(scan_id: str, url: str, scan_type: str):
    """High-performance parallel scan using multiple ZAP workers"""
    try:
        logger.info(f"Starting parallel scan {scan_id} for URL: {url}")
        
        # Update status to discovering pages
        await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.DISCOVERING, 10)
        
        # Discover pages using parallel crawling
        logger.info(f"Discovering pages for {url} using parallel crawling")
        pages = await parallel_scanner.discover_pages_parallel(url, max_pages=50)
        
        # Create scan job
        await redis_coordinator.create_scan_job(url, scan_type, pages)
        await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.SCANNING, 30)
        
        # If full site scan, run parallel scanning
        if scan_type == "full_site":
            logger.info(f"Running parallel ZAP scan for {url} with {len(pages)} pages")
            
            # Submit tasks to worker pool
            await worker_pool.submit_scan_tasks(scan_id, pages, url)
            
            # Wait for completion
            success = await worker_pool.wait_for_completion(scan_id, timeout=300)
            
            if success:
                await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.COMPLETED, 100)
                logger.info(f"Parallel scan {scan_id} completed successfully")
            else:
                await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.FAILED, 0, "Scan timed out")
                logger.error(f"Parallel scan {scan_id} failed or timed out")
        else:
            # Selective scan - wait for page selection
            await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.SCANNING, 30, "Waiting for page selection")
            
    except Exception as e:
        logger.error(f"Parallel scan {scan_id} failed: {str(e)}", exc_info=True)
        await redis_coordinator.update_scan_status(scan_id, RedisScanStatus.FAILED, 0, str(e))

async def run_sequential_scan(scan_id: str, url: str, scan_type: str):
    """Legacy sequential scan (fallback when parallel scanning is not available)"""
    try:
        logger.info(f"Starting sequential scan {scan_id} for URL: {url}")
        
        # Initialize scan result in memory
        scan_results[scan_id] = {
            "id": scan_id,
            "url": url,
            "scan_type": scan_type,
            "status": "discovering_pages",
            "vulnerabilities": [],
            "pages": [],
            "progress": 10
        }
        
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
            logger.info(f"Sequential scan {scan_id} completed with {len(vulnerabilities)} vulnerabilities")
            
        # If selective scan, wait for page selection
        else:
            scan_results[scan_id]["status"] = "waiting_for_selection"
            
    except Exception as e:
        logger.error(f"Sequential scan {scan_id} failed: {str(e)}", exc_info=True)
        scan_results[scan_id]["status"] = "failed"
        scan_results[scan_id]["error"] = str(e)

# Add new API endpoints for parallel scanning
@app.get("/system/status")
async def get_system_status():
    """Get system-wide status including worker pool and performance metrics"""
    try:
        if parallel_scanning_enabled:
            return {
                "parallel_scanning": True,
                "worker_pool": worker_pool.get_worker_status(),
                "performance": worker_pool.get_performance_stats(),
                "redis_stats": await redis_coordinator.get_system_stats()
            }
        else:
            return {
                "parallel_scanning": False,
                "zap_available": await zap_scanner.is_zap_available(),
                "message": "Parallel scanning not available - using sequential mode"
            }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {"error": "Failed to get system status"}

@app.post("/system/initialize-parallel")
async def initialize_parallel_scanning():
    """Initialize parallel scanning system"""
    global parallel_scanning_enabled
    try:
        logger.info("Initializing parallel scanning system...")
        
        # Initialize parallel scanner
        if await parallel_scanner.initialize_workers():
            # Initialize worker pool
            if await worker_pool.initialize():
                parallel_scanning_enabled = True
                logger.info("Parallel scanning system initialized successfully")
                return {
                    "status": "success",
                    "message": "Parallel scanning system initialized",
                    "workers": len(parallel_scanner.workers),
                    "performance_boost": f"Up to {len(parallel_scanner.workers)}x faster scanning"
                }
            else:
                logger.error("Failed to initialize worker pool")
                return {"status": "error", "message": "Failed to initialize worker pool"}
        else:
            logger.error("Failed to initialize parallel scanner")
            return {"status": "error", "message": "Failed to initialize parallel scanner"}
            
    except Exception as e:
        logger.error(f"Error initializing parallel scanning: {str(e)}")
        return {"status": "error", "message": f"Initialization failed: {str(e)}"}

@app.post("/system/shutdown-parallel")
async def shutdown_parallel_scanning():
    """Shutdown parallel scanning system"""
    global parallel_scanning_enabled
    try:
        logger.info("Shutting down parallel scanning system...")
        
        await parallel_scanner.shutdown()
        await worker_pool.shutdown()
        
        parallel_scanning_enabled = False
        logger.info("Parallel scanning system shutdown complete")
        
        return {"status": "success", "message": "Parallel scanning system shutdown"}
        
    except Exception as e:
        logger.error(f"Error shutting down parallel scanning: {str(e)}")
        return {"status": "error", "message": f"Shutdown failed: {str(e)}"}

# Initialize parallel scanning on startup
@app.on_event("startup")
async def startup_event():
    """Initialize parallel scanning system on startup"""
    global parallel_scanning_enabled
    try:
        logger.info("Starting CodeClinic with parallel scanning capabilities...")
        
        # Try to initialize parallel scanning
        if await parallel_scanner.initialize_workers():
            if await worker_pool.initialize():
                parallel_scanning_enabled = True
                logger.info("✅ Parallel scanning system initialized successfully")
                logger.info(f"🚀 Performance boost: Up to {len(parallel_scanner.workers)}x faster scanning")
            else:
                logger.warning("⚠️  Worker pool initialization failed - using sequential mode")
        else:
            logger.warning("⚠️  Parallel scanner initialization failed - using sequential mode")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize parallel scanning: {str(e)}")
        logger.info("🔄 Falling back to sequential scanning mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if parallel_scanning_enabled:
            logger.info("Shutting down parallel scanning system...")
            await parallel_scanner.shutdown()
            await worker_pool.shutdown()
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
