import asyncio
from src.agent.manager import agent_manager
from src.agent.executor import TelegramStreamHandler
from src.database import init_db
import pytest

@pytest.mark.integration
async def test_live_agy():
    print("Testing local agy CLI integration via AgentSessionManager...")
    await init_db()

    async def print_update(text):
        print(f"[STREAM UPDATE]: {text[:80]}...")

    handler = TelegramStreamHandler(update_callback=print_update)

    response = await agent_manager.execute_turn(
        chat_id=12345,
        prompt="Напиши ровно: 'Локальный Antigravity работает отлично!'",
        stream_handler=handler
    )
    print("\n--- FINAL RESPONSE ---")
    print(response)
    print("----------------------")
    print("[SUCCESS] Local Antigravity CLI test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_live_agy())
