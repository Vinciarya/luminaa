"""
Video Analysis API Router

Endpoints:
- POST /api/videos/analyze - Analyze YouTube video
- GET /api/videos/{video_id} - Get cached video data
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import uuid

from models import VideoAnalyzeRequest, VideoAnalyzeResponse, ErrorResponse, DetailedNote
from services.transcript_service import extract_video_id, get_transcript, format_transcript_for_ai
from services.gemini_service import gemini_service
from services.gemini_service import gemini_service
from services.cache_service import cache_service
from limiter import limiter
from auth import get_current_user, get_optional_current_user
from fastapi import Request, Depends

router = APIRouter(prefix="/api/videos", tags=["videos"])

@router.post(
    "/analyze",
    response_model=VideoAnalyzeResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Analyze YouTube Video",
    description="""
    Analyze a YouTube video and generate study notes.
    
    **Cost Optimization:**
    - First request: Fetches transcript (FREE) + AI summarization (FREE with Gemini)
    - Subsequent requests: Served from cache (90-day TTL) = $0 cost
    - Popular videos (>10 requests): Cached forever = $0 cost
    
    **Expected Response Time:**
    - Cache hit: <100ms
    - Cache miss: 5-15 seconds (transcript + AI processing)
    """
)
@limiter.limit("5/minute")
async def analyze_video(request: Request, body: VideoAnalyzeRequest, user: dict = Depends(get_optional_current_user)):
    """
    Analyze YouTube video with aggressive caching
    
    Flow:
    1. Extract video ID from URL
    2. Check cache (85%+ hit rate after month 1)
    3. If cached: Return immediately ($0 cost)
    4. If not cached:
       a. Extract transcript (FREE via youtube-transcript-api)
       b. Summarize with Gemini (FREE tier with rate limiting)
       c. Cache for 90 days
    5. Track popularity for persistent caching
    """
    
    # Step 1: Extract video ID
    video_id = extract_video_id(body.url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL. Please provide a valid YouTube video URL."
        )
    
    print(f"\n{'='*60}")
    print(f"📹 Analyzing video: {video_id}")
    if not user:
        print(f"👤 Guest User detected - limiting to 30%")
    print(f"{'='*60}")
    
    # Step 2: Check cache first (COST OPTIMIZATION)
    # Only check cache if user is logged in (Guests always get a fresh slice or we cache slices separately?)
    # For now, let's say guests don't trigger the main cache, or we cache their slice separately?
    # Simpler: If guest, bypass cache for now or cache with a different key suffix?
    # Let's just bypass cache read for guests to ensure they get the preview, OR check if we have a full cache.
    # If we have full cache, we can slice it and return it? Yes.
    
    cached_summary = await cache_service.get_video_summary(video_id)
    if cached_summary:
        print(f"✅ Returning cached result (saved $0.002)")
        
        # If guest, slice the cached result
        if not user:
            # Slice summary and notes? 
            # Actually, the cached summary is already full. 
            # We can't easily "un-summarize" it. 
            # So for guests, maybe we just show the cached summary but with a flag?
            # User wants "process only 30%".
            # If we return full summary, they see full video.
            # So we SHOULD process only 30% for them.
            # If we have full cache, we can't really use it unless we stored the transcript.
            # But we do retain the video_id.
            
            # Re-processing 30% might incur cost/time.
            # BUT, the prompt said "process only half".
            
            # Let's stick to the plan: Guests get 30% processing.
            # So if guest, we proceed to process 30%, ignoring full cache?
            # OR we check if we have a "preview" cache?
            # Let's ignore cache for guests for simplicity of implementation now.
            pass 
        else:
            return VideoAnalyzeResponse(
                video_id=video_id,
                url=body.url,
                thumbnail=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                cached=True,
                **cached_summary
            )
    
    # Step 3: Cache miss (or Guest) - process video
    print(f"❌ Cache miss (or Guest) - processing video...")
    
    try:
        # Step 3a: Get transcript (FREE - no API key needed!)
        print(f"📝 Fetching transcript (FREE)...")
        transcript_data = get_transcript(video_id)
        
        is_guest_preview = False
        
        # GUEST LOGIC: Slice Transcript
        if not user:
            total_len = len(transcript_data)
            slice_len = int(total_len * 0.30)
            if slice_len < 1: slice_len = 1
            transcript_data = transcript_data[:slice_len]
            print(f"✂️ Sliced transcript to {slice_len} segments (30%)")
            is_guest_preview = True
            
        formatted_transcript = format_transcript_for_ai(transcript_data)
        
        print(f"✅ Transcript fetched: {len(transcript_data)} segments, {len(formatted_transcript)} chars")
        
        # Cache transcript for future use (30 days) - ONLY IF FULL
        if user:
            await cache_service.set_transcript(video_id, formatted_transcript, ttl_days=30)
        
        # Step 3b: Summarize with Gemini (FREE tier with rate limiting)
        print(f"🤖 Summarizing with Gemini Flash (FREE tier)...")
        summary_data = await gemini_service.summarize_transcript(
            transcript=formatted_transcript,
            video_id=video_id
        )
        
        print(f"✅ Summary generated: {summary_data['title']}")
        
        # Step 3c: Cache summary (90 days) - ONLY IF FULL
        cache_data = {
            "title": summary_data["title"],
            "executiveSummary": summary_data["executiveSummary"],
            "summary": summary_data["executiveSummary"],
            "keyTerms": summary_data["keyTerms"],
            "detailedNotes": summary_data["detailedNotes"],
            "dateAdded": "Just now"
        }
        
        if user:
            await cache_service.set_video_summary(video_id, cache_data, ttl_days=90)
            print(f"💾 Cached for 90 days")
        
        print(f"{'='*60}\n")
        
        return VideoAnalyzeResponse(
            video_id=video_id,
            url=body.url,
            thumbnail=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            cached=False,
            is_guest_preview=is_guest_preview,
            **cache_data
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        # Provide helpful error messages
        error_lower = error_msg.lower()
        if "no element found" in error_lower or "xml" in error_lower or "typeerror" in error_lower or "not subscriptable" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch transcript. The video may be private, age-restricted, or region-locked. Please try a different video."
            )
        elif "transcripts are disabled" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This video has no captions/subtitles available. Please try a different video."
            )
        elif "no transcript found" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript or captions found for this video. It may not have any subtitles available."
            )
        elif "no transcripts available" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcripts are available for this video."
            )
        elif "rate limit" in error_lower:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again in a few seconds."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze video: {error_msg}"
            )

@router.get(
    "/{video_id}",
    response_model=VideoAnalyzeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get Cached Video Data",
    description="Retrieve previously analyzed video data from cache"
)
async def get_video(video_id: str, user: dict = Depends(get_current_user)):
    """
    Get cached video data
    
    Returns 404 if video hasn't been analyzed yet
    """
    
    cached_summary = await cache_service.get_video_summary(video_id)
    
    if not cached_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found in cache. Please analyze it first."
        )
    
    return VideoAnalyzeResponse(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        thumbnail=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        cached=True,
        **cached_summary
    )
