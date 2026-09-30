from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
from urllib.parse import urlparse
from pydantic import BaseModel
import redis.asyncio as redis
import random
import string
from app.services.shortener import save_url, get_url, generate_unique_code
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Клиент Redis (имя 'redis' — из docker-compose)
r = redis.Redis(host="redis", port=6379, decode_responses=True)


class URLRequest(BaseModel):
    url: str


class URLResponse(BaseModel):
    short_code: str
    original_url: str

@router.post(
    "/shorten",
    summary="Создать короткую ссылку",
    description="Принимает URL, проверяет формат, генерирует короткий код и сохраняет в Redis с TTL.",
    response_model=URLResponse,
    status_code=201,
)
async def shorten_url(request: URLRequest, response: Response):
    # print(f" ПОЛУЧЕН URL: '{request.url}'")
    logger.info("Получен URL: %s", request.url)

    parsed = urlparse(request.url)
    if not parsed.scheme or not parsed.netloc:
        #print("СРАБОТАЛА ПРОВЕРКА: URL невалиден!")
        logger.warning("URL невалиден: %s", request.url)
        raise HTTPException(
            status_code=422,
            detail="Неверный формат URL. Ссылка должна начинаться с http:// или https://"
        )

    code = await generate_unique_code()  # стало так
    await save_url(code, request.url)
    #print(f" Сохранено: code:{code} -> {request.url}")
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
