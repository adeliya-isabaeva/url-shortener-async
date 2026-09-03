import random
import string
from app.services.redis_client import redis_client
from typing import Optional

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


async def save_url(code: str, url: str) -> None:
    await redis_client.set(code, url)


async def get_url(code: str) -> Optional[str]:
    print(f"DEBUG get_url: looking for code='{code}'")
    result = await redis_client.get(code)
    print(f"DEBUG get_url: result='{result}'")
    return result
