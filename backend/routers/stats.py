"""
Statistics API Router

Endpoints:
- GET /api/stats - Get usage statistics and cost estimates
"""

from fastapi import APIRouter
from models import StatsResponse, CacheStats, APIKeyStats

from services.cache_service import cache_service
from services.gemini_service import gemini_service
from config import settings
from limiter import limiter
from auth import get_current_user
from fastapi import Request, Depends

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get(
    "",
    response_model=StatsResponse,
    summary="Get Usage Statistics",
    description="""
    Get comprehensive usage statistics including:
    - Cache performance (hit rate, total videos, popular videos)
    - API key usage (requests per minute/day, remaining capacity)
    - Total system capacity
    
    Use this to monitor costs and optimize usage.

    """
)
@limiter.limit("10/minute")
async def get_stats(request: Request, user: dict = Depends(get_current_user)):
    """
    Get usage statistics and cost estimates
    
    Returns:
    - Cache stats (videos cached, popular videos, total views)
    - API key stats (RPM/RPD usage per key)
    - Total capacity (combined across all keys)
    """
    
    # Get cache stats
    cache_stats = await cache_service.get_cache_stats()
    
    # Get API key stats
    api_key_stats = gemini_service.get_usage_stats()
    
    # Calculate total capacity
    num_keys = len(settings.gemini_api_keys)
    total_capacity = {
        "rpm": num_keys * settings.max_requests_per_minute,
        "rpd": num_keys * settings.max_requests_per_day
    }
    
    return StatsResponse(
        cache=CacheStats(**cache_stats),
        api_keys=api_key_stats,
        total_capacity=total_capacity
    )
