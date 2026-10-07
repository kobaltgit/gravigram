import pytest
import setup

def test_wizard_validators():
    # Bot token validation
    ok, err = setup.validate_bot_token("9876543210:AAFe3_xyz-KJH")
    assert ok is True
    assert err == ""

    ok, err = setup.validate_bot_token("")
    assert ok is False

    ok, err = setup.validate_bot_token("1234567890:ABC")
    assert ok is False

    ok, err = setup.validate_bot_token("invalid_token_format")
    assert ok is False

    # Admin ID validation
    ok, err = setup.validate_admin_id("12345678")
    assert ok is True

    ok, err = setup.validate_admin_id("-5")
    assert ok is False

    ok, err = setup.validate_admin_id("abc")
    assert ok is False

    # Port validation
    ok, err = setup.validate_port("8000")
    assert ok is True

    ok, err = setup.validate_port("0")
    assert ok is False

    ok, err = setup.validate_port("70000")
    assert ok is False

def test_select_language_cli():
    assert setup.select_language("en") == "en"
    assert setup.select_language("ru") == "ru"

def test_select_language_interactive_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert setup.select_language(None) == "en"

def test_select_language_interactive_ru(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2")
    assert setup.select_language(None) == "ru"

    monkeypatch.setattr("builtins.input", lambda _: "ru")
    assert setup.select_language(None) == "ru"

def test_t_function():
    setup.CURRENT_LANG = "en"
    assert setup.t("Hello", "Привет") == "Hello"

    setup.CURRENT_LANG = "ru"
    assert setup.t("Hello", "Привет") == "Привет"
    setup.CURRENT_LANG = "en"
