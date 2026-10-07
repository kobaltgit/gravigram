import asyncio
from unittest.mock import MagicMock
import pytest
from src.agent.manager import AgentSessionManager, find_agy_executable
from src.config import settings

def test_find_agy_executable(monkeypatch, tmp_path):
    custom_exe = tmp_path / "mock_agy.exe"
    custom_exe.write_text("mock", encoding="utf-8")

    # When explicit agy_bin_path is set in settings
    monkeypatch.setattr(settings, "agy_bin_path", str(custom_exe))
    found = find_agy_executable()
    assert found == str(custom_exe)


def test_agent_session_manager_state():
    mgr = AgentSessionManager()

    # Initial state
    assert mgr.is_task_running(999) is False
    assert mgr.cancel_task(999) is False

    # Simulate active mock process
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mgr._active_processes[999] = mock_proc

    assert mgr.is_task_running(999) is True

    # Cancel task
    assert mgr.cancel_task(999) is True
    mock_proc.terminate.assert_called_once()

    # Simulate finished process
    mock_proc.returncode = 0
    assert mgr.is_task_running(999) is False


@pytest.mark.asyncio
async def test_resolve_confirmation_workflow():
    mgr = AgentSessionManager()
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    confirm_id = "test_conf_123"

    mgr._pending_confirmations[confirm_id] = future

    # Resolving with approved=True
    resolved = mgr.resolve_confirmation(confirm_id, approved=True)
    assert resolved is True
    assert future.done() is True
    assert future.result() is True

    # Double resolving should return False
    assert mgr.resolve_confirmation(confirm_id, approved=True) is False
    assert mgr.resolve_confirmation("non_existent_id", approved=False) is False
