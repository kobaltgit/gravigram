import json
import uuid
import logging
import asyncio
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode

from src.config import settings
from src.database import (
    list_projects, set_active_project, get_active_project,
    list_sessions, set_active_session, create_session, get_active_session, delete_session,
    set_setting, get_setting, set_language, get_language,
    list_scheduled_tasks, get_scheduled_task, toggle_scheduled_task, delete_scheduled_task
)
from src.bot.keyboards import (
    get_projects_inline_keyboard, get_sessions_inline_keyboard,
    get_mode_inline_keyboard, get_models_inline_keyboard,
    get_tasks_inline_keyboard, get_language_inline_keyboard,
    get_main_reply_keyboard
)
from src.agent.models import get_available_models
from src.agent.manager import agent_manager
from src.agent.scheduler import agent_scheduler
from src.i18n import t, resolve_lang

router = Router(name="callbacks")
logger = logging.getLogger(__name__)

# --- Language Selection Callback ---

@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_language(call: types.CallbackQuery):
    target_lang = call.data.split(":")[1]
    await set_language(target_lang)
    webapp_url = settings.webapp_url or None
    alert_text = t("lang_switched", target_lang)
    await call.answer(alert_text, show_alert=True)
    await call.message.edit_text(
        f"✅ {alert_text}",
        reply_markup=get_language_inline_keyboard()
    )
    # Refresh main reply keyboard in the selected language
    await call.message.answer(
        t("start_hint", target_lang),
        reply_markup=get_main_reply_keyboard(webapp_url, lang=target_lang),
        parse_mode=ParseMode.MARKDOWN
    )

# --- Project Selection Callbacks ---

