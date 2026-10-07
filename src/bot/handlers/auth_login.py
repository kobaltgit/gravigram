import asyncio
import re
import logging
from typing import Dict, Any, Optional
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, BaseFilter
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.agent.manager import agent_manager
from src.agent.accounts import (
    list_accounts, switch_account, remove_account, sync_current_account_to_vault,
    generate_google_auth_url, exchange_code_for_tokens, save_new_account_credentials,
    DEFAULT_REDIRECT_URI
)
from src.bot.keyboards import (
    get_accounts_inline_keyboard, get_delete_account_inline_keyboard
)

logger = logging.getLogger(__name__)

router = Router(name="auth_login")

# Storage for pending authentication sessions by chat_id
# schema: { chat_id: {"process": Process, "url": str, "started_at": float} }
pending_auth: Dict[int, Dict[str, Any]] = {}

class IsWaitingAuthCode(BaseFilter):
    """Filters messages if this chat is actively waiting for an agy OAuth code."""
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id in pending_auth


async def is_agy_authenticated(agy_bin: str) -> bool:
    """Checks whether agy CLI has valid authentication by querying models."""
    try:
        proc = await asyncio.create_subprocess_exec(
            agy_bin, "models",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=12.0)
            return proc.returncode == 0 and b"gemini" in stdout.lower()
        except asyncio.TimeoutError:
            proc.kill()
            return False
    except Exception as e:
        logger.warning(f"Failed to check agy auth: {e}")
        return False


def build_accounts_menu_text(lang: str = "ru") -> str:
    """Builds the formatted text for the accounts control screen."""
    data = list_accounts()
    active = data.get("active")
    accounts = data.get("accounts", [])

    status_icon = "🟢" if active else "🔴"
    not_auth_label = "_Not authenticated_" if lang == "en" else "_Не авторизован_"
    active_display = f"`{active}`" if active else not_auth_label

    if lang == "en":
        lines = [
            "👤 **Google Accounts Management (Antigravity)**\n",
            f"{status_icon} **Current active profile:**",
            f"{active_display}\n",
        ]
        if accounts:
            lines.append(f"📁 **Saved accounts ({len(accounts)}):**")
            for acc in accounts:
                marker = "✅" if acc == active else "▫️"
                lines.append(f"{marker} `{acc}`")
            lines.append("\n👇 _Click an account below for 1-click switching, or add a new one:_")
        else:
            lines.append("⚠️ No saved profiles. Click the button below to log in:")
    else:
        lines = [
            "👤 **Управление Google аккаунтами (Antigravity)**\n",
            f"{status_icon} **Текущий активный профиль:**",
            f"{active_display}\n",
        ]
        if accounts:
            lines.append(f"📁 **Сохранённые аккаунты ({len(accounts)}):**")
            for acc in accounts:
                marker = "✅" if acc == active else "▫️"
                lines.append(f"{marker} `{acc}`")
            lines.append("\n👇 _Нажмите на аккаунт в списке ниже для переключения в 1 клик, или привяжите новый:_")
        else:
            lines.append("⚠️ Нет сохранённых профилей. Нажмите кнопку ниже для первого входа:")

    return "\n".join(lines)


@router.message(F.text.in_(["🔑 Аккаунты", "🔑 Accounts"]))
@router.message(Command("accounts"))
@router.message(Command("login"))
async def cmd_accounts_menu(message: types.Message):
    """Shows the multi-account management dashboard."""
    from src.i18n import resolve_lang
    lang = await resolve_lang(message.from_user.language_code if message.from_user else None)
    data = list_accounts()
    text = build_accounts_menu_text(lang=lang)
    kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []), lang=lang)
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


@router.callback_query(F.data == "acc_back")
async def cb_acc_back(query: types.CallbackQuery):
    """Returns to the main accounts menu."""
    await query.answer()
    from src.i18n import resolve_lang
    lang = await resolve_lang(query.from_user.language_code if query.from_user else None)
    data = list_accounts()
    text = build_accounts_menu_text(lang=lang)
    kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []), lang=lang)
    if query.message:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


@router.callback_query(F.data.startswith("acc_active:"))
async def cb_acc_already_active(query: types.CallbackQuery):
    """User clicked on the currently active account."""
    acc = query.data.split(":", 1)[1]
    from src.i18n import resolve_lang
    lang = await resolve_lang(query.from_user.language_code if query.from_user else None)
    msg = f"Account {acc} is already active ✅" if lang == "en" else f"Аккаунт {acc} уже активен ✅"
    await query.answer(msg, show_alert=False)


