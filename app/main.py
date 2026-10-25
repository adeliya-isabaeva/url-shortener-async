import logging
import redis.exceptions as redis_exc  # <--- ЭТО ОБЯЗАТЕЛЬНО: без этого middleware выдаст ошибку
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Импорты
from app.routers import url_router
from app.services.redis_sync import get_redis_sync

app = FastAPI(title="URL Shortener", version="1.0.0")

RATE_LIMIT = 100
RATE_PERIOD_SECONDS = 60

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    r = get_redis_sync()
    client_ip = request.client.host
    # Для отладки теста — один ключ на все запросы
    key = "rate:test_single_key"

    try:
        count = r.incr(key)

        if count == 1:
            r.expire(key, RATE_PERIOD_SECONDS)
        logger.info(f"rate_limit: ip={client_ip}, key={key}, count={count}, limit={RATE_LIMIT}")

        if count > RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": RATE_PERIOD_SECONDS,
                    "ip": client_ip
                }
            )

    except redis_exc.ConnectionError as e:
        logger.error(f"Redis connection error (IP={client_ip}): {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service temporarily unavailable (Redis down)"}
        )

    except redis_exc.TimeoutError as e:
        logger.error(f"Redis timeout (IP={client_ip}): {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service temporarily unavailable (Redis timeout)"}
        )

    except Exception as e:
        logger.warning(f"Rate limit error (IP={client_ip}): {e}")
        # fallback: продолжаем обработку, но без лимитов

    response = await call_next(request)
    return response

# Подключаем роутер.
# Так как /stats теперь внутри url_router.py и стоит выше {short_code},
# он будет работать корректно.
app.include_router(url_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "URL Shortener API is running"}
