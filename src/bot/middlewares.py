import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from src.config import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Restricts access to the bot strictly to TELEGRAM_ADMIN_ID.
    
    Fail-closed: if admin_id is not configured (<=0), ALL users are denied.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        admin_id = settings.telegram_admin_id

        # Fail-closed: if admin_id is not configured, deny everyone
        if admin_id <= 0:
            logger.error(
                f"SECURITY: telegram_admin_id not configured (={admin_id}). "
                f"Denying access to user_id={user.id} (@{user.username}). "
                f"Set TELEGRAM_ADMIN_ID in .env to enable the bot."
            )
            if isinstance(event, Message):
                await event.answer("⛔ Бот не настроен: TELEGRAM_ADMIN_ID не задан. Доступ заблокирован.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Бот не настроен.", show_alert=True)
            return None

        # Check if user matches the configured admin
        if user.id != admin_id:
            logger.warning(f"Unauthorized access attempt from user_id={user.id} (@{user.username})")
            if isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён. Этот бот является персональным ассистентом.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён.", show_alert=True)
            return None

        return await handler(event, data)