@router.callback_query(F.data.startswith("acc_switch:"))
async def cb_acc_switch(query: types.CallbackQuery):
    """Switches active Google account in 1 click."""
    from src.i18n import resolve_lang
    lang = await resolve_lang(query.from_user.language_code if query.from_user else None)
    target_email = query.data.split(":", 1)[1]
    success = switch_account(target_email)

    if success:
        msg = f"✅ Switched to {target_email}!" if lang == "en" else f"✅ Переключено на {target_email}!"
        await query.answer(msg, show_alert=True)
        data = list_accounts()
        text = build_accounts_menu_text(lang=lang)
        kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []), lang=lang)
        if query.message:
            await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        err = f"Failed to switch to {target_email}" if lang == "en" else f"Не удалось переключить на {target_email}"
        await query.answer(err, show_alert=True)


@router.callback_query(F.data == "acc_delete_menu")
async def cb_acc_delete_menu(query: types.CallbackQuery):
    """Shows list of accounts available to delete."""
    await query.answer()
    data = list_accounts()
    active = data.get("active")
    accounts = data.get("accounts", [])
    
    text = (
        "🗑 **Удаление сохранённых аккаунтов**\n\n"
        "Выберите аккаунт, который хотите отвязать и удалить из списка.\n"
        "_(Активный в данный момент аккаунт удалить нельзя — сначала переключитесь на другой)_"
    )
    kb = get_delete_account_inline_keyboard(active, accounts)
    if query.message:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


@router.callback_query(F.data.startswith("acc_del_confirm:"))
async def cb_acc_del_confirm(query: types.CallbackQuery):
    """Deletes an account from vault."""
    target_email = query.data.split(":", 1)[1]
    removed = remove_account(target_email)
    
    if removed:
        await query.answer(f"Аккаунт {target_email} удалён.", show_alert=True)
    else:
        await query.answer("Не удалось удалить аккаунт.", show_alert=True)

    data = list_accounts()
    text = build_accounts_menu_text()
    kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []))
    if query.message:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


@router.callback_query(F.data.in_(["acc_add", "auth_relogin"]))
async def cb_acc_add(query: types.CallbackQuery, bot: Bot):
    """Starts the OAuth flow to link a new Google account."""
    await query.answer()
    if query.message:
        await start_auth_flow(query.message, bot)


@router.callback_query(F.data == "acc_cancel_login")
async def cb_acc_cancel_login(query: types.CallbackQuery):
    """Cancels ongoing login flow."""
    chat_id = query.message.chat.id if query.message else None
    if chat_id and chat_id in pending_auth:
        pending_auth.pop(chat_id, None)
    await query.answer("Авторизация отменена.")
    data = list_accounts()
    text = build_accounts_menu_text()
    kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []))
    if query.message:
        await query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# Background server on port 8085 for automatic loopback callbacks
_auth_server_runner = None

