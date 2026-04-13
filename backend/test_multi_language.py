from services.transcript_service import get_transcript, format_transcript_for_ai
import sys
import os

# Add backend to path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_video(video_id, description):
    print(f"\n--- Testing: {description} ({video_id}) ---")
    try:
        transcript = get_transcript(video_id, languages=['en'])
        print(f"✅ Success! Fetched {len(transcript)} segments.")
        formatted = format_transcript_for_ai(transcript)
        print(f"Preview (first 100 chars): {formatted[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    # 1. English Video (Manual or Auto)
    test_video("dQw4w9WgXcQ", "English Video (Rickroll)")

    # 2. Spanish Video (Should be translated to English)
    # Video: "Aprender español - HOLA"
    test_video("P_pB12vP-I8", "Spanish Video (Manual Spanish)")

    # 3. Hindi Video (Should be translated to English)
    # Video: "PM Modi speech" usually has Hindi auto-captions
    test_video("XyS8Z-0MvM0", "Hindi Video (Auto Hindi)")
