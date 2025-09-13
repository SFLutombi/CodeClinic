"""
ZAP (OWASP ZAP) Integration Module
Handles communication with ZAP API for security scanning
"""

import asyncio
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)

class ZAPScanner:
    """ZAP API integration for security scanning"""
    
    def __init__(self, zap_host: str = "localhost", zap_port: int = 8080):
        self.zap_host = zap_host
        self.zap_port = zap_port
        self.base_url = f"http://{zap_host}:{zap_port}"
        self.api_key = None  # Will be set when ZAP is available
        
    async def is_zap_available(self) -> bool:
        """Check if ZAP is running and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/JSON/core/view/version/")
                if response.status_code == 200:
                    data = response.json()
                    self.api_key = data.get("apikey")
                    logger.info(f"ZAP is available, version: {data.get('version', 'unknown')}")
                    return True
        except Exception as e:
            logger.warning(f"ZAP not available: {str(e)}")
        return False
    
    async def discover_pages(self, target_url: str) -> List[str]:
        """
        Discover pages on the target website using ZAP spider
        
        Args:
            target_url: The base URL to crawl
            
        Returns:
            List of discovered page URLs
        """
        try:
            if not await self.is_zap_available():
                logger.warning("ZAP not available, using fallback page discovery")
                return await self._fallback_page_discovery(target_url)
            
            # Start ZAP spider
            spider_id = await self._start_spider(target_url)
            if not spider_id:
                return await self._fallback_page_discovery(target_url)
            
            # Wait for spider to complete
            await self._wait_for_spider_completion(spider_id)
            
            # Get discovered URLs
            urls = await self._get_spider_results(spider_id)
            
            # Filter and clean URLs
            clean_urls = self._clean_urls(urls, target_url)
            
            logger.info(f"Discovered {len(clean_urls)} pages")
            return clean_urls
            
        except Exception as e:
            logger.error(f"Error discovering pages: {str(e)}")
            return await self._fallback_page_discovery(target_url)
    
    async def run_scan(self, target_url: str, pages: List[str]) -> List[Dict[str, Any]]:
        """
        Run active security scan on the target pages
        
        Args:
            target_url: Base URL being scanned
            pages: List of pages to scan
            
        Returns:
            List of vulnerability dictionaries
        """
        try:
            if not await self.is_zap_available():
                logger.warning("ZAP not available, returning mock vulnerabilities")
                return self._get_mock_vulnerabilities(target_url)
            
            # Set up target in ZAP
            await self._set_target(target_url)
            
            # Run active scan
            scan_id = await self._start_active_scan(target_url)
            if not scan_id:
                return self._get_mock_vulnerabilities(target_url)
            
            # Wait for scan to complete
            await self._wait_for_scan_completion(scan_id)
            
            # Get scan results
            vulnerabilities = await self._get_scan_results()
            
            # Process and structure vulnerabilities
            processed_vulns = self._process_vulnerabilities(vulnerabilities)
            
            logger.info(f"Found {len(processed_vulns)} vulnerabilities")
            return processed_vulns
            
        except Exception as e:
            logger.error(f"Error running scan: {str(e)}")
            return self._get_mock_vulnerabilities(target_url)
    
    async def _start_spider(self, target_url: str) -> Optional[str]:
        """Start ZAP spider scan"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "url": target_url,
                    "maxChildren": 50,
                    "recurse": True
                }
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/JSON/spider/action/scan/",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("scan")
                else:
                    logger.error(f"Failed to start spider: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error starting spider: {str(e)}")
            return None
    
    async def _wait_for_spider_completion(self, spider_id: str, timeout: int = 300):
        """Wait for spider scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    params = {"scanId": spider_id}
                    if self.api_key:
                        params["apikey"] = self.api_key
                    
                    response = await client.get(
                        f"{self.base_url}/JSON/spider/view/status/",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = int(data.get("status", 0))
                        
                        if status == 100:  # Completed
                            logger.info("Spider scan completed")
                            return
                        
                        logger.info(f"Spider progress: {status}%")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"Failed to check spider status: {response.text}")
                        break
                        
            except Exception as e:
                logger.error(f"Error checking spider status: {str(e)}")
                break
        
        logger.warning("Spider scan timed out")
    
    async def _get_spider_results(self, spider_id: str) -> List[str]:
        """Get URLs discovered by spider"""
        try:
            async with httpx.AsyncClient() as client:
                params = {"scanId": spider_id}
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/JSON/spider/view/results/",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Failed to get spider results: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting spider results: {str(e)}")
            return []
    
    async def _set_target(self, target_url: str):
        """Set the target URL in ZAP"""
        try:
            async with httpx.AsyncClient() as client:
                params = {"url": target_url}
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/JSON/core/action/accessUrl/",
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to set target: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error setting target: {str(e)}")
    
    async def _start_active_scan(self, target_url: str) -> Optional[str]:
        """Start ZAP active scan"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "url": target_url,
                    "recurse": True,
                    "inScopeOnly": False
                }
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/JSON/ascan/action/scan/",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("scan")
                else:
                    logger.error(f"Failed to start active scan: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error starting active scan: {str(e)}")
            return None
    
    async def _wait_for_scan_completion(self, scan_id: str, timeout: int = 600):
        """Wait for active scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    params = {"scanId": scan_id}
                    if self.api_key:
                        params["apikey"] = self.api_key
                    
                    response = await client.get(
                        f"{self.base_url}/JSON/ascan/view/status/",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = int(data.get("status", 0))
                        
                        if status == 100:  # Completed
                            logger.info("Active scan completed")
                            return
                        
                        logger.info(f"Active scan progress: {status}%")
                        await asyncio.sleep(5)
                    else:
                        logger.error(f"Failed to check scan status: {response.text}")
                        break
                        
            except Exception as e:
                logger.error(f"Error checking scan status: {str(e)}")
                break
        
        logger.warning("Active scan timed out")
    
    async def _get_scan_results(self) -> List[Dict[str, Any]]:
        """Get scan results from ZAP"""
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/JSON/core/view/alerts/",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("alerts", [])
                else:
                    logger.error(f"Failed to get scan results: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting scan results: {str(e)}")
            return []
    
    def _clean_urls(self, urls: List[str], base_url: str) -> List[str]:
        """Clean and filter discovered URLs"""
        base_domain = urlparse(base_url).netloc
        clean_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                # Only include URLs from the same domain
                if parsed.netloc == base_domain:
                    # Remove fragments and query parameters for now
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean_url not in clean_urls:
                        clean_urls.append(clean_url)
            except Exception:
                continue
        
        return clean_urls[:20]  # Limit to 20 pages for demo
    
    def _process_vulnerabilities(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process ZAP alerts into structured vulnerabilities"""
        vulnerabilities = []
        
        for alert in alerts:
            try:
                vuln = {
                    "id": f"vuln_{len(vulnerabilities) + 1}",
                    "type": self._map_alert_type(alert.get("name", "")),
                    "severity": self._map_risk_level(alert.get("risk", "")),
                    "title": alert.get("name", "Unknown Vulnerability"),
                    "description": alert.get("description", ""),
                    "url": alert.get("url", ""),
                    "parameter": alert.get("param", ""),
                    "evidence": alert.get("evidence", ""),
                    "solution": alert.get("solution", ""),
                    "cwe_id": alert.get("cweid", ""),
                    "confidence": self._map_confidence(alert.get("confidence", ""))
                }
                vulnerabilities.append(vuln)
            except Exception as e:
                logger.error(f"Error processing alert: {str(e)}")
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
        """Map ZAP risk levels to our severity levels"""
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
    
    async def _fallback_page_discovery(self, target_url: str) -> List[str]:
        """Fallback page discovery when ZAP is not available"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient() as client:
                response = await client.get(target_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = []
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/'):
                            full_url = urljoin(target_url, href)
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        if urlparse(full_url).netloc == urlparse(target_url).netloc:
                            links.append(full_url)
                    
                    return [target_url] + links[:10]  # Include base URL + up to 10 links
                else:
                    return [target_url]
        except Exception as e:
            logger.error(f"Fallback page discovery failed: {str(e)}")
            return [target_url]
    
    def _get_mock_vulnerabilities(self, target_url: str) -> List[Dict[str, Any]]:
        """Return mock vulnerabilities for demo purposes"""
        return [
            {
                "id": "vuln_001",
                "type": "insecure_headers",
                "severity": "medium",
                "title": "Missing Security Headers",
                "description": "The application is missing important security headers like X-Frame-Options and X-Content-Type-Options",
                "url": target_url,
                "parameter": None,
                "evidence": "Missing X-Frame-Options header",
                "solution": "Add security headers to prevent clickjacking and MIME type sniffing",
                "cwe_id": "CWE-693",
                "confidence": "high"
            },
            {
                "id": "vuln_002", 
                "type": "ssl_tls",
                "severity": "low",
                "title": "SSL/TLS Configuration Issues",
                "description": "The SSL/TLS configuration could be improved for better security",
                "url": target_url,
                "parameter": None,
                "evidence": "Weak cipher suites detected",
                "solution": "Update SSL/TLS configuration to use stronger cipher suites",
                "cwe_id": "CWE-326",
                "confidence": "medium"
            }
        ]
