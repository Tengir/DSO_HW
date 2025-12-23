from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_deck_success():
    payload = {
        "title": "My first deck",
        "description": "Basics",
        "source_lang": "EN",
        "target_lang": "RU",
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "deck" in body
    deck = body["deck"]
    assert deck["title"] == payload["title"]
    assert deck["source_lang"] == "en"
    assert deck["target_lang"] == "ru"


def test_create_deck_validation_error():
    payload = {
        "title": "",
        "source_lang": "e",
        "target_lang": "ru",
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_create_deck_rejects_extra_fields():
    """Проверка отклонения лишних полей (extra='forbid')."""
    payload = {
        "title": "My deck",
        "description": "Test",
        "source_lang": "en",
        "target_lang": "ru",
        "extra_field": "should be rejected",
    }
    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
