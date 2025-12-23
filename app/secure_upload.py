from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Iterable, Tuple

from fastapi import UploadFile

from app.config import settings

# Magic bytes для проверки реального типа файла
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"
MAX_FILE_SIZE = 5_000_000  # 5MB


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


def _read_file_header(upload_file: UploadFile, length: int = 16) -> bytes:
    """Читает первые байты файла для проверки magic bytes."""
    file_obj = upload_file.file
    current_pos = file_obj.tell()
    file_obj.seek(0, os.SEEK_SET)
    header = file_obj.read(length)
    file_obj.seek(current_pos, os.SEEK_SET)
    return header


def sniff_magic_bytes(data: bytes) -> str | None:
    """Определяет MIME-тип по magic bytes.

    Returns:
        MIME-тип или None, если тип не распознан.
    """
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    if data.startswith(JPEG_SOI):
        # JPEG может не иметь EOI в начале, проверяем только SOI
        return "image/jpeg"
    return None


def _normalize_types(types: Iterable[str]) -> Tuple[str, ...]:
    return tuple(t.strip().lower() for t in types)


def validate_upload(
    upload_file: UploadFile,
    max_size_bytes: int | None = None,
    allowed_content_types: Iterable[str] | None = None,
) -> None:
    """Проверяет базовые ограничения для загружаемого файла.

    - Размер не должен превышать max_size_bytes;
    - MIME-тип должен быть в списке допустимых;
    - Проверка magic bytes для изображений.

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

    # Проверка magic bytes для изображений
    if content_type.startswith("image/"):
        header = _read_file_header(upload_file, length=16)
        detected_type = sniff_magic_bytes(header)
        if not detected_type:
            raise SecureUploadError("file magic bytes do not match content type")
        if detected_type != content_type:
            raise SecureUploadError("file magic bytes do not match content type")


def secure_save(root: Path, data: bytes, max_size: int = MAX_FILE_SIZE) -> Path:
    """Безопасно сохраняет файл с проверками.

    - Проверка размера;
    - Проверка magic bytes;
    - Канонизация пути (защита от path traversal);
    - UUID-имя файла;
    - Проверка симлинков в родительских директориях.

    Args:
        root: Корневая директория для сохранения.
        data: Данные файла в байтах.
        max_size: Максимальный размер файла.

    Returns:
        Path к сохранённому файлу.

    Raises:
        SecureUploadError: При нарушении правил безопасности.
    """
    if len(data) > max_size:
        raise SecureUploadError("file is too large")

    # Проверка magic bytes
    detected_type = sniff_magic_bytes(data)
    if not detected_type:
        raise SecureUploadError("file type not recognized by magic bytes")

    # Определяем расширение по типу
    ext_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }
    ext = ext_map.get(detected_type, ".bin")

    # Проверка симлинков в пути root ДО разрешения (resolve разрешает симлинки)
    original_root = root
    # Проверяем, что сам root не является симлинком
    if original_root.is_symlink():
        raise SecureUploadError("symlink detected in parent path")
    # Проверяем все родительские директории на наличие симлинков
    # Важно: проверяем ДО resolve(), так как resolve() разрешает симлинки
    for parent in original_root.parents:
        try:
            if parent.is_symlink():
                raise SecureUploadError("symlink detected in parent path")
        except (OSError, ValueError):
            # Игнорируем ошибки при проверке несуществующих путей
            continue

    # Канонизация пути
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise SecureUploadError("root directory does not exist")

    # Генерируем UUID-имя
    filename = f"{uuid.uuid4()}{ext}"
    target_path = (root / filename).resolve()

    # Проверка path traversal: путь должен быть внутри root
    try:
        target_path.relative_to(root)
    except ValueError:
        raise SecureUploadError("path traversal detected")

    # Проверка симлинков в родительских директориях target_path
    # Проверяем все родительские директории до root включительно
    for parent in target_path.parents:
        if parent.is_symlink():
            raise SecureUploadError("symlink detected in parent path")
        if parent == root:
            break

    # Сохраняем файл
    target_path.write_bytes(data)
    return target_path
