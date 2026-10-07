import asyncio
import time
import logging
from typing import Callable, Awaitable, Optional, Any

logger = logging.getLogger(__name__)

class TelegramStreamHandler:
    """Manages throttled updates to Telegram messages during AI streaming."""
    
    def __init__(self, update_callback: Callable[[str], Awaitable[None]], throttle_interval: float = 1.0):
        self.update_callback = update_callback
        self.throttle_interval = throttle_interval
        self.last_update_time: float = 0.0
        self.current_thoughts: str = ""
        self.current_tool: str = ""
        self.current_text: str = ""
        self._is_dirty = False
        self._running = True
        self.created_files = []

    def on_file_created(self, file_path: str):
        if file_path and file_path not in self.created_files:
            self.created_files.append(file_path)

    def on_thought(self, thought: str):
        # Accumulate thoughts for complete transparency
        if thought.strip():
            if self.current_thoughts:
                self.current_thoughts += "\n" + thought.strip()
            else:
                self.current_thoughts = thought.strip()
            self._is_dirty = True

    def on_tool_start(self, tool_name: str, tool_args: Any):
        if tool_name == "run_command":
            cmd = tool_args.get("CommandLine", "") if isinstance(tool_args, dict) else str(tool_args)
            if len(cmd) > 80:
                cmd = cmd[:77] + "..."
            self.current_tool = f"⚡ *Запуск команды:*\n`{cmd}`"
        elif tool_name in ("write_to_file", "replace_file_content"):
            file_path = tool_args.get("TargetFile", "") if isinstance(tool_args, dict) else ""
            self.current_tool = f"📝 *Правка файла:*\n`{file_path}`"
        else:
            self.current_tool = f"🛠 *Инструмент:* `{tool_name}`"
        self._is_dirty = True

    def on_tool_end(self, tool_name: str):
        self.current_tool = ""
        self._is_dirty = True

    def on_text_chunk(self, chunk: str):
        self.current_text += chunk
        self._is_dirty = True

    def render_message(self) -> str:
        parts = []
        if self.current_tool:
            parts.append(self.current_tool)
        elif self.current_thoughts and not self.current_text:
            short_thoughts = self.current_thoughts[-3500:] if len(self.current_thoughts) > 3500 else self.current_thoughts
            parts.append(f"💭 _{short_thoughts}_")
        
        if self.current_text:
            parts.append(self.current_text)
        elif not parts:
            parts.append("💭 *Выполняю задачу...*")

        rendered = "\n\n".join(parts)
        return rendered[:3900]

    async def maybe_push_update(self, force: bool = False):
        now = time.monotonic()
        if (self._is_dirty and (now - self.last_update_time >= self.throttle_interval)) or force:
            self.last_update_time = now
            self._is_dirty = False
            try:
                text = self.render_message()
                await self.update_callback(text)
            except Exception as e:
                logger.debug(f"Throttled edit failed: {e}")

    async def finish(self) -> str:
        self._running = False
        self.current_tool = ""
        self.current_thoughts = ""
        await self.maybe_push_update(force=True)
        return self.current_text
