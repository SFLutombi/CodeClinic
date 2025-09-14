"""
CodeClinic Backend - FastAPI Server
Main application entry point for the security assessment API
Simplified parallel scanning with single ZAP instance and thread-based workers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import asyncio
from typing import List, Optional, Dict, Any
import logging

from models import ScanRequest, ScanResponse, Vulnerability, ScanStatus
from zap_integration import ZAPScanner
from url_validator import URLValidator
from gemini_integration import gemini_integration, ZAPDataRequest, GameResponse
from pydantic import BaseModel


from models import ScanRequest, ScanResponse, CrawlRequest, PageSelectionRequest
from simple_scanner import SimpleParallelScanner


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models
class CreateQuizAttemptRequest(BaseModel):
    user_id: str
    user_email: Optional[str] = None
    user_username: Optional[str] = None
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    website_scan_id: str
    total_questions: int

class SaveQuestionResponseRequest(BaseModel):
    quiz_attempt_id: str
    question_id: str
    user_answer: dict
    is_correct: bool
    xp_earned: int
    time_taken: int
    user_id: str

try:
    from supabase_client import supabase_client
    logger.info("Supabase client loaded successfully")
except ImportError as e:
    logger.warning(f"Supabase client not available: {e}")
    supabase_client = None

# Initialize FastAPI app
app = FastAPI(
    title="CodeClinic API",
    description="Security assessment API for web applications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simplified parallel scanning system
scanner = SimpleParallelScanner(max_workers=4)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CodeClinic API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "zap_available": await zap_scanner.is_zap_available(),
        "gemini_available": gemini_integration.is_available(),
        "supabase_available": supabase_client and supabase_client.is_available(),
        "scanner_status": scanner.get_worker_status(),
        "version": "1.0.0"
    }

@app.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """
    Start a security scan for the provided URL
    Uses simplified parallel scanning with thread-based workers
    
    Args:
        request: ScanRequest containing URL and scan type
        
    Returns:
        ScanResponse with scan ID and initial status
    """
    try:
        # Convert Pydantic URL to string
        url_str = str(request.url)
        
        logger.info(f"Starting scan for URL: {url_str}")
        
        # Start scan using simplified scanner
        task_id = await scanner.start_scan(url_str, request.scan_type)
        message = "Scan initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get the current status of a scan"""
    try:
        # Get status from simplified scanner
        status = scanner.get_task_status(scan_id)
        if not status:
            raise HTTPException(status_code=404, detail="Scan not found")
        return status
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan status")


