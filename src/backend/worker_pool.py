"""
High-Performance Worker Pool for Parallel Security Scanning
Manages multiple ZAP instances and distributes scanning tasks
"""

import asyncio
import httpx
import json
import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue, Empty
import subprocess
import docker
import os

logger = logging.getLogger(__name__)

class WorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    STARTING = "starting"

@dataclass
class WorkerConfig:
    """Configuration for a worker instance"""
    worker_id: str
    zap_port: int
    zap_host: str = "localhost"
    max_concurrent_scans: int = 3
    memory_limit: str = "512m"
    cpu_limit: float = 0.5

@dataclass
class ScanTask:
    """Individual scanning task"""
    task_id: str
    scan_id: str
    page_url: str
    target_url: str
    priority: int = 1
    created_at: float = None
    assigned_worker: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class ZAPWorker:
    """Individual ZAP worker instance"""
    
    def __init__(self, config: WorkerConfig, redis_coordinator):
        self.config = config
        self.redis = redis_coordinator
        self.status = WorkerStatus.OFFLINE
        self.current_tasks: List[ScanTask] = []
        self.docker_container = None
        self.api_key = None
        self.last_heartbeat = time.time()
        self.scan_count = 0
        self.error_count = 0
        
    async def start(self) -> bool:
        """Start the ZAP worker instance"""
        try:
            logger.info(f"Starting ZAP worker {self.config.worker_id} on port {self.config.zap_port}")
            
            # Start ZAP in Docker
            await self._start_zap_container()
            
            # Wait for ZAP to be ready
            if await self._wait_for_zap_ready():
                self.status = WorkerStatus.IDLE
                self.last_heartbeat = time.time()
                
                # Register worker with coordinator
                await self.redis.update_worker_status(
                    self.config.worker_id,
                    self.status.value,
                    last_heartbeat=self.last_heartbeat
                )
                
                logger.info(f"ZAP worker {self.config.worker_id} started successfully")
                return True
            else:
                logger.error(f"ZAP worker {self.config.worker_id} failed to start")
                self.status = WorkerStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Failed to start ZAP worker {self.config.worker_id}: {str(e)}")
            self.status = WorkerStatus.ERROR
            return False
    
    async def _start_zap_container(self):
        """Start ZAP in Docker container"""
        try:
            client = docker.from_env()
            
            # Check if container already exists
            try:
                existing_container = client.containers.get(f"zap-worker-{self.config.worker_id}")
                if existing_container.status == "running":
                    self.docker_container = existing_container
                    return
                else:
                    existing_container.remove()
            except docker.errors.NotFound:
                pass
            
            # Create new container
            self.docker_container = client.containers.run(
                "owasp/zap2docker-stable",
                name=f"zap-worker-{self.config.worker_id}",
                ports={f"{self.config.zap_port}/tcp": self.config.zap_port},
                environment={
                    "ZAP_PORT": str(self.config.zap_port),
                    "ZAP_HOST": self.config.zap_host
                },
                detach=True,
                mem_limit=self.config.memory_limit,
                cpu_quota=int(self.config.cpu_limit * 100000),
                cpu_period=100000,
                remove=False
            )
            
            logger.info(f"Started ZAP container {self.docker_container.id} for worker {self.config.worker_id}")
            
        except Exception as e:
            logger.error(f"Failed to start ZAP container for worker {self.config.worker_id}: {str(e)}")
            raise
    
    async def _wait_for_zap_ready(self, timeout: int = 60) -> bool:
        """Wait for ZAP to be ready and get API key"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://{self.config.zap_host}:{self.config.zap_port}/JSON/core/view/version/",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.api_key = data.get("apikey")
                        logger.info(f"ZAP worker {self.config.worker_id} ready, version: {data.get('version')}")
                        return True
                        
            except Exception as e:
                logger.debug(f"ZAP worker {self.config.worker_id} not ready yet: {str(e)}")
                await asyncio.sleep(2)
        
        return False
    
    async def scan_page(self, task: ScanTask) -> List[Dict[str, Any]]:
        """Scan a single page for vulnerabilities"""
        try:
            logger.info(f"Worker {self.config.worker_id} scanning {task.page_url}")
            
            # Add task to current tasks
            self.current_tasks.append(task)
            self.status = WorkerStatus.BUSY
            
            # Update worker status
            await self.redis.update_worker_status(
                self.config.worker_id,
                self.status.value,
                current_task=task.task_id
            )
            
            # Perform the scan
            vulnerabilities = await self._perform_scan(task)
            
            # Remove task from current tasks
            self.current_tasks = [t for t in self.current_tasks if t.task_id != task.task_id]
            
            # Update status
            if not self.current_tasks:
                self.status = WorkerStatus.IDLE
            
            # Update worker status
            await self.redis.update_worker_status(
                self.config.worker_id,
                self.status.value
            )
            
            # Update statistics
            self.scan_count += 1
            self.last_heartbeat = time.time()
            
            logger.info(f"Worker {self.config.worker_id} completed scan of {task.page_url}")
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Worker {self.config.worker_id} failed to scan {task.page_url}: {str(e)}")
            self.error_count += 1
            self.status = WorkerStatus.ERROR
            return []
    
    async def _perform_scan(self, task: ScanTask) -> List[Dict[str, Any]]:
        """Perform the actual vulnerability scan"""
        try:
            base_url = f"http://{self.config.zap_host}:{self.config.zap_port}"
            
            async with httpx.AsyncClient() as client:
                # Set target URL
                await client.get(
                    f"{base_url}/JSON/core/action/accessUrl/",
                    params={
                        "url": task.target_url,
                        "apikey": self.api_key
                    }
                )
                
                # Start spider scan
                spider_response = await client.get(
                    f"{base_url}/JSON/spider/action/scan/",
                    params={
                        "url": task.page_url,
                        "apikey": self.api_key,
                        "maxChildren": 10,
                        "recurse": False
                    }
                )
                
                if spider_response.status_code != 200:
                    logger.warning(f"Spider scan failed for {task.page_url}")
                    return []
                
                # Wait for spider to complete
                spider_id = spider_response.json().get("scan")
                if spider_id:
                    await self._wait_for_spider_completion(client, spider_id)
                
                # Start active scan
                ascan_response = await client.get(
                    f"{base_url}/JSON/ascan/action/scan/",
                    params={
                        "url": task.page_url,
                        "apikey": self.api_key,
                        "recurse": False,
                        "inScopeOnly": True
                    }
                )
                
                if ascan_response.status_code != 200:
                    logger.warning(f"Active scan failed for {task.page_url}")
                    return []
                
                # Wait for active scan to complete
                ascan_id = ascan_response.json().get("scan")
                if ascan_id:
                    await self._wait_for_ascan_completion(client, ascan_id)
                
                # Get results
                alerts_response = await client.get(
                    f"{base_url}/JSON/core/view/alerts/",
                    params={"apikey": self.api_key}
                )
                
                if alerts_response.status_code == 200:
                    alerts = alerts_response.json().get("alerts", [])
                    return self._process_alerts(alerts, task.page_url)
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Scan failed for {task.page_url}: {str(e)}")
            return []
    
    async def _wait_for_spider_completion(self, client: httpx.AsyncClient, spider_id: str, timeout: int = 60):
        """Wait for spider scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await client.get(
                    f"http://{self.config.zap_host}:{self.config.zap_port}/JSON/spider/view/status/",
                    params={
                        "scanId": spider_id,
                        "apikey": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    status = int(response.json().get("status", 0))
                    if status >= 100:
                        return
                    await asyncio.sleep(1)
                else:
                    break
                    
            except Exception:
                break
    
    async def _wait_for_ascan_completion(self, client: httpx.AsyncClient, ascan_id: str, timeout: int = 120):
        """Wait for active scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await client.get(
                    f"http://{self.config.zap_host}:{self.config.zap_port}/JSON/ascan/view/status/",
                    params={
                        "scanId": ascan_id,
                        "apikey": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    status = int(response.json().get("status", 0))
                    if status >= 100:
                        return
                    await asyncio.sleep(2)
                else:
                    break
                    
            except Exception:
                break
    
    def _process_alerts(self, alerts: List[Dict[str, Any]], page_url: str) -> List[Dict[str, Any]]:
        """Process ZAP alerts into vulnerability format"""
        vulnerabilities = []
        
        for alert in alerts:
            try:
                vuln = {
                    "id": f"vuln_{uuid.uuid4().hex[:8]}",
                    "type": self._map_alert_type(alert.get("name", "")),
                    "severity": self._map_risk_level(alert.get("risk", "")),
                    "title": alert.get("name", "Unknown Vulnerability"),
                    "description": alert.get("description", ""),
                    "url": page_url,
                    "parameter": alert.get("param", ""),
                    "evidence": alert.get("evidence", ""),
                    "solution": alert.get("solution", ""),
                    "cwe_id": alert.get("cweid", ""),
                    "confidence": self._map_confidence(alert.get("confidence", ""))
                }
                vulnerabilities.append(vuln)
            except Exception as e:
                logger.warning(f"Failed to process alert: {str(e)}")
                continue
        
        return vulnerabilities
    
    def _map_alert_type(self, alert_name: str) -> str:
        """Map ZAP alert names to vulnerability types"""
        alert_lower = alert_name.lower()
        
        if "xss" in alert_lower or "cross-site scripting" in alert_lower:
            return "xss"
        elif "sql" in alert_lower and "injection" in alert_lower:
            return "sql_injection"
        elif "csrf" in alert_lower or "cross-site request forgery" in alert_lower:
            return "csrf"
        elif "header" in alert_lower:
            return "insecure_headers"
        elif "ssl" in alert_lower or "tls" in alert_lower:
            return "ssl_tls"
        elif "authentication" in alert_lower or "auth" in alert_lower:
            return "authentication"
        else:
            return "other"
    
    def _map_risk_level(self, risk: str) -> str:
        """Map ZAP risk levels to severity levels"""
        risk_mapping = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "informational"
        }
        return risk_mapping.get(risk, "low")
    
    def _map_confidence(self, confidence: str) -> str:
        """Map ZAP confidence levels"""
        confidence_mapping = {
            "High": "high",
            "Medium": "medium",
            "Low": "low"
        }
        return confidence_mapping.get(confidence, "medium")
    
    async def stop(self):
        """Stop the ZAP worker"""
        try:
            if self.docker_container:
                self.docker_container.stop()
                self.docker_container.remove()
                logger.info(f"Stopped ZAP worker {self.config.worker_id}")
            
            self.status = WorkerStatus.OFFLINE
            
        except Exception as e:
            logger.error(f"Failed to stop ZAP worker {self.config.worker_id}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "worker_id": self.config.worker_id,
            "status": self.status.value,
            "current_tasks": len(self.current_tasks),
            "scan_count": self.scan_count,
            "error_count": self.error_count,
            "last_heartbeat": self.last_heartbeat,
            "uptime": time.time() - self.last_heartbeat
        }

class WorkerPool:
    """High-performance worker pool for parallel scanning"""
    
    def __init__(self, redis_coordinator, max_workers: int = None):
        self.redis = redis_coordinator
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.workers: Dict[str, ZAPWorker] = {}
        self.task_queue = Queue()
        self.running = False
        self.worker_threads: List[threading.Thread] = []
        
        # Performance metrics
        self.total_tasks_completed = 0
        self.total_scan_time = 0
        self.start_time = None
    
    async def initialize(self) -> bool:
        """Initialize the worker pool"""
        try:
            logger.info(f"Initializing worker pool with {self.max_workers} workers")
            
            # Create worker configurations
            base_port = 8080
            for i in range(self.max_workers):
                worker_id = f"worker_{i+1}"
                config = WorkerConfig(
                    worker_id=worker_id,
                    zap_port=base_port + i
                )
                
                # Create and start worker
                worker = ZAPWorker(config, self.redis)
                if await worker.start():
                    self.workers[worker_id] = worker
                else:
                    logger.error(f"Failed to start worker {worker_id}")
            
            if not self.workers:
                logger.error("No workers could be started")
                return False
            
            # Start worker threads
            self.running = True
            for worker in self.workers.values():
                thread = threading.Thread(
                    target=self._worker_loop,
                    args=(worker,),
                    daemon=True
                )
                thread.start()
                self.worker_threads.append(thread)
            
            self.start_time = time.time()
            logger.info(f"Worker pool initialized with {len(self.workers)} workers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize worker pool: {str(e)}")
            return False
    
    def _worker_loop(self, worker: ZAPWorker):
        """Main worker loop for processing tasks"""
        while self.running:
            try:
                # Get task from queue (with timeout)
                try:
                    task = self.task_queue.get(timeout=1)
                except Empty:
                    continue
                
                # Process task
                asyncio.run(self._process_task(worker, task))
                
            except Exception as e:
                logger.error(f"Error in worker loop for {worker.config.worker_id}: {str(e)}")
                time.sleep(1)
    
    async def _process_task(self, worker: ZAPWorker, task: ScanTask):
        """Process a single task"""
        try:
            start_time = time.time()
            
            # Scan the page
            vulnerabilities = await worker.scan_page(task)
            
            # Store results
            if vulnerabilities:
                await self.redis.add_scan_results(task.scan_id, vulnerabilities)
            
            # Update progress
            await self.redis.update_scan_progress(
                task.scan_id,
                completed_pages=1,  # This would be aggregated
                total_vulnerabilities=len(vulnerabilities),
                current_phase="scanning"
            )
            
            # Update statistics
            scan_time = time.time() - start_time
            self.total_tasks_completed += 1
            self.total_scan_time += scan_time
            
            logger.info(f"Completed task {task.task_id} in {scan_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to process task {task.task_id}: {str(e)}")
    
    async def submit_scan_tasks(self, scan_id: str, pages: List[str], target_url: str):
        """Submit multiple scan tasks to the worker pool"""
        try:
            logger.info(f"Submitting {len(pages)} tasks for scan {scan_id}")
            
            # Create tasks
            tasks = []
            for i, page_url in enumerate(pages):
                task = ScanTask(
                    task_id=f"{scan_id}_task_{i}",
                    scan_id=scan_id,
                    page_url=page_url,
                    target_url=target_url,
                    priority=1 if i == 0 else 2  # Prioritize main page
                )
                tasks.append(task)
                self.task_queue.put(task)
            
            logger.info(f"Submitted {len(tasks)} tasks to worker pool")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to submit scan tasks: {str(e)}")
            return []
    
    async def wait_for_completion(self, scan_id: str, timeout: int = 300) -> bool:
        """Wait for all tasks of a scan to complete"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if all tasks are completed
                progress = await self.redis.get_scan_progress(scan_id)
                
                if progress.get("status") == "completed":
                    return True
                
                # Check if scan failed
                if progress.get("status") in ["failed", "cancelled"]:
                    return False
                
                await asyncio.sleep(2)
            
            logger.warning(f"Scan {scan_id} timed out after {timeout}s")
            return False
            
        except Exception as e:
            logger.error(f"Failed to wait for scan completion: {str(e)}")
            return False
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        return {
            "total_workers": len(self.workers),
            "active_workers": len([w for w in self.workers.values() if w.status == WorkerStatus.BUSY]),
            "idle_workers": len([w for w in self.workers.values() if w.status == WorkerStatus.IDLE]),
            "error_workers": len([w for w in self.workers.values() if w.status == WorkerStatus.ERROR]),
            "workers": {worker_id: worker.get_stats() for worker_id, worker in self.workers.items()}
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.start_time:
            uptime = time.time() - self.start_time
            avg_scan_time = self.total_scan_time / max(self.total_tasks_completed, 1)
            tasks_per_second = self.total_tasks_completed / max(uptime, 1)
        else:
            uptime = 0
            avg_scan_time = 0
            tasks_per_second = 0
        
        return {
            "uptime": uptime,
            "total_tasks_completed": self.total_tasks_completed,
            "average_scan_time": avg_scan_time,
            "tasks_per_second": tasks_per_second,
            "queue_size": self.task_queue.qsize()
        }
    
    async def shutdown(self):
        """Shutdown the worker pool"""
        try:
            logger.info("Shutting down worker pool...")
            
            self.running = False
            
            # Stop all workers
            for worker in self.workers.values():
                await worker.stop()
            
            # Wait for worker threads to finish
            for thread in self.worker_threads:
                if thread.is_alive():
                    thread.join(timeout=5)
            
            logger.info("Worker pool shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during worker pool shutdown: {str(e)}")


