from io import BytesIO

import pytest
from fastapi import UploadFile

from app.secure_upload import SecureUploadError, validate_upload


class TestUploadFile(UploadFile):
    """Подкласс UploadFile для тестов, позволяющий устанавливать content_type."""

    def __init__(self, filename: str, file: BytesIO, content_type: str):
        super().__init__(filename=filename, file=file)
        self._content_type = content_type

    @property
    def content_type(self):
        return self._content_type


def make_upload(content: bytes, content_type: str) -> UploadFile:
    return TestUploadFile(
        filename="test.bin",
        file=BytesIO(content),
        content_type=content_type,
    )


def test_secure_upload_accepts_small_allowed_file():
    upload = make_upload(b"x" * 10, "text/csv")

    # Маленький файл с разрешённым типом должен проходить без ошибок
    validate_upload(
        upload,
        max_size_bytes=1024,
        allowed_content_types=("text/csv",),
    )


def test_secure_upload_rejects_too_big_file():
    upload = make_upload(b"x" * 2048, "text/csv")

    # Файл больше лимита должен быть отклонён
    with pytest.raises(SecureUploadError):
        validate_upload(
            upload,
            max_size_bytes=1024,
            allowed_content_types=("text/csv",),
        )


def test_secure_upload_rejects_disallowed_content_type():
    upload = make_upload(b"x" * 10, "application/octet-stream")

    # Файл с недопустимым content-type должен быть отклонён
    with pytest.raises(SecureUploadError):
        validate_upload(
            upload,
            max_size_bytes=1024,
            allowed_content_types=("text/csv",),
        )


def test_upload_rejects_path_traversal_in_filename():
    """Проверяет, что filename с path traversal последовательностями отклоняется."""
    # Unix-style path traversal
    upload = TestUploadFile(
        filename="../../../etc/passwd",
        file=BytesIO(b"x" * 10),
        content_type="text/csv",
    )
    with pytest.raises(SecureUploadError) as exc_info:
        validate_upload(
            upload, max_size_bytes=1024, allowed_content_types=("text/csv",)
        )
    assert "path traversal" in str(exc_info.value).lower()

    # Windows-style path traversal
    upload = TestUploadFile(
        filename="..\\..\\windows\\system32",
        file=BytesIO(b"x" * 10),
        content_type="text/csv",
    )
    with pytest.raises(SecureUploadError) as exc_info:
        validate_upload(
            upload, max_size_bytes=1024, allowed_content_types=("text/csv",)
        )
    assert "path traversal" in str(exc_info.value).lower()


def test_upload_rejects_absolute_path_in_filename():
    """Проверяет, что абсолютные пути в filename отклоняются."""
    # Unix absolute path
    upload = TestUploadFile(
        filename="/etc/passwd",
        file=BytesIO(b"x" * 10),
        content_type="text/csv",
    )
    with pytest.raises(SecureUploadError) as exc_info:
        validate_upload(
            upload, max_size_bytes=1024, allowed_content_types=("text/csv",)
        )
    assert "absolute" in str(exc_info.value).lower()

    # Windows absolute path
    upload = TestUploadFile(
        filename="C:\\Windows\\system32",
        file=BytesIO(b"x" * 10),
        content_type="text/csv",
    )
    with pytest.raises(SecureUploadError) as exc_info:
        validate_upload(
            upload, max_size_bytes=1024, allowed_content_types=("text/csv",)
        )
    assert "absolute" in str(exc_info.value).lower()


def test_upload_accepts_safe_filename():
    """Проверяет, что безопасные имена файлов принимаются."""
    upload = TestUploadFile(
        filename="my-deck-import.csv",
        file=BytesIO(b"x" * 10),
        content_type="text/csv",
    )
    # Не должно быть исключения
    validate_upload(upload, max_size_bytes=1024, allowed_content_types=("text/csv",))
