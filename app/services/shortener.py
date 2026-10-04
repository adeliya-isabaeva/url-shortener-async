import random
import string
from typing import Optional
from fastapi import HTTPException
from app.services.redis_client import r
from dotenv import load_dotenv
import os
from redis.exceptions import RedisError
import logging
logger = logging.getLogger(__name__)

load_dotenv()  # читает .env и делает переменные доступными через os.getenv
LINK_TTL_SECONDS = int(os.getenv("LINK_TTL_SECONDS", "86400"))

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

async def generate_unique_code(max_attempts: int = 5) -> str:
    for attempt in range(max_attempts):
        code = generate_short_code()
        try:
            if not await r.exists(f"code:{code}"):
                return code
        except RedisError as e:
            # Если Redis недоступен — сразу отдаём понятный 503
            logger.error("Redis недоступен при проверке существования кода (попытка %d): %s", attempt, e, exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Сервис временно недоступен"
            )

    # Эта ошибка остаётся 500, но она про «не смогли подобрать код», а не про Redis
    raise HTTPException(
        status_code=500,
        detail="Не удалось сгенерировать уникальный код. Попробуйте ещё раз."
    )

async def save_url(code: str, url: str) -> None:
    try:
        await r.setex(f"code:{code}", LINK_TTL_SECONDS, url)
    except RedisError as e:
        logger.error("Ошибка Redis при сохранении URL: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Сервис временно недоступен")

async def get_url(code: str) -> Optional[str]:
    try:
        result = await r.get(f"code:{code}")
        return result
    except RedisError as e:
        logger.error("Ошибка Redis при получении URL: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Сервис временно недоступен")