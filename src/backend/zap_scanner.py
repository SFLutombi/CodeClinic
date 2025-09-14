"""
ZAP Scanner using the official Python API
This replaces the HTTP-based approach with the proper ZAP Python client
"""

import time
import logging
from typing import Dict, List, Optional
from zapv2 import ZAPv2

logger = logging.getLogger(__name__)

class ZAPScanner:
    """ZAP scanner using the official Python API client"""
    
    def __init__(self, zap_host: str = "localhost", zap_port: int = 8080):
        self.zap_host = zap_host
        self.zap_port = zap_port
        self.zap = None
        
    def connect(self) -> bool:
        """Connect to ZAP instance"""
        try:
            self.zap = ZAPv2(
                apikey='',  # No API key needed when api.disablekey=true
                proxies={
                    'http': f'http://{self.zap_host}:{self.zap_port}',
                    'https': f'http://{self.zap_host}:{self.zap_port}'
                }
            )
            
            # Test connection
            version = self.zap.core.version
            logger.info(f"Connected to ZAP version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ZAP: {e}")
            return False
    
    def scan_url(self, url: str, progress_callback=None) -> Dict:
        """
        Perform a complete security scan of the target URL
        
        Args:
            url: Target URL to scan
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary containing scan results
        """
        if not self.zap:
            raise Exception("ZAP not connected. Call connect() first.")
        
        results = {
            "url": url,
            "vulnerabilities": [],
            "summary": {
                "total_issues": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "info": 0
            },
            "scan_duration": 0,
            "timestamp": time.time()
        }
        
        start_time = time.time()
        
        try:
            # Progress callback for setup
            if progress_callback:
                progress_callback(10, "Setting up target...")
            
            # Set target URL in ZAP context
            self.zap.core.access_url(url)
            
            if progress_callback:
                progress_callback(20, "Target configured")
            
            # Start spider scan
            if progress_callback:
                progress_callback(30, "Starting spider scan...")
            
            logger.info(f"Starting spider scan for {url}")
            spider_scan_id = self.zap.spider.scan(url, maxchildren=50, recurse=True)
            
            if not spider_scan_id or spider_scan_id == 0:
                raise Exception("Failed to start spider scan - invalid scan ID")
            
            logger.info(f"Spider scan started with ID: {spider_scan_id}")
            
            # Wait for spider to complete
            while int(self.zap.spider.status(spider_scan_id)) < 100:
                status = int(self.zap.spider.status(spider_scan_id))
                logger.info(f"Spider progress: {status}%")
                
                if progress_callback:
                    # Spider progress: 30% to 60%
                    progress = 30 + int((status / 100) * 30)
                    progress_callback(progress, f"Spider scan: {status}%")
                
                time.sleep(2)
            
            logger.info("Spider scan completed")
            
            if progress_callback:
                progress_callback(60, "Spider scan completed")
            
            # Start active scan
            if progress_callback:
                progress_callback(70, "Starting active scan...")
            
            logger.info(f"Starting active scan for {url}")
            ascan_id = self.zap.ascan.scan(url, recurse=True, inscopeonly=True)
            
            if not ascan_id or ascan_id == 0:
                raise Exception("Failed to start active scan - invalid scan ID")
            
            logger.info(f"Active scan started with ID: {ascan_id}")
            
            # Wait for active scan to complete
            while int(self.zap.ascan.status(ascan_id)) < 100:
                status = int(self.zap.ascan.status(ascan_id))
                logger.info(f"Active scan progress: {status}%")
                
                if progress_callback:
                    # Active scan progress: 70% to 95%
                    progress = 70 + int((status / 100) * 25)
                    progress_callback(progress, f"Active scan: {status}%")
                
                time.sleep(3)
            
            logger.info("Active scan completed")
            
            if progress_callback:
                progress_callback(95, "Processing results...")
            
            # Get alerts (vulnerabilities)
            alerts = self.zap.core.alerts(baseurl=url)
            vulnerabilities = self._process_alerts(alerts)
            results["vulnerabilities"] = vulnerabilities
            
            # Update summary
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "low").lower()
                if severity == "high":
                    results["summary"]["high_risk"] += 1
                elif severity == "medium":
                    results["summary"]["medium_risk"] += 1
                elif severity == "low":
                    results["summary"]["low_risk"] += 1
                else:
                    results["summary"]["info"] += 1
            
            results["summary"]["total_issues"] = len(vulnerabilities)
            
            if progress_callback:
                progress_callback(100, "Scan completed")
            
            results["scan_duration"] = time.time() - start_time
            logger.info(f"Scan completed in {results['scan_duration']:.2f}s with {len(vulnerabilities)} vulnerabilities")
            
            return results
            
        except Exception as e:
            logger.error(f"Scan failed for {url}: {e}")
            
            # Return error result
            results["error"] = str(e)
            results["scan_duration"] = time.time() - start_time
            
            # Add a fallback vulnerability entry for the error
            results["vulnerabilities"] = [{
                "id": f"error_{int(time.time() * 1000)}",
                "type": "scan_error",
                "severity": "informational",
                "title": "Scan Error",
                "description": f"ZAP scan failed: {str(e)}",
                "url": url,
                "parameter": None,
                "evidence": "Scan could not complete",
                "solution": "Check if the target URL is accessible and ZAP is running properly",
                "cwe_id": None,
                "confidence": "low"
            }]
            results["summary"]["total_issues"] = 1
            results["summary"]["info"] = 1
            
            return results
    
    def _process_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """Process ZAP alerts into vulnerability format"""
        vulnerabilities = []
        
        for alert in alerts:
            try:
                # Map ZAP risk levels to our severity levels
                risk_mapping = {
                    "High": "high",
                    "Medium": "medium", 
                    "Low": "low",
                    "Informational": "informational"
                }
                
                # Map ZAP alert names to vulnerability types
                alert_name = alert.get("name", "").lower()
                if "xss" in alert_name or "cross-site scripting" in alert_name:
                    vuln_type = "xss"
                elif "sql" in alert_name and "injection" in alert_name:
                    vuln_type = "sql_injection"
                elif "csrf" in alert_name or "cross-site request forgery" in alert_name:
                    vuln_type = "csrf"
                elif "header" in alert_name:
                    vuln_type = "insecure_headers"
                elif "ssl" in alert_name or "tls" in alert_name:
                    vuln_type = "ssl_tls"
                elif "authentication" in alert_name or "auth" in alert_name:
                    vuln_type = "authentication"
                else:
                    vuln_type = "other"
                
                vuln = {
                    "id": f"vuln_{int(time.time() * 1000)}_{len(vulnerabilities)}",
                    "type": vuln_type,
                    "severity": risk_mapping.get(alert.get("risk", "Low"), "low"),
                    "title": alert.get("name", "Unknown Vulnerability"),
                    "description": alert.get("description", ""),
                    "url": alert.get("url", ""),
                    "parameter": alert.get("param", ""),
                    "evidence": alert.get("evidence", ""),
                    "solution": alert.get("solution", ""),
                    "cwe_id": alert.get("cweid", ""),
                    "confidence": alert.get("confidence", "medium")
                }
                vulnerabilities.append(vuln)
                
            except Exception as e:
                logger.warning(f"Failed to process alert: {str(e)}")
                continue
        
        return vulnerabilities
