import os
import sys
import json
import asyncio
import logging
import shutil
import uuid
import platform
from pathlib import Path
from typing import Dict, Optional, Callable, Awaitable, Any

from src.config import settings
from src.agent.executor import TelegramStreamHandler
from src.database import (
    get_active_project, get_active_session, create_session, get_setting,
    add_session_message, get_session_messages
)

logger = logging.getLogger(__name__)

def find_agy_executable() -> str:
    """Locates the local agy executable on the system across platforms."""
    # 1. Explicit path from config / .env
    if settings.agy_bin_path:
        custom_cand = Path(settings.agy_bin_path)
        if custom_cand.exists():
            return str(custom_cand)

    # 2. System PATH
    exe = shutil.which("agy") or shutil.which("agy.exe")
    if exe:
        return exe

    # 3. Standard Linux / macOS candidate paths
    home = Path.home()
    linux_candidates = [
        home / ".local" / "bin" / "agy",
        home / ".agy" / "bin" / "agy",
        Path("/usr/local/bin/agy"),
        Path("/usr/bin/agy"),
    ]
    for cand in linux_candidates:
        if cand.exists():
            return str(cand)

    # 4. Standard Windows candidate paths
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        win_cand = Path(local_app_data) / "agy" / "bin" / "agy.exe"
        if win_cand.exists():
            return str(win_cand)

    return "agy"


# Timeout for waiting for user confirmation (seconds)
CONFIRMATION_TIMEOUT = 120


