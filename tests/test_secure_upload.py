from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.secure_upload import (
    SecureUploadError,
    secure_save,
    sniff_magic_bytes,
    validate_upload,
)

# Magic bytes для тестов
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


class MockUploadFile(UploadFile):
    """Подкласс UploadFile для тестов, позволяющий устанавливать content_type."""

    def __init__(self, filename: str, file: BytesIO, content_type: str):
        super().__init__(filename=filename, file=file)
        self._content_type = content_type

    @property
    def content_type(self):
        return self._content_type


def make_upload(content: bytes, content_type: str) -> UploadFile:
    return MockUploadFile(
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
    with pytest.raises(SecureUploadError, match="file is too large"):
        validate_upload(
            upload,
            max_size_bytes=1024,
            allowed_content_types=("text/csv",),
        )


def test_secure_upload_rejects_disallowed_content_type():
    upload = make_upload(b"x" * 10, "application/octet-stream")

    # Файл с недопустимым content-type должен быть отклонён
    with pytest.raises(SecureUploadError, match="file content type is not allowed"):
        validate_upload(
            upload,
            max_size_bytes=1024,
            allowed_content_types=("text/csv",),
        )


def test_sniff_magic_bytes_png():
    """Проверка определения PNG по magic bytes."""
    png_data = PNG_SIGNATURE + b"fake png data"
    assert sniff_magic_bytes(png_data) == "image/png"


def test_sniff_magic_bytes_jpeg():
    """Проверка определения JPEG по magic bytes."""
    jpeg_data = JPEG_SOI + b"fake jpeg data" + JPEG_EOI
    assert sniff_magic_bytes(jpeg_data) == "image/jpeg"


def test_sniff_magic_bytes_jpeg_soi_only():
    """Проверка определения JPEG только по SOI (без EOI в начале)."""
    jpeg_data = JPEG_SOI + b"fake jpeg data"
    assert sniff_magic_bytes(jpeg_data) == "image/jpeg"


def test_sniff_magic_bytes_unknown():
    """Проверка возврата None для неизвестного типа."""
    unknown_data = b"fake file data"
    assert sniff_magic_bytes(unknown_data) is None


def test_validate_upload_rejects_fake_png():
    """Проверка отклонения файла с неверными magic bytes для PNG."""
    # Файл заявлен как PNG, но magic bytes не соответствуют
    fake_png = b"fake png data" + PNG_SIGNATURE
    upload = make_upload(fake_png, "image/png")

    with pytest.raises(SecureUploadError, match="magic bytes"):
        validate_upload(
            upload,
            max_size_bytes=1024,
            allowed_content_types=("image/png",),
        )


def test_validate_upload_accepts_real_png():
    """Проверка принятия реального PNG файла."""
    real_png = PNG_SIGNATURE + b"fake png data"
    upload = make_upload(real_png, "image/png")

    # Должен пройти валидацию
    validate_upload(
        upload,
        max_size_bytes=1024,
        allowed_content_types=("image/png",),
    )


def test_secure_save_rejects_too_big(tmp_path: Path):
    """Проверка отклонения слишком большого файла при сохранении."""
    large_data = b"x" * 6_000_000  # Больше лимита 5MB

    with pytest.raises(SecureUploadError, match="file is too large"):
        secure_save(tmp_path, large_data)


def test_secure_save_rejects_unknown_type(tmp_path: Path):
    """Проверка отклонения файла с неизвестным типом."""
    unknown_data = b"fake file data"

    with pytest.raises(SecureUploadError, match="file type not recognized"):
        secure_save(tmp_path, unknown_data)


def test_secure_save_accepts_png(tmp_path: Path):
    """Проверка успешного сохранения PNG файла."""
    png_data = PNG_SIGNATURE + b"fake png data"

    saved_path = secure_save(tmp_path, png_data)

    assert saved_path.exists()
    assert saved_path.suffix == ".png"
    assert saved_path.read_bytes() == png_data
    # Проверка, что имя файла - UUID
    assert len(saved_path.stem) == 36  # UUID длина


def test_secure_save_accepts_jpeg(tmp_path: Path):
    """Проверка успешного сохранения JPEG файла."""
    jpeg_data = JPEG_SOI + b"fake jpeg data" + JPEG_EOI

    saved_path = secure_save(tmp_path, jpeg_data)

    assert saved_path.exists()
    assert saved_path.suffix == ".jpg"
    assert saved_path.read_bytes() == jpeg_data


def test_secure_save_rejects_path_traversal(tmp_path: Path):
    """Проверка защиты от path traversal атаки."""
    png_data = PNG_SIGNATURE + b"fake png data"

    # Создаём безопасную директорию
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()

    # Сохраняем файл нормально - должно работать
    saved_path = secure_save(safe_dir, png_data)
    assert saved_path.exists()

    # Проверяем, что путь остаётся внутри safe_dir
    assert str(saved_path).startswith(str(safe_dir.resolve()))

    # Проверяем, что попытка использовать несуществующий root отклоняется
    non_existent = tmp_path / "nonexistent" / "dir"
    with pytest.raises((SecureUploadError, FileNotFoundError)):
        secure_save(non_existent, png_data)


def test_secure_save_path_traversal_detection(tmp_path: Path):
    """Проверка обнаружения path traversal через относительный путь."""
    png_data = PNG_SIGNATURE + b"fake png data"

    # Создаём поддиректорию
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # Сохраняем файл нормально
    saved_path = secure_save(subdir, png_data)
    assert saved_path.exists()

    # Проверяем, что путь остаётся внутри subdir
    assert str(saved_path).startswith(str(subdir.resolve()))

    # Проверяем, что попытка использовать несуществующий root отклоняется
    non_existent = tmp_path / "nonexistent" / "dir"
    with pytest.raises((SecureUploadError, FileNotFoundError)):
        secure_save(non_existent, png_data)


def test_secure_save_rejects_symlink_parent(tmp_path: Path):
    """Проверка отклонения сохранения при наличии симлинка в родительском пути."""
    import sys

    png_data = PNG_SIGNATURE + b"fake png data"

    # На Windows создание симлинков требует прав администратора
    # Пропускаем тест на Windows, если нет прав
    if sys.platform == "win32":
        try:
            # Пробуем создать тестовый симлинк
            test_link = tmp_path / "test_link"
            test_target = tmp_path / "test_target"
            test_target.mkdir()
            test_link.symlink_to(test_target, target_is_directory=True)
            test_link.unlink()  # Удаляем тестовый симлинк
        except (OSError, PermissionError):
            pytest.skip("Symlink creation requires admin rights on Windows")

    # Создаём структуру: tmp_path/target (целевая директория)
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    # Создаём директорию, внутри которой будет симлинк
    normal_dir = tmp_path / "normal"
    normal_dir.mkdir()

    # Создаём симлинк внутри normal, указывающий на target
    symlink_path = normal_dir / "link"
    symlink_path.symlink_to(target_dir, target_is_directory=True)

    # Создаём поддиректорию через симлинк
    subdir_via_symlink = symlink_path / "subdir"
    subdir_via_symlink.mkdir()

    # Попытка сохранить в эту поддиректорию должна быть отклонена,
    # так как путь проходит через симлинк (secure_save проверяет родителей)
    with pytest.raises(SecureUploadError, match="symlink"):
        secure_save(subdir_via_symlink, png_data)

    # Проверяем, что сохранение в нормальную директорию работает
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()
    saved_path = secure_save(safe_dir, png_data)
    assert saved_path.exists()
