import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# Настройка логирования — в самом верху
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Импорты
from app.routers import url_router
from app.services.redis_sync import get_redis_sync

# Создаём app ОДИН раз, сразу с параметрами
app = FastAPI(title="URL Shortener", version="1.0.0")

# Настройки лимита
RATE_LIMIT = 100
RATE_PERIOD_SECONDS = 60

# Middleware — обязательно ДО роутов
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    r = get_redis_sync()
    client_ip = request.client.host
    key = f"rate:{client_ip}"

    try:
        count = r.incr(key)

        if count == 1:
            r.expire(key, RATE_PERIOD_SECONDS)

        if count > RATE_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": RATE_PERIOD_SECONDS,
                    "ip": client_ip
                }
            )
    except Exception as e:
        logger.warning(f"Redis error in rate limit (IP={client_ip}): {e}")

    response = await call_next(request)
    return response

# Подключаем роуты
app.include_router(url_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "URL Shortener API is running"}