@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get the final scan results"""
    try:
        # Get task status from simplified scanner
        task_status = scanner.get_task_status(scan_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if task_status["status"] not in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Scan not yet completed")
        
        # Return results
        return {
            "id": scan_id,
            "status": task_status["status"],
            "progress": task_status["progress"],
            "vulnerabilities": task_status["results"].get("vulnerabilities", []) if task_status["results"] else [],
            "total_vulnerabilities": len(task_status["results"].get("vulnerabilities", [])) if task_status["results"] else 0,
            "scan_duration": task_status["results"].get("scan_duration", 0) if task_status["results"] else 0,
            "error": task_status.get("error")
        }
    except Exception as e:
        logger.error(f"Error getting scan results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scan results")



@app.post("/generate-game")
async def generate_cybersec_game(
    request: ZAPDataRequest, 
    website_url: str = None, 
    user_id: str = None, 
    user_email: str = None,
    user_username: str = None,
    user_full_name: str = None,
    user_avatar_url: str = None,
    save_to_db: bool = True
):
    """
    Generate cybersecurity training questions from ZAP scan data and optionally save to database
    
    Args:
        request: ZAPDataRequest containing ZAP data and number of questions
        website_url: URL of the website being scanned (for database storage)
        user_id: ID of the user generating questions (optional)
        save_to_db: Whether to save the generated data to database (default: True)
        
    Returns:
        JSON payload with generated questions, vulnerability guide, and scan_id if saved
    """
    try:
        if not gemini_integration.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Gemini API is not available. Please check GEMINI_API_KEY environment variable."
            )
        
        # Handle website_url - use provided value or extract from ZAP data
        if not website_url or website_url == "Unknown":
            website_url = _extract_website_from_zap_data(request.zap_data)
        
        logger.info(f"Generating {request.num_questions} questions from ZAP data for website: {website_url}")
        result = await gemini_integration.generate_cybersec_questions(
            zap_data=request.zap_data,
            num_questions=request.num_questions
        )
        
        response_data = {
            "questions": result.exercises,
            "vulnerability_guide": result.vulnerability_guide
        }
        
        # Save to database if requested and database is available
        if save_to_db and supabase_client and supabase_client.is_available():
            try:
                logger.info("Saving generated questions and guide to database")
                
                # Create or get user if user_id is provided
                db_user_id = None
                if user_id:
                    logger.info(f"Creating/getting user: user_id={user_id}, email={user_email}, username={user_username}, full_name={user_full_name}, avatar_url={user_avatar_url}")
                    db_user_id = await supabase_client.create_or_get_user(
                        clerk_user_id=user_id,
                        email=user_email,
                        username=user_username,
                        full_name=user_full_name,
                        avatar_url=user_avatar_url
                    )
                    logger.info(f"User created/retrieved with DB ID: {db_user_id}")
                else:
                    logger.warning("No user_id provided - creating anonymous scan")
                
                # Check if scan already exists for this user and website
                scan_id = None
                if db_user_id:
                    scan_id = await supabase_client.get_existing_scan(website_url, db_user_id)
                
                # Create new scan only if it doesn't exist
                if not scan_id:
                    scan_data = {
                        "website_url": website_url,
                        "zap_data": request.zap_data,
                        "created_by": db_user_id,
                        "is_public": True
                    }
                    scan_id = await supabase_client.save_website_scan(scan_data)
                if scan_id:
                    # Save questions and guide
                    questions_saved = await supabase_client.save_questions(scan_id, result.exercises, created_by=db_user_id)
                    guide_saved = await supabase_client.save_vulnerability_guide(scan_id, result.vulnerability_guide)
                    
                    if questions_saved and guide_saved:
                        response_data["scan_id"] = scan_id
                        response_data["saved_to_database"] = True
                        logger.info(f"Successfully saved scan data with ID: {scan_id}")
                    else:
                        logger.warning("Failed to save questions or guide to database")
                        response_data["saved_to_database"] = False
                else:
                    logger.warning("Failed to save website scan to database")
                    response_data["saved_to_database"] = False
                    
            except Exception as db_error:
                logger.error(f"Database save error: {str(db_error)}")
                response_data["saved_to_database"] = False
                response_data["database_error"] = str(db_error)
        else:
            if not save_to_db:
                logger.info("Database save disabled by request")
            else:
                logger.warning("Database not available - skipping save")
            response_data["saved_to_database"] = False
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error generating cybersecurity questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@app.post("/scan/{scan_id}/generate-questions", response_model=GameResponse)
async def generate_questions_from_scan(scan_id: str, num_questions: int = 25):
    """
    Generate cybersecurity questions from completed scan results
    
    Args:
        scan_id: ID of the completed scan
        num_questions: Number of questions to generate (1-50)
        
    Returns:
        GameResponse with generated questions
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        if scan_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="Scan not yet completed")
        
        if not gemini_integration.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Gemini API is not available. Please check GEMINI_API_KEY environment variable."
            )
        
        # Convert vulnerabilities to ZAP data format
        zap_data = _format_vulnerabilities_for_gemini(scan_data["vulnerabilities"])
        
        result = await gemini_integration.generate_cybersec_questions(
            zap_data=zap_data,
            num_questions=num_questions
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions from scan {scan_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

def _format_vulnerabilities_for_gemini(vulnerabilities: List[Vulnerability]) -> str:
    """Format vulnerabilities list into ZAP data format for Gemini"""
    if not vulnerabilities:
        return "No vulnerabilities found in scan."
    
    formatted_data = []
    for vuln in vulnerabilities:
        formatted_data.append(f"{vuln.name} - {vuln.severity} - {vuln.url}")
    
    return "\n".join(formatted_data)

def _extract_website_from_zap_data(zap_data: str) -> str:
    """Extract website URL from ZAP data if available"""
    try:
        # Look for common URL patterns in the ZAP data
        import re
        
        # Common URL patterns
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, zap_data)
            if matches:
                # Take the first match and clean it up
                url = matches[0]
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                return url
        
        # If no URL found, return a generic name
        return "Security Scan Results"
        
    except Exception:
        return "Security Scan Results"

async def run_scan(scan_id: str, url: str, scan_type: str):
    """Background task to run the actual scan"""

@app.post("/crawl/start", response_model=ScanResponse)
async def start_crawl(request: CrawlRequest):
    """
    Start crawling a website to discover pages
    This is the first step in the improved workflow
    """
    try:
        # Convert Pydantic URL to string
        url_str = str(request.url)
        
        logger.info(f"Starting crawl for URL: {url_str}")
        
        # Start crawl using simplified scanner
        task_id = await scanner.start_crawl(url_str)
        message = "Crawl initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start crawl: {str(e)}")


