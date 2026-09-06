import random
import string
from typing import Optional
from fastapi import HTTPException
from app.services.redis_client import r

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

async def generate_unique_code(max_attempts: int = 5) -> str:
    for attempt in range(max_attempts):
        code = generate_short_code()
        if not await r.exists(f"code:{code}"):
            return code
    raise HTTPException(
        status_code=500,
        detail="Не удалось сгенерировать уникальный код. Попробуйте ещё раз."
    )

async def save_url(code: str, url: str) -> None:
    await r.setex(f"code:{code}", 86400, url)

async def get_url(code: str) -> Optional[str]:
    print(f"DEBUG get_url: looking for code='{code}'")
    result = await r.get(f"code:{code}")
    print(f"DEBUG get_url: result='{result}'")
    return result
