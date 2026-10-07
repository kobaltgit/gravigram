from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from typing import List, Dict, Any, Optional
from src.i18n import t

def get_main_reply_keyboard(webapp_url: Optional[str] = None, lang: str = "ru") -> ReplyKeyboardMarkup:
    """Bottom persistent menu for quick navigation with bilingual support."""
    keyboard = [
        [
            KeyboardButton(text=t("btn_new_chat", lang)),
            KeyboardButton(text=t("btn_projects", lang)),
            KeyboardButton(text=t("btn_sessions", lang)),
        ],
        [
            KeyboardButton(text=t("btn_tasks", lang)),
            KeyboardButton(text=t("btn_actions", lang)),
            KeyboardButton(text=t("btn_accounts", lang)),
        ],
        [
            KeyboardButton(text=f"🌐 {t('btn_language', lang)} (RU/EN)"),
        ]
    ]
    if webapp_url:
        keyboard.insert(0, [KeyboardButton(text=t("btn_miniapp", lang), web_app=WebAppInfo(url=webapp_url))])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for switching interface language."""
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_quick_actions_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Quick devops / inspection actions for the agent."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_sys_status", lang), callback_data="quick:sys_status"),
            InlineKeyboardButton(text=t("btn_git_status", lang), callback_data="quick:git_status"),
        ],
        [
            InlineKeyboardButton(text=t("btn_list_files", lang), callback_data="quick:list_files"),
            InlineKeyboardButton(text=t("btn_run_tests", lang), callback_data="quick:run_tests"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_projects_inline_keyboard(projects: List[Dict[str, Any]], lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline menu of projects for fast switching."""
    buttons = []
    for p in projects:
        status = "✅ " if p.get("is_active") else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{status}{p['name']}",
                callback_data=f"proj_select:{p['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_add_project", lang), callback_data="proj_add")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_sessions_inline_keyboard(sessions: List[Dict[str, Any]], lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline menu of sessions for the current project."""
    buttons = []
    for s in sessions:
        status = "✅ " if s.get("is_active") else ""
        title = s['title'][:20] + ("..." if len(s['title']) > 20 else "")
        buttons.append([
            InlineKeyboardButton(
                text=f"{status}{title}",
                callback_data=f"sess_select:{s['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"sess_del:{s['id']}"
            ),
        ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_new_session", lang), callback_data="sess_new")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tasks_inline_keyboard(tasks: List[Dict[str, Any]], lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline list of scheduled agent tasks."""
    buttons = []
    for t_item in tasks:
        is_act = t_item.get("is_active", 1) == 1
        status_icon = "🟢" if is_act else "⚪"
        cron = t_item.get("cron_expression", "")
        title = t_item.get("title", f"Task #{t_item['id']}")
        
        # Row 1: Title and cron
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {title} ({cron})",
                callback_data=f"task_view:{t_item['id']}"
            )
        ])
        # Row 2: Actions (Toggle, Run Now, Delete)
        buttons.append([
            InlineKeyboardButton(text=t("task_btn_run", lang), callback_data=f"task_run:{t_item['id']}"),
            InlineKeyboardButton(text=t("task_btn_pause", lang) if is_act else t("task_btn_resume", lang), callback_data=f"task_toggle:{t_item['id']}"),
            InlineKeyboardButton(text=t("task_btn_delete", lang), callback_data=f"task_del:{t_item['id']}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_mode_inline_keyboard(confirm_mode: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline toggle for autonomy modes."""
    auto_icon = "⚪" if confirm_mode else "🟢"
    confirm_icon = "🟢" if confirm_mode else "⚪"
    buttons = [
        [
            InlineKeyboardButton(text=f"{auto_icon} {t('mode_autonomous', lang)}", callback_data="mode_auto"),
            InlineKeyboardButton(text=f"{confirm_icon} {t('mode_confirm', lang)}", callback_data="mode_confirm"),
        ],
        [
            InlineKeyboardButton(text=t("btn_select_model", lang), callback_data="models_list")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_models_inline_keyboard(models: List[Dict[str, Any]], current_model: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline list of Antigravity AI models."""
    buttons = []
    for m in models:
        m_id = m.get("id", "")
        m_name = m.get("name", m_id)
        is_selected = (current_model == m_id)
        prefix = "✅ " if is_selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix}{m_name}",
                callback_data=f"set_model:{m_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_back_to_settings", lang), callback_data="mode_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_action_keyboard(confirm_id: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Buttons to approve or reject a command in confirm mode."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_allow", lang), callback_data=f"conf_yes:{confirm_id}"),
            InlineKeyboardButton(text=t("btn_reject", lang), callback_data=f"conf_no:{confirm_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Button to stop active task."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_cancel_task", lang), callback_data="task_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_accounts_inline_keyboard(active: Optional[str], accounts: List[str], lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline menu of Google accounts for 1-click switching."""
    buttons = []
    for acc in accounts:
        is_active = (acc == active)
        status_icon = "✅ " if is_active else "🔄 "
        label = f"{status_icon}{acc}"
        cb_data = f"acc_active:{acc}" if is_active else f"acc_switch:{acc}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=cb_data)])

    # Action buttons
    action_row = [
        InlineKeyboardButton(text=t("btn_login_new", lang), callback_data="acc_add"),
    ]
    if len(accounts) > 1:
        action_row.append(InlineKeyboardButton(text=t("btn_delete_accounts", lang), callback_data="acc_delete_menu"))
    buttons.append(action_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_delete_account_inline_keyboard(active: Optional[str], accounts: List[str], lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline menu for selecting an account to delete."""
    buttons = []
    for acc in accounts:
        if acc != active:
            buttons.append([
                InlineKeyboardButton(text=f"❌ {t('task_btn_delete', lang)} {acc}", callback_data=f"acc_del_confirm:{acc}")
            ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_back_to_accounts", lang), callback_data="acc_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
