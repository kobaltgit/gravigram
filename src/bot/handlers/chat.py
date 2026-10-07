import os
import tempfile
import logging
from pathlib import Path
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode

from src.config import settings
from src.agent.executor import TelegramStreamHandler
from src.agent.manager import agent_manager
from src.bot.keyboards import get_cancel_keyboard, get_confirm_action_keyboard
from src.bot.commands import cmd_new, cmd_projects, cmd_sessions

router = Router(name="chat")
logger = logging.getLogger(__name__)

from src.bot.formatter import markdown_to_telegram_html

async def safe_edit(msg: types.Message, text: str, reply_markup=None):
    """Converts LLM Markdown to Telegram HTML and edits message with fallback."""
    formatted = markdown_to_telegram_html(text)
    try:
        await msg.edit_text(formatted, parse_mode=ParseMode.HTML, reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception as e1:
        if "message is not modified" in str(e1).lower():
            return
        try:
            await msg.edit_text(text, parse_mode=None, reply_markup=reply_markup, disable_web_page_preview=True)
        except Exception as e2:
            if "message is not modified" not in str(e2).lower():
                logger.warning(f"safe_edit failed: {e2}")

async def safe_send(bot: Bot, chat_id: int, text: str, reply_markup=None):
    """Converts LLM Markdown to Telegram HTML and sends message with fallback."""
    formatted = markdown_to_telegram_html(text)
    try:
        return await bot.send_message(chat_id=chat_id, text=formatted, parse_mode=ParseMode.HTML, reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception:
        try:
            return await bot.send_message(chat_id=chat_id, text=text, parse_mode=None, reply_markup=reply_markup, disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"safe_send failed: {e}")

async def deliver_created_artifacts(bot: Bot, chat_id: int, files: list):
    """Automatically sends newly created files/reports as Telegram documents."""
    if not files:
        return
    from aiogram.types import FSInputFile
    for fpath in files:
        p = Path(fpath)
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            try:
                doc = FSInputFile(str(p), filename=p.name)
                await bot.send_document(
                    chat_id=chat_id,
                    document=doc,
                    caption=f"📄 **Создан файл:** `{p.name}`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.warning(f"Failed to auto-deliver artifact {p.name}: {e}")

@router.message(F.text.in_(["➕ Новая беседа", "➕ New Chat"]))
async def btn_new_chat(message: types.Message):
    await cmd_new(message)

@router.message(F.text.in_(["📂 Проекты", "📂 Projects"]))
async def btn_projects(message: types.Message):
    await cmd_projects(message)

@router.message(F.text.in_(["💬 Сессии", "💬 Sessions"]))
async def btn_sessions(message: types.Message):
    await cmd_sessions(message)

@router.message(F.text.in_(["⏰ Задания", "⏰ Tasks"]))
async def btn_tasks(message: types.Message):
    from src.bot.commands import cmd_tasks
    await cmd_tasks(message)

@router.message(F.text.in_(["⚡ Действия", "⚡ Actions"]))
async def btn_quick_actions(message: types.Message):
    from src.bot.commands import cmd_quick
    await cmd_quick(message)

@router.message(F.text.in_(["🔑 Аккаунты", "🔑 Accounts"]))
async def btn_accounts(message: types.Message):
    from src.bot.handlers.auth_login import cmd_accounts_menu
    await cmd_accounts_menu(message)

@router.message(F.text.startswith("🌐 "))
async def btn_language(message: types.Message):
    from src.bot.commands import cmd_language
    await cmd_language(message)

async def run_prompt_with_streaming(
    chat_id: int,
    bot: Bot,
    prompt_text: str,
    initial_status: str = "💭 *Инициализирую задачу...*",
    status_msg: types.Message = None
):
    """Executes an agent turn with real-time streaming, confirmation callbacks, and artifact delivery."""
    if agent_manager.is_task_running(chat_id):
        await bot.send_message(
            chat_id=chat_id,
            text="⏳ **Агент уже выполняет задачу.**\nПожалуйста, дождитесь окончания или нажмите /cancel для отмены."
        )
        return

    if not status_msg:
        status_msg = await bot.send_message(chat_id=chat_id, text=initial_status, parse_mode=ParseMode.MARKDOWN)

    async def update_tg(text: str):
        await safe_edit(status_msg, text, reply_markup=get_cancel_keyboard())

    stream_handler = TelegramStreamHandler(update_callback=update_tg)

    async def confirm_callback(confirm_id: str, description: str, tool_name: str):
        await bot.send_message(
            chat_id=chat_id,
            text=f"🔐 **Запрос подтверждения:**\n\n{description}\n\n_Разрешить выполнение?_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirm_action_keyboard(confirm_id),
        )

    try:
        final_result = await agent_manager.execute_turn(
            chat_id=chat_id,
            prompt=prompt_text,
            stream_handler=stream_handler,
            request_confirm_callback=confirm_callback,
        )
        if final_result and final_result.strip():
            if len(final_result) <= 3900:
                await safe_edit(status_msg, final_result)
            else:
                try:
                    await status_msg.delete()
                except Exception:
                    pass
                for chunk in [final_result[i:i+3900] for i in range(0, len(final_result), 3900)]:
                    await safe_send(bot, chat_id, chunk)
        else:
            await safe_edit(status_msg, "⚠️ Агент завершил работу без ответа (возможно, исчерпан лимит квоты модели).")

        # Deliver any artifacts created during execution
        await deliver_created_artifacts(bot, chat_id, stream_handler.created_files)
    except Exception as e:
        logger.exception("Turn execution failed:")
        await safe_edit(status_msg, f"⚠️ Ошибка выполнения: {str(e)}")

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message, bot: Bot):
    """Processes user text prompt, starts agent turn with live streaming."""
    await run_prompt_with_streaming(
        chat_id=message.chat.id,
        bot=bot,
        prompt_text=message.text
    )

@router.message(F.voice)
async def handle_voice_message(message: types.Message, bot: Bot):
    """Downloads voice message, transcribes locally via faster-whisper, and responds with text + voice."""
    if agent_manager.is_task_running(message.chat.id):
        await message.answer("⏳ **Агент занят.** Дождитесь завершения или используйте /cancel.")
        return

    status_msg = await message.answer("🎙 *Слушаю и расшифровываю голосовое сообщение...*", parse_mode=ParseMode.MARKDOWN)

    with tempfile.TemporaryDirectory() as tmpdir:
        voice_file_path = Path(tmpdir) / f"{message.voice.file_unique_id}.ogg"
        await bot.download(message.voice, destination=voice_file_path)

        try:
            from src.agent.transcriber import transcribe_audio_file
            transcribed_text = await transcribe_audio_file(str(voice_file_path))
            
            if not transcribed_text:
                await safe_edit(status_msg, "❌ Не удалось распознать речь в голосовом сообщении.")
                return

            await safe_edit(status_msg, f"🎙 **Распознано:**\n_«{transcribed_text}»_\n\n💭 *Приступаю к выполнению...*")

        except Exception as e:
            logger.exception("Voice transcription failed:")
            await safe_edit(status_msg, f"❌ Ошибка транскрипции голоса: {str(e)}")
            return

    # Execute transcribed text as agent prompt
    async def update_tg(text: str):
        full = f"🎙 **Распознано:** _«{transcribed_text}»_\n\n{text}"
        await safe_edit(status_msg, full, reply_markup=get_cancel_keyboard())

    stream_handler = TelegramStreamHandler(update_callback=update_tg)

    async def confirm_callback(confirm_id: str, description: str, tool_name: str):
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"🔐 **Запрос подтверждения:**\n\n{description}\n\n_Разрешить выполнение?_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirm_action_keyboard(confirm_id),
        )

    try:
        final_result = await agent_manager.execute_turn(
            chat_id=message.chat.id,
            prompt=transcribed_text,
            stream_handler=stream_handler,
            request_confirm_callback=confirm_callback,
        )
        if final_result and final_result.strip():
            full = f"🎙 **Распознано:** _«{transcribed_text}»_\n\n{final_result}"
            if len(full) <= 3900:
                await safe_edit(status_msg, full)
            else:
                await safe_edit(status_msg, f"🎙 **Распознано:** _«{transcribed_text}»_\n\n(Ответ ниже):")
                for i in range(0, len(final_result), 3900):
                    part = final_result[i:i+3900]
                    await safe_send(bot, message.chat.id, part)
        else:
            await safe_edit(status_msg, f"🎙 **Распознано:** _«{transcribed_text}»_\n\n⚠️ Агент завершил работу без ответа.")

        # Deliver any artifacts created during voice execution
        await deliver_created_artifacts(bot, message.chat.id, stream_handler.created_files)

    except Exception as e:
        await safe_edit(status_msg, f"⚠️ Ошибка выполнения: {str(e)}")

@router.message(F.photo)
async def handle_photo_message(message: types.Message, bot: Bot):
    """Handles screenshots or images sent with task caption."""
    if agent_manager.is_task_running(message.chat.id):
        await message.answer("⏳ **Агент занят.** Дождитесь завершения или используйте /cancel.")
        return

    caption = message.caption or "Проанализируй этот скриншот/изображение и скажи, что на нём."
    status_msg = await message.answer("🖼 *Загружаю и анализирую изображение...*", parse_mode=ParseMode.MARKDOWN)

    with tempfile.TemporaryDirectory() as tmpdir:
        photo = message.photo[-1] # Highest resolution
        photo_path = Path(tmpdir) / f"{photo.file_unique_id}.jpg"
        await bot.download(photo, destination=photo_path)

        async def update_tg(text: str):
            await safe_edit(status_msg, text)

        stream_handler = TelegramStreamHandler(update_callback=update_tg)

        async def confirm_callback(confirm_id: str, description: str, tool_name: str):
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"🔐 **Запрос подтверждения:**\n\n{description}\n\n_Разрешить выполнение?_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirm_action_keyboard(confirm_id),
            )

        try:
            final_result = await agent_manager.execute_turn(
                chat_id=message.chat.id,
                prompt=caption,
                stream_handler=stream_handler,
                request_confirm_callback=confirm_callback,
                image_paths=[str(photo_path)],
            )
            if final_result and final_result.strip():
                await safe_edit(status_msg, final_result)
            else:
                await safe_edit(status_msg, "⚠️ Агент завершил работу без ответа (проверьте квоту модели).")

            # Deliver any artifacts created during photo execution
            await deliver_created_artifacts(bot, message.chat.id, stream_handler.created_files)

        except Exception as e:
            await safe_edit(status_msg, f"⚠️ Ошибка обработки: {str(e)}")

