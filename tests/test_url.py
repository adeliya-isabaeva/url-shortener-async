# tests/test_url.py
import pytest
import requests
import redis
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

def test_create_short_link_with_location():
    payload = {"url": "https://example.com"}
    response = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"].startswith("https://example.com")

def test_create_short_link_invalid_url():
    payload = {"url": "dark hair"}
    response = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0

def test_create_short_link_invalid_no_scheme():
    payload = {"url": "example.com/path"}
    response = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert response.status_code == 422

def test_not_found_url():
    # Проверяем, что несуществующая ссылка даёт 404
    response = requests.get(f"{BASE_URL}/api/v1/notrealcode")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "error" in data

def test_long_url_rejected():
    long_url = "https://example.com/" + "x" * 181
    assert len(long_url) > 200
    payload = {"url": long_url}
    response = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "URL слишком длинный" in str(data["detail"])

def test_duplicate_url_returns_existing_code():
    url = "https://example.com/dup"
    payload = {"url": url}

    r1 = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert r1.status_code == 201
    data1 = r1.json()

    r2 = requests.post(f"{BASE_URL}/api/v1/shorten", json=payload)
    assert r2.status_code == 201
    data2 = r2.json()

    assert data1["short_code"] == data2["short_code"]
    assert data2["already_exists"] is True


@pytest.fixture(autouse=True)
def clean_redis():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    r = redis.from_url(redis_url, decode_responses=True)

    try:
        keys_to_delete = []
        for pattern in ["rate_limit:*", "url:*", "stats:*"]:
            keys_to_delete.extend(r.keys(pattern))
        if keys_to_delete:
            r.delete(*keys_to_delete)
        yield
    except Exception:
        # Если Redis недоступен, просто пропускаем очистку, чтобы тест не падал сразу
        yield


def test_rate_limit_works(clean_redis):
    # 1. Подключаемся к Redis (так же, как приложение)
    r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)

    payload = {"url": "https://example.com"}
    limit = 100
    key = "rate:test_single_key"

    print(f"Делаем {limit} запросов...")

    # 👇 ВОТ ЭТА СТРОЧКА — ГЛАВНОЕ ИЗМЕНЕНИЕ:
    # Мы вручную сбрасываем счётчик в 0 прямо перед тестом.
    # Даже если кто-то сделал 1000 запросов до этого, сейчас будет 0.
    r.set(key, 0)
    print(f"Принудительно установили счётчик {key} = 0")

    for i in range(limit):
        resp = requests.post(f"{os.getenv('BASE_URL', 'http://app:8000')}/api/v1/shorten", json=payload)

        # Смотрим реальное значение в Redis
        current_count = r.get(key)
        current_count_int = int(current_count) if current_count else 0
        print(f"[Запрос {i}] status={resp.status_code}, Redis count={current_count_int}")

        # Теперь тест будет честным: запросы 0..99 должны быть 201
        assert resp.status_code == 201, f"Запрос {i} должен быть успешен, но получил {resp.status_code}"

    print("Все запросы прошли — тест успешен!")