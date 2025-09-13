"""
CodeClinic Backend - Gemini AI Integration
Handles AI-powered cybersecurity question generation from ZAP scan data
"""

from google import genai
import json
import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Sample ZAP data for testing
SAMPLE_ZAP_DATA = """Missing Anti-clickjacking Header - Medium - https://webwriter.io/dashboard/
Missing Anti-clickjacking Header - Medium - https://webwriter.io/
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/api/
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/admin/
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/684-9de7e8eb5c803a7c.js
Re-examine Cache-control Directives - Informational - https://webwriter.io/robots.txt
Re-examine Cache-control Directives - Informational - https://webwriter.io/sitemap.xml
Modern Web Application - Informational - https://webwriter.io/admin/
Retrieved from Cache - Informational - https://webwriter.io/_next/static/css/7c7af1ce1d610d49.css
Retrieved from Cache - Informational - https://webwriter.io/_next/static/chunks/684-9de7e8eb5c803a7c.js
Modern Web Application - Informational - https://webwriter.io/api/
Re-examine Cache-control Directives - Informational - https://webwriter.io/dashboard/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/sitemap.xml
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/684-9de7e8eb5c803a7c.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/css/7c7af1ce1d610d49.css
Re-examine Cache-control Directives - Informational - https://webwriter.io/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/robots.txt
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/admin/
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/dashboard/
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/api/
Modern Web Application - Informational - https://webwriter.io/dashboard/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/dashboard/
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/
Modern Web Application - Informational - https://webwriter.io/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/
X-Content-Type-Options Header Missing - Low - https://webwriter.io/dashboard/
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/admin/
X-Content-Type-Options Header Missing - Low - https://webwriter.io/
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/css/7c7af1ce1d610d49.css
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/684-9de7e8eb5c803a7c.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/sitemap.xml
X-Content-Type-Options Header Missing - Low - https://webwriter.io/robots.txt
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/api/
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/dashboard/
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/640-d7450ef566d8d5b4.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/webpack-596a7359c2210d14.js
Missing Anti-clickjacking Header - Medium - https://webwriter.io/terms
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/_next/static/
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/images/
Retrieved from Cache - Informational - https://webwriter.io/_next/static/chunks/640-d7450ef566d8d5b4.js
Missing Anti-clickjacking Header - Medium - https://webwriter.io/privacy
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/640-d7450ef566d8d5b4.js
Modern Web Application - Informational - https://webwriter.io/_next/static/
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/webpack-596a7359c2210d14.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/640-d7450ef566d8d5b4.js
Modern Web Application - Informational - https://webwriter.io/images/
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/_next/static/
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/images/
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/app/page-89801bf2fc80b6be.js
Re-examine Cache-control Directives - Informational - https://webwriter.io/privacy
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/9da6db1e-cb64917ee3ab7dbb.js
Re-examine Cache-control Directives - Informational - https://webwriter.io/terms
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/terms
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/privacy
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/images/
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/main-app-5e5e30756b95da64.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/media/b0088cce7ac0b424-s.p.woff2
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/privacy
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/terms
X-Content-Type-Options Header Missing - Low - https://webwriter.io/terms
X-Content-Type-Options Header Missing - Low - https://webwriter.io/privacy
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/terms
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/privacy
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/main-app-5e5e30756b95da64.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/media/b0088cce7ac0b424-s.p.woff2
Retrieved from Cache - Informational - https://webwriter.io/_next/static/chunks/app/page-89801bf2fc80b6be.js
Retrieved from Cache - Informational - https://webwriter.io/_next/static/chunks/9da6db1e-cb64917ee3ab7dbb.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/main-app-5e5e30756b95da64.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/app/page-89801bf2fc80b6be.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/9da6db1e-cb64917ee3ab7dbb.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/app/page-89801bf2fc80b6be.js
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/4bd1b696-015c8ee44a0e55b4.js
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flogo.png&w=48&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flogo.png&w=32&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flogo.png&w=64
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/9da6db1e-cb64917ee3ab7dbb.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/app/dashboard/page-4d1c2ad6e41d811e.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flogo.png&w=64
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flogo.png&w=48&q=75
Retrieved from Cache - Informational - https://webwriter.io/_next/static/chunks/4bd1b696-015c8ee44a0e55b4.js
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flogo.png&w=32&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/app/dashboard/page-4d1c2ad6e41d811e.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/4bd1b696-015c8ee44a0e55b4.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=32&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=48&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/4bd1b696-015c8ee44a0e55b4.js
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=48&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=32&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flogo.png&w=96&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flogo.png&w=64&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flogo.png&w=96&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=96&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=640&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flogo.png&w=96
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=96&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flogo.png&w=64&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=750&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=640&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/120-7cc6b844b684e9bc.js
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flogo.png&w=96
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=64&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/120-7cc6b844b684e9bc.js
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flogo.png&w=64&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=750&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Ffeather.png&w=64&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=3840&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=750&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/favicon.ico
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=2048&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=750&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Ffeather.png&w=64&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=3840&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/favicon.ico
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=640&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Ffeather.png&w=64&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=3840&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=640&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=1920&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=2048&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=3840&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=2048&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=1200&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=2048&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Ffeather.png&w=128
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=1080&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Ffeather.png&w=64&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=1920&q=75
Information Disclosure - Suspicious Comments - Informational - https://webwriter.io/_next/static/chunks/polyfills-42372ed130431b0a.js
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=1200&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=1080&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Ffeather.png&w=128
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/static/chunks/polyfills-42372ed130431b0a.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1920&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1080&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Feditor.avif&w=828&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1200&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Feditor.avif&w=3840
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1920&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Feditor.avif&w=828&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/static/chunks/polyfills-42372ed130431b0a.js
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/cdn-cgi/l/email-protection
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/cdn-cgi/l/email-protection
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1080&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=828&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=1200&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Ffeather.png&w=128&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Feditor.avif&w=828&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Ffeather.png&w=128&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Feditor.avif&w=3840
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Ffeather.png&w=128&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=16&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Ffeather.png&w=128&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=64&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fgolden_quill.png&w=128
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=16&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fgolden_quill.png&w=128
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=64&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=96&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=32&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fgolden_wizard.png&w=256
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=64&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=64&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=16&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=128&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fgolden_wizard.png&w=256
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=256&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=64&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=16&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=32&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=96&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=128&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=64&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=256&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flemon_squeezy.png&w=32
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=32&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=128&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=256&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=96&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=64&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Flemon_squeezy.png&w=32
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fquestion_mark.png&w=128
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=128&q=75
Content Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=128&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fgolden_quill.png&w=64&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=96&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fgolden_wizard.png&w=256&q=75
X-Content-Type-Options Header Missing - Low - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fquestion_mark.png&w=128
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Flemon_squeezy.png&w=32&q=75
Modern Web Application - Informational - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=128&q=75
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=128&q=75
Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) - Low - https://webwriter.io/%2Fimages%2Fquestion_mark.png&w=128&q=75
Retrieved from Cache - Informational - https://webwriter.io/images/smallwizard.svg
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/images/smallwizard.svg
X-Content-Type-Options Header Missing - Low - https://webwriter.io/images/smallwizard.svg
Retrieved from Cache - Informational - https://webwriter.io/images/dragon.svg
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/images/dragon.svg
Retrieved from Cache - Informational - https://webwriter.io/images/potion.svg
Strict-Transport-Security Header Not Set - Low - https://webwriter.io/images/potion.svg
X-Content-Type-Options Header Missing - Low - https://webwriter.io/images/dragon.svg
X-Content-Type-Options Header Missing - Low - https://webwriter.io/images/potion.svg
SQL Injection - SQLite (Time Based) - High - https://webwriter.io/_next/image?q=75&url=%2Fimages%2Fquestion_mark.png&w=128"""

