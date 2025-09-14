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
            
            # Check if scan ID is valid (should be numeric)
            try:
                scan_id_int = int(ascan_id)
                if scan_id_int <= 0:
                    raise Exception(f"Failed to start active scan - invalid scan ID: {ascan_id}")
            except (ValueError, TypeError):
                raise Exception(f"Failed to start active scan - invalid scan ID: {ascan_id}")
            
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
            
            # Provide more specific error messages
            error_message = str(e)
            if "url_not_found" in error_message or "does_not_exist" in error_message:
                error_message = "Target URL is not accessible or does not exist"
            elif "connection" in error_message.lower():
                error_message = "Unable to connect to the target URL"
            elif "timeout" in error_message.lower():
                error_message = "Request timed out - the target may be slow or unreachable"
            
            # Return error result
            results["error"] = error_message
            results["scan_duration"] = time.time() - start_time
            
            # Add a fallback vulnerability entry for the error
            results["vulnerabilities"] = [{
                "id": f"error_{int(time.time() * 1000)}",
                "type": "scan_error",
                "severity": "informational",
                "title": "Scan Error",
                "description": f"Security scan could not complete: {error_message}",
                "url": url,
                "parameter": None,
                "evidence": "Scan could not complete",
                "solution": "Please check if the target URL is accessible and try again",
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
    
    def crawl_url(self, url: str, progress_callback=None) -> Dict:
        """
        Perform crawling to discover pages on the target URL
        
        Args:
            url: Target URL to crawl
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary containing discovered pages
        """
        if not self.zap:
            raise Exception("ZAP not connected. Call connect() first.")
        
        results = {
            "url": url,
            "discovered_pages": [],
            "crawl_duration": 0,
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
                    # Spider progress: 30% to 90%
                    progress = 30 + int((status / 100) * 60)
                    progress_callback(progress, f"Spider scan: {status}%")
                
                time.sleep(2)
            
            logger.info("Spider scan completed")
            
            if progress_callback:
                progress_callback(90, "Processing discovered pages...")
            
            # Get discovered URLs
            discovered_urls = self.zap.spider.results(spider_scan_id)
            
            # Process and format the discovered pages
            pages = []
            for page_url in discovered_urls:
                pages.append({
                    "url": page_url,
                    "title": self._get_page_title(page_url),
                    "status_code": 200  # Assume successful if discovered
                })
            
            results["discovered_pages"] = pages
            
            if progress_callback:
                progress_callback(100, "Crawl completed")
            
            results["crawl_duration"] = time.time() - start_time
            logger.info(f"Crawl completed in {results['crawl_duration']:.2f}s with {len(pages)} pages discovered")
            
            return results
            
        except Exception as e:
            logger.error(f"Crawl failed for {url}: {e}")
            
            # Return error result
            results["error"] = str(e)
            results["crawl_duration"] = time.time() - start_time
            
            return results
    
    def scan_selected_pages(self, base_url: str, selected_pages: List[str], progress_callback=None) -> Dict:
        """
        Perform security scan on selected pages
        
        Args:
            base_url: Base URL of the site
            selected_pages: List of page URLs to scan
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary containing scan results
        """
        if not self.zap:
            raise Exception("ZAP not connected. Call connect() first.")
        
        results = {
            "url": base_url,
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
            self.zap.core.access_url(base_url)
            
            if progress_callback:
                progress_callback(20, "Target configured")
            
            # Add selected pages to ZAP context
            if progress_callback:
                progress_callback(30, "Adding pages to scan scope...")
            
            for page_url in selected_pages:
                self.zap.core.access_url(page_url)
            
            if progress_callback:
                progress_callback(40, f"Added {len(selected_pages)} pages to scope")
            
            # Start active scan on selected pages
            if progress_callback:
                progress_callback(50, "Starting active scan...")
            
            logger.info(f"Starting active scan for {len(selected_pages)} selected pages")
            ascan_id = self.zap.ascan.scan(base_url, recurse=True, inscopeonly=True)
            
            # Check if scan ID is valid (should be numeric)
            try:
                scan_id_int = int(ascan_id)
                if scan_id_int <= 0:
                    raise Exception(f"Failed to start active scan - invalid scan ID: {ascan_id}")
            except (ValueError, TypeError):
                raise Exception(f"Failed to start active scan - invalid scan ID: {ascan_id}")
            
            logger.info(f"Active scan started with ID: {ascan_id}")
            
            # Wait for active scan to complete
            while int(self.zap.ascan.status(ascan_id)) < 100:
                status = int(self.zap.ascan.status(ascan_id))
                logger.info(f"Active scan progress: {status}%")
                
                if progress_callback:
                    # Active scan progress: 50% to 90%
                    progress = 50 + int((status / 100) * 40)
                    progress_callback(progress, f"Active scan: {status}%")
                
                time.sleep(3)
            
            logger.info("Active scan completed")
            
            if progress_callback:
                progress_callback(90, "Processing results...")
            
            # Get alerts (vulnerabilities) for all scanned pages
            all_alerts = []
            for page_url in selected_pages:
                alerts = self.zap.core.alerts(baseurl=page_url)
                all_alerts.extend(alerts)
            
            # Remove duplicates based on URL and alert name
            unique_alerts = []
            seen = set()
            for alert in all_alerts:
                key = (alert.get('url', ''), alert.get('name', ''))
                if key not in seen:
                    seen.add(key)
                    unique_alerts.append(alert)
            
            vulnerabilities = self._process_alerts(unique_alerts)
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
            logger.info(f"Selected pages scan completed in {results['scan_duration']:.2f}s with {len(vulnerabilities)} vulnerabilities")
            
            return results
            
        except Exception as e:
            logger.error(f"Selected pages scan failed: {e}")
            
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
                "url": base_url,
                "parameter": None,
                "evidence": "Scan could not complete",
                "solution": "Check if the target URL is accessible and ZAP is running properly",
                "cwe_id": None,
                "confidence": "low"
            }]
            results["summary"]["total_issues"] = 1
            results["summary"]["info"] = 1
            
            return results
    
    def _get_page_title(self, url: str) -> str:
        """Get page title from ZAP"""
        try:
            # Try to get the title from ZAP's site tree
            site_tree = self.zap.core.sites()
            for site in site_tree:
                if url in site:
                    # This is a simplified approach - in reality you'd need to parse the site tree
                    return f"Page from {url}"
            return "Discovered Page"
        except:
            return "Discovered Page"
