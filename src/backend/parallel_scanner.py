"""
Parallel Security Scanner
High-performance parallel scanning with multiple ZAP instances and worker pools
"""

import asyncio
import httpx
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum
import redis
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue
import threading

logger = logging.getLogger(__name__)

class ScanWorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class ScanTask:
    """Individual scan task for a page"""
    task_id: str
    scan_id: str
    page_url: str
    target_url: str
    priority: int = 1
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class ScanWorker:
    """ZAP worker instance"""
    worker_id: str
    zap_host: str
    zap_port: int
    status: ScanWorkerStatus
    current_task: Optional[ScanTask] = None
    last_heartbeat: float = None
    
    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = time.time()

class ParallelScanner:
    """
    High-performance parallel security scanner using multiple ZAP instances
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 max_workers: int = None,
                 zap_ports: List[int] = None):
        """
        Initialize parallel scanner
        
        Args:
            redis_url: Redis connection URL for coordination
            max_workers: Maximum number of parallel workers (default: CPU count)
            zap_ports: List of ZAP ports to use for workers
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.max_workers = max_workers or min(mp.cpu_count(), 8)  # Cap at 8 for resource management
        self.zap_ports = zap_ports or list(range(8080, 8080 + self.max_workers))
        
        # Worker management
        self.workers: Dict[str, ScanWorker] = {}
        self.task_queue: Queue = Queue()
        self.results: Dict[str, List[Dict[str, Any]]] = {}
        self.scan_progress: Dict[str, Dict[str, Any]] = {}
        
        # Threading
        self.worker_threads: List[threading.Thread] = []
        self.coordinator_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Performance metrics
        self.scan_stats = {
            "total_scans": 0,
            "total_pages_scanned": 0,
            "average_scan_time": 0,
            "parallel_efficiency": 0
        }
    
    async def initialize_workers(self) -> bool:
        """Initialize and start all ZAP worker instances"""
        try:
            logger.info(f"Initializing {self.max_workers} ZAP workers...")
            
            # Start ZAP instances in parallel
            startup_tasks = []
            for i, port in enumerate(self.zap_ports[:self.max_workers]):
                worker_id = f"worker_{i+1}"
                startup_tasks.append(self._start_zap_instance(worker_id, port))
            
            # Wait for all ZAP instances to start
            results = await asyncio.gather(*startup_tasks, return_exceptions=True)
            
            successful_workers = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to start worker {i+1}: {result}")
                else:
                    successful_workers += 1
            
            if successful_workers == 0:
                logger.error("No ZAP workers could be started")
                return False
            
            logger.info(f"Successfully started {successful_workers} ZAP workers")
            
            # Start coordinator thread
            self.running = True
            self.coordinator_thread = threading.Thread(target=self._coordinator_loop, daemon=True)
            self.coordinator_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize workers: {str(e)}")
            return False
    
    async def _start_zap_instance(self, worker_id: str, port: int) -> bool:
        """Start a single ZAP instance"""
        try:
            # Check if ZAP is already running on this port
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:{port}/JSON/core/view/version/", timeout=5)
                if response.status_code == 200:
                    logger.info(f"ZAP already running on port {port}")
                else:
                    # Start new ZAP instance (this would typically be done via Docker or subprocess)
                    logger.info(f"Starting ZAP instance on port {port}")
                    # In a real implementation, you'd start ZAP here
                    # For now, we'll assume it's available
            
            # Create worker
            worker = ScanWorker(
                worker_id=worker_id,
                zap_host="localhost",
                zap_port=port,
                status=ScanWorkerStatus.IDLE
            )
            
            self.workers[worker_id] = worker
            logger.info(f"Worker {worker_id} initialized on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ZAP instance on port {port}: {str(e)}")
            return False
    
    def _coordinator_loop(self):
        """Main coordinator loop for task distribution"""
        while self.running:
            try:
                # Check for idle workers
                idle_workers = [w for w in self.workers.values() if w.status == ScanWorkerStatus.IDLE]
                
                # Distribute tasks to idle workers
                for worker in idle_workers:
                    if not self.task_queue.empty():
                        task = self.task_queue.get()
                        self._assign_task_to_worker(worker, task)
                
                # Update worker statuses
                self._update_worker_statuses()
                
                # Sleep briefly to prevent busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in coordinator loop: {str(e)}")
                time.sleep(1)
    
    def _assign_task_to_worker(self, worker: ScanWorker, task: ScanTask):
        """Assign a task to a specific worker"""
        try:
            worker.current_task = task
            worker.status = ScanWorkerStatus.BUSY
            worker.last_heartbeat = time.time()
            
            # Start worker thread for this task
            worker_thread = threading.Thread(
                target=self._worker_scan_loop,
                args=(worker, task),
                daemon=True
            )
            worker_thread.start()
            self.worker_threads.append(worker_thread)
            
            logger.info(f"Assigned task {task.task_id} to worker {worker.worker_id}")
            
        except Exception as e:
            logger.error(f"Failed to assign task to worker: {str(e)}")
            worker.status = ScanWorkerStatus.ERROR
    
    def _worker_scan_loop(self, worker: ScanWorker, task: ScanTask):
        """Worker thread that performs the actual scanning"""
        try:
            logger.info(f"Worker {worker.worker_id} starting scan of {task.page_url}")
            
            # Perform the scan
            vulnerabilities = self._scan_page_with_worker(worker, task)
            
            # Store results
            scan_id = task.scan_id
            if scan_id not in self.results:
                self.results[scan_id] = []
            
            self.results[scan_id].extend(vulnerabilities)
            
            # Update progress
            self._update_scan_progress(scan_id, task.page_url, len(vulnerabilities))
            
            # Mark worker as idle
            worker.current_task = None
            worker.status = ScanWorkerStatus.IDLE
            worker.last_heartbeat = time.time()
            
            logger.info(f"Worker {worker.worker_id} completed scan of {task.page_url}")
            
        except Exception as e:
            logger.error(f"Worker {worker.worker_id} failed to scan {task.page_url}: {str(e)}")
            worker.status = ScanWorkerStatus.ERROR
    
    def _scan_page_with_worker(self, worker: ScanWorker, task: ScanTask) -> List[Dict[str, Any]]:
        """Scan a single page using a specific worker"""
        try:
            # This would integrate with the existing ZAP integration
            # For now, we'll simulate the scan
            time.sleep(0.5)  # Simulate scan time
            
            # Return mock vulnerabilities for demonstration
            return [
                {
                    "id": f"vuln_{task.task_id}_1",
                    "type": "insecure_headers",
                    "severity": "medium",
                    "title": "Missing Security Headers",
                    "description": f"Security headers missing on {task.page_url}",
                    "url": task.page_url,
                    "solution": "Add security headers to prevent clickjacking",
                    "confidence": "high"
                }
            ]
            
        except Exception as e:
            logger.error(f"Scan failed for {task.page_url}: {str(e)}")
            return []
    
    def _update_worker_statuses(self):
        """Update status of all workers"""
        current_time = time.time()
        for worker in self.workers.values():
            # Check for stale workers
            if current_time - worker.last_heartbeat > 30:  # 30 second timeout
                if worker.status == ScanWorkerStatus.BUSY:
                    worker.status = ScanWorkerStatus.ERROR
                    logger.warning(f"Worker {worker.worker_id} timed out")
    
    def _update_scan_progress(self, scan_id: str, page_url: str, vuln_count: int):
        """Update scan progress and store in Redis"""
        try:
            if scan_id not in self.scan_progress:
                self.scan_progress[scan_id] = {
                    "total_pages": 0,
                    "completed_pages": 0,
                    "total_vulnerabilities": 0,
                    "status": "scanning",
                    "start_time": time.time()
                }
            
            progress = self.scan_progress[scan_id]
            progress["completed_pages"] += 1
            progress["total_vulnerabilities"] += vuln_count
            
            # Calculate progress percentage
            if progress["total_pages"] > 0:
                progress_percentage = int((progress["completed_pages"] / progress["total_pages"]) * 100)
            else:
                progress_percentage = 0
            
            # Store in Redis for real-time updates
            self.redis_client.hset(f"scan_progress:{scan_id}", mapping={
                "progress": progress_percentage,
                "completed_pages": progress["completed_pages"],
                "total_pages": progress["total_pages"],
                "total_vulnerabilities": progress["total_vulnerabilities"],
                "status": "scanning"
            })
            
            logger.info(f"Scan {scan_id}: {progress_percentage}% complete ({progress['completed_pages']}/{progress['total_pages']} pages)")
            
        except Exception as e:
            logger.error(f"Failed to update scan progress: {str(e)}")
    
    async def discover_pages_parallel(self, target_url: str, max_pages: int = 50) -> List[str]:
        """Discover pages using parallel crawling"""
        try:
            logger.info(f"Starting parallel page discovery for {target_url}")
            
            # Use multiple concurrent HTTP requests for faster discovery
            discovered_pages = set([target_url])
            pages_to_crawl = [target_url]
            crawled_pages = set()
            
            # Parallel crawling with semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
            
            async def crawl_page(url: str) -> List[str]:
                async with semaphore:
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            response = await client.get(url)
                            if response.status_code == 200:
                                # Simple link extraction (in production, use BeautifulSoup)
                                links = []
                                # This is a simplified version - in reality you'd parse HTML
                                return [target_url]  # Placeholder
                            return []
                    except Exception as e:
                        logger.warning(f"Failed to crawl {url}: {str(e)}")
                        return []
            
            # Crawl pages in parallel
            while pages_to_crawl and len(discovered_pages) < max_pages:
                current_batch = pages_to_crawl[:10]  # Process 10 pages at a time
                pages_to_crawl = pages_to_crawl[10:]
                
                tasks = [crawl_page(url) for url in current_batch if url not in crawled_pages]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        for link in result:
                            if link not in discovered_pages and len(discovered_pages) < max_pages:
                                discovered_pages.add(link)
                                if link not in crawled_pages:
                                    pages_to_crawl.append(link)
                
                crawled_pages.update(current_batch)
            
            pages_list = list(discovered_pages)[:max_pages]
            logger.info(f"Discovered {len(pages_list)} pages in parallel")
            return pages_list
            
        except Exception as e:
            logger.error(f"Parallel page discovery failed: {str(e)}")
            return [target_url]
    
    async def run_parallel_scan(self, scan_id: str, target_url: str, pages: List[str]) -> List[Dict[str, Any]]:
        """Run parallel security scan on multiple pages"""
        try:
            logger.info(f"Starting parallel scan {scan_id} for {len(pages)} pages")
            
            # Initialize scan progress
            self.scan_progress[scan_id] = {
                "total_pages": len(pages),
                "completed_pages": 0,
                "total_vulnerabilities": 0,
                "status": "scanning",
                "start_time": time.time()
            }
            
            # Create tasks for each page
            for i, page_url in enumerate(pages):
                task = ScanTask(
                    task_id=f"{scan_id}_task_{i}",
                    scan_id=scan_id,
                    page_url=page_url,
                    target_url=target_url,
                    priority=1 if i == 0 else 2  # Prioritize main page
                )
                self.task_queue.put(task)
            
            # Wait for all tasks to complete
            start_time = time.time()
            while self.scan_progress[scan_id]["completed_pages"] < len(pages):
                await asyncio.sleep(1)
                
                # Check for timeout (5 minutes max)
                if time.time() - start_time > 300:
                    logger.warning(f"Scan {scan_id} timed out")
                    break
            
            # Get results
            results = self.results.get(scan_id, [])
            
            # Update final status
            self.scan_progress[scan_id]["status"] = "completed"
            self.scan_progress[scan_id]["end_time"] = time.time()
            
            # Update statistics
            scan_time = time.time() - start_time
            self.scan_stats["total_scans"] += 1
            self.scan_stats["total_pages_scanned"] += len(pages)
            self.scan_stats["average_scan_time"] = (
                (self.scan_stats["average_scan_time"] * (self.scan_stats["total_scans"] - 1) + scan_time) 
                / self.scan_stats["total_scans"]
            )
            
            # Calculate parallel efficiency
            sequential_time = len(pages) * 0.5  # Assume 0.5s per page sequentially
            self.scan_stats["parallel_efficiency"] = sequential_time / scan_time if scan_time > 0 else 1
            
            logger.info(f"Parallel scan {scan_id} completed in {scan_time:.2f}s with {len(results)} vulnerabilities")
            logger.info(f"Parallel efficiency: {self.scan_stats['parallel_efficiency']:.2f}x speedup")
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel scan failed: {str(e)}")
            return []
    
    def get_scan_progress(self, scan_id: str) -> Dict[str, Any]:
        """Get current scan progress"""
        try:
            # Try to get from Redis first
            redis_data = self.redis_client.hgetall(f"scan_progress:{scan_id}")
            if redis_data:
                return {
                    "progress": int(redis_data.get("progress", 0)),
                    "completed_pages": int(redis_data.get("completed_pages", 0)),
                    "total_pages": int(redis_data.get("total_pages", 0)),
                    "total_vulnerabilities": int(redis_data.get("total_vulnerabilities", 0)),
                    "status": redis_data.get("status", "unknown")
                }
            
            # Fallback to local data
            return self.scan_progress.get(scan_id, {
                "progress": 0,
                "completed_pages": 0,
                "total_pages": 0,
                "total_vulnerabilities": 0,
                "status": "unknown"
            })
            
        except Exception as e:
            logger.error(f"Failed to get scan progress: {str(e)}")
            return {"progress": 0, "status": "error"}
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        return {
            "total_workers": len(self.workers),
            "idle_workers": len([w for w in self.workers.values() if w.status == ScanWorkerStatus.IDLE]),
            "busy_workers": len([w for w in self.workers.values() if w.status == ScanWorkerStatus.BUSY]),
            "error_workers": len([w for w in self.workers.values() if w.status == ScanWorkerStatus.ERROR]),
            "workers": {
                worker_id: {
                    "status": worker.status.value,
                    "current_task": worker.current_task.task_id if worker.current_task else None,
                    "last_heartbeat": worker.last_heartbeat
                }
                for worker_id, worker in self.workers.items()
            }
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.scan_stats,
            "active_workers": len([w for w in self.workers.values() if w.status == ScanWorkerStatus.BUSY]),
            "queue_size": self.task_queue.qsize()
        }
    
    async def shutdown(self):
        """Shutdown all workers and cleanup"""
        logger.info("Shutting down parallel scanner...")
        self.running = False
        
        # Wait for coordinator thread to finish
        if self.coordinator_thread and self.coordinator_thread.is_alive():
            self.coordinator_thread.join(timeout=5)
        
        # Wait for worker threads to finish
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=2)
        
        logger.info("Parallel scanner shutdown complete")


