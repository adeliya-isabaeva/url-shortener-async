import os
import pytest
from redis.asyncio import from_url


@pytest.mark.asyncio
async def test_redis_set_and_get():
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    r = from_url(REDIS_URL, decode_responses=True)

    # Проверяем запись и чтение
    await r.set("test_key", "test_value")
    val = await r.get("test_key")
    assert val == "test_value"

    # Чистим за собой
    await r.delete("test_key")
