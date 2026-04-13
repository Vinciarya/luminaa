from services.transcript_service import get_transcript

try:
    print("Testing get_transcript from service...")
    video_id = "dQw4w9WgXcQ"
    transcript = get_transcript(video_id)
    print(f"✅ Success! Fetched {len(transcript)} segments.")
except Exception as e:
    print(f"❌ Error: {e}")
