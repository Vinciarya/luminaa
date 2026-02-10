from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Gemini API Keys (for rotation)
    gemini_api_key_1: str
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Supabase (optional)
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Rate Limiting
    max_requests_per_minute: int = 15
    max_requests_per_day: int = 1500
    
    # Cache Settings
    cache_ttl_days: int = 90
    popular_video_threshold: int = 10
    
    # CORS
    frontend_url: str = "http://localhost:5173"
    
    # Environment
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    @property
    def gemini_api_keys(self) -> List[str]:
        """Get list of all configured Gemini API keys"""
        keys = [self.gemini_api_key_1]
        if self.gemini_api_key_2:
            keys.append(self.gemini_api_key_2)
        if self.gemini_api_key_3:
            keys.append(self.gemini_api_key_3)
        return keys

settings = Settings()
