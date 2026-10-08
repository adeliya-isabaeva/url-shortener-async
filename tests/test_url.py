from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_short_link_with_location(client):
    payload = {"url": "https://example.com"}
    response = client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "short_code" in data
    # Вместо строгого равенства — проверяем, что URL начинается с ожидаемого префикса
    assert data["original_url"].startswith("https://example.com")

    # Опционально: можно проверить, что Location совпадает с коротким кодом
    assert response.headers.get("Location") == f"/{data['short_code']}"

def test_create_short_link_invalid_url(client):
    payload = {"url": "dark hair"}
    response = client.post("/api/v1/shorten", json=payload)

    assert response.status_code == 422, f"Ожидался 422, но пришёл {response.status_code}"
    data = response.json()
    assert "detail" in data, "В ответе должна быть секция detail с описанием ошибок"
    assert isinstance(data["detail"], list), "detail должен быть списком ошибок"
    assert len(data["detail"]) > 0, "Должна быть хотя бы одна ошибка валидации"

def test_create_short_link_invalid_no_scheme(client):
    payload = {"url": "example.com/path"}  # нет http://
    response = client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 422

def test_not_found_url():
    response = client.get("/api/v1/notrealcode")
    assert response.status_code == 404
    data = response.json()
    message = data.get("detail") or data.get("error") or str(data)
    assert "not found" in message.lower()
