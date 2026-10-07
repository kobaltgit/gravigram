import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from croniter import croniter

from src.config import settings
from src.database import (
    list_scheduled_tasks, get_scheduled_task,
    update_task_run_timestamps, toggle_scheduled_task,
    create_task_run, finish_task_run
)
from src.agent.manager import agent_manager
from src.agent.executor import TelegramStreamHandler

logger = logging.getLogger(__name__)

def parse_schedule_expression(expr: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parses a schedule expression (standard cron or friendly format like '09:00')
    and returns the next datetime execution.
    """
    now = base_time or datetime.now()
    expr = expr.strip()

    # Friendly format HH:MM (e.g. '09:00' -> '0 9 * * *')
    if ":" in expr and len(expr.split(":")) == 2 and not expr.startswith("interval"):
        parts = expr.split(":")
        try:
            h, m = int(parts[0]), int(parts[1])
            cron_expr = f"{m} {h} * * *"
            itr = croniter(cron_expr, now)
            return itr.get_next(datetime)
        except Exception:
            pass

    try:
        itr = croniter(expr, now)
        return itr.get_next(datetime)
    except Exception as e:
        logger.warning(f"Failed to parse cron expression '{expr}': {e}")
        return None

class AgentScheduler:
    """Background asynchronous scheduler that launches autonomous Antigravity turns."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._bot = None

    def set_bot(self, bot):
        self._bot = bot

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._scheduler_loop())
            logger.info("AgentScheduler background loop started.")

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("AgentScheduler stopped.")

    async def _scheduler_loop(self):
        """Checks active scheduled tasks every 30 seconds."""
        # Wait 5 seconds on startup
        await asyncio.sleep(5)
        while self._running:
            try:
                await self._check_and_run_due_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            await asyncio.sleep(30)

    async def _check_and_run_due_tasks(self):
        tasks = await list_scheduled_tasks(active_only=True)
        now = datetime.now()

        for t in tasks:
            next_run_str = t.get("next_run_at")
            next_run = None
            if next_run_str:
                try:
                    next_run = datetime.fromisoformat(next_run_str)
                except Exception:
                    pass

            # If next_run is not set yet, calculate it
            if not next_run:
                next_run = parse_schedule_expression(t["cron_expression"], now)
                if next_run:
                    await update_task_run_timestamps(
                        t["id"],
                        last_run=t.get("last_run_at") or now.isoformat(),
                        next_run=next_run.isoformat()
                    )
                continue

            # Check if task is due
            if now >= next_run:
                # Calculate future run
                future_run = parse_schedule_expression(t["cron_expression"], now)
                future_str = future_run.isoformat() if future_run else None
                await update_task_run_timestamps(
                    t["id"],
                    last_run=now.isoformat(),
                    next_run=future_str
                )
                
                # Execute agent task in background
                asyncio.create_task(self.run_task(t["id"]))

    async def run_task(self, task_id: int) -> bool:
        """Executes a scheduled task immediately with the Antigravity agent."""
        task_data = await get_scheduled_task(task_id)
        if not task_data:
            logger.warning(f"Task {task_id} not found")
            return False

        admin_id = settings.telegram_admin_id
        if not admin_id or not self._bot:
            logger.warning("Cannot run scheduled task: Telegram bot or admin_id is not available.")
            return False

        title = task_data["title"]
        prompt = task_data["prompt"]
        project_name = task_data.get("project_name") or "По умолчанию"

        logger.info(f"⏰ Starting scheduled agent task #{task_id}: '{title}'...")
        start_time = time.time()
        run_id = await create_task_run(task_id)

        status_msg = None
        try:
            status_msg = await self._bot.send_message(
                chat_id=admin_id,
                text=f"⏰ **[Плановое задание]** `{title}`\n📁 Проект: `{project_name}`\n\n💭 *ИИ-агент просыпается и приступает к задаче...*",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send initial schedule message: {e}")

        async def update_tg(text: str):
            if status_msg:
                try:
                    await status_msg.edit_text(
                        f"⏰ **[Плановое задание]** `{title}`\n\n{text}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    try:
                        await status_msg.edit_text(f"⏰ **[Плановое задание]** `{title}`\n\n{text}")
                    except Exception:
                        pass

        stream_handler = TelegramStreamHandler(update_callback=update_tg)

        try:
            task_prompt = (
                f"Выполни задание: {prompt}\n"
                "Запусти нужные команды, собери данные и выдай подробный и структурированный отчет на русском языке. "
                "Не используй инструмент schedule, выполни проверку прямо сейчас."
            )
            final_result = await agent_manager.execute_turn(
                chat_id=admin_id,
                prompt=task_prompt,
                stream_handler=stream_handler,
                force_new_conversation=True
            )

            execution_time = time.time() - start_time
            await finish_task_run(
                run_id=run_id,
                status="success",
                execution_time_seconds=execution_time,
                output_preview=final_result or ""
            )

            if final_result and final_result.strip():
                from src.bot.formatter import markdown_to_telegram_html
                header = f"✅ **[Отчёт по плановому заданию]** `{title}`\n\n"
                full_text = header + final_result
                formatted_full = markdown_to_telegram_html(full_text)
                if len(formatted_full) <= 3900:
                    try:
                        await status_msg.edit_text(formatted_full, parse_mode="HTML", disable_web_page_preview=True)
                    except Exception:
                        await status_msg.edit_text(full_text, parse_mode=None, disable_web_page_preview=True)
                else:
                    try:
                        await status_msg.edit_text(f"✅ <b>[Отчёт по плановому заданию]</b> <code>{title}</code> (отчёт ниже):", parse_mode="HTML")
                    except Exception:
                        await status_msg.edit_text(f"✅ [Отчёт по плановому заданию] {title} (отчёт ниже):", parse_mode=None)
                    # Split and send
                    for i in range(0, len(final_result), 3900):
                        part = final_result[i:i+3900]
                        formatted_part = markdown_to_telegram_html(part)
                        try:
                            await self._bot.send_message(chat_id=admin_id, text=formatted_part, parse_mode="HTML", disable_web_page_preview=True)
                        except Exception:
                            await self._bot.send_message(chat_id=admin_id, text=part, parse_mode=None, disable_web_page_preview=True)

            # Auto-deliver any artifacts generated during task execution
            if stream_handler.created_files and self._bot:
                from aiogram.types import FSInputFile
                for fpath in stream_handler.created_files:
                    p = Path(fpath)
                    if p.exists() and p.is_file() and p.stat().st_size > 0:
                        try:
                            doc = FSInputFile(str(p), filename=p.name)
                            await self._bot.send_document(
                                chat_id=admin_id,
                                document=doc,
                                caption=f"📄 **Создан файл (плановое задание):** `{p.name}`",
                                parse_mode="Markdown"
                            )
                        except Exception as doc_err:
                            logger.warning(f"Failed to deliver scheduled task artifact: {doc_err}")

            logger.info(f"✅ Scheduled agent task #{task_id} completed successfully in {execution_time:.2f}s.")
            return True

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing scheduled task #{task_id}: {e}", exc_info=True)
            await finish_task_run(
                run_id=run_id,
                status="failed",
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
            if status_msg:
                try:
                    await status_msg.edit_text(
                        f"❌ <b>Ошибка при выполнении планового задания:</b> <code>{title}</code>\n\n<code>{str(e)}</code>",
                        parse_mode="HTML"
                    )
                except Exception:
                    await status_msg.edit_text(
                        f"❌ Ошибка при выполнении планового задания: {title}\n\n{str(e)}",
                        parse_mode=None
                    )
                    pass
            return False

agent_scheduler = AgentScheduler()
