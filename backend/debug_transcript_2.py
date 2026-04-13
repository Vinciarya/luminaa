from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("--- Debugging YouTubeTranscriptApi ---")
try:
    print(f"Type: {type(YouTubeTranscriptApi)}")
    print(f"Has get_transcript: {hasattr(YouTubeTranscriptApi, 'get_transcript')}")
    
    if hasattr(YouTubeTranscriptApi, 'get_transcript'):
        attr = getattr(YouTubeTranscriptApi, 'get_transcript')
        print(f"Attribute type: {type(attr)}")
        print(f"Is method: {inspect.ismethod(attr)}")
        print(f"Is function: {inspect.isfunction(attr)}")
    else:
        print("get_transcript attribute NOT found")
        # Print all attributes to see what's there
        print(f"Attributes: {[a for a in dir(YouTubeTranscriptApi) if not a.startswith('__')]}")
        
except Exception as e:
    print(f"Error inspecting: {e}")

print("--- Attempting Fetch ---")
try:
    # Test with a public video
    video_id = "dQw4w9WgXcQ"
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("Successfully fetched transcript")
except Exception as e:
    print(f"Failed to fetch: {e}")