async def ensure_auth_callback_server(bot: Bot):
    """Starts local loopback server on port 8085 to catch automatic OAuth redirect."""
    global _auth_server_runner
    if _auth_server_runner is not None:
        return

    from aiohttp import web
    app = web.Application()

    async def handle_callback(request: web.Request):
        code = request.query.get("code")
        error = request.query.get("error")
        if error:
            html = f"<html><body><h2 style='color:red;'>Ошибка авторизации: {error}</h2></body></html>"
            return web.Response(text=html, content_type="text/html")

        if not code:
            return web.Response(text="<html><body><h2>Код не получен.</h2></body></html>", content_type="text/html")

        token_data = await exchange_code_for_tokens(code, redirect_uri=DEFAULT_REDIRECT_URI)
        if not token_data or "access_token" not in token_data:
            return web.Response(text="<html><body><h2 style='color:red;'>Ошибка обмена кода на токены.</h2></body></html>", content_type="text/html")

        new_email = save_new_account_credentials(token_data)

        # Notify waiting chat_ids
        active_chats = list(pending_auth.keys())
        for chat_id in active_chats:
            pending_auth.pop(chat_id, None)
            try:
                data = list_accounts()
                kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []))
                await bot.send_message(
                    chat_id,
                    f"🎉 **Аккаунт `{new_email or 'Google'}` успешно подключен и активирован!**\n\n"
                    "Профиль сохранён в хранилище. Теперь вы можете переключаться между аккаунтами в 1 клик в меню «🔑 Аккаунты».",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb
                )
            except Exception as e:
                logger.error(f"Failed to notify chat {chat_id} of successful auth: {e}")

        success_html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Авторизация успешна</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding-top: 50px;">
          <h2 style="color: #2e7d32;">✅ Авторизация Google успешно завершена!</h2>
          <p style="font-size: 16px; color: #555;">Профиль сохранён в Antigravity. Можете закрыть эту вкладку и вернуться в Telegram.</p>
        </body>
        </html>
        """
        return web.Response(text=success_html, content_type="text/html")

    app.router.add_get("/auth/callback", handle_callback)

    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 8085)
        await site.start()
        _auth_server_runner = runner
        logger.info("OAuth local callback receiver running on http://127.0.0.1:8085/auth/callback")
    except Exception as e:
        logger.warning(f"Could not start OAuth loopback server on port 8085: {e}")


async def start_auth_flow(message: types.Message, bot: Bot):
    """Initiates direct Google OAuth 2.0 flow and prompts user with the auth URL."""
    chat_id = message.chat.id

    # Backup current account to vault so nothing is ever lost
    sync_current_account_to_vault()

    auth_url = generate_google_auth_url(DEFAULT_REDIRECT_URI)

    # Set pending auth state for this chat
    pending_auth[chat_id] = {
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "started_at": asyncio.get_event_loop().time(),
    }

    # Start loopback listener if possible
    await ensure_auth_callback_server(bot)

    auth_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Войти через Google", url=auth_url)
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="acc_cancel_login")
            ]
        ]
    )

    auth_text = (
        "🔐 **Авторизация нового Google аккаунта**\n\n"
        "Для подключения аккаунта выполните 3 простых шага:\n\n"
        "1️⃣ Нажмите кнопку **«🌐 Войти через Google»** ниже или откройте ссылку:\n"
        f"👉 [Ссылка для входа в Google]({auth_url})\n\n"
        "2️⃣ Выберите нужный Google аккаунт и разрешите доступ.\n\n"
        "3️⃣ После подтверждения в браузере:\n"
        "• Если вы входите с этого же ПК — вход подхватится автоматически.\n"
        "• Если вход выполняется с телефона/другого устройства — скопируйте **всю ссылку из адресной строки браузера** (вида `http://localhost:8085/auth/callback?code=...`) или сам **код** и **отправьте сообщением в этот чат**.\n\n"
        "_Для отмены нажмите «❌ Отмена» или отправьте /cancel_"
    )

    await message.answer(
        auth_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=auth_kb,
        disable_web_page_preview=True
    )


@router.message(Command("cancel_login"))
async def cmd_cancel_login(message: types.Message):
    """Cancels an ongoing authentication process."""
    chat_id = message.chat.id
    if chat_id in pending_auth:
        pending_auth.pop(chat_id, None)
        await message.answer("🛑 Процесс авторизации отменён.")
    else:
        await message.answer("Активных процессов авторизации нет.")


@router.message(IsWaitingAuthCode())
async def handle_auth_code_submission(message: types.Message, bot: Bot):
    """Receives the authorization key/code or redirect URL from the user."""
    chat_id = message.chat.id
    session = pending_auth.pop(chat_id, None)

    if not session:
        return

    text = message.text.strip()
    if text.startswith("/"):
        await message.answer("🛑 Авторизация отменена.")
        return

    status_msg = await message.answer("⏳ Проверяю код и получаю токены от Google...")

    redirect_uri = session.get("redirect_uri", DEFAULT_REDIRECT_URI)
    token_data = await exchange_code_for_tokens(text, redirect_uri=redirect_uri)

    if not token_data or "access_token" not in token_data:
        # Restore pending session so user can retry or cancel
        pending_auth[chat_id] = session
        await status_msg.edit_text(
            "❌ **Не удалось подтвердить код в Google.**\n\n"
            "Возможные причины:\n"
            "• Код был скопирован не полностью\n"
            "• Истёк срок действия одноразового кода\n\n"
            "👉 Попробуйте скопировать ссылку из адресной строки браузера целиком или нажмите /cancel_login для отмены.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    new_email = save_new_account_credentials(token_data)
    data = list_accounts()
    kb = get_accounts_inline_keyboard(data.get("active"), data.get("accounts", []))

    if new_email:
        await status_msg.edit_text(
            f"🎉 **Аккаунт `{new_email}` успешно подключен и сохранён!**\n\n"
            f"Текущий активный профиль Antigravity переключен на `{new_email}`.\n"
            "Вы можете в любой момент переключаться между аккаунтами в меню «🔑 Аккаунты».",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
    else:
        await status_msg.edit_text(
            "⚠️ **Токены получены, но не удалось определить Email аккаунта.**\n"
            "Учётные данные сохранены в хранилище.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
