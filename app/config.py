from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Tuple


class ConfigError(Exception):
    """Ошибка конфигурации: критический секрет не задан в проде."""


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

    def __post_init__(self):
        """Проверяет, что в проде критичные секреты заданы через env (fail-fast)."""
        env = os.getenv("APP_ENV", "development").lower()
        is_production = env in ("production", "prod")

        if is_production:
            # В проде секретный ключ должен быть задан явно, не дефолтный
            if self.secret_key == "dev-secret-key":
                raise ConfigError(
                    "APP_SECRET_KEY must be set in production environment. "
                    "Do not use default dev-secret-key in production."
                )


settings = Settings()
