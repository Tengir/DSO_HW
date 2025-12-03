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
