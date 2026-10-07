import os
import re
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def clean_text_for_speech(text: str) -> str:
    """
    Cleans markdown formatting, code blocks, URLs, and emojis,
    while preserving natural Russian text and English technical terms (e.g. Proxmox, Nginx, Docker, CT 107).
    """
    if not text:
        return ""

    # 1. Remove triple backtick code blocks ```...```
    cleaned = re.sub(r'```[\s\S]*?```', '', text)
    
    # 2. Remove inline code `...`
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # 3. Remove markdown links [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # 4. Remove bold/italics symbols, brackets, bullets
    cleaned = re.sub(r'[*_#~>|`\-=+•●►\(\)\[\]\{\}]', ' ', cleaned)

    # 5. Remove URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)

    # 6. Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # 7. Take concise summary (up to ~300 chars) for quick, pleasant spoken delivery
    if len(cleaned) > 300:
        cut_point = cleaned[:300].rfind('.')
        if cut_point > 100:
            cleaned = cleaned[:cut_point + 1]
        else:
            cleaned = cleaned[:297] + "..."

    return cleaned

async def text_to_speech(text: str, voice: str = "ru-RU-DmitryNeural", rate: str = "+20%") -> Tuple[Optional[str], Optional[str]]:
    """
    Synthesizes speech using Microsoft Neural Voice (Dmitry Neural).
    - Speed: rate="+20%" (brisk, natural tempo).
    - Bilingual: Accurately pronounces English terms (Proxmox, Nginx, Docker, SQLite, etc.) and Russian narrative.
    Returns: (ogg_path, mp3_path)
    """
    clean = clean_text_for_speech(text)
    if not clean or len(clean) < 2:
        return None, None

    temp_dir = tempfile.gettempdir()
    base_hash = hash(clean) & 0xFFFFFFFF
    mp3_path = os.path.join(temp_dir, f"speech_{os.getpid()}_{base_hash}.mp3")
    ogg_path = os.path.join(temp_dir, f"voice_{os.getpid()}_{base_hash}.ogg")

    generated = False

    # 1. Primary: Microsoft Edge Neural Voice (Dmitry Neural at +20% speed)
    try:
        import edge_tts
        comm = edge_tts.Communicate(clean, voice=voice, rate=rate)
        await asyncio.wait_for(comm.save(mp3_path), timeout=25.0)
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 200:
            generated = True
            logger.info(f"Generated bilingual speech with Microsoft Dmitry Neural (+20%) for {len(clean)} chars.")
    except Exception as e:
        logger.warning(f"Edge TTS synthesis error ({e}), trying Google TTS fallback...")

    # 2. Fallback: Google TTS
    if not generated:
        try:
            from gtts import gTTS
            def _sync_gtts():
                tts = gTTS(text=clean, lang="ru", slow=False)
                tts.save(mp3_path)

            loop = asyncio.get_running_loop()
            await asyncio.wait_for(loop.run_in_executor(None, _sync_gtts), timeout=20.0)
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 200:
                generated = True
                logger.info("Generated fallback speech with Google TTS.")
        except Exception as e:
            logger.error(f"Fallback Google TTS failed: {e}", exc_info=True)

    if not generated or not os.path.exists(mp3_path):
        return None, None

    # Convert to OGG Opus for native Telegram voice bubbles
    try:
        cmd_ogg = [
            "ffmpeg", "-y",
            "-i", mp3_path,
            "-c:a", "libopus",
            "-b:a", "32k",
            "-v", "error",
            ogg_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_ogg,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
    except Exception as e:
        logger.warning(f"Opus conversion warning: {e}")

    final_ogg = ogg_path if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0 else None
    final_mp3 = mp3_path if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0 else None

    return final_ogg, final_mp3
