import os
import pytest
from redis.asyncio import from_url


@pytest.fixture(autouse=True)
def fresh_redis():
    import app.services.redis_client as redis_client

    new_r = from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        decode_responses=True
    )
    redis_client.r = new_r

    # Если shortener импортирует r напрямую — патчим и там
    try:
        import app.services.shortener as shortener
        shortener.r = new_r
    except ImportError:
        pass

    yield
