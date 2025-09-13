"""
URL Validation Module
Handles URL validation and accessibility checking
"""

import asyncio
import httpx
import validators
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class URLValidator:
    """URL validation and accessibility checking"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def is_valid_url(self, url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            # Use validators library for basic URL validation
            if not validators.url(url):
                return False
            
            # Additional checks
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            return False
    
    async def is_accessible(self, url: str) -> bool:
        """
        Check if URL is accessible via HTTP request
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is accessible, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Send HEAD request first (faster)
                response = await client.head(url, follow_redirects=True)
                
                # If HEAD fails, try GET
                if response.status_code >= 400:
                    response = await client.get(url, follow_redirects=True)
                
                # Consider 2xx and 3xx as accessible
                return 200 <= response.status_code < 400
                
        except httpx.TimeoutException:
            logger.warning(f"URL {url} timed out")
            return False
        except httpx.ConnectError:
            logger.warning(f"Could not connect to {url}")
            return False
        except Exception as e:
            logger.error(f"Error checking URL accessibility: {str(e)}")
            return False
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent processing
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        try:
            parsed = urlparse(url)
            
            # Ensure scheme is lowercase
            scheme = parsed.scheme.lower()
            
            # Ensure netloc is lowercase
            netloc = parsed.netloc.lower()
            
            # Remove trailing slash from path (except root)
            path = parsed.path
            if path.endswith('/') and path != '/':
                path = path.rstrip('/')
            
            # Reconstruct URL
            normalized = f"{scheme}://{netloc}{path}"
            
            # Add query and fragment if they exist
            if parsed.query:
                normalized += f"?{parsed.query}"
            if parsed.fragment:
                normalized += f"#{parsed.fragment}"
            
            return normalized
            
        except Exception as e:
            logger.error(f"URL normalization error: {str(e)}")
            return url
    
    def get_domain(self, url: str) -> str:
        """
        Extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name or empty string if invalid
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception as e:
            logger.error(f"Domain extraction error: {str(e)}")
            return ""
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same domain, False otherwise
        """
        try:
            domain1 = self.get_domain(url1)
            domain2 = self.get_domain(url2)
            return domain1 == domain2 and domain1 != ""
        except Exception as e:
            logger.error(f"Domain comparison error: {str(e)}")
            return False
