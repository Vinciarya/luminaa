from youtube_transcript_api import YouTubeTranscriptApi

try:
    print("Attempting to fetch with instantiation...")
    ytt_api = YouTubeTranscriptApi()
    # using a known working video ID (rick roll)
    transcript = ytt_api.fetch("dQw4w9WgXcQ")
    print(f"Success! Fetched {len(transcript)} segments.")
    print("First segment:", transcript[0])
except Exception as e:
    print(f"Error fetching: {e}")
