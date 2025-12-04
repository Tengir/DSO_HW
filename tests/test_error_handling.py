import json

from fastapi.testclient import TestClient

from app.main import app

# В тестах не поднимаем исключения на уровне клиента, чтобы проверить JSON-ответ
client = TestClient(app, raise_server_exceptions=False)


def test_unhandled_exception_returns_problem_details():
    """Проверяет, что необработанное исключение возвращает RFC7807-формат без stack trace."""

    # Создаём endpoint, который выбрасывает необработанное исключение
    @app.get("/test-unhandled-error")
    def test_unhandled_error():
        raise ValueError("This is a test error")

    response = client.get("/test-unhandled-error")
    assert response.status_code == 500

    body = response.json()
    assert "error" in body
    problem = body["error"]

    # Проверяем RFC7807-формат
    assert problem["status"] == 500
    assert problem["title"] == "Internal server error"
    assert "detail" in problem
    assert problem["code"] == "internal_error"
    assert "type" in problem

    # Проверяем, что stack trace НЕ попал в ответ
    body_str = json.dumps(body)
    assert "traceback" not in body_str.lower()
    assert (
        "file" not in body_str.lower()
        or "file" not in problem.get("detail", "").lower()
    )
    assert (
        "line" not in body_str.lower()
        or "line" not in problem.get("detail", "").lower()
    )


def test_error_response_contains_no_file_paths():
    """Проверяет, что ответ об ошибке не содержит путей к файлам проекта."""

    @app.get("/test-file-path-leak")
    def test_file_path_leak():
        # Симулируем ошибку, которая могла бы раскрыть путь
        raise RuntimeError("Error in /app/main.py:123")

    response = client.get("/test-file-path-leak")
    assert response.status_code == 500

    body = response.json()
    body_str = json.dumps(body)

    # Проверяем, что пути к файлам не попали в ответ
    assert "/app/" not in body_str
    assert "main.py" not in body_str
    assert "DSO_HW" not in body_str
