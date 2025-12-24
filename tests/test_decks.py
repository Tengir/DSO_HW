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
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_deck_crud_flow():
    headers = get_auth_headers()
    payload = {
        "title": "My deck",
        "description": "Basics",
        "source_lang": "EN",
        "target_lang": "RU",
    }

    response = client.post("/api/v1/decks", json=payload, headers=headers)
    assert response.status_code == 201
    deck = response.json()["deck"]

    response = client.get("/api/v1/decks", headers=headers)
    assert response.status_code == 200
    items = response.json()["decks"]["items"]
    assert any(item["id"] == deck["id"] for item in items)

    response = client.get(f"/api/v1/decks/{deck['id']}", headers=headers)
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/decks/{deck['id']}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["deck"]["title"] == "Updated"

    response = client.delete(f"/api/v1/decks/{deck['id']}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/api/v1/decks/{deck['id']}", headers=headers)
    assert response.status_code == 404


def test_deck_owner_only_access():
    owner_headers = get_auth_headers()
    other_headers = get_auth_headers()

    response = client.post(
        "/api/v1/decks",
        json={
            "title": "Private deck",
            "source_lang": "en",
            "target_lang": "ru",
        },
        headers=owner_headers,
    )
    deck_id = response.json()["deck"]["id"]

    response = client.get(f"/api/v1/decks/{deck_id}", headers=other_headers)
    assert response.status_code == 403
