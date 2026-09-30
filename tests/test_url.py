from app.main import app
from fastapi.testclient import TestClient
import requests

client = TestClient(app)

def test_create_short_link_with_location():
    payload = {"url": "https://example.com"}
    response = client.post("/api/v1/shorten", json=payload)

    assert response.status_code == 201  # Важно: именно 201
    data = response.json()

    # Проверяем JSON
    assert "short_code" in data
    code = data["short_code"]

    # Проверяем заголовок Location
    assert "Location" in response.headers
    assert response.headers["Location"] == f"/{code}"

def test_create_short_link_invalid_url():
    payload = {"url": "dark hair"}
    response = client.post("/api/v1/shorten", json=payload)

    assert response.status_code == 422, f"Ожидался 422, но пришёл {response.status_code}"
    data = response.json()
    # Опционально: можно проверить, что в ответе есть детали ошибки валидации
    assert "detail" in data or any("error" in k.lower() for k in data.keys())

BASE_URL = "http://localhost:8001"

def test_not_found_url():
    response = requests.get(f"{BASE_URL}/api/v1/notrealcode")
    assert response.status_code == 404
    data = response.json()
    # Проверяем, что есть осмысленное сообщение об ошибке
    message = data.get("detail") or data.get("error") or str(data)
    assert "not found" in message.lower()
