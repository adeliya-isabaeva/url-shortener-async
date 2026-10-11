# app/services/redis_client.py
import os
import asyncio
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
_redis_client = None


async def get_redis_client():
    """Возвращает готовый клиент Redis. Если Redis не готов — ждёт и пробует снова."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    max_retries = 10
    delay = 2  # секунды между попытками

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Попытка подключения к Redis (попытка {attempt}/{max_retries})...")
            client = Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)

            # Сразу делаем ping, чтобы убедиться, что соединение реально работает
            await client.ping()

            _redis_client = client
            logger.info("Redis успешно подключён!")
            return _redis_client

        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}")
            if attempt == max_retries:
                logger.error("Все попытки исчерпаны. Redis недоступен.")
                raise
            # Ждём перед следующей попыткой
            await asyncio.sleep(delay)


# Для совместимости со старым кодом (если где-то вызывается r())
def r():
    # Эта функция теперь просто возвращает синхронный обёртку,
    # но лучше везде использовать async get_redis_client()
    # Если у тебя в роутере было r(), оставь эту заглушку,
    # но в идеале перепиши роутер на использование get_redis_client()
    return _redis_client or Redis.from_url(REDIS_URL, decode_responses=True)
