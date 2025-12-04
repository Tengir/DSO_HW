import pytest

from app.config import ConfigError, Settings


def test_settings_fails_if_secret_key_missing_in_prod(monkeypatch):
    """Проверяет, что в проде без APP_SECRET_KEY Settings выбрасывает ConfigError."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        Settings()

    assert "APP_SECRET_KEY" in str(exc_info.value)
    assert "production" in str(exc_info.value).lower()


def test_settings_allows_dev_defaults_in_dev_mode(monkeypatch):
    """Проверяет, что в dev-режиме дефолтные значения разрешены."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)

    # Не должно быть исключения
    cfg = Settings()
    assert cfg.secret_key == "dev-secret-key"


def test_settings_accepts_custom_secret_in_prod(monkeypatch):
    """Проверяет, что в проде с заданным секретом всё работает."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET_KEY", "prod-secret-key-12345")

    # Не должно быть исключения
    cfg = Settings()
    assert cfg.secret_key == "prod-secret-key-12345"


def test_settings_defaults_to_dev_mode_if_env_not_set(monkeypatch):
    """Проверяет, что по умолчанию (без APP_ENV) используется dev-режим."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)

    # Не должно быть исключения
    cfg = Settings()
    assert cfg.secret_key == "dev-secret-key"
