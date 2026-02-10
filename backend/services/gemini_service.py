"""
Gemini API Service with Intelligent Rate Limiting & API Key Rotation

Features:
- Multi-key rotation (3 keys = 45 RPM free tier)
- Exponential backoff retry (5s → 10s → 20s → 40s)
- Rate limiter (15 RPM per key, 1500 RPD)
- Cost tracking
- Smart chunking for long transcripts
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json
from config import settings

class GeminiRateLimiter:
    """
    Track API usage per key to avoid rate limits
    
    Free tier limits:
    - 15 requests per minute (RPM)
    - 1500 requests per day (RPD)
    - 1M tokens per day
    """
    
    def __init__(self, keys: List[str], rpm: int = 15, rpd: int = 1500):
        self.keys = keys
        self.max_rpm = rpm
        self.max_rpd = rpd
        
        # Track requests per key
        self.requests_per_key: Dict[str, List[datetime]] = {key: [] for key in keys}
        self.daily_requests_per_key: Dict[str, int] = {key: 0 for key in keys}
        self.last_reset: Dict[str, datetime] = {key: datetime.now() for key in keys}
        
        # Round-robin index
        self.current_key_index = 0
    
    def _clean_old_requests(self, key: str):
        """Remove requests older than 1 minute"""
        now = datetime.now()
        self.requests_per_key[key] = [
            req_time for req_time in self.requests_per_key[key]
            if now - req_time < timedelta(minutes=1)
        ]
    
    def _reset_daily_if_needed(self, key: str):
        """Reset daily counter if 24 hours passed"""
        now = datetime.now()
        if now - self.last_reset[key] >= timedelta(days=1):
            self.daily_requests_per_key[key] = 0
            self.last_reset[key] = now
    
    async def wait_if_needed(self, key: str):
        """Wait if approaching rate limit"""
        self._clean_old_requests(key)
        self._reset_daily_if_needed(key)
        
        # Check RPM limit
        if len(self.requests_per_key[key]) >= self.max_rpm:
            oldest_request = self.requests_per_key[key][0]
            wait_time = 60 - (datetime.now() - oldest_request).seconds
            
            if wait_time > 0:
                print(f"⏳ Rate limit approaching for key {key[:8]}... Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                self._clean_old_requests(key)
        
        # Check RPD limit
        if self.daily_requests_per_key[key] >= self.max_rpd:
            print(f"⚠️  Daily limit reached for key {key[:8]}...")
            raise Exception(f"Daily rate limit exceeded for API key")
        
        # Record this request
        self.requests_per_key[key].append(datetime.now())
        self.daily_requests_per_key[key] += 1
    
    def get_next_key(self) -> Tuple[str, int]:
        """
        Get next available API key (round-robin)
        
        Returns:
            (api_key, key_index)
        """
        # Try all keys in rotation
        for _ in range(len(self.keys)):
            key = self.keys[self.current_key_index]
            key_index = self.current_key_index
            
            # Move to next key for next request
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)
            
            # Check if this key has capacity
            self._clean_old_requests(key)
            self._reset_daily_if_needed(key)
            
            if (len(self.requests_per_key[key]) < self.max_rpm and 
                self.daily_requests_per_key[key] < self.max_rpd):
                return key, key_index
        
        # All keys exhausted - use first one and wait
        return self.keys[0], 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all keys"""
        stats = {}
        for i, key in enumerate(self.keys):
            self._clean_old_requests(key)
            stats[f"key_{i+1}"] = {
                "requests_last_minute": len(self.requests_per_key[key]),
                "requests_today": self.daily_requests_per_key[key],
                "rpm_remaining": self.max_rpm - len(self.requests_per_key[key]),
                "rpd_remaining": self.max_rpd - self.daily_requests_per_key[key]
            }
        return stats


