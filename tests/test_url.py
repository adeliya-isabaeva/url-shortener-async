# tests/test_url.py
import pytest
import requests

BASE_URL = "http://localhost:8000"

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
