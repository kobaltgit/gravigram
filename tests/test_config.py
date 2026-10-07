import pytest
from pathlib import Path
from src.config import Settings, BASE_DIR

def test_base_dir_structure():
    assert BASE_DIR.exists()
    assert (BASE_DIR / "src").is_dir()
    assert (BASE_DIR / "pyproject.toml").exists() or (BASE_DIR / "README.md").exists()

def test_settings_defaults():
    s = Settings(
        telegram_bot_token="test:token",
        telegram_admin_id=12345,
        _env_file=None
    )
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.default_model == "gemini-3.7-flash"
    assert s.confirm_mode is False
    assert "127.0.0.1" in s.trusted_proxies

def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "987654")
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setenv("CONFIRM_MODE", "true")
    monkeypatch.setenv("DEFAULT_MODEL", "gemini-3.1-pro")

    s = Settings(_env_file=None)
    assert s.telegram_admin_id == 987654
    assert s.port == 9090
    assert s.confirm_mode is True
    assert s.default_model == "gemini-3.1-pro"

def test_trusted_proxies_list():
    s = Settings(trusted_proxies="127.0.0.1, ::1, 192.168.5.128", _env_file=None)
    proxies = [p.strip() for p in s.trusted_proxies.split(",") if p.strip()]
    assert "127.0.0.1" in proxies
    assert "::1" in proxies
    assert "192.168.5.128" in proxies
