import asyncio
import pytest
from src.agent.executor import TelegramStreamHandler

@pytest.mark.asyncio
async def test_stream_handler_thoughts_and_rendering():
    updates = []
    async def mock_callback(msg: str):
        updates.append(msg)

    handler = TelegramStreamHandler(update_callback=mock_callback, throttle_interval=0.01)

    # Initially empty
    assert "Выполняю задачу" in handler.render_message()

    # Append thoughts
    handler.on_thought("Analyzing requirements...")
    handler.on_thought("Checking database schema...")
    assert "Analyzing requirements" in handler.current_thoughts
    assert "Checking database schema" in handler.current_thoughts

    # Tool execution
    handler.on_tool_start("run_command", {"CommandLine": "git status --porcelain"})
    msg = handler.render_message()
    assert "git status" in msg

    handler.on_tool_end("run_command")
    assert handler.current_tool == ""

    # Text chunk
    handler.on_text_chunk("Done! Everything is up to date.")
    final_render = handler.render_message()
    assert "Done! Everything is up to date." in final_render

    # Finish
    result = await handler.finish()
    assert result == "Done! Everything is up to date."
    assert len(updates) > 0


@pytest.mark.asyncio
async def test_stream_handler_tool_args_formatting():
    async def mock_cb(msg): pass
    handler = TelegramStreamHandler(update_callback=mock_cb)

    # Long command truncated
    long_cmd = "python " + "a" * 100
    handler.on_tool_start("run_command", {"CommandLine": long_cmd})
    assert "..." in handler.current_tool

    # Write file tool
    handler.on_tool_start("write_to_file", {"TargetFile": "/path/to/script.py"})
    assert "/path/to/script.py" in handler.current_tool

    # File created tracking
    handler.on_file_created("/path/to/script.py")
    handler.on_file_created("/path/to/script.py")  # duplicate
    assert len(handler.created_files) == 1
