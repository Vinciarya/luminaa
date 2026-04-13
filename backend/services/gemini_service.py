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
import math
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
        
        # Configure models — one per key, with generous output limits
        self.models = []
        for key in self.api_keys:
            genai.configure(api_key=key)
            self.models.append(
                genai.GenerativeModel(
                    'gemini-flash-latest',
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=8192,
                        temperature=0.2,
                    )
                )
            )
        
        print(f"✅ Gemini service initialized with {len(self.api_keys)} API keys")
        print(f"📊 Total capacity: {len(self.api_keys) * 15} RPM, {len(self.api_keys) * 1500} RPD")
    
    def _make_model(self, api_key: str) -> genai.GenerativeModel:
        """Create a model instance with a specific API key and generous output limit."""
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            'gemini-flash-latest',
            generation_config=genai.GenerationConfig(
                max_output_tokens=8192,
                temperature=0.2,
            )
        )
    
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
        video_title: Optional[str] = None,
        duration_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """
        Summarize video transcript using Gemini Flash.

        For videos longer than ~15 minutes the transcript is split into chunks
        which are summarized individually and then merged, ensuring the full
        video is always covered.

        Args:
            transcript: Formatted transcript with [MM:SS] timestamps
            video_id: YouTube video ID
            video_title: Optional video title
            duration_seconds: Total video length (used to scale note count)

        Returns:
            {
                "title": str,
                "executiveSummary": str,
                "keyTerms": List[str],
                "detailedNotes": List[{timestamp, topic, content}]
            }
        """
        duration_minutes = duration_seconds / 60.0 if duration_seconds else 0

        # Dynamically scale: aim for ~1-2 notes per minute
        if duration_minutes >= 30:
            target_notes = "25-40"
        elif duration_minutes >= 20:
            target_notes = "20-30"
        elif duration_minutes >= 10:
            target_notes = "12-20"
        elif duration_minutes >= 5:
            target_notes = "8-12"
        else:
            target_notes = "5-10"

        duration_hint = (
            f"VIDEO DURATION: approximately {int(duration_minutes)} minutes" 
            if duration_minutes > 0 
            else ""
        )

        # For very long transcripts, split into chunks of ~80k chars and merge
        CHUNK_SIZE = 80000
        if len(transcript) > CHUNK_SIZE:
            return await self._summarize_chunked(
                transcript, video_id, video_title, duration_seconds, target_notes
            )

        prompt = f"""
You are an advanced video content analyzer. Analyze this COMPLETE YouTube video transcript and create a comprehensive study guide.

VIDEO ID: {video_id}
{f"VIDEO TITLE: {video_title}" if video_title else ""}
{duration_hint}

TRANSCRIPT:
{transcript}

Generate a structured study guide in JSON format with the following structure:

{{
  "title": "Video Title (extract from content or use provided title)",
  "executiveSummary": "Concise 4-6 sentence summary covering the ENTIRE video from start to finish",
  "keyTerms": ["Term 1", "Term 2", "Term 3", ...],
  "detailedNotes": [
    {{
      "timestamp": "MM:SS or HH:MM:SS (use exact timestamps from transcript)",
      "topic": "Section Topic",
      "content": "Detailed explanation of this section (2-4 sentences)"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- COVER THE ENTIRE VIDEO — first note near 00:00, last note near the end of the video
- Extract timestamps from [MM:SS] or [HH:MM:SS] markers in the transcript exactly
- Create {target_notes} detailed notes spread evenly across the full duration
- Every major topic change, concept, or section must have its own note
- Key terms should be domain-specific concepts, not generic words
- Executive summary must cover the complete arc of the video, not just the beginning
- Return ONLY valid JSON, no markdown formatting, no code fences
"""
        
        try:
            response_text = await self._generate_with_retry(prompt)
            return self._parse_summary_json(response_text, video_id)
        
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            raise Exception(f"Failed to summarize video: {str(e)}")

    async def _summarize_chunked(
        self,
        transcript: str,
        video_id: str,
        video_title: Optional[str],
        duration_seconds: float,
        target_notes: str,
    ) -> Dict[str, Any]:
        """
        Handle very long transcripts (>15 min) by splitting into chunks,
        summarizing each, then merging into a final result.
        """
        CHUNK_SIZE = 80000
        lines = transcript.split("\n")

        # Build chunks that respect line boundaries
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0
        for line in lines:
            if current_len + len(line) > CHUNK_SIZE and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = len(line)
            else:
                current_chunk.append(line)
                current_len += len(line)
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        print(f"📦 Transcript split into {len(chunks)} chunks for processing")

        all_notes: List[Dict] = []
        all_key_terms: List[str] = []
        partial_summaries: List[str] = []
        title = f"Video {video_id}"

        for i, chunk in enumerate(chunks):
            chunk_prompt = f"""
Analyze this SECTION ({i+1}/{len(chunks)}) of a YouTube video transcript.
{f"VIDEO TITLE: {video_title}" if video_title else ""}

TRANSCRIPT SECTION:
{chunk}

Return JSON:
{{
  "title": "video title if identifiable",
  "sectionSummary": "2-3 sentence summary of this section",
  "keyTerms": ["term1", "term2"],
  "notes": [
    {{"timestamp": "MM:SS", "topic": "Topic", "content": "2-3 sentence explanation"}}
  ]
}}

REQUIREMENTS:
- Cover ALL content in this section with notes (aim for one note per major topic)
- Use exact [MM:SS] timestamps from the transcript
- Return ONLY valid JSON, no markdown
"""
            try:
                resp = await self._generate_with_retry(chunk_prompt)
                chunk_data = self._parse_raw_json(resp)
                if chunk_data.get("title") and chunk_data["title"] != f"Video {video_id}":
                    title = chunk_data["title"]
                partial_summaries.append(chunk_data.get("sectionSummary", ""))
                all_key_terms.extend(chunk_data.get("keyTerms", []))
                all_notes.extend(chunk_data.get("notes", []))
            except Exception as e:
                print(f"⚠️ Chunk {i+1} error: {e}")

        # De-duplicate key terms
        seen = set()
        unique_terms = []
        for t in all_key_terms:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                unique_terms.append(t)

        # Merge partial summaries into a final executive summary
        merge_prompt = f"""
You analyzed a video in {len(chunks)} sections. Here are the section summaries:
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(partial_summaries))}

Write a single cohesive 4-6 sentence executive summary covering the ENTIRE video.
Return ONLY the plain text summary, nothing else.
"""
        try:
            exec_summary = await self._generate_with_retry(merge_prompt)
            exec_summary = exec_summary.strip()
        except Exception:
            exec_summary = " ".join(partial_summaries)

        # Sort notes by timestamp
        def ts_to_seconds(ts: str) -> float:
            parts = ts.replace("[", "").replace("]", "").split(":")
            try:
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
            except Exception:
                pass
            return 0.0

        all_notes.sort(key=lambda n: ts_to_seconds(n.get("timestamp", "0:00")))

        return {
            "title": title,
            "executiveSummary": exec_summary,
            "keyTerms": unique_terms[:30],
            "detailedNotes": all_notes,
            "summary": exec_summary,
        }

    def _parse_raw_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from a raw LLM response."""
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in LLM response")
        return json.loads(text[json_start:json_end])

    def _parse_summary_json(self, response_text: str, video_id: str) -> Dict[str, Any]:
        """Parse and normalise a summarize_transcript LLM response."""
        data = self._parse_raw_json(response_text)
        exec_summary = data.get("executiveSummary", "")
        return {
            "title": data.get("title", f"Video {video_id}"),
            "executiveSummary": exec_summary,
            "keyTerms": data.get("keyTerms", []),
            "detailedNotes": data.get("detailedNotes", []),
            "summary": exec_summary,
        }
    
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
