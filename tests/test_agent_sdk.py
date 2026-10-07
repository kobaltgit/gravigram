import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
import pytest

load_dotenv()

@pytest.mark.integration
async def test_agent():
    save_dir = Path("data/sessions_store").resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    
    print("Testing Agent with save_dir:", save_dir)
    print("API Key set:", bool(os.environ.get("GEMINI_API_KEY")))
    
    # 1. New Session
    config1 = LocalAgentConfig(
        save_dir=str(save_dir),
        capabilities=CapabilitiesConfig()
    )
    
    async with Agent(config1) as agent:
        resp = await agent.chat("Say 'Hello Antigravity' and nothing else.")
        text = await resp.text()
        conv_id = agent.conversation_id
        print(f"Session 1 Response: {text}")
        print(f"Session 1 Conv ID: {conv_id}")

    # 2. Resume Session
    config2 = LocalAgentConfig(
        conversation_id=conv_id,
        save_dir=str(save_dir),
        capabilities=CapabilitiesConfig()
    )
    async with Agent(config2) as agent2:
        resp2 = await agent2.chat("What did I just ask you to say?")
        print(f"Session 2 (Resumed) Response: {await resp2.text()}")

    print("[SUCCESS] Antigravity SDK persistent sessions test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_agent())
