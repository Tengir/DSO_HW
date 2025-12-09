from app.config import Settings


def test_settings_reads_secret_key_from_env(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")

    cfg = Settings()

    assert cfg.secret_key == "test-secret"


def test_settings_masks_secret_in_repr():
    """Проверка маскирования секрета в строковом представлении."""
    cfg = Settings()

    repr_str = repr(cfg)
    str_str = str(cfg)

    # Секрет должен быть замаскирован
    assert "secret_key='***'" in repr_str
    assert "secret_key='***'" in str_str
    assert "dev-secret-key" not in repr_str
    assert "dev-secret-key" not in str_str

    # Но реальное значение должно остаться доступным
    assert cfg.secret_key == "dev-secret-key"
