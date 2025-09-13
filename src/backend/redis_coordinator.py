"""
Redis-based coordination system for parallel scanning
Handles inter-process communication and result aggregation
"""

import redis
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ScanStatus(Enum):
    PENDING = "pending"
    DISCOVERING = "discovering"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScanJob:
    """Scan job definition"""
    scan_id: str
    target_url: str
    scan_type: str
    pages: List[str]
    status: ScanStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: int = 0
    total_vulnerabilities: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanJob':
        data['status'] = ScanStatus(data['status'])
        return cls(**data)

class RedisCoordinator:
    """
    Redis-based coordination system for parallel scanning
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        
        # Redis keys
        self.scan_jobs_key = "scan_jobs"
        self.scan_results_key = "scan_results"
        self.scan_progress_key = "scan_progress"
        self.worker_tasks_key = "worker_tasks"
        self.worker_results_key = "worker_results"
        self.worker_status_key = "worker_status"
        
        # Channels for real-time updates
        self.scan_updates_channel = "scan_updates"
        self.worker_updates_channel = "worker_updates"
    
    async def create_scan_job(self, target_url: str, scan_type: str, pages: List[str]) -> str:
        """Create a new scan job"""
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        
        job = ScanJob(
            scan_id=scan_id,
            target_url=target_url,
            scan_type=scan_type,
            pages=pages,
            status=ScanStatus.PENDING,
            created_at=time.time()
        )
        
        # Store job in Redis
        self.redis_client.hset(
            self.scan_jobs_key,
            scan_id,
            json.dumps(job.to_dict(), default=str)
        )
        
        # Initialize progress tracking
        self.redis_client.hset(
            self.scan_progress_key,
            scan_id,
            json.dumps({
                "progress": 0,
                "status": "pending",
                "total_pages": len(pages),
                "completed_pages": 0,
                "total_vulnerabilities": 0,
                "current_phase": "initializing"
            })
        )
        
        logger.info(f"Created scan job {scan_id} for {len(pages)} pages")
        return scan_id
    
    async def get_scan_job(self, scan_id: str) -> Optional[ScanJob]:
        """Get scan job by ID"""
        try:
            job_data = self.redis_client.hget(self.scan_jobs_key, scan_id)
            if job_data:
                return ScanJob.from_dict(json.loads(job_data))
            return None
        except Exception as e:
            logger.error(f"Failed to get scan job {scan_id}: {str(e)}")
            return None
    
    async def update_scan_status(self, scan_id: str, status: ScanStatus, 
                                progress: int = None, error_message: str = None):
        """Update scan status and progress"""
        try:
            # Update job status
            job = await self.get_scan_job(scan_id)
            if job:
                job.status = status
                if progress is not None:
                    job.progress = progress
                if error_message:
                    job.error_message = error_message
                if status == ScanStatus.SCANNING and not job.started_at:
                    job.started_at = time.time()
                elif status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
                    job.completed_at = time.time()
                
                # Save updated job
                self.redis_client.hset(
                    self.scan_jobs_key,
                    scan_id,
                    json.dumps(job.to_dict(), default=str)
                )
            
            # Update progress tracking
            progress_data = {
                "progress": progress or 0,
                "status": status.value,
                "updated_at": time.time()
            }
            
            # Get existing progress data
            existing_progress = self.redis_client.hget(self.scan_progress_key, scan_id)
            if existing_progress:
                existing_data = json.loads(existing_progress)
                progress_data.update(existing_data)
            
            self.redis_client.hset(
                self.scan_progress_key,
                scan_id,
                json.dumps(progress_data)
            )
            
            # Publish update
            await self.publish_scan_update(scan_id, {
                "status": status.value,
                "progress": progress or 0,
                "error_message": error_message
            })
            
        except Exception as e:
            logger.error(f"Failed to update scan status for {scan_id}: {str(e)}")
    
    async def update_scan_progress(self, scan_id: str, completed_pages: int, 
                                 total_vulnerabilities: int, current_phase: str = None):
        """Update detailed scan progress"""
        try:
            # Get existing progress
            progress_data = self.redis_client.hget(self.scan_progress_key, scan_id)
            if progress_data:
                data = json.loads(progress_data)
            else:
                data = {}
            
            # Update progress data
            data.update({
                "completed_pages": completed_pages,
                "total_vulnerabilities": total_vulnerabilities,
                "updated_at": time.time()
            })
            
            if current_phase:
                data["current_phase"] = current_phase
            
            # Calculate progress percentage
            total_pages = data.get("total_pages", 1)
            progress_percentage = int((completed_pages / total_pages) * 100)
            data["progress"] = progress_percentage
            
            # Save updated progress
            self.redis_client.hset(
                self.scan_progress_key,
                scan_id,
                json.dumps(data)
            )
            
            # Publish progress update
            await self.publish_scan_update(scan_id, {
                "progress": progress_percentage,
                "completed_pages": completed_pages,
                "total_pages": total_pages,
                "total_vulnerabilities": total_vulnerabilities,
                "current_phase": current_phase
            })
            
        except Exception as e:
            logger.error(f"Failed to update scan progress for {scan_id}: {str(e)}")
    
    async def add_scan_results(self, scan_id: str, vulnerabilities: List[Dict[str, Any]]):
        """Add vulnerabilities to scan results"""
        try:
            # Store vulnerabilities
            for vuln in vulnerabilities:
                vuln_id = vuln.get("id", f"vuln_{uuid.uuid4().hex[:8]}")
                self.redis_client.hset(
                    f"{self.scan_results_key}:{scan_id}",
                    vuln_id,
                    json.dumps(vuln)
                )
            
            # Update total count
            total_vulns = len(vulnerabilities)
            progress_data = self.redis_client.hget(self.scan_progress_key, scan_id)
            if progress_data:
                data = json.loads(progress_data)
                data["total_vulnerabilities"] = data.get("total_vulnerabilities", 0) + total_vulns
                self.redis_client.hset(
                    self.scan_progress_key,
                    scan_id,
                    json.dumps(data)
                )
            
            logger.info(f"Added {total_vulns} vulnerabilities to scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to add scan results for {scan_id}: {str(e)}")
    
    async def get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all vulnerabilities for a scan"""
        try:
            results = self.redis_client.hgetall(f"{self.scan_results_key}:{scan_id}")
            vulnerabilities = []
            
            for vuln_id, vuln_data in results.items():
                try:
                    vuln = json.loads(vuln_data)
                    vulnerabilities.append(vuln)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse vulnerability {vuln_id}")
                    continue
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Failed to get scan results for {scan_id}: {str(e)}")
            return []
    
    async def get_scan_progress(self, scan_id: str) -> Dict[str, Any]:
        """Get current scan progress"""
        try:
            progress_data = self.redis_client.hget(self.scan_progress_key, scan_id)
            if progress_data:
                return json.loads(progress_data)
            else:
                return {
                    "progress": 0,
                    "status": "unknown",
                    "total_pages": 0,
                    "completed_pages": 0,
                    "total_vulnerabilities": 0,
                    "current_phase": "unknown"
                }
        except Exception as e:
            logger.error(f"Failed to get scan progress for {scan_id}: {str(e)}")
            return {"progress": 0, "status": "error"}
    
    async def create_worker_task(self, scan_id: str, page_url: str, worker_id: str) -> str:
        """Create a task for a worker"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = {
            "task_id": task_id,
            "scan_id": scan_id,
            "page_url": page_url,
            "worker_id": worker_id,
            "status": "pending",
            "created_at": time.time()
        }
        
        # Store task
        self.redis_client.hset(
            f"{self.worker_tasks_key}:{worker_id}",
            task_id,
            json.dumps(task)
        )
        
        # Add to worker queue
        self.redis_client.lpush(f"worker_queue:{worker_id}", task_id)
        
        logger.info(f"Created task {task_id} for worker {worker_id} on {page_url}")
        return task_id
    
    async def get_worker_tasks(self, worker_id: str) -> List[Dict[str, Any]]:
        """Get tasks for a specific worker"""
        try:
            tasks = self.redis_client.hgetall(f"{self.worker_tasks_key}:{worker_id}")
            return [json.loads(task_data) for task_data in tasks.values()]
        except Exception as e:
            logger.error(f"Failed to get tasks for worker {worker_id}: {str(e)}")
            return []
    
    async def update_worker_status(self, worker_id: str, status: str, 
                                 current_task: str = None, last_heartbeat: float = None):
        """Update worker status"""
        try:
            worker_data = {
                "worker_id": worker_id,
                "status": status,
                "current_task": current_task,
                "last_heartbeat": last_heartbeat or time.time(),
                "updated_at": time.time()
            }
            
            self.redis_client.hset(
                self.worker_status_key,
                worker_id,
                json.dumps(worker_data)
            )
            
            # Publish worker update
            await self.publish_worker_update(worker_id, worker_data)
            
        except Exception as e:
            logger.error(f"Failed to update worker status for {worker_id}: {str(e)}")
    
    async def get_worker_status(self, worker_id: str = None) -> Dict[str, Any]:
        """Get worker status(es)"""
        try:
            if worker_id:
                worker_data = self.redis_client.hget(self.worker_status_key, worker_id)
                if worker_data:
                    return json.loads(worker_data)
                return {}
            else:
                workers = self.redis_client.hgetall(self.worker_status_key)
                return {wid: json.loads(data) for wid, data in workers.items()}
        except Exception as e:
            logger.error(f"Failed to get worker status: {str(e)}")
            return {}
    
    async def publish_scan_update(self, scan_id: str, update_data: Dict[str, Any]):
        """Publish scan update to subscribers"""
        try:
            message = {
                "scan_id": scan_id,
                "timestamp": time.time(),
                "data": update_data
            }
            
            self.redis_client.publish(
                self.scan_updates_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Failed to publish scan update: {str(e)}")
    
    async def publish_worker_update(self, worker_id: str, update_data: Dict[str, Any]):
        """Publish worker update to subscribers"""
        try:
            message = {
                "worker_id": worker_id,
                "timestamp": time.time(),
                "data": update_data
            }
            
            self.redis_client.publish(
                self.worker_updates_channel,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Failed to publish worker update: {str(e)}")
    
    async def subscribe_to_scan_updates(self, scan_id: str, callback):
        """Subscribe to updates for a specific scan"""
        try:
            await self.pubsub.subscribe(self.scan_updates_channel)
            
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        if data.get('scan_id') == scan_id:
                            await callback(data)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to subscribe to scan updates: {str(e)}")
    
    async def cleanup_scan_data(self, scan_id: str):
        """Clean up scan data after completion"""
        try:
            # Remove from active jobs
            self.redis_client.hdel(self.scan_jobs_key, scan_id)
            
            # Remove progress data
            self.redis_client.hdel(self.scan_progress_key, scan_id)
            
            # Remove results (optional - you might want to keep them)
            # self.redis_client.delete(f"{self.scan_results_key}:{scan_id}")
            
            logger.info(f"Cleaned up data for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup scan data for {scan_id}: {str(e)}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            # Count active scans
            active_scans = self.redis_client.hlen(self.scan_jobs_key)
            
            # Count workers
            workers = self.redis_client.hlen(self.worker_status_key)
            
            # Count total vulnerabilities across all scans
            scan_keys = self.redis_client.keys(f"{self.scan_results_key}:*")
            total_vulnerabilities = 0
            for scan_key in scan_keys:
                vuln_count = self.redis_client.hlen(scan_key)
                total_vulnerabilities += vuln_count
            
            return {
                "active_scans": active_scans,
                "total_workers": workers,
                "total_vulnerabilities": total_vulnerabilities,
                "redis_memory_usage": self.redis_client.info()['used_memory_human']
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {str(e)}")
            return {}


