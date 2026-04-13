"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any

# ==================== VIDEO MODELS ====================

class VideoAnalyzeRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }

class DetailedNote(BaseModel):
    timestamp: Optional[str] = Field(None, description="Timestamp in MM:SS or HH:MM:SS format")
    topic: str = Field(..., description="Topic or section header")
    content: str = Field(..., description="Detailed explanation")

class VideoAnalyzeResponse(BaseModel):
    video_id: str
    title: str
    url: str
    thumbnail: str
    executiveSummary: str
    summary: str  # Alias for executiveSummary
    keyTerms: List[str]
    detailedNotes: List[DetailedNote]
    dateAdded: str
    processed: bool = True
    cached: bool = Field(..., description="Whether result was from cache")
    is_guest_preview: bool = False
    preview_duration_minutes: Optional[float] = Field(None, description="Minutes of video covered in this preview (guests only)")
    full_duration_minutes: Optional[float] = Field(None, description="Total video duration in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "Never Gonna Give You Up",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
                "executiveSummary": "A classic 1987 pop song...",
                "summary": "A classic 1987 pop song...",
                "keyTerms": ["pop music", "1987", "Rick Astley"],
                "detailedNotes": [
                    {
                        "timestamp": "00:15",
                        "topic": "Introduction",
                        "content": "The song begins with..."
                    }
                ],
                "dateAdded": "Just now",
                "processed": True,
                "cached": False
            }
        }

# ==================== CHAT MODELS ====================

class ChatCreateRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ"
            }
        }

class ChatCreateResponse(BaseModel):
    session_id: str
    message: str = "Chat session created successfully"

class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User's message/question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "message": "What is the main topic of this video?"
            }
        }

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str

# ==================== STATS MODELS ====================

class CacheStats(BaseModel):
    total_videos: int
    popular_videos: int
    total_views: int
    cache_enabled: bool

class APIKeyStats(BaseModel):
    requests_last_minute: int
    requests_today: int
    rpm_remaining: int
    rpd_remaining: int

class StatsResponse(BaseModel):
    cache: CacheStats
    api_keys: Dict[str, APIKeyStats]
    total_capacity: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "cache": {
                    "total_videos": 150,
                    "popular_videos": 25,
                    "total_views": 500,
                    "cache_enabled": True
                },
                "api_keys": {
                    "key_1": {
                        "requests_last_minute": 5,
                        "requests_today": 120,
                        "rpm_remaining": 10,
                        "rpd_remaining": 1380
                    }
                },
                "total_capacity": {
                    "rpm": 45,
                    "rpd": 4500
                }
            }
        }

# ==================== ERROR MODELS ====================

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Video not found",
                "detail": "The video may be private or deleted"
            }
        }
