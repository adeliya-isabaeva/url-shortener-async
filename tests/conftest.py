import os
import pytest
import redis as sync_redis
from redis.asyncio import from_url
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def fresh_redis():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Синхронный клиент — только для очистки базы
    sync_r = sync_redis.from_url(redis_url, decode_responses=True)
    sync_r.flushdb()

    # Асинхронный клиент — для приложения
    r = from_url(redis_url, decode_responses=True)

    import app.services.redis_client as redis_client
    redis_client.r = r

    try:
        import app.services.shortener as shortener
        shortener.r = r
    except ImportError:
        pass

    yield r

    sync_r.flushdb()
    sync_r.close()
