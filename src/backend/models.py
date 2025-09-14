"""
Pydantic models for CodeClinic API
Data validation and serialization models
"""

from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

class ScanType(str, Enum):
    """Types of scans available"""
    FULL_SITE = "full_site"
    SELECTIVE_PAGES = "selective_pages"


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

