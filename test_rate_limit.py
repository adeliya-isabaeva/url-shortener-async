base = "http://app:8000"        # ✅ Работает: стучимся в сервис app на его внутреннем порту
endpoint = "/api/v1/shorten"

print(f"Начинаю тест rate limiting: 110 запросов к {base}{endpoint}")

for i in range(110):
    try:
        resp = requests.post(
            f"{base}{endpoint}",
            json={"url": "https://example.com"},
            timeout=5  # Добавим таймаут, чтобы не висело вечно
        )
        detail = resp.json().get("detail", "")
        print(f"{i}: status={resp.status_code}, detail='{detail}'")
    except Exception as e:
        print(f"{i}: ошибка соединения - {e}")