class ZAPDataRequest(BaseModel):
    """Request model for generating cybersecurity questions from ZAP data"""
    zap_data: str = Field(..., description="ZAP scan results as string")
    num_questions: int = Field(default=25, ge=1, le=50, description="Number of questions to generate (1-50)")

class GameResponse(BaseModel):
    """Response model for generated cybersecurity questions"""
    exercises: List[Dict[str, Any]] = Field(..., description="List of generated questions")
    total_questions: int = Field(..., description="Total number of questions generated")

class GeminiIntegration:
    """Handles Gemini AI integration for cybersecurity question generation"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client"""
        try:
            if not os.getenv("GEMINI_API_KEY"):
                logger.warning("GEMINI_API_KEY not found in environment variables")
                return
            
            self.client = genai.Client()
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available and configured"""
        return self.client is not None and os.getenv("GEMINI_API_KEY") is not None
    
    async def generate_cybersec_questions(self, zap_data: str, num_questions: int = 25) -> GameResponse:
        """
        Generate cybersecurity training questions from ZAP scan data
        
        Args:
            zap_data: ZAP scan results as string
            num_questions: Number of questions to generate
            
        Returns:
            GameResponse with generated questions
            
        Raises:
            Exception: If generation fails
        """
        if not self.is_available():
            raise Exception("Gemini API is not available. Please check GEMINI_API_KEY environment variable.")
        
        # Sanitize the ZAP data to remove control characters
        sanitized_zap_data = self._sanitize_zap_data(zap_data)
        prompt = self._build_prompt(sanitized_zap_data, num_questions)
        
        try:
            logger.info(f"Generating {num_questions} cybersecurity questions from ZAP data")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Clean and parse the response
            exercises = self._parse_response(response.text, num_questions)
            
            logger.info(f"Successfully generated {len(exercises)} questions")
            return GameResponse(
                exercises=exercises,
                total_questions=len(exercises)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {str(e)}")
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def _sanitize_zap_data(self, zap_data: str) -> str:
        """Sanitize ZAP data by removing control characters and normalizing whitespace"""
        import re
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', zap_data)
        
        # Normalize line endings
        sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\n\s*\n', '\n', sanitized)
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    def _build_prompt(self, zap_data: str, num_questions: int) -> str:
        """Build the prompt for Gemini API"""
        return f"""You are an expert cybersecurity tutor. I will give you ZAP scan results and you need to create {num_questions} different cybersecurity training questions.

