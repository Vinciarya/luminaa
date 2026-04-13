import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if redis_url.startswith("redis://"):
    redis_url = redis_url.replace("redis://", "rediss://", 1)

print(f"Connecting with SSL to: {redis_url.split('@')[-1]}")

try:
    r = redis.from_url(redis_url, ssl_cert_reqs=None)
    print("Ping:", r.ping())
    print("✅ Redis SSL connection successful!")
except Exception as e:
    print(f"❌ Redis SSL connection failed: {e}")
