import os
import sys
import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.config import settings
from src.database import init_db
from src.agent.scheduler import agent_scheduler
from src.bot.middlewares import AuthMiddleware
from src.bot.commands import router as commands_router
from src.bot.handlers.chat import router as chat_router
from src.bot.handlers.callbacks import router as callbacks_router
from src.bot.handlers.auth_login import router as auth_login_router
from src.server.app import app as fastapi_app

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError in logs
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("antigravity_bot")

async def start_bot(dp: Dispatcher, bot: Bot):
    """Starts Telegram bot polling with automatic reconnection on network errors."""
    logger.info("Starting Telegram Bot (Long Polling)...")
    while True:
        try:
            await dp.start_polling(bot)
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Telegram Bot network/polling error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

async def start_server():
    """Starts FastAPI web server for Mini App."""
    config = uvicorn.Config(
        app=fastapi_app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting FastAPI server on http://{settings.host}:{settings.port}...")
    await server.serve()

async def main():
    logger.info("Initializing database...")
    await init_db()

    token = settings.telegram_bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or token.startswith("1234567890:ABC"):
        logger.warning(
            "⚠️ TELEGRAM_BOT_TOKEN is not set or using example value in .env!\n"
            "Telegram bot polling will be skipped, but Web Server will start.\n"
            "Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_ID in .env file."
        )
        await start_server()
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Register Middlewares
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register Routers
    dp.include_router(commands_router)
    dp.include_router(auth_login_router)
    dp.include_router(callbacks_router)
    dp.include_router(chat_router)

    # Initialize and start Background Agent Scheduler
    agent_scheduler.set_bot(bot)
    agent_scheduler.start()

    try:
        # Run Bot Polling and FastAPI Server concurrently
        await asyncio.gather(
            start_bot(dp, bot),
            start_server(),
        )
    finally:
        agent_scheduler.stop()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application stopped.")
