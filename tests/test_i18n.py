import pytest
from src.i18n import TRANSLATIONS, t, resolve_lang
from src.database import set_language


def test_translation_dictionaries_parity():
    ru_keys = set(TRANSLATIONS["ru"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())

    missing_in_en = ru_keys - en_keys
    missing_in_ru = en_keys - ru_keys

    assert not missing_in_en, f"Keys missing in EN translations: {missing_in_en}"
    assert not missing_in_ru, f"Keys missing in RU translations: {missing_in_ru}"

def test_t_function_translations():
    # Russian translation
    assert "Добро пожаловать" in t("start_title", lang="ru")

    # English translation
    assert "Welcome" in t("start_title", lang="en")

    # Fallback to key if unknown
    assert t("non_existent_key_12345", lang="ru") == "non_existent_key_12345"
    assert t("non_existent_key_12345", lang="en") == "non_existent_key_12345"

def test_t_function_interpolation():
    # String interpolation
    result = t("account_switched_alert", lang="en", email="alice@example.com")
    assert "alice@example.com" in result

    # Robustness against missing parameters
    result_safe = t("account_switched_alert", lang="en")
    assert "{email}" in result_safe or "Account switched" in result_safe

async def test_resolve_lang():
    # When DB is explicitly set to en
    await set_language("en")
    assert await resolve_lang("ru") == "en"
    assert await resolve_lang(None) == "en"

    # When DB is explicitly set to ru
    await set_language("ru")
    assert await resolve_lang("en") == "ru"
    assert await resolve_lang(None) == "ru"
