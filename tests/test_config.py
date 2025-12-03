from app.config import Settings


def test_settings_reads_secret_key_from_env(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")

    cfg = Settings()

    assert cfg.secret_key == "test-secret"
