@echo off
cd /d "D:\Projects\active\antigravity_bot"
call "D:\Projects\active\antigravity_bot\venv\Scripts\activate.bat"
python run.py >> "D:\Projects\active\antigravity_bot\bot.log" 2>&1
