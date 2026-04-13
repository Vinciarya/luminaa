from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print(f"Type: {type(YouTubeTranscriptApi)}")
print(f"Dir: {dir(YouTubeTranscriptApi)}")

try:
    print(f"Has get_transcript: {hasattr(YouTubeTranscriptApi, 'get_transcript')}")
    if hasattr(YouTubeTranscriptApi, 'get_transcript'):
        print(f"get_transcript info: {inspect.getattr_static(YouTubeTranscriptApi, 'get_transcript')}")
except Exception as e:
    print(f"Error checking attribute: {e}")

try:
    # Try fetching a known video transcript
    t = YouTubeTranscriptApi.get_transcript("dQw4w9WgXcQ")
    print("Successfully fetched transcript")
except Exception as e:
    print(f"Failed to fetch: {e}")
