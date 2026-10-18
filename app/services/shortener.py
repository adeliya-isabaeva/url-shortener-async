import random
import string
from typing import Optional
from fastapi import HTTPException
from app.services.redis_client import get_redis_client  # <-- ВАЖНО: импортируем не r, а get_redis_client
from dotenv import load_dotenv
import os
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

load_dotenv()
LINK_TTL_SECONDS = int(os.getenv("LINK_TTL_SECONDS", "86400"))

from app.services.redis_sync import get_redis_sync

async def get_total_count():
    r = get_redis_sync()
    # Считаем все ключи, начинающиеся с "code:"
    return len(r.keys("code:*"))

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


async def generate_unique_code(max_attempts: int = 5) -> str:
    # Получаем клиент один раз перед циклом (или можно внутри, если боишься таймаутов)
    client = await get_redis_client()

    for attempt in range(max_attempts):
        code = generate_short_code()
        try:
            # Теперь вызываем exists у клиента, а не у функции r
            exists = await client.exists(f"code:{code}")
            if not exists:
                return code
        except RedisError as e:
            logger.error("Redis недоступен при проверке существования кода (попытка %d): %s", attempt, e, exc_info=True)
            raise

    logger.error("Не удалось подобрать уникальный код после %d попыток", max_attempts)
    raise RuntimeError("Не удалось сгенерировать уникальный код")


async def save_url(code: str, url: str) -> None:
    client = await get_redis_client()
    try:
        # Сначала сохраняем саму ссылку
        await client.set(f"code:{code}", str(url), ex=LINK_TTL_SECONDS)

        # --- ВОТ ЭТА СТРОКА — СЧЁТЧИК (асинхронно!) ---
        await client.incr("counter:shortened")
        # -----------------------------------------------
    except RedisError as e:
        logger.error("Ошибка Redis при сохранении URL: %s", e, exc_info=True)
        raise


async def get_url(code: str) -> Optional[str]:
    client = await get_redis_client()  # <-- Получаем клиента
    try:
        result = await client.get(f"code:{code}")
        return result
    except RedisError as e:
        logger.error("Ошибка Redis при получении URL: %s", e, exc_info=True)
        raise
