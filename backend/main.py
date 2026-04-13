"""
FastAPI Main Application

YouTube Summarizer Backend with:
- FREE transcript extraction (youtube-transcript-api)
- Gemini Flash AI (FREE tier with multi-key rotation)
- Redis caching (90-day TTL, popular videos cached forever)
- Rate limiting (45 RPM with 3 keys)
- Cost tracking

Target: $0-10/month for 1000+ videos
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from config import settings
from services.cache_service import cache_service
from routers import videos, chat, stats

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_storage_url)

# ==================== LIFESPAN EVENTS ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    print("\n" + "="*60)
    print("🚀 Starting YouTube Summarizer Backend")
    print("="*60)
    
    # Connect to Redis
    await cache_service.connect()
    
    print(f"✅ Backend ready!")
    print(f"📊 API Keys: {len(settings.gemini_api_keys)}")
    print(f"📊 Total Capacity: {len(settings.gemini_api_keys) * 15} RPM")
    print(f"💾 Cache TTL: {settings.cache_ttl_days} days")
    print(f"⭐ Popular Video Threshold: {settings.popular_video_threshold} views")
    print("="*60 + "\n")
    
    yield
    
    # Shutdown
    print("\n" + "="*60)
    print("👋 Shutting down...")
    await cache_service.disconnect()
    print("="*60 + "\n")

# ==================== APP INITIALIZATION ====================

app = FastAPI(
    title="YouTube Summarizer API",
    description="""
    **Cost-Optimized YouTube Video Summarizer**
    
    Features:
    - 🆓 FREE transcript extraction (no API keys needed)
    - 🤖 Gemini Flash AI summarization (FREE tier)
    - 💾 Aggressive caching (90-day TTL, 85%+ hit rate)
    - ⚡ Multi-key rotation (45 RPM capacity)
    - 📊 Real-time usage statistics
    
    **Cost Target:** $0-10/month for 1000+ videos
    
    **How it works:**
    1. First request: Extract transcript (FREE) + AI summary (FREE)
    2. Cache for 90 days
    3. Popular videos (>10 requests): Cached forever
    4. Result: 85%+ requests served from cache = $0 cost
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== MIDDLEWARE ====================

# CORS - Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cost Tracking Middleware
@app.middleware("http")
async def cost_tracking_middleware(request: Request, call_next):
    """
    Track request costs and performance
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log request
    print(f"📊 {request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    
    # Add performance headers
    response.headers["X-Process-Time"] = f"{duration:.2f}s"
    
    return response

# Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global error handler for uncaught exceptions
    """
    print(f"❌ Unhandled error: {exc}")
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )
    
    # Manually add CORS for error responses
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# ==================== ROUTES ====================

# Include routers
app.include_router(videos.router)
app.include_router(chat.router)
app.include_router(stats.router)

# Health check
@app.get("/", tags=["health"])
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "YouTube Summarizer API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """
    Detailed health check
    """
    cache_stats = await cache_service.get_cache_stats()
    
    return {
        "status": "healthy",
        "redis": "connected" if cache_stats["cache_enabled"] else "disconnected",
        "api_keys": len(settings.gemini_api_keys),
        "environment": settings.environment
    }

# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False
    )
