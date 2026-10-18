# app/services/redis_sync.py
import os
import redis
from functools import lru_cache

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@lru_cache()
def get_redis_sync():
    host = REDIS_URL.replace("redis://", "").split(":")[0]
    return redis.Redis(
        host=host,
        port=6379,
        db=0,
        decode_responses=True,
        socket_timeout=2.0,           # ждать ответ не дольше 2 сек
        socket_connect_timeout=2.0    # ждать подключение не дольше 2 сек
    )