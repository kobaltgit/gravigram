import uuid
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode

from src.config import settings
from src.database import (
    get_active_project, list_projects,
    get_active_session, list_sessions, create_session,
    get_setting, set_setting,
    list_scheduled_tasks, create_scheduled_task, delete_scheduled_task
)
from src.agent.models import register_new_model, remove_model, get_available_models
from src.bot.keyboards import (
    get_main_reply_keyboard, get_projects_inline_keyboard,
    get_sessions_inline_keyboard, get_mode_inline_keyboard,
    get_tasks_inline_keyboard, get_quick_actions_keyboard,
    get_language_inline_keyboard
)
from src.agent.manager import agent_manager
from src.agent.scheduler import parse_schedule_expression
from src.i18n import t, resolve_lang

router = Router(name="commands")

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Greeting, overview of active project and session."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    active_project = await get_active_project()
    active_session = await get_active_session(active_project["id"] if active_project else None)
    
    proj_name = active_project["name"] if active_project else t("not_selected", lang)
    proj_path = active_project["path"] if active_project else "-"
    sess_title = active_session["title"] if active_session else t("new_chat", lang)

    webapp_url = settings.webapp_url or None

    text = (
        f"{t('start_title', lang)}\n\n"
        f"{t('start_desc', lang)}\n\n"
        f"📂 **{t('active_project', lang)}:** `{proj_name}`\n"
        f"📍 **{t('project_path', lang)}:** `{proj_path}`\n"
        f"💬 **{t('current_session', lang)}:** `{sess_title}`\n\n"
        f"{t('start_hint', lang)}"
    )
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(webapp_url, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """List available commands."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    lines = [
        t("help_title", lang),
        "",
        t("help_new", lang),
        t("help_projects", lang),
        t("help_chats", lang),
        t("help_tasks", lang),
        t("help_add_task", lang),
        t("help_mode", lang),
        t("help_quick", lang),
        t("help_lang", lang),
        t("help_login", lang),
        t("help_add_model", lang),
        t("help_cancel", lang),
        t("help_status", lang),
    ]
    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("lang"))
@router.message(Command("language"))
async def cmd_language(message: types.Message):
    """Show language selection menu."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    await message.answer(
        t("lang_menu_title", lang),
        reply_markup=get_language_inline_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("quick"))
async def cmd_quick(message: types.Message):
    """Show quick action buttons for agent inspection tasks."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    await message.answer(
        t("quick_actions_title", lang),
        reply_markup=get_quick_actions_keyboard(lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("new"))
async def cmd_new(message: types.Message):
    """Starts a new clean conversation session in the active project."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    active_project = await get_active_project()
    if not active_project:
        await message.answer(t("no_active_project", lang))
        return

    conv_id = str(uuid.uuid4())
    default_title = t("new_chat", lang)
    session = await create_session(
        project_id=active_project["id"],
        title=default_title,
        conversation_id=conv_id,
        make_active=True
    )
    await message.answer(
        t("session_created", lang, name=active_project['name']),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("projects"))
async def cmd_projects(message: types.Message):
    """List projects for switching."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    projects = await list_projects()
    await message.answer(
        t("choose_project", lang),
        reply_markup=get_projects_inline_keyboard(projects, lang=lang)
    )

@router.message(Command("chats"))
@router.message(Command("sessions"))
async def cmd_sessions(message: types.Message):
    """List sessions for the current active project."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    active_project = await get_active_project()
    if not active_project:
        await message.answer(t("no_active_project", lang))
        return

    sessions = await list_sessions(project_id=active_project["id"])
    await message.answer(
        t("sessions_in_project", lang, name=active_project['name']),
        reply_markup=get_sessions_inline_keyboard(sessions, lang=lang)
    )

