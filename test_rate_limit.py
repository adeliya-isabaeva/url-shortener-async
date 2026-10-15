import requests

base = "http://localhost:8001"
endpoint = "/api/v1/shorten"  # <-- важно: твой префикс из include_router

print(f"Начинаю тест rate limiting: 110 запросов к {base}{endpoint}")

for i in range(110):
    resp = requests.post(
        f"{base}{endpoint}",
        json={"url": "https://example.com"}
    )
    detail = resp.json().get("detail", "")
    print(f"{i}: status={resp.status_code}, detail='{detail}'")
