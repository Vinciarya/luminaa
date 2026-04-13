from youtube_transcript_api import YouTubeTranscriptApi
import inspect
import sys

with open("debug_output.txt", "w") as f:
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Path: {sys.path}\n\n")
    
    try:
        f.write(f"YouTubeTranscriptApi object: {YouTubeTranscriptApi}\n")
        f.write(f"Type: {type(YouTubeTranscriptApi)}\n")
        f.write(f"Module: {YouTubeTranscriptApi.__module__}\n")
        try:
            f.write(f"File: {inspect.getfile(YouTubeTranscriptApi)}\n")
        except:
            f.write("File: Could not determine\n")
            
        f.write(f"Dir: {dir(YouTubeTranscriptApi)}\n")
    except Exception as e:
        f.write(f"Error inspecting: {e}\n")
