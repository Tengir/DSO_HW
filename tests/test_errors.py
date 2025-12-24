from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_auth_headers():
    email = f"user-{uuid4()}@example.com"
    password = "Password123"
    register_payload = {
        "email": email,
        "password": password,
        "locale": "ru",
        "proficiency_level": "b1",
    }
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201

    login_payload = {"email": email, "password": password}
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_deck_success():
    headers = get_auth_headers()
    payload = {
        "title": "My first deck",
        "description": "Basics",
        "source_lang": "EN",
        "target_lang": "RU",
    }
    response = client.post("/api/v1/decks", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert "deck" in body
    deck = body["deck"]
    assert deck["title"] == payload["title"]
    assert deck["source_lang"] == "en"
    assert deck["target_lang"] == "ru"


def test_create_deck_validation_error():
    headers = get_auth_headers()
    payload = {
        "title": "",
        "source_lang": "e",
        "target_lang": "ru",
    }
    response = client.post("/api/v1/decks", json=payload, headers=headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"


def test_create_deck_rejects_extra_fields():
    """Проверка отклонения лишних полей (extra='forbid')."""
    headers = get_auth_headers()
    payload = {
        "title": "My deck",
        "description": "Test",
        "source_lang": "en",
        "target_lang": "ru",
        "extra_field": "should be rejected",
    }
    response = client.post("/api/v1/decks", json=payload, headers=headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
