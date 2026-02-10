"""
FREE Transcript Extraction Service
Uses youtube-transcript-api (no API key needed, no rate limits)
"""

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
from typing import List, Dict, Optional

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from various YouTube URL formats
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If URL is already just the ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    return None

def get_transcript(video_id: str, languages: List[str] = ['en'], max_retries: int = 3) -> List[Dict]:
    """
    Get transcript with timestamps (100% FREE)
    
    Args:
        video_id: YouTube video ID
        languages: Preferred languages (default: English)
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of transcript segments with 'text', 'start', 'duration'
    
    Raises:
        TranscriptsDisabled: If video has no captions
        NoTranscriptFound: If requested language not available
    """
    import time
    
    # Create API instance (v1.2.4 uses instance methods)
    api = YouTubeTranscriptApi()
    
    for attempt in range(max_retries):
        try:
            # v1.2.4 API: instance.fetch(video_id, languages)
            transcript = api.fetch(video_id, languages=languages)
            
            # Convert FetchedTranscript objects to dicts
            result = []
            for segment in transcript:
                result.append({
                    'text': segment.text,
                    'start': segment.start,
                    'duration': segment.duration
                })
            
            return result
        
        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video {video_id}")
        except NoTranscriptFound:
            # Try without language specification (get any available)
            try:
                transcript = api.fetch(video_id)
                result = []
                for segment in transcript:
                    result.append({
                        'text': segment.text,
                        'start': segment.start,
                        'duration': segment.duration
                    })
                return result
            except:
                raise Exception(f"No transcript found for video {video_id}")
        except Exception as e:
            error_str = str(e).lower()
            # Don't retry on permanent errors
            if "disabled" in error_str or "not found" in error_str or "private" in error_str:
                raise Exception(f"Error fetching transcript: {str(e)}")
            
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                wait_time = 2 ** attempt
                print(f"⚠️  Transcript fetch attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Error fetching transcript: {str(e)}")

def format_transcript_for_ai(transcript: List[Dict], max_length: int = 50000) -> str:
    """
    Format transcript for AI summarization
    
    Args:
        transcript: Raw transcript from YouTubeTranscriptApi
        max_length: Maximum character length (default: 50k chars)
    
    Returns:
        Formatted transcript string with timestamps
    """
    formatted_parts = []
    
    for segment in transcript:
        timestamp = format_timestamp(segment['start'])
        text = segment['text'].strip()
        formatted_parts.append(f"[{timestamp}] {text}")
    
    full_text = "\n".join(formatted_parts)
    
    # Truncate if too long (to save on token costs)
    if len(full_text) > max_length:
        full_text = full_text[:max_length] + "\n\n[Transcript truncated for length...]"
    
    return full_text

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def get_transcript_text_only(video_id: str) -> str:
    """
    Get plain text transcript without timestamps (for embeddings)
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        Plain text transcript
    """
    transcript = get_transcript(video_id)
    return " ".join([segment['text'] for segment in transcript])

# Example usage:
if __name__ == "__main__":
    # Test with a public video
    video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    try:
        transcript = get_transcript(video_id)
        print(f"✅ Transcript fetched: {len(transcript)} segments")
        
        formatted = format_transcript_for_ai(transcript)
        print(f"✅ Formatted transcript: {len(formatted)} characters")
        print("\nFirst 500 chars:")
        print(formatted[:500])
        
    except Exception as e:
        print(f"❌ Error: {e}")
