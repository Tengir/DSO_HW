import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_error_uses_problem_details():
    payload = {
        "title": "",
        "source_lang": "e",
        "target_lang": "ru",
    }

    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert "error" in body
    problem = body["error"]

    # Старое поле code осталось для обратной совместимости
    assert problem["code"] == "validation_error"

    # Новые поля из RFC7807-совместного формата
    assert problem["status"] == 422
    assert problem["title"] == "Validation error"
    assert "detail" in problem
    assert "type" in problem


def test_error_contains_correlation_id():
    """Проверка наличия correlation_id в ответе с ошибкой."""
    payload = {
        "title": "",
        "source_lang": "e",
        "target_lang": "ru",
    }

    response = client.post("/api/v1/decks", json=payload)
    assert response.status_code == 422

    body = response.json()
    problem = body["error"]

    # Проверка наличия correlation_id
    assert "correlation_id" in problem
    correlation_id = problem["correlation_id"]

    # Проверка формата UUID
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(uuid_pattern, correlation_id, re.IGNORECASE) is not None


def test_error_correlation_id_is_unique():
    """Проверка, что correlation_id уникален для каждого запроса."""
    payload = {
        "title": "",
        "source_lang": "e",
        "target_lang": "ru",
    }

    response1 = client.post("/api/v1/decks", json=payload)
    response2 = client.post("/api/v1/decks", json=payload)

    assert response1.status_code == 422
    assert response2.status_code == 422

    correlation_id1 = response1.json()["error"]["correlation_id"]
    correlation_id2 = response2.json()["error"]["correlation_id"]

    # Каждый запрос должен иметь уникальный correlation_id
    assert correlation_id1 != correlation_id2


def test_error_masks_email_in_detail():
    """Проверка маскирования email в деталях ошибки."""
    from app.errors import mask_pii

    # Тест функции маскирования напрямую
    text_with_email = "User email: student@example.com failed"
    masked = mask_pii(text_with_email)

    assert "student***@example.com" in masked
    assert "student@example.com" not in masked


def test_error_masks_jwt_token_in_detail():
    """Проверка маскирования JWT токена в деталях ошибки."""
    from app.errors import mask_pii

    # Тест функции маскирования напрямую
    text_with_token = (
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    )
    masked = mask_pii(text_with_token)

    assert "Bearer ***" in masked or "***" in masked
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked


def test_error_masks_password_in_detail():
    """Проверка маскирования пароля в деталях ошибки."""
    from app.errors import mask_pii

    # Тест функции маскирования напрямую
    text_with_password = "password=secret123"
    masked = mask_pii(text_with_password)

    assert "password=***" in masked
    assert "secret123" not in masked


def test_error_masks_multiple_pii():
    """Проверка маскирования нескольких типов PII одновременно."""
    from app.errors import mask_pii

    text = "User student@example.com with password=secret123 and token=eyJhbGci"
    masked = mask_pii(text)

    assert "student***@example.com" in masked
    assert "password=***" in masked
    assert "student@example.com" not in masked
    assert "secret123" not in masked
