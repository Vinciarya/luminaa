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
    Supports all languages with English translation fallback
    """
    print(f"DEBUG: get_transcript called for {video_id}")
    import time
    
    for attempt in range(max_retries):
        try:
            # Step 1: List all available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Step 2: Try to find a manual or generated transcript in the requested languages
            try:
                # find_transcript prefers manually created transcripts over generated ones
                transcript = transcript_list.find_transcript(languages)
            except:
                # Step 3: Fallback - find ANY available transcript and translate it to English
                # If 'en' was requested but not found, this catches it
                try:
                    # Find any manual or generated transcript
                    # find_transcript without args might not work as expected, 
                    # so we iterate through the available ones
                    available = list(transcript_list._manually_created_transcripts.values()) + \
                               list(transcript_list._generated_transcripts.values())
                    
                    if not available:
                        raise Exception("No transcripts available")
                    
                    # Preferred: Use the first one and translate to English
                    source_transcript = available[0]
                    if 'en' in languages:
                         transcript = source_transcript.translate('en')
                         print(f"DEBUG: Translated {source_transcript.language_code} to English")
                    else:
                         transcript = source_transcript
                except Exception as translate_err:
                    print(f"DEBUG: Translation failed: {translate_err}")
                    # If translation fails, try to just fetch the first one available
                    transcript = transcript_list.find_transcript([]) # find_transcript([]) often works as "any"
            
            # Step 4: Fetch the content
            fetched_data = transcript.fetch()
            
            # youtube-transcript-api v1.0+ returns a FetchedTranscript object (not a list of dicts).
            # Use .to_raw_data() if available, otherwise fall back to attribute access.
            if hasattr(fetched_data, 'to_raw_data'):
                raw_segments = fetched_data.to_raw_data()
            else:
                raw_segments = fetched_data  # older versions already return a list of dicts
            
            # Convert transcript segments (supports both dict and object-style segments)
            result = []
            for segment in raw_segments:
                if isinstance(segment, dict):
                    result.append({
                        'text': segment['text'],
                        'start': segment['start'],
                        'duration': segment['duration']
                    })
                else:
                    # FetchedTranscriptSnippet object (v1.0+)
                    result.append({
                        'text': segment.text,
                        'start': segment.start,
                        'duration': segment.duration
                    })
            
            return result
        
        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video {video_id}")
        except NoTranscriptFound:
            raise Exception(f"No transcript found for video {video_id}")
        except Exception as e:
            error_str = str(e).lower()
            print(f"DEBUG: fetch_transcript error on attempt {attempt+1}: {type(e).__name__}: {e}")
            
            # Don't retry on permanent errors
            if any(x in error_str for x in ["disabled", "not found", "private", "no transcripts available"]):
                raise Exception(f"Error fetching transcript: {str(e)}")
            
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                wait_time = 2 ** attempt
                print(f"⚠️  Transcript fetch attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Re-raise with full context so the router can show the real error
                raise Exception(f"Error fetching transcript ({type(e).__name__}): {str(e)}")

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
