import asyncio
from src.agent.manager import agent_manager
from src.agent.executor import TelegramStreamHandler
from src.database import init_db
import pytest

@pytest.mark.integration
async def test_disk_space_query():
    print("Testing disk space query via Antigravity CLI...")
    await init_db()

    updates = []
    async def print_update(text):
        updates.append(text)
        print(f"[LIVE STREAM]: {text}")

    handler = TelegramStreamHandler(update_callback=print_update)

    response = await agent_manager.execute_turn(
        chat_id=12345,
        prompt="ты можешь сказать сколько свободного места на диске c?",
        stream_handler=handler
    )
    print("\n--- FINAL DELIVERED TEXT ---")
    print(response)
    print("----------------------------")
    assert len(response.strip()) > 0, "Response must not be empty"
    print("[SUCCESS] Disk space query returned valid response!")

if __name__ == "__main__":
    asyncio.run(test_disk_space_query())
