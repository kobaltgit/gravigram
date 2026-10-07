import os
import logging
import asyncio
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading local Whisper model (base)...")
        # CPU with int8 quantization for ultra-fast low-memory local transcription
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Local Whisper model loaded successfully.")
    return _whisper_model

async def transcribe_audio_file(audio_path: str) -> Optional[str]:
    """Transcribes an audio file (e.g. .ogg, .mp3, .wav) to text locally without any API keys."""
    if not os.path.exists(audio_path):
        return None

    def _sync_transcribe():
        model = get_whisper_model()
        segments, info = model.transcribe(audio_path, beam_size=5, language=None)
        text_parts = [segment.text.strip() for segment in segments]
        return " ".join(text_parts).strip()

    try:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, _sync_transcribe)
        return text if text else None
    except Exception as e:
        logger.error(f"Local Whisper transcription error: {e}", exc_info=True)
        return None
