# app/services/redis_sync.py
import os
import redis
from functools import lru_cache

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@lru_cache()
def get_redis_sync():
    # Для rate limiting нам нужна скорость и атомарность, sync redis идеален
    # host извлекаем из redis://redis:6379 -> 'redis'
    host = REDIS_URL.replace("redis://", "").split(":")[0]
    return redis.Redis(host=host, port=6379, db=0, decode_responses=True)
