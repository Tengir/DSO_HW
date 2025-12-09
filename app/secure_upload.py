from __future__ import annotations

import os
from typing import Iterable, Tuple

from fastapi import UploadFile

from app.config import settings


class SecureUploadError(ValueError):
    """Ошибки, связанные с валидацией загружаемых файлов."""


def _get_file_size(upload_file: UploadFile) -> int:
    """Возвращает размер файла в байтах, не оставляя курсор в конце."""
    file_obj = upload_file.file
    current_pos = file_obj.tell()
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(current_pos, os.SEEK_SET)
    return size


def _normalize_types(types: Iterable[str]) -> Tuple[str, ...]:
    return tuple(t.strip().lower() for t in types)


def validate_upload(
    upload_file: UploadFile,
    max_size_bytes: int | None = None,
    allowed_content_types: Iterable[str] | None = None,
) -> None:
    """Проверяет базовые ограничения для загружаемого файла.

    - Размер не должен превышать max_size_bytes;
    - MIME-тип должен быть в списке допустимых.

    Если проверка не проходит, выбрасывается SecureUploadError.
    """
    size_limit = max_size_bytes or settings.max_upload_size_bytes
    allowed_types = _normalize_types(
        allowed_content_types or settings.allowed_upload_content_types
    )

    size = _get_file_size(upload_file)
    if size > size_limit:
        raise SecureUploadError("file is too large")

    content_type = (upload_file.content_type or "").lower()
    if content_type not in allowed_types:
        raise SecureUploadError("file content type is not allowed")
