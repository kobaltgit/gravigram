from src.bot.keyboards import (
    get_main_reply_keyboard,
    get_language_inline_keyboard,
    get_quick_actions_keyboard,
    get_projects_inline_keyboard,
    get_sessions_inline_keyboard,
    get_tasks_inline_keyboard,
    get_mode_inline_keyboard,
    get_models_inline_keyboard,
    get_confirm_action_keyboard
)

def test_main_reply_keyboard():
    # Russian without webapp
    kb_ru = get_main_reply_keyboard(webapp_url=None, lang="ru")
    assert any("Новая беседа" in btn.text for row in kb_ru.keyboard for btn in row)
    assert any("Язык" in btn.text for row in kb_ru.keyboard for btn in row)

    # English with webapp
    kb_en = get_main_reply_keyboard(webapp_url="https://agy.example.com", lang="en")
    assert any("New Chat" in btn.text for row in kb_en.keyboard for btn in row)
    assert any("Mini App" in btn.text for row in kb_en.keyboard for btn in row)
    # WebAppInfo attached to first button
    assert kb_en.keyboard[0][0].web_app.url == "https://agy.example.com"


def test_language_inline_keyboard():
    kb = get_language_inline_keyboard()
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "set_lang:ru" in callbacks
    assert "set_lang:en" in callbacks


def test_quick_actions_keyboard():
    kb_ru = get_quick_actions_keyboard(lang="ru")
    kb_en = get_quick_actions_keyboard(lang="en")

    callbacks = [btn.callback_data for row in kb_ru.inline_keyboard for btn in row]
    assert "quick:sys_status" in callbacks
    assert "quick:run_tests" in callbacks

    # Check text localization
    ru_texts = [btn.text for row in kb_ru.inline_keyboard for btn in row]
    en_texts = [btn.text for row in kb_en.inline_keyboard for btn in row]
    assert any("Тесты" in t or "Запустить" in t for t in ru_texts)
    assert any("Run Tests" in t for t in en_texts)


def test_projects_inline_keyboard():
    projects = [
        {"id": 1, "name": "Active Proj", "is_active": 1},
        {"id": 2, "name": "Inactive Proj", "is_active": 0},
    ]
    kb = get_projects_inline_keyboard(projects, lang="ru")
    buttons = [btn for row in kb.inline_keyboard for btn in row]

    active_btn = next(b for b in buttons if b.callback_data == "proj_select:1")
    assert "✅" in active_btn.text

    inactive_btn = next(b for b in buttons if b.callback_data == "proj_select:2")
    assert "✅" not in inactive_btn.text

    assert any(b.callback_data == "proj_add" for b in buttons)


def test_sessions_inline_keyboard():
    sessions = [
        {"id": 10, "title": "A very long session title that exceeds twenty chars", "is_active": 1},
    ]
    kb = get_sessions_inline_keyboard(sessions, lang="en")
    buttons = [btn for row in kb.inline_keyboard for btn in row]

    sel_btn = next(b for b in buttons if b.callback_data == "sess_select:10")
    assert "..." in sel_btn.text
    assert any(b.callback_data == "sess_del:10" for b in buttons)
    assert any(b.callback_data == "sess_new" for b in buttons)


def test_tasks_inline_keyboard():
    tasks = [
        {"id": 5, "title": "Backup", "cron_expression": "0 0 * * *", "is_active": 1},
    ]
    kb = get_tasks_inline_keyboard(tasks, lang="ru")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]

    assert "task_view:5" in callbacks
    assert "task_run:5" in callbacks
    assert "task_toggle:5" in callbacks
    assert "task_del:5" in callbacks


def test_mode_and_models_keyboards():
    # Autonomous mode (confirm_mode = False)
    kb_auto = get_mode_inline_keyboard(confirm_mode=False, lang="ru")
    auto_btns = [btn for row in kb_auto.inline_keyboard for btn in row]
    auto_btn = next(b for b in auto_btns if b.callback_data == "mode_auto")
    assert "🟢" in auto_btn.text

    # Confirm mode (confirm_mode = True)
    kb_conf = get_mode_inline_keyboard(confirm_mode=True, lang="en")
    conf_btns = [btn for row in kb_conf.inline_keyboard for btn in row]
    conf_btn = next(b for b in conf_btns if b.callback_data == "mode_confirm")
    assert "🟢" in conf_btn.text

    # Models list keyboard
    models = [
        {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash"},
        {"id": "claude-sonnet-4.6", "name": "Claude Sonnet 4.6"},
    ]
    kb_models = get_models_inline_keyboard(models, current_model="gemini-3.7-flash", lang="en")
    model_btns = [btn for row in kb_models.inline_keyboard for btn in row]
    active_m = next(b for b in model_btns if b.callback_data == "set_model:gemini-3.7-flash")
    assert "✅" in active_m.text


def test_confirm_action_keyboard():
    kb = get_confirm_action_keyboard("cid_12345", lang="ru")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "conf_yes:cid_12345" in callbacks
    assert "conf_no:cid_12345" in callbacks
