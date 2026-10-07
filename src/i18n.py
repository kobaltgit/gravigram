from typing import Optional, Dict, Any
from src.database import get_language, set_language

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        # Reply Keyboard
        "btn_new_chat": "➕ Новая беседа",
        "btn_projects": "📂 Проекты",
        "btn_sessions": "💬 Сессии",
        "btn_tasks": "⏰ Задания",
        "btn_actions": "⚡ Действия",
        "btn_accounts": "🔑 Аккаунты",
        "btn_language": "🌐 Язык",
        "btn_miniapp": "🎛 Панель управления (Mini App)",

        # Start & Welcome
        "start_title": "👋 **Добро пожаловать в Gravigram!**",
        "start_desc": "Универсальный центр управления персональным AI-агентом Google Antigravity прямо из Telegram.",
        "active_project": "Активный проект",
        "project_path": "Путь",
        "current_session": "Текущая беседа",
        "not_selected": "Не выбран",
        "new_chat": "Новая беседа",
        "start_hint": "💡 *Отправьте мне текстовое сообщение, голосовую заметку или скриншот с задачей.*",

        # Help
        "help_title": "🛠 **Доступные команды:**",
        "help_new": "➕ `/new` — Начать новую чистую беседу в текущем проекте",
        "help_projects": "📂 `/projects` — Выбрать или добавить рабочий проект",
        "help_chats": "💬 `/chats` — Список сохраненных бесед текущего проекта",
        "help_tasks": "⏰ `/tasks` (или `/schedule`) — Запланированные автозадания агента",
        "help_add_task": "➕ `/add_task <время/cron> <промпт>` — Создать плановое задание",
        "help_mode": "⚙️ `/mode` — Настройки (модель ИИ, режим безопасности)",
        "help_quick": "⚡ `/quick` — Быстрые действия (статус ОС, git, тесты)",
        "help_lang": "🌐 `/lang` — Переключение языка (RU / EN)",
        "help_login": "🔑 `/login` — Авторизация / смена Google аккаунта в Antigravity",
        "help_add_model": "➕ `/add_model <id> [Название]` — Добавить новую модель в список",
        "help_cancel": "⏹ `/cancel` — Прервать выполнение текущей задачи",
        "help_status": "📊 `/status` — Сводка о текущем окружении и модели",

        # Projects
        "choose_project": "📂 **Выберите активный проект:**",
        "project_changed": "📂 **Активный проект изменён:**",
        "btn_add_project": "➕ Добавить проект по пути",
        "add_project_help": "📝 Чтобы добавить новый проект, отправьте сообщение в формате:\n`/add_project <Название> <Путь к папке>`\n\n*Пример:* `/add_project MyBot D:\\Projects\\my_bot`",
        "no_active_project": "⚠️ Сначала выберите или создайте проект через `/projects`.",
        "project_selected_alert": "Выбран проект: {name}",

        # Sessions
        "sessions_in_project": "💬 **Беседы в проекте '{name}':**",
        "session_switched": "💬 **Активная беседа переключена:** `{title}`",
        "btn_new_session": "➕ Создать новую беседу",
        "session_created": "✨ **Создана новая беседа в проекте '{name}'!**\nКонтекст сброшен. Все последующие сообщения будут относиться к новой теме.",
        "session_selected_alert": "Беседа: {title}",
        "session_deleted": "🗑 Сессия удалена.",
        "session_created_alert": "Создана новая сессия",

        # Tasks
        "no_tasks": "⏰ **Запланированных заданий агента пока нет.**\n\n💡 Чтобы создать задание, используйте команду:\n`/add_task 09:00 Проверь статус серверов и дисков`\nили напишите агенту в чат своими словами.",
        "tasks_header": "⏰ **Запланированные задания ИИ-агента:**",
        "task_format_error": "📝 **Формат команды:** `/add_task <время/cron> <Текст задания для агента>`\n\n*Примеры:*\n• `/add_task 08:30 Запусти тесты в проекте и составь отчет`\n• `/add_task 09:00 Проверь статус контейнеров на Proxmox и диски`\n• `/add_task 0 18 * * 5 Проверь git-коммиты за неделю`",
        "task_created": "✅ **Задание запланировано!**",
        "task_title": "Название",
        "task_schedule": "Расписание",
        "task_project": "Проект",
        "task_prompt": "Промпт агенту",
        "task_next_run": "Следующий запуск",
        "task_btn_run": "⚡ Запустить",
        "task_btn_pause": "⏸ Пауза",
        "task_btn_resume": "▶ Включить",
        "task_btn_delete": "🗑 Удалить",

        # Mode & Settings
        "settings_header": "⚙️ **Настройки Gravigram:**",
        "current_model": "Текущая модель",
        "mode_label": "Режим",
        "mode_autonomous": "Автономный (/auto)",
        "mode_confirm": "С подтверждением (/confirm)",
        "btn_select_model": "🤖 Выбрать модель ИИ",
        "model_default": "По умолчанию (Antigravity Auto)",
        "btn_back_to_settings": "🔙 Назад к настройкам",
        "mode_switched": "Режим безопасности: {mode}",
        "model_switched": "Модель переключена на: {model}",

        # Quick Actions
        "quick_actions_title": "⚡ **Быстрые действия (Quick Actions):**\n\nВыберите операцию для выполнения агентом:",
        "btn_sys_status": "📊 Статус системы (RAM/Диск)",
        "btn_git_status": "🔍 Git статус",
        "btn_list_files": "📁 Файлы проекта",
        "btn_run_tests": "🧪 Запустить тесты",

        # Confirm & Control
        "confirm_header": "⚠️ **Требуется подтверждение действия**",
        "btn_allow": "✅ Разрешить",
        "btn_reject": "❌ Отклонить",
        "btn_cancel_task": "⏹ Остановить выполнение",
        "task_initializing": "💭 *Инициализирую задачу...*",
        "task_in_progress": "⚠️ Агент уже выполняет задачу. Дождитесь завершения или используйте /cancel.",
        "task_cancelled": "⏹ **Команда отмены отправлена.** Задача останавливается...",
        "no_active_task": "ℹ️ В данный момент нет активных выполняющихся задач.",

        # Language
        "lang_menu_title": "🌐 **Выберите язык интерфейса / Select interface language:**",
        "lang_switched": "🇷🇺 Язык интерфейса переключен на русский!",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        # Accounts
        "accounts_title": "🔑 **Менеджер Google Аккаунтов (Antigravity):**",
        "active_account": "Активный аккаунт",
        "not_authenticated": "Не авторизован",
        "accounts_list": "Сохранённые аккаунты",
        "no_saved_accounts": "Нет сохранённых аккаунтов",
        "btn_login_new": "➕ Войти в новый аккаунт",
        "btn_delete_accounts": "🗑 Удалить...",
        "btn_back_to_accounts": "⬅️ Назад к аккаунтам",
        "account_switched_alert": "Аккаунт переключен: {email}",
    },
    "en": {
        # Reply Keyboard
        "btn_new_chat": "➕ New Chat",
        "btn_projects": "📂 Projects",
        "btn_sessions": "💬 Sessions",
        "btn_tasks": "⏰ Tasks",
        "btn_actions": "⚡ Actions",
        "btn_accounts": "🔑 Accounts",
        "btn_language": "🌐 Language",
        "btn_miniapp": "🎛 Control Panel (Mini App)",

        # Start & Welcome
        "start_title": "👋 **Welcome to Gravigram!**",
        "start_desc": "Universal personal Google Antigravity AI agent control plane directly inside Telegram.",
        "active_project": "Active project",
        "project_path": "Path",
        "current_session": "Current session",
        "not_selected": "None",
        "new_chat": "New conversation",
        "start_hint": "💡 *Send me a text message, voice note, or screenshot with your task.*",

        # Help
        "help_title": "🛠 **Available Commands:**",
        "help_new": "➕ `/new` — Start a new clean conversation in the active project",
        "help_projects": "📂 `/projects` — Select or add a workspace project",
        "help_chats": "💬 `/chats` — List saved conversations in the active project",
        "help_tasks": "⏰ `/tasks` (or `/schedule`) — Scheduled agent automations",
        "help_add_task": "➕ `/add_task <time/cron> <prompt>` — Create a scheduled task",
        "help_mode": "⚙️ `/mode` — Settings (AI model, autonomy & confirmation)",
        "help_quick": "⚡ `/quick` — Quick diagnostic actions (OS status, git, tests)",
        "help_lang": "🌐 `/lang` — Toggle interface language (EN / RU)",
        "help_login": "🔑 `/login` — Authenticate / switch Google Antigravity account",
        "help_add_model": "➕ `/add_model <id> [Title]` — Register a new custom model",
        "help_cancel": "⏹ `/cancel` — Interrupt the currently running task",
        "help_status": "📊 `/status` — Overview of environment, model, and status",

        # Projects
        "choose_project": "📂 **Select active project:**",
        "project_changed": "📂 **Active project changed:**",
        "btn_add_project": "➕ Add project by path",
        "add_project_help": "📝 To add a new project, send a message formatted as:\n`/add_project <Name> <Path to folder>`\n\n*Example:* `/add_project MyBot D:\\Projects\\my_bot`",
        "no_active_project": "⚠️ Please select or create a project first via `/projects`.",
        "project_selected_alert": "Selected project: {name}",

        # Sessions
        "sessions_in_project": "💬 **Conversations in project '{name}':**",
        "session_switched": "💬 **Active conversation switched:** `{title}`",
        "btn_new_session": "➕ Create new conversation",
        "session_created": "✨ **New conversation created in '{name}'!**\nContext has been reset. All future messages belong to this new thread.",
        "session_selected_alert": "Conversation: {title}",
        "session_deleted": "🗑 Session deleted.",
        "session_created_alert": "New session created",

        # Tasks
        "no_tasks": "⏰ **No scheduled agent tasks yet.**\n\n💡 To create a task, use:\n`/add_task 09:00 Check server health and disk usage`\nor ask the agent in chat directly.",
        "tasks_header": "⏰ **Scheduled AI Agent Tasks:**",
        "task_format_error": "📝 **Command format:** `/add_task <time/cron> <Agent task description>`\n\n*Examples:*\n• `/add_task 08:30 Run project tests and summarize report`\n• `/add_task 09:00 Check Proxmox containers and storage`\n• `/add_task 0 18 * * 5 Review weekly git commits`",
        "task_created": "✅ **Task scheduled!**",
        "task_title": "Title",
        "task_schedule": "Schedule",
        "task_project": "Project",
        "task_prompt": "Agent Prompt",
        "task_next_run": "Next run",
        "task_btn_run": "⚡ Run Now",
        "task_btn_pause": "⏸ Pause",
        "task_btn_resume": "▶ Resume",
        "task_btn_delete": "🗑 Delete",

        # Mode & Settings
        "settings_header": "⚙️ **Gravigram Settings:**",
        "current_model": "Current model",
        "mode_label": "Mode",
        "mode_autonomous": "Autonomous (/auto)",
        "mode_confirm": "With confirmation (/confirm)",
        "btn_select_model": "🤖 Select AI Model",
        "model_default": "Default (Antigravity Auto)",
        "btn_back_to_settings": "🔙 Back to settings",
        "mode_switched": "Safety mode: {mode}",
        "model_switched": "Model changed to: {model}",

        # Quick Actions
        "quick_actions_title": "⚡ **Quick Actions:**\n\nSelect a diagnostic task for the agent:",
        "btn_sys_status": "📊 System Status (RAM/Disk)",
        "btn_git_status": "🔍 Git Status",
        "btn_list_files": "📁 Project Files",
        "btn_run_tests": "🧪 Run Tests",

        # Confirm & Control
        "confirm_header": "⚠️ **Action Confirmation Required**",
        "btn_allow": "✅ Allow",
        "btn_reject": "❌ Reject",
        "btn_cancel_task": "⏹ Stop Execution",
        "task_initializing": "💭 *Initializing task...*",
        "task_in_progress": "⚠️ Agent is already executing a task. Wait for completion or use /cancel.",
        "task_cancelled": "⏹ **Cancel signal sent.** Task is stopping...",
        "no_active_task": "ℹ️ No active tasks running right now.",

        # Language
        "lang_menu_title": "🌐 **Select interface language / Выберите язык интерфейса:**",
        "lang_switched": "🇬🇧 Interface language switched to English!",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        # Accounts
        "accounts_title": "🔑 **Google Accounts Manager (Antigravity):**",
        "active_account": "Active account",
        "not_authenticated": "Not authenticated",
        "accounts_list": "Saved accounts",
        "no_saved_accounts": "No saved accounts",
        "btn_login_new": "➕ Add new account",
        "btn_delete_accounts": "🗑 Delete...",
        "btn_back_to_accounts": "⬅️ Back to accounts",
        "account_switched_alert": "Account switched: {email}",
    }
}

def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Translates a key into the target language, falling back to 'ru', then 'en', then key."""
    lang_dict = TRANSLATIONS.get(lang.lower(), TRANSLATIONS["ru"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["ru"].get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

async def resolve_lang(user_lang_code: Optional[str] = None) -> str:
    """Resolves language: DB setting first, then user's telegram language code, defaults to 'ru'."""
    db_lang = await get_language()
    if db_lang in ("ru", "en"):
        return db_lang
    if user_lang_code:
        if user_lang_code.lower().startswith("ru"):
            return "ru"
        return "en"
    return "ru"
