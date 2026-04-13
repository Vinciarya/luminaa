"""
Redis Caching Service with Aggressive Caching Strategy
- Transcripts: 30 days TTL
- Summaries: 90 days TTL
- Popular videos (>10 requests): Never expire
- Chat sessions: 24 hours TTL

Target: 85%+ cache hit rate after month 1
"""

import redis.asyncio as redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta
from config import settings

class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl_days = settings.cache_ttl_days
        self.popular_threshold = settings.popular_video_threshold
    
    async def connect(self):
        """Connect to Redis (Upstash or local)"""
        try:
            # The protocol (redis:// vs rediss://) is now handled in settings.redis_storage_url
            self.redis_client = await redis.from_url(
                settings.redis_storage_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=30
            )
            
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis connected successfully")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("⚠️  Running without cache (will be slower and more expensive)")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    # ==================== VIDEO SUMMARY CACHING ====================
    
    async def get_video_summary(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached video summary
        
        Returns None if not cached (cache miss)
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"summary:{video_id}"
            data = await self.redis_client.get(key)
            
            if data:
                # Increment view count for popularity tracking
                await self.increment_view_count(video_id)
                print(f"✅ Cache HIT: {video_id}")
                return json.loads(data)
            
            print(f"❌ Cache MISS: {video_id}")
            return None
        
        except Exception as e:
            print(f"⚠️  Cache read error: {e}")
            return None
    
    async def set_video_summary(
        self, 
        video_id: str, 
        data: Dict[str, Any], 
        ttl_days: Optional[int] = None
    ):
        """
        Cache video summary with TTL
        
        Args:
            video_id: YouTube video ID
            data: Summary data to cache
            ttl_days: Time to live in days (default: 90 days)
        """
        if not self.redis_client:
            return
        
        try:
            key = f"summary:{video_id}"
            ttl = ttl_days or self.cache_ttl_days
            
            await self.redis_client.setex(
                key,
                timedelta(days=ttl),
                json.dumps(data)
            )
            
            print(f"💾 Cached summary: {video_id} (TTL: {ttl} days)")
        
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
    
    # ==================== TRANSCRIPT CACHING ====================
    
    async def get_transcript(self, video_id: str) -> Optional[str]:
        """Get cached transcript"""
        if not self.redis_client:
            return None
        
        try:
            key = f"transcript:{video_id}"
            return await self.redis_client.get(key)
        except Exception as e:
            print(f"⚠️  Cache read error: {e}")
            return None
    
    async def set_transcript(self, video_id: str, transcript: str, ttl_days: int = 30):
        """Cache transcript (30 days default - transcripts rarely change)"""
        if not self.redis_client:
            return
        
        try:
            key = f"transcript:{video_id}"
            await self.redis_client.setex(
                key,
                timedelta(days=ttl_days),
                transcript
            )
            print(f"💾 Cached transcript: {video_id} (TTL: {ttl_days} days)")
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
    
    # ==================== POPULARITY TRACKING ====================
    
    async def increment_view_count(self, video_id: str) -> int:
        """
        Increment view count for popularity tracking
        
        Returns current view count
        """
        if not self.redis_client:
            return 0
        
        try:
            key = f"views:{video_id}"
            count = await self.redis_client.incr(key)
            
            # Check if video became popular
            if count == self.popular_threshold:
                await self.make_popular_persistent(video_id)
            
            return count
        except Exception as e:
            print(f"⚠️  View count error: {e}")
            return 0
    
    async def get_view_count(self, video_id: str) -> int:
        """Get view count for a video"""
        if not self.redis_client:
            return 0
        
        try:
            key = f"views:{video_id}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            return 0
    
    async def make_popular_persistent(self, video_id: str):
        """
        Remove expiry for popular videos (cache forever)
        
        This is a key cost optimization: popular videos never expire,
        so we never re-process them = $0 cost for repeat requests
        """
        if not self.redis_client:
            return
        
        try:
            summary_key = f"summary:{video_id}"
            transcript_key = f"transcript:{video_id}"
            
            # Remove expiry (persist forever)
            await self.redis_client.persist(summary_key)
            await self.redis_client.persist(transcript_key)
            
            print(f"⭐ Video {video_id} is now POPULAR - cached forever!")
        except Exception as e:
            print(f"⚠️  Persist error: {e}")
    
    # ==================== CHAT SESSION CACHING ====================
    
    async def set_chat_session(self, session_id: str, context: str, ttl_hours: int = 24):
        """Cache chat session context (24 hours)"""
        if not self.redis_client:
            return
        
        try:
            key = f"chat:{session_id}"
            await self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                context
            )
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
    
    async def get_chat_session(self, session_id: str) -> Optional[str]:
        """Get cached chat session context"""
        if not self.redis_client:
            return None
        
        try:
            key = f"chat:{session_id}"
            return await self.redis_client.get(key)
        except Exception as e:
            return None
    
    # ==================== STATISTICS ====================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring
        
        Returns:
            - total_videos: Number of cached videos
            - popular_videos: Number of popular (persistent) videos
            - total_views: Total view count across all videos
        """
        if not self.redis_client:
            return {
                "total_videos": 0,
                "popular_videos": 0,
                "total_views": 0,
                "cache_enabled": False
            }
        
        try:
            # Count cached summaries
            summary_keys = []
            async for key in self.redis_client.scan_iter("summary:*"):
                summary_keys.append(key)
            
            # Count popular videos (no TTL)
            popular_count = 0
            for key in summary_keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # -1 means no expiry
                    popular_count += 1
            
            # Get total views
            total_views = 0
            async for key in self.redis_client.scan_iter("views:*"):
                count = await self.redis_client.get(key)
                total_views += int(count) if count else 0
            
            return {
                "total_videos": len(summary_keys),
                "popular_videos": popular_count,
                "total_views": total_views,
                "cache_enabled": True
            }
        
        except Exception as e:
            print(f"⚠️  Stats error: {e}")
            return {
                "total_videos": 0,
                "popular_videos": 0,
                "total_views": 0,
                "cache_enabled": True,
                "error": str(e)
            }

# Global cache instance
cache_service = CacheService()
