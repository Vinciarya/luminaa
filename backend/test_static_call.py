from youtube_transcript_api import YouTubeTranscriptApi

try:
    print("Testing static get_transcript call...")
    video_id = "dQw4w9WgXcQ"
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print(f"✅ Success! Fetched {len(transcript)} segments.")
except Exception as e:
    print(f"❌ Error: {e}")
