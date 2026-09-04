from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlparse
from pydantic import BaseModel
import redis.asyncio as redis
import random
import string
from app.services.shortener import save_url, get_url, generate_unique_code

router = APIRouter()

# Клиент Redis (имя 'redis' — из docker-compose)
r = redis.Redis(host="redis", port=6379, decode_responses=True)


class URLRequest(BaseModel):
    url: str


class URLResponse(BaseModel):
    short_code: str
    original_url: str

@router.post("/shorten", response_model=URLResponse)
async def shorten_url(request: URLRequest):
    print(f"🚀 ПОЛУЧЕН URL: '{request.url}'")

    parsed = urlparse(request.url)
    if not parsed.scheme or not parsed.netloc:
        print("⚠️ СРАБОТАЛА ПРОВЕРКА: URL невалиден!")
        raise HTTPException(
            status_code=422,
            detail="Неверный формат URL. Ссылка должна начинаться с http:// или https://"
        )

    code = await generate_unique_code()  # стало так
    await save_url(code, request.url)
    print(f"✅ Сохранено: code:{code} -> {request.url}")
    return URLResponse(short_code=code, original_url=request.url)


@router.get("/{short_code}")
async def redirect_url(short_code: str):
    original_url = await get_url(short_code)
    if original_url is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=original_url, status_code=302)
