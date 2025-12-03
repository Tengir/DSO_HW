from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type_: str = "about:blank",
    instance: Optional[str] = None,
    code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Собирает RFC7807-совместный объект ошибки внутри поля `error`.

    Мы сохраняем поле `code`, чтобы не ломать текущие тесты и NFR-04.
    """
    problem: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
    }
    if detail is not None:
        problem["detail"] = detail
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
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Возвращает JSONResponse с объектом ошибки в формате problem details."""
    body = build_problem(
        status_code=status_code,
        title=title,
        detail=detail,
        type_=type_,
        instance=str(request.url),
        code=code,
        extra=extra,
    )
    return JSONResponse(status_code=status_code, content=body)
