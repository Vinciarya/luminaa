import asyncio
from services.gemini_service import gemini_service
from services.transcript_service import get_transcript, format_transcript_for_ai
import json

async def test_analyze():
    video_id = "dQw4w9WgXcQ"
    print(f"Testing analysis for video: {video_id}")
    
    try:
        print("1. Fetching transcript...")
        transcript_data = get_transcript(video_id)
        formatted_transcript = format_transcript_for_ai(transcript_data)
        print(f"   Success! Transcript length: {len(formatted_transcript)}")
        
        print("2. Summarizing with Gemini...")
        summary_data = await gemini_service.summarize_transcript(
            transcript=formatted_transcript,
            video_id=video_id
        )
        print("   Success! Summary title:", summary_data['title'])
        print(json.dumps(summary_data, indent=2))
        
    except Exception as e:
        print(f"❌ Error encountered: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyze())
