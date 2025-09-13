"""
Pydantic models for CodeClinic API
Data validation and serialization models
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime

class ScanType(str, Enum):
    """Types of scans available"""
    FULL_SITE = "full_site"
    SELECTIVE_PAGES = "selective_pages"

class SeverityLevel(str, Enum):
    """Vulnerability severity levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

class VulnerabilityType(str, Enum):
    """Common vulnerability types"""
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    CSRF = "csrf"
    INSECURE_HEADERS = "insecure_headers"
    SSL_TLS = "ssl_tls"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPOSURE = "data_exposure"
    OTHER = "other"

class ScanRequest(BaseModel):
    """Request model for starting a scan"""
    url: HttpUrl = Field(..., description="URL to scan")
    scan_type: ScanType = Field(..., description="Type of scan to perform")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "scan_type": "full_site"
            }
        }

class Vulnerability(BaseModel):
    """Individual vulnerability model"""
    id: str = Field(..., description="Unique vulnerability ID")
    type: VulnerabilityType = Field(..., description="Type of vulnerability")
    severity: SeverityLevel = Field(..., description="Severity level")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    url: str = Field(..., description="Affected URL")
    parameter: Optional[str] = Field(None, description="Affected parameter")
    evidence: Optional[str] = Field(None, description="Evidence of the vulnerability")
    solution: Optional[str] = Field(None, description="Suggested solution")
    cwe_id: Optional[str] = Field(None, description="CWE ID if available")
    confidence: Optional[str] = Field(None, description="Confidence level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "vuln_001",
                "type": "xss",
                "severity": "high",
                "title": "Cross-Site Scripting (XSS)",
                "description": "The application is vulnerable to XSS attacks",
                "url": "https://example.com/search",
                "parameter": "q",
                "evidence": "<script>alert('XSS')</script>",
                "solution": "Implement proper input validation and output encoding",
                "cwe_id": "CWE-79",
                "confidence": "high"
            }
        }

class ScanResponse(BaseModel):
    """Response model for scan initiation"""
    scan_id: str = Field(..., description="Unique scan identifier")
    status: str = Field(..., description="Current scan status")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_123_1234567890",
                "status": "started",
                "message": "Scan initiated successfully"
            }
        }

class ScanStatus(BaseModel):
    """Detailed scan status model"""
    id: str = Field(..., description="Scan ID")
    url: str = Field(..., description="Scanned URL")
    scan_type: ScanType = Field(..., description="Type of scan")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    vulnerabilities: List[Vulnerability] = Field(default_factory=list, description="Found vulnerabilities")
    pages: List[str] = Field(default_factory=list, description="Discovered pages")
    selected_pages: Optional[List[str]] = Field(None, description="Selected pages for scanning")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now, description="Scan creation time")
    completed_at: Optional[datetime] = Field(None, description="Scan completion time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "scan_123_1234567890",
                "url": "https://example.com",
                "scan_type": "full_site",
                "status": "completed",
                "progress": 100,
                "vulnerabilities": [],
                "pages": ["https://example.com", "https://example.com/about"],
                "created_at": "2025-01-27T10:00:00Z",
                "completed_at": "2025-01-27T10:05:00Z"
            }
        }

class PageInfo(BaseModel):
    """Information about a discovered page"""
    url: str = Field(..., description="Page URL")
    title: Optional[str] = Field(None, description="Page title")
    status_code: int = Field(..., description="HTTP status code")
    content_type: Optional[str] = Field(None, description="Content type")
    size: Optional[int] = Field(None, description="Page size in bytes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/about",
                "title": "About Us",
                "status_code": 200,
                "content_type": "text/html",
                "size": 2048
            }
        }