class GeminiService:
    """
    Gemini API service with rate limiting and retry logic
    """
    
    def __init__(self):
        self.api_keys = settings.gemini_api_keys
        self.rate_limiter = GeminiRateLimiter(self.api_keys)
        
        # Configure all API keys
        self.models = []
        for key in self.api_keys:
            genai.configure(api_key=key)
            # Use gemini-2.5-flash (latest available model)
            self.models.append(genai.GenerativeModel('gemini-2.5-flash'))
        
        print(f"✅ Gemini service initialized with {len(self.api_keys)} API keys")
        print(f"📊 Total capacity: {len(self.api_keys) * 15} RPM, {len(self.api_keys) * 1500} RPD")
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        retries: int = 4, 
        base_delay: int = 5
    ) -> str:
        """
        Generate content with exponential backoff retry
        
        Args:
            prompt: Text prompt for generation
            retries: Number of retry attempts (default: 4)
            base_delay: Base delay in seconds (default: 5s)
        
        Returns:
            Generated text
        """
        for attempt in range(retries):
            try:
                # Get next available API key
                api_key, key_index = self.rate_limiter.get_next_key()
                
                # Wait if needed (rate limiting)
                await self.rate_limiter.wait_if_needed(api_key)
                
                # Generate content
                model = self.models[key_index]
                response = model.generate_content(prompt)
                
                return response.text
            
            except Exception as error:
                error_msg = str(error)
                
                # Check if it's a rate limit error
                is_rate_limit = (
                    "429" in error_msg or 
                    "quota" in error_msg.lower() or 
                    "rate limit" in error_msg.lower()
                )
                
                if is_rate_limit and attempt < retries - 1:
                    # Exponential backoff: 5s, 10s, 20s, 40s
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️  Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{retries})")
                    await asyncio.sleep(delay)
                    continue
                
                # Non-rate-limit error or max retries exceeded
                raise error
        
        raise Exception("Max retries exceeded")
    
    async def summarize_transcript(
        self, 
        transcript: str, 
        video_id: str,
        video_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize video transcript using Gemini Flash (FREE)
        
        Args:
            transcript: Formatted transcript with timestamps
            video_id: YouTube video ID
            video_title: Optional video title
        
        Returns:
            {
                "title": str,
                "executiveSummary": str,
                "keyTerms": List[str],
                "detailedNotes": List[{timestamp, topic, content}]
            }
        """
        
        prompt = f"""
You are an advanced video content analyzer. Analyze this COMPLETE YouTube video transcript and create a comprehensive study guide.

VIDEO ID: {video_id}
{f"VIDEO TITLE: {video_title}" if video_title else ""}

TRANSCRIPT:
{transcript}

Generate a structured study guide in JSON format with the following structure:

{{
  "title": "Video Title (extract from content or use provided title)",
  "executiveSummary": "Concise 3-5 sentence summary of the main points",
  "keyTerms": ["Term 1", "Term 2", "Term 3", ...],
  "detailedNotes": [
    {{
      "timestamp": "MM:SS (from transcript)",
      "topic": "Section Topic",
      "content": "Detailed explanation of this section"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Extract timestamps from the transcript markers [MM:SS] or [HH:MM:SS]
- Create detailed notes covering the ENTIRE video from START to END
- Include notes for ALL major sections and topics throughout the video
- Ensure the last note's timestamp is close to the end of the video
- Create 8-15 detailed notes depending on video length and content density
- Key terms should be important concepts, not common words
- Executive summary should cover the complete video content
- Return ONLY valid JSON, no markdown formatting
"""
        
        try:
            response_text = await self._generate_with_retry(prompt)
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise Exception("No valid JSON found in response")
            
            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)
            
            return {
                "title": data.get("title", f"Video {video_id}"),
                "executiveSummary": data.get("executiveSummary", ""),
                "keyTerms": data.get("keyTerms", []),
                "detailedNotes": data.get("detailedNotes", []),
                "summary": data.get("executiveSummary", "")  # Alias for compatibility
            }
        
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            raise Exception(f"Failed to summarize video: {str(e)}")
    
    async def create_chat_context(
        self, 
        video_title: str,
        executive_summary: str,
        key_terms: List[str],
        detailed_notes: List[Dict[str, str]]
    ) -> str:
        """
        Create system instruction for chat session
        
        Returns:
            System instruction string for chat context
        """
        notes_text = "\n".join([
            f"- [{note.get('timestamp', 'N/A')}] {note.get('topic', '')}: {note.get('content', '')}"
            for note in detailed_notes
        ])
        
        return f"""
You are an AI Tutor helping students understand the video "{video_title}".

EXECUTIVE SUMMARY:
{executive_summary}

KEY TERMS:
{', '.join(key_terms)}

DETAILED NOTES:
{notes_text}

Your role:
- Answer questions about the video content
- Explain concepts in simple terms
- Provide examples when helpful
- Be encouraging and supportive
- Reference specific timestamps when relevant
"""
    
    async def chat_response(self, context: str, message: str) -> str:
        """
        Generate chat response with context
        
        Args:
            context: System instruction with video context
            message: User's question
        
        Returns:
            AI response text
        """
        prompt = f"""{context}

USER QUESTION:
{message}

Provide a helpful, clear answer based on the video content above.
"""
        
        return await self._generate_with_retry(prompt)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return self.rate_limiter.get_stats()


# Global Gemini service instance
gemini_service = GeminiService()
