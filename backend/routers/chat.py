"""
Chat Session API Router

Endpoints:
- POST /api/chat/create - Create chat session with video context
- POST /api/chat/message - Send message to chat session
"""

from fastapi import APIRouter, HTTPException, status
import uuid

from models import (
    ChatCreateRequest, 
    ChatCreateResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ErrorResponse
)
from services.gemini_service import gemini_service
from services.cache_service import cache_service
from limiter import limiter
from auth import get_current_user
from fastapi import Request, Depends

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post(
    "/create",
    response_model=ChatCreateResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Create Chat Session",
    description="Create a new chat session for a video with AI tutor context"

)
@limiter.limit("10/minute")
async def create_chat_session(request: Request, body: ChatCreateRequest, user: dict = Depends(get_current_user)):
    """
    Create chat session with video context
    
    Flow:
    1. Get video summary from cache
    2. Create system instruction with video context
    3. Generate session ID
    4. Cache session context (24 hours)
    """
    
    video_id = body.video_id
    
    # Get video summary from cache
    video_data = await cache_service.get_video_summary(video_id)
    
    if not video_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found. Please analyze it first using /api/videos/analyze"
        )
    
    # Create chat context
    context = await gemini_service.create_chat_context(
        video_title=video_data.get("title", "Unknown Video"),
        executive_summary=video_data.get("executiveSummary", ""),
        key_terms=video_data.get("keyTerms", []),
        detailed_notes=video_data.get("detailedNotes", [])
    )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Cache session context (24 hours)
    await cache_service.set_chat_session(session_id, context, ttl_hours=24)
    
    print(f"💬 Chat session created: {session_id} for video {video_id}")
    
    return ChatCreateResponse(
        session_id=session_id,
        message=f"Chat session created for '{video_data.get('title', 'Unknown Video')}'"
    )

@router.post(
    "/message",
    response_model=ChatMessageResponse,
    responses={
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse}
    },
    summary="Send Chat Message",
    description="Send a message to an existing chat session and get AI response"

)
@limiter.limit("20/minute")
async def send_chat_message(request: Request, body: ChatMessageRequest, user: dict = Depends(get_current_user)):
    """
    Send message to chat session
    
    Flow:
    1. Get session context from cache
    2. Generate AI response with context
    3. Return response
    """
    
    session_id = body.session_id
    message = body.message
    
    # Get session context
    context = await cache_service.get_chat_session(session_id)
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or expired. Please create a new session."
        )
    
    try:
        # Generate AI response
        print(f"💬 Processing message for session {session_id[:8]}...")
        response_text = await gemini_service.chat_response(context, message)
        
        print(f"✅ Response generated ({len(response_text)} chars)")
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id
        )
    
    except Exception as e:
        error_msg = str(e)
        
        if "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again in a few seconds."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate response: {error_msg}"
            )