@router.message(Command("tasks"))
@router.message(Command("schedule"))
async def cmd_tasks(message: types.Message):
    """List scheduled agent tasks."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    tasks = await list_scheduled_tasks()
    if not tasks:
        await message.answer(t("no_tasks", lang), parse_mode=ParseMode.MARKDOWN)
        return

    await message.answer(
        t("tasks_header", lang),
        reply_markup=get_tasks_inline_keyboard(tasks, lang=lang)
    )

@router.message(Command("add_task"))
async def cmd_add_task(message: types.Message):
    """Creates a new scheduled task."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(t("task_format_error", lang), parse_mode=ParseMode.MARKDOWN)
        return

    cron_expr = parts[1].strip()
    prompt = parts[2].strip()
    title = prompt[:30] + ("..." if len(prompt) > 30 else "")

    active_project = await get_active_project()
    proj_id = active_project["id"] if active_project else None

    next_run = parse_schedule_expression(cron_expr)
    next_run_str = next_run.isoformat() if next_run else None

    task = await create_scheduled_task(
        title=title,
        cron_expression=cron_expr,
        prompt=prompt,
        project_id=proj_id,
        next_run_at=next_run_str
    )

    next_info = f"\n📅 *{t('task_next_run', lang)}:* `{next_run.strftime('%Y-%m-%d %H:%M')}`" if next_run else ""
    proj_label = active_project['name'] if active_project else t("not_selected", lang)

    await message.answer(
        f"{t('task_created', lang)}\n\n"
        f"📋 **{t('task_title', lang)}:** `{task['title']}`\n"
        f"⏰ **{t('task_schedule', lang)}:** `{cron_expr}`\n"
        f"📁 **{t('task_project', lang)}:** `{proj_label}`\n"
        f"💬 **{t('task_prompt', lang)}:** {prompt}{next_info}",
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("mode"))
async def cmd_mode(message: types.Message):
    """Show and switch autonomy mode."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    mode_val = (await get_setting("confirm_mode", "false")).lower() == "true"
    current_model = await get_setting("model", "")
    model_name = current_model if current_model else t("model_default", lang)
    mode_str = t("mode_confirm", lang) if mode_val else t("mode_autonomous", lang)
    
    await message.answer(
        f"{t('settings_header', lang)}\n\n"
        f"🧠 **{t('current_model', lang)}:** `{model_name}`\n"
        f"🛡 **{t('mode_label', lang)}:** `{mode_str}`\n\n"
        f"👇",
        reply_markup=get_mode_inline_keyboard(mode_val, lang=lang),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("add_model"))
async def cmd_add_model(message: types.Message):
    """Adds a new model identifier dynamically."""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "📝 **Format:** `/add_model <model_id> [Title]`\n*Example:* `/add_model gemini-4.0-pro Gemini 4.0 Pro`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    model_id = parts[1].strip()
    name = parts[2].strip() if len(parts) > 2 else model_id

    await register_new_model(model_id=model_id, name=name, description="Custom model")
    await message.answer(
        f"✅ **Model added:** `{name}` (`{model_id}`)\nSelect it via `/mode` or in the Mini App.",
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("del_model"))
async def cmd_del_model(message: types.Message):
    """Deletes a custom model."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("📝 **Format:** `/del_model <model_id>`")
        return
    model_id = parts[1].strip()
    success = await remove_model(model_id)
    if success:
        await message.answer(f"🗑 Model `{model_id}` deleted.")
    else:
        await message.answer(f"⚠️ Model `{model_id}` not found.")

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    """Aborts the currently executing task if any."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    if agent_manager.cancel_task(message.chat.id):
        await message.answer(t("task_cancelled", lang))
    else:
        await message.answer(t("no_active_task", lang))

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Displays current system and agent status."""
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    active_project = await get_active_project()
    active_session = await get_active_session(active_project["id"] if active_project else None)
    confirm_mode = (await get_setting("confirm_mode", "false")).lower() == "true"
    model = await get_setting("model", "")
    model_name = model if model else t("model_default", lang)

    proj_name = active_project["name"] if active_project else t("not_selected", lang)
    proj_path = active_project["path"] if active_project else "-"
    sess_title = active_session["title"] if active_session else t("new_chat", lang)

    tasks = await list_scheduled_tasks(active_only=True)
    mode_status = t("mode_confirm", lang) if confirm_mode else t("mode_autonomous", lang)
    is_running = agent_manager.is_task_running(message.chat.id)

    text = (
        "📊 **Gravigram Status:**\n\n"
        f"📂 **{t('active_project', lang)}:** `{proj_name}`\n"
        f"📍 **{t('project_path', lang)}:** `{proj_path}`\n"
        f"💬 **{t('current_session', lang)}:** `{sess_title}`\n"
        f"🧠 **{t('current_model', lang)}:** `{model_name}`\n"
        f"⏰ **Tasks (Active):** `{len(tasks)}`\n"
        f"🛡 **{t('mode_label', lang)}:** `{mode_status}`\n"
        f"⚡ **Task status:** `{'Running' if is_running else 'Idle'}`"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)
