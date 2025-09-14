"""
Supabase client for CodeClinic backend
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Supabase, but don't fail if it's not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Supabase not available: {e}")
    SUPABASE_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class Client:
        pass
    def create_client(*args, **kwargs):
        return None

class SupabaseClient:
    """Supabase client wrapper for database operations"""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase library not available - database features disabled")
            self.client = None
            return
            
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for backend
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not found in environment variables - database features disabled")
            self.client = None
        else:
            try:
                # Initialize with minimal options to avoid compatibility issues
                self.client: Client = create_client(
                    self.url,
                    self.key
                )
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    async def get_or_create_user(self, clerk_user_id: str, user_data: Dict[str, Any]) -> Optional[str]:
        """Get or create user and return user ID"""
        try:
            # First, try to find existing user
            result = self.client.table('users').select('id').eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new user
            user_record = {
                'clerk_user_id': clerk_user_id,
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'full_name': user_data.get('full_name'),
                'avatar_url': user_data.get('avatar_url')
            }
            
            result = self.client.table('users').insert(user_record).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                logger.error(f"Failed to create user: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            return None
    
    async def create_or_get_user(self, clerk_user_id: str, email: str = None, username: str = None, full_name: str = None, avatar_url: str = None) -> Optional[str]:
        """Create or get user from Clerk data"""
        try:
            logger.info(f"Looking for existing user with Clerk ID: {clerk_user_id}")
            
            # First, try to get existing user
            existing_user = self.client.table('users').select('id').eq('clerk_user_id', clerk_user_id).execute()
            
            if existing_user.data:
                user_id = existing_user.data[0]['id']
                logger.info(f"Found existing user with ID: {user_id}")
                
                # Update user information if provided (in case it changed in Clerk)
                if any([email, username, full_name, avatar_url]):
                    update_data = {}
                    if email: update_data['email'] = email
                    if username: update_data['username'] = username
                    if full_name: update_data['full_name'] = full_name
                    if avatar_url: update_data['avatar_url'] = avatar_url
                    
                    if update_data:
                        update_result = self.client.table('users').update(update_data).eq('id', user_id).execute()
                        if update_result.data:
                            logger.info(f"Updated user information for {user_id}: {update_data}")
                
                return user_id
            
            # Create new user if doesn't exist
            user_data = {
                'clerk_user_id': clerk_user_id,
                'email': email,
                'username': username,
                'full_name': full_name,
                'avatar_url': avatar_url
            }
            
            logger.info(f"Creating new user with data: {user_data}")
            response = self.client.table('users').insert(user_data).execute()
            
            if response.data:
                logger.info(f"Successfully created new user: {clerk_user_id} with DB ID: {response.data[0]['id']}")
                return response.data[0]['id']
            else:
                logger.error(f"Failed to create user: {response}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating/getting user: {str(e)}")
            return None

    async def get_existing_scan(self, website_url: str, user_id: str) -> Optional[str]:
        """Get existing scan for user and website"""
        try:
            result = self.client.table('website_scans').select('id').eq('website_url', website_url).eq('created_by', user_id).execute()
            
            if result.data:
                return result.data[0]['id']
            return None
                
        except Exception as e:
            logger.error(f"Error getting existing scan: {str(e)}")
            return None

    async def save_website_scan(self, scan_data: Dict[str, Any]) -> Optional[str]:
        """Save website scan and return scan ID"""
        try:
            result = self.client.table('website_scans').insert(scan_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                logger.error(f"Failed to save website scan: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving website scan: {str(e)}")
            return None
    
    async def save_questions(self, scan_id: str, questions: List[Dict[str, Any]], created_by: str = None) -> bool:
        """Save questions for a website scan"""
        try:
            # Get the created_by from the scan if not provided
            if not created_by:
                scan_data = self.client.table('website_scans').select('created_by').eq('id', scan_id).execute()
                if scan_data.data:
                    created_by = scan_data.data[0].get('created_by')
            
            question_records = []
            for q in questions:
                question_record = {
                    'website_scan_id': scan_id,
                    'created_by': created_by,  # Add direct user reference
                    'vuln_type': q.get('vuln_type', ''),
                    'title': q.get('title', ''),
                    'short_explain': q.get('short_explain', ''),
                    'exercise_type': q.get('exercise_type', ''),
                    'exercise_prompt': q.get('exercise_prompt', ''),
                    'choices': q.get('choices', []),
                    'answer_key': q.get('answer_key', []),
                    'hints': q.get('hints', []),
                    'difficulty': q.get('difficulty', ''),
                    'xp': q.get('xp', 0),
                    'badge': q.get('badge', '')
                }
                question_records.append(question_record)
            
            result = self.client.table('questions').insert(question_records).execute()
            
            if result.data:
                logger.info(f"Saved {len(question_records)} questions for scan {scan_id}")
                return True
            else:
                logger.error(f"Failed to save questions: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving questions: {str(e)}")
            return False
    
    async def save_vulnerability_guide(self, scan_id: str, guide_entries: List[Dict[str, Any]]) -> bool:
        """Save vulnerability guide entries for a website scan"""
        try:
            guide_records = []
            for guide in guide_entries:
                guide_record = {
                    'website_scan_id': scan_id,
                    'name': guide.get('name', ''),
                    'severity': guide.get('severity', ''),
                    'category': guide.get('category', ''),
                    'description': guide.get('description', ''),
                    'how_it_arises': guide.get('howItArises', []),
                    'exploitation_methods': guide.get('exploitationMethods', []),
                    'real_world_examples': guide.get('realWorldExamples', []),
                    'prevention_methods': guide.get('preventionMethods', []),
                    'code_examples': guide.get('codeExamples', {}),
                    'quiz_answers': guide.get('quizAnswers', {})
                }
                guide_records.append(guide_record)
            
            result = self.client.table('vulnerability_guides').insert(guide_records).execute()
            
            if result.data:
                logger.info(f"Saved {len(guide_records)} guide entries for scan {scan_id}")
                return True
            else:
                logger.error(f"Failed to save vulnerability guide: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving vulnerability guide: {str(e)}")
            return False
    
    async def save_quiz_attempt(self, attempt_data: Dict[str, Any]) -> Optional[str]:
        """Save quiz attempt and return attempt ID"""
        try:
            result = self.client.table('quiz_attempts').insert(attempt_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                logger.error(f"Failed to save quiz attempt: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving quiz attempt: {str(e)}")
            return None
    
    async def save_question_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Save individual question response and return response ID"""
        try:
            # Get user_id from quiz_attempt if not provided
            if 'user_id' not in response_data and 'quiz_attempt_id' in response_data:
                attempt_result = self.client.table('quiz_attempts').select('user_id').eq('id', response_data['quiz_attempt_id']).execute()
                if attempt_result.data:
                    response_data['user_id'] = attempt_result.data[0]['user_id']
            
            result = self.client.table('question_responses').insert(response_data).execute()
            
            if result.data:
                logger.info(f"Saved question response: {result.data[0]['id']}")
                return result.data[0]['id']
            else:
                logger.error(f"Failed to save question response: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving question response: {str(e)}")
            return None
    
    async def save_question_responses(self, attempt_id: str, responses: List[Dict[str, Any]]) -> bool:
        """Save individual question responses"""
        try:
            response_records = []
            for response in responses:
                response_record = {
                    'quiz_attempt_id': attempt_id,
                    'question_id': response.get('question_id'),
                    'user_answer': response.get('user_answer'),
                    'is_correct': response.get('is_correct', False),
                    'xp_earned': response.get('xp_earned', 0),
                    'time_taken': response.get('time_taken')
                }
                response_records.append(response_record)
            
            result = self.client.table('question_responses').insert(response_records).execute()
            
            if result.data:
                logger.info(f"Saved {len(response_records)} question responses for attempt {attempt_id}")
                return True
            else:
                logger.error(f"Failed to save question responses: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving question responses: {str(e)}")
            return False

    
    async def get_public_scans(self, difficulty: Optional[str] = None, 
                             exercise_type: Optional[str] = None,
                             limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get public scans with optional filters"""
        try:
            # Get website scans with user info
            scan_query = self.client.table('website_scans').select('''
                id,
                website_url,
                scan_date,
                created_by,
                users!website_scans_created_by_fkey(username, full_name)
            ''').eq('is_public', True).order('scan_date', desc=True).range(offset, offset + limit - 1)
            
            scan_result = scan_query.execute()
            scans = scan_result.data if scan_result.data else []
            
            # For each scan, get question statistics
            result_scans = []
            for scan in scans:
                # Get questions for this scan
                questions_query = self.client.table('questions').select('difficulty, exercise_type').eq('website_scan_id', scan['id'])
                questions_result = questions_query.execute()
                questions = questions_result.data if questions_result.data else []
                
                # Extract user info
                user_info = scan.get('users', {}) if scan.get('users') else {}
                
                # Build scan data - focus on website info rather than user info
                scan_data = {
                    'scan_id': scan['id'],
                    'website_url': scan['website_url'],
                    'website_title': self._extract_website_title(scan['website_url']),
                    'scan_date': scan['scan_date'],
                    'created_by_username': user_info.get('username', 'Anonymous'),
                    'created_by_full_name': user_info.get('full_name', 'Anonymous User'),
                    'question_count': len(questions),
                    'difficulties': list(set([q['difficulty'] for q in questions if q['difficulty']])),
                    'exercise_types': list(set([q['exercise_type'] for q in questions if q['exercise_type']]))
                }
                
                # Apply filters
                if difficulty and difficulty not in scan_data['difficulties']:
                    continue
                if exercise_type and exercise_type not in scan_data['exercise_types']:
                    continue
                
                result_scans.append(scan_data)
            
            return result_scans
            
        except Exception as e:
            logger.error(f"Error getting public scans: {str(e)}")
            return []
    
    def _extract_website_title(self, website_url: str) -> str:
        """Extract a clean website title from URL"""
        if not website_url or website_url == "Unknown":
            return "Unknown Website"
        
        try:
            # Remove protocol
            if website_url.startswith(('http://', 'https://')):
                website_url = website_url.split('://', 1)[1]
            
            # Remove www
            if website_url.startswith('www.'):
                website_url = website_url[4:]
            
            # Remove path and query parameters
            website_url = website_url.split('/')[0].split('?')[0]
            
            # Capitalize first letter of each part
            parts = website_url.split('.')
            if len(parts) >= 2:
                # Take the main domain part (usually the second to last part)
                main_part = parts[-2] if len(parts) > 2 else parts[0]
                return main_part.replace('-', ' ').replace('_', ' ').title()
            else:
                return website_url.replace('-', ' ').replace('_', ' ').title()
                
        except Exception:
            return "Unknown Website"
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data from user_stats table"""
        try:
            # Get user stats with user information
            result = self.client.table('user_stats').select('''
                total_xp,
                total_questions_answered,
                total_correct_answers,
                badges_earned,
                accuracy_percentage,
                users!user_stats_user_id_fkey(
                    id,
                    username,
                    full_name,
                    email,
                    avatar_url
                )
            ''').order('total_xp', desc=True).limit(limit).execute()
            
            if not result.data:
                return []
            
            # Format leaderboard data
            leaderboard = []
            for stat in result.data:
                user = stat.get('users', {})
                if not user:
                    continue
                
                leaderboard.append({
                    'user_id': user['id'],
                    'username': user.get('username', 'Anonymous'),
                    'full_name': user.get('full_name', 'Anonymous'),
                    'email': user.get('email', ''),
                    'avatar_url': user.get('avatar_url', ''),
                    'total_xp': stat.get('total_xp', 0),
                    'correct_answers': stat.get('total_correct_answers', 0),
                    'total_questions': stat.get('total_questions_answered', 0),
                    'accuracy': float(stat.get('accuracy_percentage', 0)),
                    'badges_earned': stat.get('badges_earned', [])
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return []
    
    async def update_user_stats(self, user_id: str) -> bool:
        """Manually update user stats for a specific user"""
        try:
            # Calculate stats from question_responses
            responses_result = self.client.table('question_responses').select('xp_earned, is_correct, badge').eq('user_id', user_id).execute()
            
            if not responses_result.data:
                return True  # No responses to update
            
            responses = responses_result.data
            total_xp = sum(response.get('xp_earned', 0) for response in responses)
            total_questions = len(responses)
            correct_answers = sum(1 for response in responses if response.get('is_correct', False))
            badges = [response.get('badge') for response in responses if response.get('badge')]
            unique_badges = list(set(badges))  # Remove duplicates
            accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # Insert or update user stats
            stats_data = {
                'user_id': user_id,
                'total_xp': total_xp,
                'total_questions_answered': total_questions,
                'total_correct_answers': correct_answers,
                'badges_earned': unique_badges,
                'accuracy_percentage': round(accuracy, 2),
                'updated_at': 'now()'
            }
            
            result = self.client.table('user_stats').upsert(stats_data, on_conflict='user_id').execute()
            
            if result.data:
                logger.info(f"Updated user stats for user {user_id}: {total_xp} XP, {correct_answers}/{total_questions} correct")
                return True
            else:
                logger.error(f"Failed to update user stats for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user stats for user {user_id}: {str(e)}")
            return False
    
    async def get_scan_questions(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get questions for a specific scan"""
        try:
            result = self.client.table('questions').select('*').eq('website_scan_id', scan_id).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting scan questions: {str(e)}")
            return []
    
    async def get_scan_guide(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get vulnerability guide for a specific scan"""
        try:
            result = self.client.table('vulnerability_guides').select('*').eq('website_scan_id', scan_id).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting scan guide: {str(e)}")
            return []
    
    async def get_scan_info(self, scan_id: str) -> Dict[str, Any]:
        """Get scan information including website details"""
        try:
            result = self.client.table('website_scans').select('''
                id,
                website_url,
                scan_date,
                created_by,
                users!website_scans_created_by_fkey(username, full_name)
            ''').eq('id', scan_id).execute()
            
            if result.data and len(result.data) > 0:
                scan = result.data[0]
                user_info = scan.get('users', {}) if scan.get('users') else {}
                
                return {
                    'website_url': scan.get('website_url', 'Unknown'),
                    'website_title': self._extract_website_title(scan.get('website_url', 'Unknown')),
                    'created_by_username': user_info.get('username', 'Anonymous'),
                    'created_by_full_name': user_info.get('full_name', 'Anonymous User'),
                    'scan_date': scan.get('scan_date')
                }
            else:
                return {
                    'website_url': 'Unknown',
                    'website_title': 'Unknown Website',
                    'created_by_username': 'Anonymous',
                    'created_by_full_name': 'Anonymous User',
                    'scan_date': None
                }
                
        except Exception as e:
            logger.error(f"Error getting scan info: {str(e)}")
            return {
                'website_url': 'Unknown',
                'website_title': 'Unknown Website',
                'created_by_username': 'Anonymous',
                'created_by_full_name': 'Anonymous User',
                'scan_date': None
            }

# Global instance
supabase_client = SupabaseClient()
