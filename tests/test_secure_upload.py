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
