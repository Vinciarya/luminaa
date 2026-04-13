import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
print(f"Connecting to: {redis_url.split('@')[-1]}")

try:
    r = redis.from_url(redis_url)
    print("Ping:", r.ping())
    r.set("test_key", "hello")
    print("Get test_key:", r.get("test_key"))
    print("✅ Redis connection successful!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
