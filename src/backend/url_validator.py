"""
URL Validation Module
Handles URL validation and accessibility checking
"""

import httpx
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class URLValidator:
    """URL validation and accessibility checking"""
    
    def __init__(self, timeout: int = 5):
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
            # Basic URL validation using urllib.parse
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check if URL starts with http:// or https://
            if not url.startswith(('http://', 'https://')):
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
    
