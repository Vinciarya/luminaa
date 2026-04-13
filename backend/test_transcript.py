
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print(f"YouTubeTranscriptApi imported: {YouTubeTranscriptApi}")
    print(f"Has get_transcript: {hasattr(YouTubeTranscriptApi, 'get_transcript')}")
    print(f"Dir: {dir(YouTubeTranscriptApi)}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
