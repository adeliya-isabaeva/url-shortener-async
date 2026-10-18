# app/routers/url_router.py
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from app.services.redis_client import get_redis_client
from app.services.shortener import generate_unique_code, get_url
import os
import logging
from app.services.shortener import get_total_count

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_URL_LENGTH = 200

# Читаем TTL из ENV, по умолчанию 3600 секунд (1 час), если не задано
try:
    LINK_TTL_SECONDS = int(os.getenv("LINK_TTL_SECONDS", "3600"))
except ValueError:
    logger.warning("LINK_TTL_SECONDS is not a valid integer, using default 3600")
    LINK_TTL_SECONDS = 3600


class URLRequest(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    short_code: str
    original_url: HttpUrl
    already_exists: bool = False

@router.get("/stats", summary="Статистика сервиса")
async def get_stats():
    total = await get_total_count()
    return {"total_shortened": total}

@router.post(
    "/shorten",
    summary="Создать короткую ссылку",
    description="Принимает URL, проверяет формат, генерирует короткий код и сохраняет в Redis с TTL.",
    response_model=URLResponse,
    status_code=201,
)
async def shorten_url(request: URLRequest, response: Response):
    url_str = str(request.url)
    logger.info("Получен URL: %s", url_str)

    if len(url_str) > MAX_URL_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL слишком длинный"
        )

    existing_key = f"url:{url_str}"

    # ВАЖНО: используем асинхронную функцию, которая сама умеет ждать Redis
    client = await get_redis_client()

    try:
        existing_code = await client.get(existing_key)
    except Exception as e:
        # Если даже после всех попыток get_redis_client не смог подключиться — это реальная авария
        logger.error("Не удалось получить данные из Redis: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Redis временно недоступен")

    if existing_code:
        return URLResponse(
            short_code=existing_code,
            original_url=request.url,
            already_exists=True,
        )

    # Генерация уникального short_code
    try:
        code = await generate_unique_code()
    except Exception as e:
        logger.error("Ошибка при генерации кода: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Сервис временно недоступен")

    code_key = f"code:{code}"

    # Сохраняем данные
    await client.set(code_key, url_str, ex=LINK_TTL_SECONDS)
    await client.set(existing_key, code, ex=LINK_TTL_SECONDS)

    response.headers["Location"] = f"/{code}"
    return URLResponse(
        short_code=code,
        original_url=request.url,
        already_exists=False,
    )

@router.get(
    "/{short_code}",
    summary="Перейти по короткой ссылке",
    description="По короткому коду находит оригинальный URL в Redis и делает HTTP 302 редирект. Если ссылка не найдена или истёк TTL — возвращает 404.",
    responses={
        302: {"description": "Редирект на оригинальный URL"},
        404: {"description": "Короткая ссылка не найдена или срок действия истёк"},
    },
)
async def redirect_url(short_code: str):
    original_url = await get_url(short_code)
    if original_url is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=original_url, status_code=302)


@router.get(
    "/stats",
    summary="Статистика сервиса",
    description="Возвращает общее количество созданных коротких ссылок.",
    response_model=dict,
)
async def get_stats():
    client = await get_redis_client()

    try:
        count = await client.get("counter:shortened")
        # Если ключа нет (ещё ни одной ссылки), Redis вернёт None
        total = int(count) if count is not None else 0
        return {"total_shortened": total}
    except Exception as e:
        logger.error("Ошибка получения статистики: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Не удалось получить статистику")