Here is the ZAP scan data:
{zap_data}

Create exactly {num_questions} questions based on these vulnerabilities. Only generate question types that have deterministic answers.

Each question should be a JSON object with these fields:
- vuln_type: short vulnerability identifier
- title: question title
- short_explain: 1-2 sentence explanation
- exercise_type: one of ["mcq", "fix_config", "sandbox"]
- exercise_prompt: the actual question
- choices: array of {{id, text}} for mcq/fix_config, empty array for sandbox
- answer_key: array of correct answers (must match choice ids for mcq/fix_config, or exact expected output for sandbox)
- hints: array of helpful hints
- difficulty: "beginner", "intermediate", or "advanced"
- xp: points awarded (50-300)
- badge: achievement badge name

Constraints:
- Ensure all answers are deterministic and unambiguous.
- For mcq and fix_config, only one correct answer.
- For sandbox, provide exact expected outputs (no subjective answers).
- Do not generate any free-text or open-ended questions.

Return ONLY a valid JSON array of {num_questions} question objects. No other text."""
    
    def _parse_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse and clean the Gemini response"""
        try:
            # Clean the response text
            json_text = response_text.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            elif json_text.startswith('```'):
                json_text = json_text.replace('```', '').strip()
            
            # Parse JSON
            exercises = json.loads(json_text)
            
            # Validate that we got a list
            if not isinstance(exercises, list):
                raise ValueError("Response is not a list")
            
            # Validate each exercise has required fields
            required_fields = [
                'vuln_type', 'title', 'short_explain', 'exercise_type',
                'exercise_prompt', 'choices', 'answer_key', 'hints',
                'difficulty', 'xp', 'badge'
            ]
            
            # Validate exercise types
            valid_exercise_types = ['mcq', 'fix_config', 'sandbox']
            
            for i, exercise in enumerate(exercises):
                if not isinstance(exercise, dict):
                    raise ValueError(f"Exercise {i} is not a dictionary")
                
                for field in required_fields:
                    if field not in exercise:
                        raise ValueError(f"Exercise {i} missing required field: {field}")
                
                # Validate exercise type
                if exercise['exercise_type'] not in valid_exercise_types:
                    raise ValueError(f"Exercise {i} has invalid exercise_type: {exercise['exercise_type']}. Must be one of {valid_exercise_types}")
                
                # Validate answer_key has only one answer for mcq and fix_config
                if exercise['exercise_type'] in ['mcq', 'fix_config']:
                    if len(exercise['answer_key']) != 1:
                        raise ValueError(f"Exercise {i} ({exercise['exercise_type']}) must have exactly one answer")
            
            return exercises
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise Exception(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
            raise Exception(f"Failed to parse response: {str(e)}")
    

# Global instance
gemini_integration = GeminiIntegration()
