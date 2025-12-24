from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_user(email: str, password: str):
    payload = {
        "email": email,
        "password": password,
        "locale": "ru",
        "proficiency_level": "b1",
    }
    return client.post("/api/v1/auth/register", json=payload)


def login_user(email: str, password: str):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def test_register_and_login_success():
    email = f"user-{uuid4()}@example.com"
    password = "Password123"

    response = register_user(email, password)
    assert response.status_code == 201
    body = response.json()["user"]
    assert body["email"] == email
    assert body["role"] == "user"

    response = login_user(email, password)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials():
    response = login_user("missing@example.com", "Password123")
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "unauthorized"
