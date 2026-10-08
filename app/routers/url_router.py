from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl
import redis.asyncio as redis
import random
import string
from app.services.shortener import save_url, get_url, generate_unique_code
import os
import logging
import redis

logger = logging.getLogger(__name__)

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class URLRequest(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    short_code: str
    original_url: HttpUrl

@router.post(
    "/shorten",
    summary="Создать короткую ссылку",
    description="Принимает URL, проверяет формат, генерирует короткий код и сохраняет в Redis с TTL.",
    response_model=URLResponse,
    status_code=201,
)
async def shorten_url(request: URLRequest, response: Response):
    logger.info("Получен URL: %s", request.url)

    code = await generate_unique_code()
    await save_url(code, request.url)
    logger.info("Сохранено: code=%s -> %s", code, request.url)

    response.headers["Location"] = f"/{code}"
    return URLResponse(short_code=code, original_url=request.url)


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