@app.get("/crawl/{scan_id}/pages")
async def get_discovered_pages(scan_id: str):
    """Get the pages discovered during crawling"""
    try:
        # Get task status from simplified scanner
        task_status = scanner.get_task_status(scan_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Crawl not found")
        
        if task_status["status"] not in ["completed"]:
            raise HTTPException(status_code=400, detail="Crawl not yet completed")
        
        # Return discovered pages
        return {
            "scan_id": scan_id,
            "pages": task_status["results"].get("discovered_pages", []) if task_status["results"] else [],
            "total_pages": len(task_status["results"].get("discovered_pages", [])) if task_status["results"] else 0
        }
    except Exception as e:
        logger.error(f"Error getting discovered pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get discovered pages")


@app.post("/scan/start-selected", response_model=ScanResponse)
async def start_selected_scan(request: PageSelectionRequest):
    """
    Start scanning selected pages after crawling
    This is the second step in the improved workflow
    """
    try:
        # Start scan for selected pages using simplified scanner
        task_id = await scanner.start_scan_selected(request.scan_id, request.selected_pages)
        message = "Selected page scan initiated successfully"
        
        return ScanResponse(
            scan_id=task_id,
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting selected scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start selected scan: {str(e)}")


@app.get("/system/status")
async def get_system_status():
    """Get system-wide status and performance metrics"""
    try:
        return {
            "scanner_status": scanner.get_worker_status(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {"error": "Failed to get system status"}

@app.on_event("startup")
async def startup_event():
    """Initialize simplified parallel scanning system on startup"""
    try:
        logger.info("Starting CodeClinic with simplified parallel scanning...")
        
        # Initialize simplified scanner
        if await scanner.initialize():
            logger.info("✅ Simplified parallel scanning system initialized successfully")
            logger.info(f"🚀 Performance boost: {scanner.max_workers} worker threads ready")
        else:
            logger.warning("⚠️  Scanner initialization failed - using sequential mode")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize scanner: {str(e)}")
        logger.info("🔄 Falling back to sequential scanning mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down simplified parallel scanning system...")
        scanner.shutdown()
        logger.info("CodeClinic shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Database endpoints
@app.post("/save-scan-results")
async def save_scan_results(request: ZAPDataRequest, website_url: str, user_id: str = None):
    """
    Save scan results to database with questions and vulnerability guide
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Generate questions and guide
        result = await gemini_integration.generate_cybersec_questions(
            zap_data=request.zap_data,
            num_questions=request.num_questions
        )
        
        # Save website scan
        scan_data = {
            "website_url": website_url,
            "zap_data": request.zap_data,
            "created_by": user_id,
            "is_public": True
        }
        
        scan_id = await supabase_client.save_website_scan(scan_data)
        if not scan_id:
            raise HTTPException(status_code=500, detail="Failed to save scan")
        
        # Save questions and guide
        questions_saved = await supabase_client.save_questions(scan_id, result.exercises)
        guide_saved = await supabase_client.save_vulnerability_guide(scan_id, result.vulnerability_guide)
        
        if not questions_saved or not guide_saved:
            raise HTTPException(status_code=500, detail="Failed to save questions or guide")
        
        return {
            "scan_id": scan_id,
            "questions": result.exercises,
            "vulnerability_guide": result.vulnerability_guide
        }
        
    except Exception as e:
        logger.error(f"Error saving scan results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save scan results: {str(e)}")

@app.get("/public-scans")
async def get_public_scans(
    difficulty: Optional[str] = None,
    exercise_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get public scans with optional filters
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        scans = await supabase_client.get_public_scans(difficulty, exercise_type, limit, offset)
        return {"scans": scans}
        
    except Exception as e:
        logger.error(f"Error getting public scans: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get public scans: {str(e)}")

@app.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get leaderboard data
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        leaderboard = await supabase_client.get_leaderboard(limit)
        return {"leaderboard": leaderboard}
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@app.post("/update-user-stats/{user_id}")
async def update_user_stats(user_id: str):
    """
    Manually update user stats for a specific user
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        success = await supabase_client.update_user_stats(user_id)
        
        if success:
            return {"success": True, "message": f"User stats updated for user {user_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update user stats")
        
    except Exception as e:
        logger.error(f"Error updating user stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user stats: {str(e)}")

@app.post("/update-user-info")
async def update_user_info(request: dict):
    """
    Update user information (email, username, full_name, avatar_url)
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        user_id = request.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Update user information
        update_data = {}
        if 'email' in request: update_data['email'] = request['email']
        if 'username' in request: update_data['username'] = request['username']
        if 'full_name' in request: update_data['full_name'] = request['full_name']
        if 'avatar_url' in request: update_data['avatar_url'] = request['avatar_url']
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = supabase_client.client.table('users').update(update_data).eq('id', user_id).execute()
        
        if result.data:
            return {"success": True, "message": f"User information updated for user {user_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update user information")
        
    except Exception as e:
        logger.error(f"Error updating user info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user info: {str(e)}")

@app.get("/scan/{scan_id}/questions")
async def get_scan_questions(scan_id: str):
    """
    Get questions for a specific scan
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        questions = await supabase_client.get_scan_questions(scan_id)
        guide = await supabase_client.get_scan_guide(scan_id)
        
        # Get scan information
        scan_info = await supabase_client.get_scan_info(scan_id)
        
        return {
            "questions": questions,
            "vulnerability_guide": guide,
            "website_title": scan_info.get('website_title', 'Unknown Website'),
            "website_url": scan_info.get('website_url', 'Unknown'),
            "created_by": scan_info.get('created_by_username', 'Anonymous')
        }
        
    except Exception as e:
        logger.error(f"Error getting scan questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get scan questions: {str(e)}")

@app.post("/create-quiz-attempt")
async def create_quiz_attempt(request: CreateQuizAttemptRequest):
    """
    Create a new quiz attempt
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Log the user data being received
        logger.info(f"Received user data: user_id={request.user_id}, email={request.user_email}, username={request.user_username}, full_name={request.user_full_name}, avatar_url={request.user_avatar_url}")
        
        # Get or create user
        db_user_id = await supabase_client.create_or_get_user(
            clerk_user_id=request.user_id,
            email=request.user_email,
            username=request.user_username,
            full_name=request.user_full_name,
            avatar_url=request.user_avatar_url
        )
        
        if not db_user_id:
            raise HTTPException(status_code=400, detail="Failed to create or get user")
        
        attempt_data = {
            "user_id": db_user_id,
            "website_scan_id": request.website_scan_id,
            "total_questions": request.total_questions,
            "correct_answers": 0,
            "total_xp": 0,
            "badges_earned": [],
            "time_taken": 0
        }
        
        attempt_id = await supabase_client.save_quiz_attempt(attempt_data)
        
        if attempt_id:
            return {"attempt_id": attempt_id, "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to create quiz attempt")
            
    except Exception as e:
        logger.error(f"Error creating quiz attempt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create quiz attempt: {str(e)}")

@app.post("/save-question-response")
async def save_question_response(request: SaveQuestionResponseRequest):
    """
    Save individual question response
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        response_data = {
            "quiz_attempt_id": request.quiz_attempt_id,
            "question_id": request.question_id,
            "user_answer": request.user_answer,
            "is_correct": request.is_correct,
            "xp_earned": request.xp_earned,
            "time_taken": request.time_taken,
            "user_id": request.user_id
        }
        
        response_id = await supabase_client.save_question_response(response_data)
        
        if response_id:
            return {"response_id": response_id, "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to save question response")
            
    except Exception as e:
        logger.error(f"Error saving question response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save question response: {str(e)}")

@app.post("/save-quiz-attempt")
async def save_quiz_attempt(
    user_id: str,
    scan_id: str,
    total_questions: int,
    correct_answers: int,
    total_xp: int,
    badges_earned: List[str],
    time_taken: Optional[int] = None,
    responses: List[Dict[str, Any]] = None
):
    """
    Save quiz attempt and responses
    """
    try:
        if not supabase_client or not supabase_client.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Save quiz attempt
        attempt_data = {
            "user_id": user_id,
            "website_scan_id": scan_id,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "total_xp": total_xp,
            "badges_earned": badges_earned,
            "time_taken": time_taken
        }
        
        attempt_id = await supabase_client.save_quiz_attempt(attempt_data)
        if not attempt_id:
            raise HTTPException(status_code=500, detail="Failed to save quiz attempt")
        
        # Save individual responses if provided
        if responses:
            responses_saved = await supabase_client.save_question_responses(attempt_id, responses)
            if not responses_saved:
                logger.warning("Failed to save some question responses")
        
        return {"attempt_id": attempt_id, "success": True}
        
    except Exception as e:
        logger.error(f"Error saving quiz attempt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save quiz attempt: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
