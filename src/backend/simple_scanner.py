"""
Simplified Parallel Scanner using Threading
This replaces the complex Docker-based approach with a simple thread-based system.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import redis
import httpx
from dataclasses import dataclass
from enum import Enum
from zap_scanner import ZAPScanner

logger = logging.getLogger(__name__)

class ScanStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ScanTask:
    task_id: str
    url: str
    scan_type: str
    status: ScanStatus
    worker_id: Optional[str] = None
    progress: int = 0
    results: Optional[Dict] = None
    error: Optional[str] = None
    created_at: float = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

class SimpleParallelScanner:
    """
    Simplified parallel scanner using threading instead of Docker containers.
    Uses a single ZAP instance with multiple worker threads.
    """
    
    def __init__(self, max_workers: int = 4, zap_host: str = None, zap_port: int = None):
        import os
        self.max_workers = max_workers
        self.zap_host = zap_host or os.getenv("ZAP_HOST", "localhost")
        self.zap_port = zap_port or int(os.getenv("ZAP_PORT", "8080"))
        self.zap_base_url = f"http://{self.zap_host}:{self.zap_port}"
        
        # Redis for task coordination
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Task storage
        self.tasks: Dict[str, ScanTask] = {}
        
        # Worker status
        self.workers = {}
        
        logger.info(f"Initialized SimpleParallelScanner with {max_workers} workers")
    
    async def initialize(self) -> bool:
        """Initialize the scanner and check ZAP connectivity"""
        try:
            # Test ZAP connectivity
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.zap_base_url}/JSON/core/view/version/", timeout=10)
                if response.status_code == 200:
                    version_info = response.json()
                    logger.info(f"Connected to ZAP version {version_info.get('version', 'unknown')}")
                    return True
                else:
                    logger.error(f"ZAP returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to connect to ZAP: {e}")
            return False
    
    def _is_zap_accessible(self) -> bool:
        """Check if ZAP is accessible (synchronous version)"""
        try:
            import httpx
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self.zap_base_url}/JSON/core/view/version/")
                if response.status_code == 200:
                    version_info = response.json()
                    logger.info(f"ZAP is accessible, version {version_info.get('version', 'unknown')}")
                    return True
                else:
                    logger.error(f"ZAP returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to connect to ZAP: {e}")
            return False
    
    async def start_scan(self, url: str, scan_type: str = "full_site") -> str:
        """Start a new scan task"""
        task_id = f"scan_{int(time.time() * 1000)}"
        
        task = ScanTask(
            task_id=task_id,
            url=url,
            scan_type=scan_type,
            status=ScanStatus.PENDING,
            created_at=time.time()
        )
        
        self.tasks[task_id] = task
        
        # Store in Redis for persistence
        self.redis_client.hset(f"task:{task_id}", mapping={
            "url": url,
            "scan_type": scan_type,
            "status": ScanStatus.PENDING.value,
            "created_at": str(task.created_at)
        })
        
        # Submit to thread pool
        future = self.executor.submit(self._run_scan_task, task_id)
        
        logger.info(f"Started scan task {task_id} for {url}")
        return task_id
    
    async def start_crawl(self, url: str) -> str:
        """Start a new crawl task to discover pages"""
        task_id = f"crawl_{int(time.time() * 1000)}"
        
        task = ScanTask(
            task_id=task_id,
            url=url,
            scan_type="crawl",
            status=ScanStatus.PENDING,
            created_at=time.time()
        )
        
        self.tasks[task_id] = task
        
        # Store in Redis for persistence
        self.redis_client.hset(f"task:{task_id}", mapping={
            "url": url,
            "scan_type": "crawl",
            "status": ScanStatus.PENDING.value,
            "created_at": str(task.created_at)
        })
        
        # Submit to thread pool
        future = self.executor.submit(self._run_crawl_task, task_id)
        
        logger.info(f"Started crawl task {task_id} for {url}")
        return task_id
    
    async def start_scan_selected(self, crawl_task_id: str, selected_pages: List[str]) -> str:
        """Start scanning selected pages from a previous crawl"""
        task_id = f"scan_{int(time.time() * 1000)}"
        
        # Get the original URL from the crawl task
        crawl_task = self.tasks.get(crawl_task_id)
        if not crawl_task:
            raise Exception(f"Crawl task {crawl_task_id} not found")
        
        task = ScanTask(
            task_id=task_id,
            url=crawl_task.url,
            scan_type="selective_pages",
            status=ScanStatus.PENDING,
            created_at=time.time()
        )
        
        # Store selected pages in the task
        task.results = {"selected_pages": selected_pages}
        
        self.tasks[task_id] = task
        
        # Store in Redis for persistence
        self.redis_client.hset(f"task:{task_id}", mapping={
            "url": crawl_task.url,
            "scan_type": "selective_pages",
            "status": ScanStatus.PENDING.value,
            "created_at": str(task.created_at),
            "selected_pages": ",".join(selected_pages)
        })
        
        # Submit to thread pool
        future = self.executor.submit(self._run_scan_selected_task, task_id)
        
        logger.info(f"Started selected scan task {task_id} for {len(selected_pages)} pages")
        return task_id
    
    def _run_scan_task(self, task_id: str) -> None:
        """Run a scan task in a worker thread"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            # Update task status
            task.status = ScanStatus.RUNNING
            task.started_at = time.time()
            task.worker_id = f"worker_{task_id[-4:]}"
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.RUNNING.value)
            self.redis_client.hset(f"task:{task_id}", "worker_id", task.worker_id)
            self.redis_client.hset(f"task:{task_id}", "started_at", str(task.started_at))
            
            logger.info(f"Worker {task.worker_id} starting scan for {task.url}")
            
            # Perform the actual scan using ZAP Python API
            results = self._perform_zap_scan(task.url, task.scan_type, task_id)
            
            # Update task with results
            task.status = ScanStatus.COMPLETED
            task.completed_at = time.time()
            task.results = results
            task.progress = 100
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.COMPLETED.value)
            self.redis_client.hset(f"task:{task_id}", "completed_at", str(task.completed_at))
            self.redis_client.hset(f"task:{task_id}", "progress", "100")
            
            logger.info(f"Worker {task.worker_id} completed scan for {task.url}")
            
        except Exception as e:
            logger.error(f"Worker failed for task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = ScanStatus.FAILED
                self.tasks[task_id].error = str(e)
                self.tasks[task_id].completed_at = time.time()
                
                self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.FAILED.value)
                self.redis_client.hset(f"task:{task_id}", "error", str(e))
                self.redis_client.hset(f"task:{task_id}", "completed_at", str(time.time()))
    
    def _run_crawl_task(self, task_id: str) -> None:
        """Run a crawl task in a worker thread"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            # Update task status
            task.status = ScanStatus.RUNNING
            task.started_at = time.time()
            task.worker_id = f"worker_{task_id[-4:]}"
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.RUNNING.value)
            self.redis_client.hset(f"task:{task_id}", "worker_id", task.worker_id)
            self.redis_client.hset(f"task:{task_id}", "started_at", str(task.started_at))
            
            logger.info(f"Worker {task.worker_id} starting crawl for {task.url}")
            
            # Perform the crawl to discover pages
            results = self._perform_zap_crawl(task.url, task_id)
            
            # Update task with results
            task.status = ScanStatus.COMPLETED
            task.completed_at = time.time()
            task.results = results
            task.progress = 100
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.COMPLETED.value)
            self.redis_client.hset(f"task:{task_id}", "completed_at", str(task.completed_at))
            self.redis_client.hset(f"task:{task_id}", "progress", "100")
            
            logger.info(f"Worker {task.worker_id} completed crawl for {task.url}")
            
        except Exception as e:
            logger.error(f"Worker failed for crawl task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = ScanStatus.FAILED
                self.tasks[task_id].error = str(e)
                self.tasks[task_id].completed_at = time.time()
                
                self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.FAILED.value)
                self.redis_client.hset(f"task:{task_id}", "error", str(e))
                self.redis_client.hset(f"task:{task_id}", "completed_at", str(time.time()))
    
    def _run_scan_selected_task(self, task_id: str) -> None:
        """Run a scan task for selected pages in a worker thread"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            # Update task status
            task.status = ScanStatus.RUNNING
            task.started_at = time.time()
            task.worker_id = f"worker_{task_id[-4:]}"
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.RUNNING.value)
            self.redis_client.hset(f"task:{task_id}", "worker_id", task.worker_id)
            self.redis_client.hset(f"task:{task_id}", "started_at", str(task.started_at))
            
            logger.info(f"Worker {task.worker_id} starting selected scan for {task.url}")
            
            # Perform the scan for selected pages
            selected_pages = task.results.get("selected_pages", []) if task.results else []
            results = self._perform_zap_scan_selected(task.url, selected_pages, task_id)
            
            # Update task with results
            task.status = ScanStatus.COMPLETED
            task.completed_at = time.time()
            task.results = results
            task.progress = 100
            
            self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.COMPLETED.value)
            self.redis_client.hset(f"task:{task_id}", "completed_at", str(task.completed_at))
            self.redis_client.hset(f"task:{task_id}", "progress", "100")
            
            logger.info(f"Worker {task.worker_id} completed selected scan for {task.url}")
            
        except Exception as e:
            logger.error(f"Worker failed for selected scan task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = ScanStatus.FAILED
                self.tasks[task_id].error = str(e)
                self.tasks[task_id].completed_at = time.time()
                
                self.redis_client.hset(f"task:{task_id}", "status", ScanStatus.FAILED.value)
                self.redis_client.hset(f"task:{task_id}", "error", str(e))
                self.redis_client.hset(f"task:{task_id}", "completed_at", str(time.time()))
    
    def _perform_zap_scan(self, url: str, scan_type: str, task_id: str) -> Dict:
        """Perform the actual ZAP scan using Python API"""
        try:
            # Create ZAP scanner instance
            zap_scanner = ZAPScanner(self.zap_host, self.zap_port)
            
            # Connect to ZAP
            if not zap_scanner.connect():
                raise Exception("Failed to connect to ZAP instance")
            
            # Progress callback function
            def progress_callback(progress, message):
                logger.info(f"Scan progress: {progress}% - {message}")
                self.redis_client.hset(f"task:{task_id}", "progress", str(progress))
                # Also update the task in memory
                if task_id in self.tasks:
                    self.tasks[task_id].progress = progress
            
            # Perform the scan
            results = zap_scanner.scan_url(url, progress_callback=progress_callback)
            
            logger.info(f"ZAP scan completed for {url} in {results['scan_duration']:.2f}s with {len(results['vulnerabilities'])} vulnerabilities")
            
            return results
            
        except Exception as e:
            logger.error(f"ZAP scan failed for {url}: {e}")
            
            # Provide fallback results for demo purposes
            fallback_results = {
                "url": url,
                "status": "completed",
                "scan_duration": time.time() - (self.tasks[task_id].started_at or time.time()),
                "vulnerabilities": [
                    {
                        "id": "fallback_001",
                        "type": "info",
                        "severity": "informational",
                        "title": "Scan Error",
                        "description": f"ZAP scan failed: {str(e)}",
                        "url": url,
                        "parameter": None,
                        "evidence": "Scan could not complete",
                        "solution": "Check if the target URL is accessible and ZAP is running properly",
                        "cwe_id": None,
                        "confidence": "low"
                    }
                ],
                "summary": {
                    "total_issues": 1,
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0,
                    "info": 1
                }
            }
            
            return fallback_results
    
    def _perform_zap_crawl(self, url: str, task_id: str) -> Dict:
        """Perform ZAP crawling to discover pages"""
        try:
            # Create ZAP scanner instance
            zap_scanner = ZAPScanner(self.zap_host, self.zap_port)
            
            # Connect to ZAP
            if not zap_scanner.connect():
                raise Exception("Failed to connect to ZAP instance")
            
            # Progress callback function
            def progress_callback(progress, message):
                logger.info(f"Crawl progress: {progress}% - {message}")
                self.redis_client.hset(f"task:{task_id}", "progress", str(progress))
                # Also update the task in memory
                if task_id in self.tasks:
                    self.tasks[task_id].progress = progress
            
            # Perform the crawl
            results = zap_scanner.crawl_url(url, progress_callback=progress_callback)
            
            logger.info(f"ZAP crawl completed for {url} in {results['crawl_duration']:.2f}s with {len(results['discovered_pages'])} pages")
            
            return results
            
        except Exception as e:
            logger.error(f"ZAP crawl failed for {url}: {e}")
            
            # Provide fallback results
            fallback_results = {
                "url": url,
                "status": "completed",
                "crawl_duration": time.time() - (self.tasks[task_id].started_at or time.time()),
                "discovered_pages": [],
                "error": str(e)
            }
            
            return fallback_results
    
    def _perform_zap_scan_selected(self, url: str, selected_pages: List[str], task_id: str) -> Dict:
        """Perform ZAP scan for selected pages"""
        try:
            # Create ZAP scanner instance
            zap_scanner = ZAPScanner(self.zap_host, self.zap_port)
            
            # Connect to ZAP
            if not zap_scanner.connect():
                raise Exception("Failed to connect to ZAP instance")
            
            # Progress callback function
            def progress_callback(progress, message):
                logger.info(f"Scan progress: {progress}% - {message}")
                self.redis_client.hset(f"task:{task_id}", "progress", str(progress))
                # Also update the task in memory
                if task_id in self.tasks:
                    self.tasks[task_id].progress = progress
            
            # Perform the scan for selected pages
            results = zap_scanner.scan_selected_pages(url, selected_pages, progress_callback=progress_callback)
            
            logger.info(f"ZAP scan completed for {len(selected_pages)} selected pages in {results['scan_duration']:.2f}s with {len(results['vulnerabilities'])} vulnerabilities")
            
            return results
            
        except Exception as e:
            logger.error(f"ZAP scan failed for selected pages: {e}")
            
            # Provide fallback results
            fallback_results = {
                "url": url,
                "status": "completed",
                "scan_duration": time.time() - (self.tasks[task_id].started_at or time.time()),
                "vulnerabilities": [
                    {
                        "id": "fallback_001",
                        "type": "info",
                        "severity": "informational",
                        "title": "Scan Error",
                        "description": f"ZAP scan failed: {str(e)}",
                        "url": url,
                        "parameter": None,
                        "evidence": "Scan could not complete",
                        "solution": "Check if the target URL is accessible and ZAP is running properly",
                        "cwe_id": None,
                        "confidence": "low"
                    }
                ],
                "summary": {
                    "total_issues": 1,
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0,
                    "info": 1
                }
            }
            
            return fallback_results
    
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a scan task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "url": task.url,
            "scan_type": task.scan_type,
            "status": task.status.value,
            "worker_id": task.worker_id,
            "progress": task.progress,
            "message": self._get_progress_message(task),
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error": task.error,
            "results": task.results
        }
    
    def _get_progress_message(self, task: ScanTask) -> str:
        """Generate user-friendly progress message based on task status and progress"""
        if task.status == ScanStatus.PENDING:
            return "Queued for processing..."
        elif task.status == ScanStatus.RUNNING:
            if task.scan_type == "crawl":
                if task.progress < 20:
                    return "Setting up crawl..."
                elif task.progress < 50:
                    return "Discovering pages..."
                elif task.progress < 90:
                    return "Processing discovered pages..."
                else:
                    return "Finalizing crawl results..."
            else:  # scan
                if task.progress < 20:
                    return "Setting up security scan..."
                elif task.progress < 50:
                    return "Running spider scan..."
                elif task.progress < 80:
                    return "Running active security tests..."
                elif task.progress < 95:
                    return "Analyzing vulnerabilities..."
                else:
                    return "Generating security report..."
        elif task.status == ScanStatus.COMPLETED:
            return "Scan completed successfully!"
        elif task.status == ScanStatus.FAILED:
            return f"Scan failed: {task.error or 'Unknown error'}"
        else:
            return "Processing..."
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all scan tasks"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def get_worker_status(self) -> Dict:
        """Get worker pool status"""
        return {
            "max_workers": self.max_workers,
            "active_workers": len([t for t in self.tasks.values() if t.status == ScanStatus.RUNNING]),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == ScanStatus.PENDING]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == ScanStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == ScanStatus.FAILED])
        }
    
    def shutdown(self):
        """Shutdown the scanner and cleanup resources"""
        logger.info("Shutting down SimpleParallelScanner...")
        self.executor.shutdown(wait=True)
        logger.info("SimpleParallelScanner shutdown complete")
