import os
import json
import time
from typing import Optional, Any
try:
    import redis
except ImportError:
    redis = None

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

class RedisCacheManager:
    def __init__(self):
        self.client = None
        self.local_memory_fallback = {}
        if redis is not None:
            try:
                self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True, socket_connect_timeout=2)
                self.client.ping()
                print("Connected to Redis Cache successfully.")
            except Exception as e:
                print(f"Redis connection unavailable ({e}). Using in-memory fallback cache.")
                self.client = None
        else:
            print("Redis library not installed in host environment. Using in-memory fallback cache.")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if self.client:
            try:
                data = self.client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        # Fallback check
        cached = self.local_memory_fallback.get(key)
        if cached and cached["expiry"] > time.time():
            return cached["value"]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 120):
        val_str = json.dumps(value)
        if self.client:
            try:
                self.client.setex(key, ttl_seconds, val_str)
                return
            except Exception:
                pass
        self.local_memory_fallback[key] = {
            "value": value,
            "expiry": time.time() + ttl_seconds
        }

    def delete(self, key: str):
        if self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass
        if key in self.local_memory_fallback:
            del self.local_memory_fallback[key]

cache_manager = RedisCacheManager()