class AgentSessionManager:
    """Manages active Antigravity CLI sessions on the local computer."""
    
    def __init__(self):
        self._active_processes: Dict[int, asyncio.subprocess.Process] = {}
        self._pending_confirmations: Dict[str, asyncio.Future] = {}
        self.agy_path = find_agy_executable()
        logger.info(f"Using Antigravity CLI binary at: {self.agy_path}")

    def find_agy(self) -> str:
        return self.agy_path

    def is_task_running(self, chat_id: int) -> bool:
        proc = self._active_processes.get(chat_id)
        return proc is not None and proc.returncode is None

    def cancel_task(self, chat_id: int) -> bool:
        proc = self._active_processes.get(chat_id)
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                return True
            except Exception as e:
                logger.warning(f"Error terminating agy process: {e}")
        return False

    def resolve_confirmation(self, confirm_id: str, approved: bool) -> bool:
        """Resolves a pending confirmation request from the user."""
        future = self._pending_confirmations.pop(confirm_id, None)
        if future and not future.done():
            future.set_result(approved)
            return True
        return False

    async def _handle_permission_request(
        self,
        process: asyncio.subprocess.Process,
        tool_name: str,
        tool_params: dict,
        stream_handler: TelegramStreamHandler,
        request_confirm_callback: Optional[Callable[[str, str, str], Awaitable[None]]],
    ) -> bool:
        """
        Handles a permission request from agy when running without --dangerously-skip-permissions.
        
        Creates an asyncio.Future, sends a confirmation keyboard to the user via callback,
        waits for the user's decision, and writes 'y' or 'n' to agy's stdin.
        
        Returns True if approved, False if denied or timed out.
        """
        confirm_id = str(uuid.uuid4())[:8]
        
        # Format tool info for the user
        params_str = ""
        if tool_params:
            for k, v in list(tool_params.items())[:5]:
                val = str(v)[:100]
                params_str += f"\n  • `{k}`: `{val}`"
        
        description = f"🔧 **{tool_name}**{params_str}"
        
        # Create future for this confirmation
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_confirmations[confirm_id] = future
        
        # Send confirmation keyboard to user
        if request_confirm_callback:
            await request_confirm_callback(confirm_id, description, tool_name)
        else:
            logger.warning(f"No confirm callback set, auto-denying permission for {tool_name}")
            self._pending_confirmations.pop(confirm_id, None)
            if process.stdin and not process.stdin.is_closing():
                try:
                    process.stdin.write(b"n\n")
                    await process.stdin.drain()
                except Exception as e:
                    logger.warning(f"Error writing auto-deny to stdin: {e}")
            return False
        
        # Wait for user response with timeout
        try:
            approved = await asyncio.wait_for(future, timeout=CONFIRMATION_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending_confirmations.pop(confirm_id, None)
            stream_handler.on_thought(f"⏰ Таймаут подтверждения для {tool_name} ({CONFIRMATION_TIMEOUT}с)")
            await stream_handler.maybe_push_update(force=True)
            approved = False
        
        # Write response to agy's stdin
        if process.stdin and not process.stdin.is_closing():
            try:
                response = "y\n" if approved else "n\n"
                process.stdin.write(response.encode("utf-8"))
                await process.stdin.drain()
                logger.info(f"Permission {'approved' if approved else 'denied'} for {tool_name} (confirm_id={confirm_id})")
            except Exception as e:
                logger.warning(f"Error writing permission response to stdin: {e}")
        
        return approved

    async def execute_turn(
        self,
        chat_id: int,
        prompt: str,
        stream_handler: TelegramStreamHandler,
        request_confirm_callback: Optional[Callable[[str, str, str], Awaitable[None]]] = None,
        image_paths: Optional[list] = None,
        force_new_conversation: bool = False,
    ) -> str:
        """Executes a turn via the local Antigravity CLI (agy), streaming output to Telegram."""
        
        # 1. Resolve active project and active session
        project = await get_active_project()
        workspace_path = project["path"] if project else settings.default_workspace_path
        Path(workspace_path).mkdir(parents=True, exist_ok=True)

        session = await get_active_session(project["id"] if project else None)
        if not session:
            session = await create_session(
                project_id=project["id"] if project else 1,
                title=prompt[:30] + ("..." if len(prompt) > 30 else ""),
                conversation_id=str(uuid.uuid4()),
                make_active=True
            )
        session_id = session["id"]

        # Build clean dialogue context (Sliding Window Memory)
        dialogue_context = ""
        if session_id and not force_new_conversation:
            recent_msgs = await get_session_messages(session_id, limit=6)
            if recent_msgs:
                dialogue_lines = []
                for m in recent_msgs:
                    role_label = "👤 Пользователь" if m["role"] == "user" else "🤖 Ассистент"
                    dialogue_lines.append(f"{role_label}: {m['content']}")
                dialogue_context = (
                    "[История диалога в этой сессии]:\n" +
                    "\n".join(dialogue_lines) +
                    "\n\n[Текущий ответ/запрос пользователя]:\n"
                )

        current_model = await get_setting("model", "")

        # Read confirm_mode from DB to decide whether to skip permissions
        confirm_mode_str = await get_setting("confirm_mode", "false")
        confirm_mode = confirm_mode_str.lower() == "true"

        # Provide infrastructure hints dynamically or from custom settings
        if settings.system_context_hint:
            context_prefix = f"[Системный контекст: {settings.system_context_hint.strip()}. Отвечай кратко и структурированно на русском языке.]\n"
        else:
            context_prefix = (
                f"[Системный контекст: Хост: {platform.node()}, ОС: {platform.system()} {platform.release()} ({platform.machine()}). "
                f"Отвечай кратко и структурированно на русском языке.]\n"
            )

        if confirm_mode:
            context_prefix += (
                "[РЕЖИМ БЕЗОПАСНОСТИ: Включен режим подтверждения (/confirm). "
                "Информационные команды (проверка диска, чтение файлов, статус служб) выполняй сразу. "
                "Перед выполнением любых изменяющих или потенциально опасных команд (удаление файлов, остановка контейнеров, модификация системных настроек) "
                "ты ОБЯЗАН сначала описать пользователю планируемое действие и команду и дождаться его подтверждения.]\n\n"
            )
        else:
            context_prefix += "[РЕЖИМ: Полностью автономный (/auto). Выполняй задачи до конца самостоятельно.]\n\n"

        full_prompt = context_prefix + dialogue_context + prompt

        # Handle image paths: copy to workspace so agy can access them
        extra_add_dirs = []
        if image_paths:
            uploads_dir = Path(workspace_path) / ".agy_uploads"
            uploads_dir.mkdir(exist_ok=True)
            accessible_paths = []
            for img_path in image_paths:
                src = Path(img_path)
                if src.exists():
                    dest = uploads_dir / src.name
                    shutil.copy2(str(src), str(dest))
                    accessible_paths.append(str(dest))
                else:
                    accessible_paths.append(img_path)
            
            if accessible_paths:
                full_prompt += "\n\n[Приложенные изображения: " + ", ".join(accessible_paths) + "]"
                extra_add_dirs.append(str(uploads_dir))

        # 2. Build agy CLI command (without bloated raw multi-turn JSONL transcript)
        cmd = [
            self.agy_path,
            "-p", full_prompt,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
            "--add-dir", workspace_path,
        ]

        # Add extra directories for image access
        for d in extra_add_dirs:
            cmd.extend(["--add-dir", d])

        if current_model and current_model != "gemini-3.7-flash":
            cmd.extend(["--model", current_model])

        stream_handler.on_thought("Инициализирую задачу...")
        await stream_handler.maybe_push_update(force=True)

        logger.info(f"Executing: {' '.join(cmd)} (cwd={workspace_path}, confirm_mode={confirm_mode})")

        # 3. Launch subprocess with 32MB stream buffer limit (prevents LimitOverrunError on large tool outputs)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if confirm_mode else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_path,
            limit=32 * 1024 * 1024,  # 32 MB buffer for large tool outputs/file scans
        )
        self._active_processes[chat_id] = process

        full_response = ""

        try:
            while True:
                try:
                    line = await process.stdout.readline()
                except (ValueError, Exception) as stream_err:
                    logger.warning(f"Stdout stream read error (recovering): {stream_err}")
                    raw_data = await process.stdout.read(65536)
                    if not raw_data:
                        break
                    line = raw_data

                if not line:
                    break
                
                decoded_line = line.decode("utf-8", errors="replace").strip() if isinstance(line, bytes) else str(line).strip()
                if not decoded_line:
                    continue

                try:
                    event_data = json.loads(decoded_line)
                    event_type = event_data.get("event")

                    if event_type == "init":
                        pass

                    elif event_type == "step_update":
                        step = event_data.get("step_update", {})
                        step_type = step.get("step_type")
                        state = step.get("state")

                        if step_type == "agent_response":
                            delta = step.get("text_delta", "")
                            if delta:
                                stream_handler.on_text_chunk(delta)
                                await stream_handler.maybe_push_update()

                        elif step_type in ("tool", "tool_call"):
                            tool_name = step.get("tool_name", "")
                            tool_info = step.get("tool_info", {})

                            # Handle permission requests in confirm_mode (only on ACTIVE phase)
                            if confirm_mode and tool_name in ("ask_permission", "ask_custom_permission") and state == "ACTIVE":
                                params = tool_info.get("parameters", {}) if isinstance(tool_info, dict) else {}
                                # Extract the actual tool being requested
                                requested_tool = params.get("tool_name", tool_name)
                                stream_handler.on_thought(f"🔐 Запрашиваю подтверждение: {requested_tool}")
                                await stream_handler.maybe_push_update(force=True)
                                await self._handle_permission_request(
                                    process, requested_tool, params,
                                    stream_handler, request_confirm_callback
                                )
                            elif state == "ACTIVE":
                                params = tool_info.get("parameters", {}) if isinstance(tool_info, dict) else {}
                                stream_handler.on_tool_start(tool_name, params)
                                await stream_handler.maybe_push_update(force=True)
                            elif state == "DONE":
                                stream_handler.on_tool_end(tool_name)
                                if tool_name in ("write_to_file", "create_file", "generate_image"):
                                    params = tool_info.get("parameters", {}) if isinstance(tool_info, dict) else {}
                                    target = params.get("TargetFile") or params.get("file_path") or params.get("path")
                                    if target:
                                        stream_handler.on_file_created(str(target))
                                await stream_handler.maybe_push_update(force=True)

                        elif step_type == "thought":
                            thought = step.get("thought", "")
                            if thought:
                                stream_handler.on_thought(thought)
                                await stream_handler.maybe_push_update()

                        elif step_type == "error_message":
                            err = step.get("message", "") or step.get("text", "") or ""
                            if err:
                                stream_handler.on_text_chunk(f"\n⚠️ {err}\n")
                                await stream_handler.maybe_push_update()

                    elif event_type == "result":
                        res = event_data.get("result", {})
                        resp = res.get("response", "")
                        err = res.get("error", "")
                        status = res.get("status", "")

                        if err:
                            logger.warning(f"Antigravity CLI result warning/error: {err} (status={status})")

                        if resp and not stream_handler.current_text:
                            stream_handler.on_text_chunk(resp)
                        
                        # Only show error to user if no text response was produced at all
                        if not stream_handler.current_text and err:
                            stream_handler.on_text_chunk(f"⚠️ {err}")
                            await stream_handler.maybe_push_update(force=True)

                        full_response = stream_handler.current_text or resp or (f"⚠️ {err}" if err else "")

                except json.JSONDecodeError:
                    if "error" in decoded_line.lower() or "traceback" in decoded_line.lower():
                        stream_handler.on_text_chunk(decoded_line + "\n")
                        await stream_handler.maybe_push_update()

            await process.wait()

            if process.returncode != 0 and not full_response and not stream_handler.current_text:
                stderr_data = await process.stderr.read() if process.stderr else b""
                err_text = stderr_data.decode("utf-8", errors="replace").strip()
                if err_text:
                    stream_handler.on_text_chunk(f"\n\n⚠️ Ошибка Antigravity (код {process.returncode}):\n`{err_text}`")

            final_text = await stream_handler.finish()
            if not final_text and full_response:
                final_text = full_response

            # Save clean dialogue turn to session history
            if session_id and final_text and not final_text.startswith("⚠️"):
                try:
                    await add_session_message(session_id, "user", prompt)
                    await add_session_message(session_id, "assistant", final_text)
                except Exception as e:
                    logger.warning(f"Failed to persist session dialogue: {e}")

            return final_text

        except asyncio.CancelledError:
            self.cancel_task(chat_id)
            stream_handler.on_text_chunk("\n\n⏹ *Задача прервана пользователем.*")
            await stream_handler.finish()
            raise
        finally:
            self._active_processes.pop(chat_id, None)
            # Clean up any remaining pending confirmations for this session
            for cid in list(self._pending_confirmations.keys()):
                future = self._pending_confirmations.pop(cid, None)
                if future and not future.done():
                    future.cancel()

agent_manager = AgentSessionManager()
