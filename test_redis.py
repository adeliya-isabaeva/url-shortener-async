import asyncio
import redis.asyncio as redis


async def test():
    r = redis.from_url("redis://localhost:6379", decode_responses=True)

    # Проверяем запись и чтение
    await r.set("test_key", "test_value")
    val = await r.get("test_key")
    print(f"test_key -> {val}")

    # Проверяем, виден ли ключ из POST
    val2 = await r.get("mYMafI")
    print(f"mYMafI -> {val2}")

    # Сколько всего ключей
    keys = await r.keys("*")
    print(f"all keys: {keys}")


asyncio.run(test())
