"""
FREE Transcript Extraction Service
Uses youtube-transcript-api (no API key needed, no rate limits)
"""

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import html
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
    Supports all languages with English translation fallback.
    Compatible with youtube-transcript-api >= 1.0.0.
    """
    print(f"DEBUG: get_transcript called for {video_id}")
    import time

    ytt = YouTubeTranscriptApi()  # v1.0+ requires instantiation

    for attempt in range(max_retries):
        try:
            # Step 1: List all available transcripts
            transcript_list = ytt.list(video_id)

            # Step 2: Try the requested languages first
            transcript = None
            try:
                transcript = transcript_list.find_transcript(languages)
            except NoTranscriptFound:
                pass

            # Step 3: Fallback — iterate the transcript list (v1.0+ public API)
            if transcript is None:
                available = list(transcript_list)   # TranscriptList is directly iterable in v1.0+
                if not available:
                    raise Exception("No transcripts available for this video")

                source_transcript = available[0]
                if 'en' in languages and source_transcript.language_code != 'en':
                    try:
                        transcript = source_transcript.translate('en')
                        print(f"DEBUG: Translated {source_transcript.language_code} to English")
                    except Exception as translate_err:
                        print(f"DEBUG: Translation failed ({translate_err}), using original language")
                        transcript = source_transcript
                else:
                    transcript = source_transcript

            # Step 4: Fetch the content
            fetched_data = transcript.fetch()

            # v1.0+ returns a FetchedTranscript object; .to_raw_data() gives list of dicts.
            # Older versions already returned a list of dicts directly.
            if hasattr(fetched_data, 'to_raw_data'):
                raw_segments = fetched_data.to_raw_data()
            else:
                raw_segments = fetched_data

            # Normalise segments — handles both dict and FetchedTranscriptSnippet objects
            result = []
            for segment in raw_segments:
                if isinstance(segment, dict):
                    result.append({
                        'text': html.unescape(segment['text']).strip(),
                        'start': segment['start'],
                        'duration': segment['duration'],
                    })
                else:
                    result.append({
                        'text': html.unescape(segment.text).strip(),
                        'start': segment.start,
                        'duration': segment.duration,
                    })

            # Remove empty segments
            result = [s for s in result if s['text']]
            return result

        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video {video_id}")
        except NoTranscriptFound:
            raise Exception(f"No transcript found for video {video_id}")
        except Exception as e:
            error_str = str(e).lower()
            print(f"DEBUG: fetch_transcript error on attempt {attempt + 1}: {type(e).__name__}: {e}")

            # Don't retry on permanent / unrecoverable errors
            if any(x in error_str for x in ["disabled", "not found", "private", "no transcripts available"]):
                raise Exception(f"Error fetching transcript: {str(e)}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential back-off: 1s, 2s
                print(f"WARNING: Transcript fetch attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Error fetching transcript ({type(e).__name__}): {str(e)}")

def format_transcript_for_ai(transcript: List[Dict], max_length: int = 200000) -> str:
    """
    Format transcript for AI summarization.

    Segments are grouped into ~30-second blocks to reduce line count while
    preserving every word — this dramatically cuts token usage without losing
    any content.

    Args:
        transcript: Raw transcript from YouTubeTranscriptApi
        max_length: Maximum character length (default: 200k — covers ~25 min videos)

    Returns:
        Formatted transcript string with timestamps
    """
    if not transcript:
        return ""

    formatted_parts = []
    block_start = transcript[0]['start']
    block_texts = []
    BLOCK_SECONDS = 30  # group into 30-second blocks

    for segment in transcript:
        if segment['start'] - block_start >= BLOCK_SECONDS and block_texts:
            timestamp = format_timestamp(block_start)
            formatted_parts.append(f"[{timestamp}] {' '.join(block_texts)}")
            block_start = segment['start']
            block_texts = []
        block_texts.append(segment['text'])

    # Flush the final block
    if block_texts:
        timestamp = format_timestamp(block_start)
        formatted_parts.append(f"[{timestamp}] {' '.join(block_texts)}")

    full_text = "\n".join(formatted_parts)

    # Hard safety cap — should almost never trigger now
    if len(full_text) > max_length:
        # Try to cut at a newline boundary so timestamps stay intact
        cut_pos = full_text.rfind("\n", 0, max_length)
        if cut_pos == -1:
            cut_pos = max_length
        full_text = full_text[:cut_pos] + "\n\n[Transcript continues beyond AI context limit...]"

    return full_text


def get_video_duration(transcript: List[Dict]) -> float:
    """
    Return total video duration in seconds from transcript data.
    Uses the last segment's start + duration.
    """
    if not transcript:
        return 0.0
    last = transcript[-1]
    return last['start'] + last.get('duration', 0)

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
