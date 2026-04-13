from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print(f"Class: {YouTubeTranscriptApi}")
print(f"Type of Class: {type(YouTubeTranscriptApi)}")

try:
    obj = YouTubeTranscriptApi()
    print(f"Instance created: {obj}")
    print(f"Type of Instance: {type(obj)}")
    print(f"Dir of Instance: {dir(obj)}")
    
    if hasattr(obj, 'fetch'):
        print(f"Instance has 'fetch': {getattr(obj, 'fetch')}")
        try:
            transcript = obj.fetch("dQw4w9WgXcQ")
            print("Fetch successful")
        except Exception as e:
            print(f"Fetch failed: {e}")
    else:
        print("Instance DOES NOT have 'fetch'")
        
    if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
         print("Class has static 'list_transcripts'")
    else:
         print("Class DOES NOT have static 'list_transcripts'")

except Exception as e:
    print(f"Instantiation failed: {e}")
