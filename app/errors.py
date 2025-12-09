from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


def mask_pii(text: str) -> str:
    """Маскирует персональные данные в тексте.

    Маскирует:
    - Email адреса (user@example.com -> u***@example.com)
    - JWT токены (Bearer eyJ... -> Bearer ***)
    - Пароли (password=secret -> password=***)

    Args:
        text: Текст для маскирования.

    Returns:
        Текст с замаскированными PII.
    """
    if not text:
        return text

    # Маскирование email
    email_pattern = r"\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"
    text = re.sub(email_pattern, r"\1***@\2", text)

    # Маскирование JWT токенов (Bearer token или просто длинный токен)
    jwt_pattern = r"(Bearer\s+)?([A-Za-z0-9_-]{20,})"
    text = re.sub(jwt_pattern, lambda m: f"{m.group(1) or ''}***", text)

    # Маскирование паролей в строках вида password=xxx
    password_pattern = r"(password|pwd|secret|token)\s*[=:]\s*[^\s&]+"
    text = re.sub(password_pattern, r"\1=***", text, flags=re.IGNORECASE)

    return text


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type_: str = "about:blank",
    instance: Optional[str] = None,
    code: Optional[str] = None,
    correlation_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Собирает RFC7807-совместный объект ошибки внутри поля `error`.

    Мы сохраняем поле `code`, чтобы не ломать текущие тесты и NFR-04.
    Добавлен correlation_id для трейсабельности запросов.
    """
    # Генерируем correlation_id, если не передан
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    # Маскируем PII в detail
    masked_detail = mask_pii(detail) if detail else None

    problem: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
        "correlation_id": correlation_id,
    }
    if masked_detail is not None:
        problem["detail"] = masked_detail
    if instance is not None:
        problem["instance"] = instance
    if code is not None:
        problem["code"] = code
    if extra:
        problem.update(extra)
    return {"error": problem}


def problem_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type_: str = "about:blank",
    code: Optional[str] = None,
    correlation_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Возвращает JSONResponse с объектом ошибки в формате problem details.

    Включает correlation_id для трейсабельности и маскирует PII в detail.
    """
    body = build_problem(
        status_code=status_code,
        title=title,
        detail=detail,
        type_=type_,
        instance=str(request.url),
        code=code,
        correlation_id=correlation_id,
        extra=extra,
    )
    return JSONResponse(status_code=status_code, content=body)
