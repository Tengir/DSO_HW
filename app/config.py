from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Settings:
    """Простые настройки приложения, читаемые из переменных окружения.

    Для учебного проекта используем безопасные дефолты, но в бою
    значения должны приходить из env.
    """

    secret_key: str = field(
        default_factory=lambda: os.getenv("APP_SECRET_KEY", "dev-secret-key")
    )
    max_upload_size_bytes: int = field(
        default_factory=lambda: int(
            os.getenv("APP_MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024))
        )
    )
    allowed_upload_content_types: Tuple[str, ...] = (
        "text/csv",
        "application/json",
    )


settings = Settings()