@router.callback_query(F.data.startswith("proj_select:"))
async def cb_select_project(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    project_id = int(call.data.split(":")[1])
    await set_active_project(project_id)
    projects = await list_projects()
    active_project = await get_active_project()

    await call.message.edit_text(
        f"{t('project_changed', lang)} `{active_project['name']}`\n📍 `{active_project['path']}`",
        reply_markup=get_projects_inline_keyboard(projects, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer(t("project_selected_alert", lang, name=active_project['name']))

@router.callback_query(F.data == "proj_add")
async def cb_add_project_help(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    await call.message.answer(
        t("add_project_help", lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

# --- Session Selection Callbacks ---

@router.callback_query(F.data.startswith("sess_select:"))
async def cb_select_session(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    session_id = int(call.data.split(":")[1])
    await set_active_session(session_id)
    active_project = await get_active_project()
    sessions = await list_sessions(active_project["id"] if active_project else None)
    active_session = await get_active_session(active_project["id"] if active_project else None)

    await call.message.edit_text(
        f"{t('session_switched', lang, title=active_session['title'])}",
        reply_markup=get_sessions_inline_keyboard(sessions, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer(t("session_selected_alert", lang, title=active_session['title']))

@router.callback_query(F.data == "sess_new")
async def cb_new_session(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    active_project = await get_active_project()
    if not active_project:
        await call.answer(t("no_active_project", lang), show_alert=True)
        return

    conv_id = str(uuid.uuid4())
    default_title = t("new_chat", lang)
    await create_session(
        project_id=active_project["id"],
        title=default_title,
        conversation_id=conv_id,
        make_active=True
    )
    sessions = await list_sessions(project_id=active_project["id"])
    await call.message.edit_text(
        t("session_created", lang, name=active_project['name']),
        reply_markup=get_sessions_inline_keyboard(sessions, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer(t("session_created_alert", lang))

@router.callback_query(F.data.startswith("sess_del:"))
async def cb_delete_session(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    session_id = int(call.data.split(":")[1])
    active_project = await get_active_project()
    project_id = active_project["id"] if active_project else None

    # Delete the session (and cascading messages)
    await delete_session(session_id)

    # If deleted session was active, activate another or create one
    sessions = await list_sessions(project_id=project_id)
    active_session = await get_active_session(project_id)
    if not active_session and sessions:
        await set_active_session(sessions[0]["id"])
        sessions = await list_sessions(project_id=project_id)
        active_session = sessions[0]
    elif not sessions and active_project:
        new_session = await create_session(
            project_id=active_project["id"],
            title=t("new_chat", lang),
            conversation_id=str(uuid.uuid4()),
            make_active=True
        )
        sessions = [new_session]
        active_session = new_session

    title = active_session['title'] if active_session else "-"
    await call.message.edit_text(
        f"{t('session_deleted', lang)}\n{t('current_session', lang)}: `{title}`",
        reply_markup=get_sessions_inline_keyboard(sessions, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer(t("session_deleted", lang))

# --- Scheduled Task Callbacks ---

@router.callback_query(F.data.startswith("task_view:"))
async def cb_task_view(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    task_id = int(call.data.split(":")[1])
    task = await get_scheduled_task(task_id)
    if not task:
        await call.answer("Task not found / Задание не найдено", show_alert=True)
        return

    is_act = task.get("is_active") == 1
    status_label = "🟢 Active" if is_act else "⏸ Paused"
    if lang == "ru":
        status_label = "🟢 Активно" if is_act else "⏸ На паузе"

    proj_name = task.get("project_name") or "-"
    last_run = task.get("last_run_at") or "-"
    next_run = task.get("next_run_at") or "-"

    text = (
        f"⏰ **{t('task_title', lang)} #{task['id']}:** `{task['title']}`\n\n"
        f"📊 **Status:** {status_label}\n"
        f"⏱ **{t('task_schedule', lang)}:** `{task['cron_expression']}`\n"
        f"📁 **{t('task_project', lang)}:** `{proj_name}`\n"
        f"📅 **{t('task_next_run', lang)}:** `{next_run}`\n"
        f"🕒 **Last run:** `{last_run}`\n\n"
        f"💬 **{t('task_prompt', lang)}:**\n{task['prompt']}"
    )
    tasks = await list_scheduled_tasks()
    await call.message.edit_text(text, reply_markup=get_tasks_inline_keyboard(tasks, lang=lang), parse_mode=ParseMode.MARKDOWN)
    await call.answer()

@router.callback_query(F.data.startswith("task_toggle:"))
async def cb_task_toggle(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    task_id = int(call.data.split(":")[1])
    task = await get_scheduled_task(task_id)
    if not task:
        await call.answer("Task not found / Задание не найдено", show_alert=True)
        return

    new_state = not (task.get("is_active", 1) == 1)
    await toggle_scheduled_task(task_id, new_state)
    tasks = await list_scheduled_tasks()
    await call.message.edit_reply_markup(reply_markup=get_tasks_inline_keyboard(tasks, lang=lang))
    msg = f"Task #{task_id}: {'active' if new_state else 'paused'}"
    if lang == "ru":
        msg = f"Задание #{task_id}: {'включено' if new_state else 'поставлено на паузу'}"
    await call.answer(msg)

@router.callback_query(F.data.startswith("task_run:"))
async def cb_task_run(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    task_id = int(call.data.split(":")[1])
    msg = "⚡ Запускаю выполнение задания..." if lang == "ru" else "⚡ Running task now..."
    await call.answer(msg)
    asyncio.create_task(agent_scheduler.run_task(task_id))

@router.callback_query(F.data.startswith("task_del:"))
async def cb_task_del(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    task_id = int(call.data.split(":")[1])
    await delete_scheduled_task(task_id)
    tasks = await list_scheduled_tasks()
    if tasks:
        await call.message.edit_reply_markup(reply_markup=get_tasks_inline_keyboard(tasks, lang=lang))
    else:
        await call.message.edit_text(t("no_tasks", lang), parse_mode=ParseMode.MARKDOWN)
    msg = f"Задание #{task_id} удалено" if lang == "ru" else f"Task #{task_id} deleted"
    await call.answer(msg)

# --- Autonomy & Model Settings Callbacks ---

@router.callback_query(F.data == "mode_auto")
async def cb_mode_auto(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    await set_setting("confirm_mode", "false")
    await call.message.edit_reply_markup(reply_markup=get_mode_inline_keyboard(False, lang=lang))
    await call.answer(t("mode_switched", lang, mode=t("mode_autonomous", lang)))

@router.callback_query(F.data == "mode_confirm")
async def cb_mode_confirm(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    await set_setting("confirm_mode", "true")
    await call.message.edit_reply_markup(reply_markup=get_mode_inline_keyboard(True, lang=lang))
    await call.answer(t("mode_switched", lang, mode=t("mode_confirm", lang)))

@router.callback_query(F.data == "mode_menu")
async def cb_mode_menu(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    confirm_mode = (await get_setting("confirm_mode", "false")).lower() == "true"
    current_model = await get_setting("model", "")
    model_name = current_model if current_model else t("model_default", lang)
    mode_str = t("mode_confirm", lang) if confirm_mode else t("mode_autonomous", lang)
    await call.message.edit_text(
        f"{t('settings_header', lang)}\n\n{t('current_model', lang)}: `{model_name}`\n{t('mode_label', lang)}: `{mode_str}`",
        reply_markup=get_mode_inline_keyboard(confirm_mode, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@router.callback_query(F.data == "models_list")
async def cb_models_list(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    models = await get_available_models()
    current_model = await get_setting("model", "")
    await call.message.edit_text(
        f"🤖 **{t('btn_select_model', lang)}:**",
        reply_markup=get_models_inline_keyboard(models, current_model, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    model_id = call.data.split(":", 1)[1]
    await set_setting("model", model_id)
    models = await get_available_models()
    await call.message.edit_reply_markup(
        reply_markup=get_models_inline_keyboard(models, model_id, lang=lang)
    )
    name = model_id if model_id else t("model_default", lang)
    await call.answer(t("model_switched", lang, model=name))

# --- Task Cancellation Callback ---

@router.callback_query(F.data == "task_cancel")
async def cb_task_cancel(call: types.CallbackQuery):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    if agent_manager.cancel_task(call.message.chat.id):
        await call.answer(t("task_cancelled", lang))
    else:
        await call.answer(t("no_active_task", lang))

# --- Confirmation Approvals ---

@router.callback_query(F.data.startswith("conf_yes:"))
async def cb_confirm_yes(call: types.CallbackQuery):
    confirm_id = call.data.split(":", 1)[1]
    if agent_manager.resolve_confirmation(confirm_id, approved=True):
        await call.message.edit_text(f"{call.message.text}\n\n✅ *Allowed by user.*", parse_mode=ParseMode.MARKDOWN)
        await call.answer("Command allowed")
    else:
        await call.answer("Confirmation expired.")

@router.callback_query(F.data.startswith("conf_no:"))
async def cb_confirm_no(call: types.CallbackQuery):
    confirm_id = call.data.split(":", 1)[1]
    if agent_manager.resolve_confirmation(confirm_id, approved=False):
        await call.message.edit_text(f"{call.message.text}\n\n❌ *Rejected by user.*", parse_mode=ParseMode.MARKDOWN)
        await call.answer("Command rejected")
    else:
        await call.answer("Confirmation expired.")

# --- Telegram Mini App WebApp Data Handler ---

@router.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """Processes JSON messages sent from Flutter Web Mini App via Telegram.WebApp.sendData()."""
    raw_data = message.web_app_data.data
    try:
        data = json.loads(raw_data)
        action = data.get("action")
        
        if action == "select_project":
            proj_id = int(data.get("project_id"))
            await set_active_project(proj_id)
            active = await get_active_project()
            await message.answer(f"📱 **Mini App:** active project switched to `{active['name']}`", parse_mode=ParseMode.MARKDOWN)
        
        elif action == "select_session":
            sess_id = int(data.get("session_id"))
            await set_active_session(sess_id)
            active_project = await get_active_project()
            active_session = await get_active_session(active_project["id"] if active_project else None)
            await message.answer(f"📱 **Mini App:** active conversation switched to `{active_session['title']}`", parse_mode=ParseMode.MARKDOWN)

        elif action == "new_session":
            active_project = await get_active_project()
            conv_id = str(uuid.uuid4())
            await create_session(
                project_id=active_project["id"],
                title="New Chat",
                conversation_id=conv_id,
                make_active=True
            )
            await message.answer(f"📱 **Mini App:** new conversation created in `{active_project['name']}`", parse_mode=ParseMode.MARKDOWN)

        else:
            await message.answer(f"📱 **Mini App data received:** `{raw_data}`")

    except Exception as e:
        logger.exception("Error processing WebApp data:")
        await message.answer(f"⚠️ Error processing WebApp data: `{str(e)}`")

# --- Quick Actions Callback Handler ---

@router.callback_query(F.data.startswith("quick:"))
async def cb_quick_action(call: types.CallbackQuery, bot: Bot):
    lang = await resolve_lang(call.from_user.language_code if call.from_user else None)
    action = call.data.split(":", 1)[1]
    
    if lang == "en":
        prompts = {
            "sys_status": "Please collect system information: OS, free disk space, CPU load, and RAM usage, and provide a neat summary.",
            "git_status": "Check git repository status of the active project: git status, recent commits, and uncommitted changes.",
            "list_files": "Show file structure and major directories of the active project up to depth 2.",
            "run_tests": "Run project tests or syntax checks and report the result."
        }
    else:
        prompts = {
            "sys_status": "Пожалуйста, собери краткую информацию о текущей системе: ОС, свободное место на дисках, загрузка CPU и использование RAM, и выведи аккуратный отчёт.",
            "git_status": "Проверь статус git репозитория текущего проекта: git status, последние коммиты и незакоммиченные изменения.",
            "list_files": "Покажи структуру файлов и основных каталогов текущего проекта на глубину 2 уровня.",
            "run_tests": "Запусти тесты проекта или проверку синтаксиса и сообщи результат."
        }
    prompt = prompts.get(action)
    if not prompt:
        await call.answer("Unknown action")
        return

    await call.answer("Starting task..." if lang == "en" else "Запускаю задачу...")
    from src.bot.handlers.chat import run_prompt_with_streaming
    status_msg = await call.message.answer(f"⚡ **[{t('quick_actions_title', lang).split(':')[0]}]** `{action}`\n\n{t('task_initializing', lang)}", parse_mode=ParseMode.MARKDOWN)
    await run_prompt_with_streaming(
        chat_id=call.message.chat.id,
        bot=bot,
        prompt_text=prompt,
        status_msg=status_msg
    )
