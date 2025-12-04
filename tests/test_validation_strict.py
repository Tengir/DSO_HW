from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_deck_creation_rejects_extra_fields():
    """Проверяет, что лишние поля отклоняются (extra='forbid')."""
    payload = {
        "title": "My deck",
        "source_lang": "en",
        "target_lang": "ru",
        "extra_field": "should be rejected",  # Лишнее поле
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    # Проверяем, что в деталях ошибки есть информация о лишнем поле
    assert "extra_field" in str(body["error"].get("details", [])).lower()


def test_deck_creation_rejects_invalid_language_code():
    """Проверяет, что неверный код языка (не 2 символа) отклоняется."""
    payload = {
        "title": "My deck",
        "source_lang": "eng",  # 3 символа вместо 2
        "target_lang": "ru",
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    # Проверяем, что ошибка связана с source_lang
    details = body["error"].get("details", [])
    assert any("source_lang" in str(d).lower() for d in details)


def test_deck_creation_rejects_too_long_title():
    """Проверяет, что слишком длинный title отклоняется."""
    payload = {
        "title": "x" * 101,  # 101 символ, лимит 100
        "source_lang": "en",
        "target_lang": "ru",
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_deck_creation_accepts_valid_iso639_codes():
    """Проверяет, что валидные ISO 639-1 коды (2 символа) принимаются."""
    payload = {
        "title": "My deck",
        "source_lang": "EN",  # Будет нормализован в "en"
        "target_lang": "RU",  # Будет нормализован в "ru"
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 201
    body = response.json()
    deck = body["deck"]
    assert deck["source_lang"] == "en"
    assert deck["target_lang"] == "ru"