@router.message(F.document)
async def handle_document_message(message: types.Message, bot: Bot):
    """Handles incoming document files (logs, python scripts, text, json, configs)."""
    if agent_manager.is_task_running(message.chat.id):
        await message.answer("⏳ **Агент занят.** Дождитесь завершения или используйте /cancel.")
        return

    doc = message.document
    filename = doc.file_name or "uploaded_file"
    caption = message.caption or f"Пользователь прикрепил файл '{filename}'. Проанализируй его содержимое и выполни инструкции или предоставь разбор."

    status_msg = await message.answer(f"📥 *Загружаю и анализирую документ* `{filename}`...", parse_mode=ParseMode.MARKDOWN)

    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / filename
        await bot.download(doc, destination=doc_path)

        async def update_tg(text: str):
            await safe_edit(status_msg, text)

        stream_handler = TelegramStreamHandler(update_callback=update_tg)

        async def confirm_callback(confirm_id: str, description: str, tool_name: str):
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"🔐 **Запрос подтверждения:**\n\n{description}\n\n_Разрешить выполнение?_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirm_action_keyboard(confirm_id),
            )

        try:
            final_result = await agent_manager.execute_turn(
                chat_id=message.chat.id,
                prompt=caption,
                stream_handler=stream_handler,
                request_confirm_callback=confirm_callback,
                image_paths=[str(doc_path)],
            )
            if final_result and final_result.strip():
                if len(final_result) <= 3900:
                    await safe_edit(status_msg, final_result)
                else:
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                    for chunk in [final_result[i:i+3900] for i in range(0, len(final_result), 3900)]:
                        await safe_send(bot, message.chat.id, chunk)
            else:
                await safe_edit(status_msg, "⚠️ Агент завершил работу без ответа.")

            # Deliver any artifacts created during document execution
            await deliver_created_artifacts(bot, message.chat.id, stream_handler.created_files)

        except Exception as e:
            logger.exception("Document execution failed:")
            await safe_edit(status_msg, f"⚠️ Ошибка обработки документа: {str(e)}")
